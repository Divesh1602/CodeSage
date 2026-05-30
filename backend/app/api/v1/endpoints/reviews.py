from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.pull_request import PullRequest, PRStatus
from app.models.review import Review, ReviewComment
from app.models.repository import Repository

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/pr/{pr_id}")
async def get_pr_review(
    pr_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pr = db.query(PullRequest).filter(PullRequest.id == pr_id).first()
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")

    repo = db.query(Repository).filter(
        Repository.id == pr.repository_id,
        Repository.user_id == current_user.id,
    ).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    review = (
        db.query(Review)
        .filter(Review.pull_request_id == pr_id)
        .order_by(Review.created_at.desc())
        .first()
    )
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    comments = db.query(ReviewComment).filter(ReviewComment.review_id == review.id).all()

    return {
        "review": {
            "id": review.id,
            "status": review.review_status.value,
            "score": review.score,
            "security_score": review.security_score,
            "performance_score": review.performance_score,
            "quality_score": review.quality_score,
            "summary": review.summary,
            "total_issues": review.total_issues,
            "critical_issues": review.critical_issues,
            "high_issues": review.high_issues,
            "medium_issues": review.medium_issues,
            "low_issues": review.low_issues,
            "created_at": review.created_at.isoformat(),
        },
        "pull_request": {
            "id": pr.id,
            "pr_number": pr.pr_number,
            "title": pr.title,
            "author": pr.author,
            "pr_url": pr.pr_url,
        },
        "comments": [
            {
                "id": c.id,
                "file_name": c.file_name,
                "line_number": c.line_number,
                "severity": c.severity.value,
                "category": c.category,
                "issue": c.issue,
                "suggestion": c.suggestion,
                "code_snippet": c.code_snippet,
            }
            for c in comments
        ],
    }


@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repos = db.query(Repository).filter(Repository.user_id == current_user.id).all()
    repo_ids = [r.id for r in repos]

    if not repo_ids:
        return {
            "total_reviews": 0,
            "total_issues": 0,
            "repos_connected": 0,
            "average_score": 0,
            "recent_reviews": [],
        }

    prs = db.query(PullRequest).filter(PullRequest.repository_id.in_(repo_ids)).all()
    pr_ids = [p.id for p in prs]

    reviews = (
        db.query(Review)
        .filter(Review.pull_request_id.in_(pr_ids))
        .filter(Review.review_status == "completed")
        .all()
    )

    total_issues = sum(r.total_issues or 0 for r in reviews)
    scores = [r.score for r in reviews if r.score is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    # Recent reviews
    recent = (
        db.query(Review, PullRequest, Repository)
        .join(PullRequest, Review.pull_request_id == PullRequest.id)
        .join(Repository, PullRequest.repository_id == Repository.id)
        .filter(Repository.user_id == current_user.id)
        .order_by(Review.created_at.desc())
        .limit(5)
        .all()
    )

    recent_data = []
    for review, pr, repo in recent:
        recent_data.append({
            "pr_title": pr.title,
            "repo_name": repo.repo_name,
            "score": review.score,
            "total_issues": review.total_issues,
            "created_at": review.created_at.isoformat(),
            "pr_id": pr.id,
        })

    return {
        "total_reviews": len(reviews),
        "total_issues": total_issues,
        "repos_connected": len([r for r in repos if r.enabled]),
        "average_score": avg_score,
        "recent_reviews": recent_data,
    }


@router.delete("/pr/{pr_id}")
async def delete_pr_review(
    pr_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pr = db.query(PullRequest).filter(PullRequest.id == pr_id).first()
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")
    repo = db.query(Repository).filter(
        Repository.id == pr.repository_id,
        Repository.user_id == current_user.id,
    ).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    db.delete(pr)
    db.commit()
    return {"message": "Review deleted"}


@router.post("/pr/{pr_id}/rerun")
async def rerun_pr_review(
    pr_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.workers.review_tasks import process_review

    pr = db.query(PullRequest).filter(PullRequest.id == pr_id).first()
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR not found")
    repo = db.query(Repository).filter(
        Repository.id == pr.repository_id,
        Repository.user_id == current_user.id,
    ).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    pr.status = PRStatus.PENDING
    db.commit()

    background_tasks.add_task(process_review, pr_id)
    return {"message": "Review re-queued"}
