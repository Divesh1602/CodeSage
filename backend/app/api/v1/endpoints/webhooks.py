import json
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.github.client import verify_webhook_signature
from app.models.repository import Repository
from app.models.pull_request import PullRequest, PRStatus
from app.workers.review_tasks import process_review
from app.core.logging import logger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    payload_bytes = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not verify_webhook_signature(payload_bytes, signature):
        logger.warning("webhook_signature_invalid", signature=signature[:20])
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    event_type = request.headers.get("X-GitHub-Event", "")
    if event_type != "pull_request":
        return {"status": "ignored", "event": event_type}

    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    action = payload.get("action", "")
    if action not in ("opened", "synchronize", "reopened"):
        return {"status": "ignored", "action": action}

    gh_pr = payload.get("pull_request", {})
    gh_repo = payload.get("repository", {})
    repo_id = gh_repo.get("id")

    repo = db.query(Repository).filter(
        Repository.github_repo_id == repo_id,
        Repository.enabled == True,
    ).first()

    if not repo:
        logger.info("webhook_repo_not_enabled", github_repo_id=repo_id)
        return {"status": "ignored", "reason": "repo not enabled"}

    pr_number = gh_pr.get("number")
    existing_pr = db.query(PullRequest).filter(
        PullRequest.repository_id == repo.id,
        PullRequest.pr_number == pr_number,
    ).first()

    if existing_pr and action == "opened":
        return {"status": "ignored", "reason": "pr already exists"}

    if not existing_pr:
        pr = PullRequest(
            repository_id=repo.id,
            pr_number=pr_number,
            title=gh_pr.get("title", "Untitled PR"),
            author=gh_pr.get("user", {}).get("login", "unknown"),
            author_avatar=gh_pr.get("user", {}).get("avatar_url"),
            pr_url=gh_pr.get("html_url"),
            base_branch=gh_pr.get("base", {}).get("ref"),
            head_branch=gh_pr.get("head", {}).get("ref"),
            status=PRStatus.PENDING,
        )
        db.add(pr)
        db.commit()
        db.refresh(pr)
    else:
        pr = existing_pr
        pr.status = PRStatus.PENDING
        db.commit()

    background_tasks.add_task(process_review, pr.id)
    logger.info("review_job_queued", pr_id=pr.id, pr_number=pr_number)

    return {"status": "accepted", "pr_id": pr.id}
