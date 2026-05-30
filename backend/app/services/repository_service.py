from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.repository import Repository
from app.models.user import User
from app.github.client import GitHubClient
from app.core.config import settings
from app.core.logging import logger
from typing import Optional


async def sync_repositories(user: User, db: Session) -> list[Repository]:
    gh = GitHubClient(user.github_access_token)
    gh_repos = await gh.list_repositories(per_page=100)

    # Only keep repos owned by this user (not collaborator/org repos)
    owned_ids = set()
    synced = []

    for gh_repo in gh_repos:
        # Skip repos where the owner is not this user
        if gh_repo.get("owner", {}).get("login") != user.github_username:
            continue

        owned_ids.add(gh_repo["id"])
        repo = db.query(Repository).filter(
            Repository.github_repo_id == gh_repo["id"]
        ).first()

        if repo:
            repo.repo_name = gh_repo["name"]
            repo.repo_full_name = gh_repo["full_name"]
            repo.repo_url = gh_repo["html_url"]
            repo.description = gh_repo.get("description")
            repo.language = gh_repo.get("language")
            repo.is_private = gh_repo["private"]
        else:
            repo = Repository(
                user_id=user.id,
                github_repo_id=gh_repo["id"],
                repo_name=gh_repo["name"],
                repo_full_name=gh_repo["full_name"],
                repo_url=gh_repo["html_url"],
                description=gh_repo.get("description"),
                language=gh_repo.get("language"),
                is_private=gh_repo["private"],
                enabled=False,
            )
            db.add(repo)

        synced.append(repo)

    # Remove any previously synced repos that are no longer owned by this user
    if owned_ids:
        db.query(Repository).filter(
            Repository.user_id == user.id,
            Repository.github_repo_id.notin_(owned_ids),
        ).delete(synchronize_session=False)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.error("repo_sync_integrity_error", user_id=user.id)

    return synced


async def toggle_repository(
    repo: Repository, user: User, enable: bool, webhook_base_url: str, db: Session
) -> Repository:
    gh = GitHubClient(user.github_access_token)
    owner, repo_name = repo.repo_full_name.split("/", 1)

    if enable and not repo.webhook_id:
        webhook_url = f"{webhook_base_url}/api/v1/webhooks/github"
        try:
            hook = await gh.create_webhook(owner, repo_name, webhook_url)
            repo.webhook_id = hook["id"]
        except Exception as e:
            logger.error("webhook_create_failed", error=str(e), repo=repo.repo_full_name)

    elif not enable and repo.webhook_id:
        try:
            await gh.delete_webhook(owner, repo_name, repo.webhook_id)
            repo.webhook_id = None
        except Exception as e:
            logger.warning("webhook_delete_failed", error=str(e), repo=repo.repo_full_name)

    repo.enabled = enable
    db.commit()
    db.refresh(repo)
    return repo
