from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.repository import Repository
from app.models.pull_request import PullRequest
from app.models.review import Review
from app.services.repository_service import sync_repositories, toggle_repository
from app.core.config import settings

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.get("")
async def list_repositories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repos = db.query(Repository).filter(Repository.user_id == current_user.id).all()
    return [_repo_to_dict(r, db) for r in repos]


@router.post("/sync")
async def sync_repos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repos = await sync_repositories(current_user, db)
    return {"synced": len(repos), "repositories": [_repo_to_dict(r, db) for r in repos]}


@router.patch("/{repo_id}/toggle")
async def toggle_repo(
    repo_id: str,
    body: dict,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = db.query(Repository).filter(
        Repository.id == repo_id, Repository.user_id == current_user.id
    ).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    enable = body.get("enabled", False)
    base_url = settings.WEBHOOK_BASE_URL or str(request.base_url).rstrip("/")
    repo = await toggle_repository(repo, current_user, enable, base_url, db)
    return _repo_to_dict(repo, db)


@router.get("/{repo_id}/pull-requests")
async def list_pull_requests(
    repo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = db.query(Repository).filter(
        Repository.id == repo_id, Repository.user_id == current_user.id
    ).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    prs = (
        db.query(PullRequest)
        .filter(PullRequest.repository_id == repo_id)
        .order_by(PullRequest.created_at.desc())
        .limit(50)
        .all()
    )
    return [_pr_to_dict(pr, db) for pr in prs]


def _repo_to_dict(repo: Repository, db: Session) -> dict:
    pr_count = db.query(PullRequest).filter(PullRequest.repository_id == repo.id).count()
    return {
        "id": repo.id,
        "repo_name": repo.repo_name,
        "repo_full_name": repo.repo_full_name,
        "repo_url": repo.repo_url,
        "description": repo.description,
        "language": repo.language,
        "is_private": repo.is_private,
        "enabled": repo.enabled,
        "pr_count": pr_count,
        "created_at": repo.created_at.isoformat(),
    }


def _pr_to_dict(pr: PullRequest, db: Session) -> dict:
    latest_review = (
        db.query(Review)
        .filter(Review.pull_request_id == pr.id)
        .order_by(Review.created_at.desc())
        .first()
    )
    return {
        "id": pr.id,
        "pr_number": pr.pr_number,
        "title": pr.title,
        "author": pr.author,
        "author_avatar": pr.author_avatar,
        "pr_url": pr.pr_url,
        "status": pr.status.value,
        "score": latest_review.score if latest_review else None,
        "total_issues": latest_review.total_issues if latest_review else None,
        "created_at": pr.created_at.isoformat(),
    }
