import asyncio
from app.workers.celery_app import celery_app
from app.database.base import SessionLocal
from app.models import PullRequest, Review, ReviewComment, ReviewStatus, PRStatus, Severity
from app.agents.review_agent import ReviewOrchestrator
from app.github.client import GitHubClient
from app.core.logging import logger
from app.utils.github_comment import format_review_comment


@celery_app.task(
    bind=True,
    name="app.workers.review_tasks.process_pull_request_review",
    max_retries=3,
    default_retry_delay=60,
)
def process_pull_request_review(self, pr_id: str):
    """Process a PR review asynchronously."""
    try:
        asyncio.run(_process_review(pr_id))
    except Exception as exc:
        logger.error("review_task_failed", pr_id=pr_id, error=str(exc))
        raise self.retry(exc=exc)


async def _process_review(pr_id: str):
    db = SessionLocal()
    try:
        pr = db.query(PullRequest).filter(PullRequest.id == pr_id).first()
        if not pr:
            logger.error("pr_not_found", pr_id=pr_id)
            return

        # Mark PR as processing
        pr.status = PRStatus.PROCESSING
        db.commit()

        # Create review record
        review = Review(pull_request_id=pr_id, review_status=ReviewStatus.PROCESSING)
        db.add(review)
        db.commit()
        db.refresh(review)

        # Fetch diff from GitHub
        repo = pr.repository
        user = repo.owner
        gh = GitHubClient(user.github_access_token)

        owner, repo_name = repo.repo_full_name.split("/", 1)
        files = await gh.get_pr_files(owner, repo_name, pr.pr_number)

        # Build unified diff string
        diff_parts = []
        for f in files:
            patch = f.get("patch", "")
            if patch:
                diff_parts.append(f"--- {f['filename']}\n+++ {f['filename']}\n{patch}")
        full_diff = "\n".join(diff_parts)

        if not full_diff.strip():
            review.review_status = ReviewStatus.COMPLETED
            review.summary = "No code changes detected in this PR."
            review.score = 10.0
            pr.status = PRStatus.COMPLETED
            db.commit()
            return

        # Run AI review
        orchestrator = ReviewOrchestrator()
        result = await orchestrator.run_review(full_diff, files)

        # Persist review results
        review.review_status = ReviewStatus.COMPLETED
        review.score = result["score"]
        review.security_score = result.get("security_score")
        review.performance_score = result.get("performance_score")
        review.quality_score = result.get("quality_score")
        review.total_issues = result["total_issues"]
        review.critical_issues = result["severity_counts"].get("critical", 0)
        review.high_issues = result["severity_counts"].get("high", 0)
        review.medium_issues = result["severity_counts"].get("medium", 0)
        review.low_issues = result["severity_counts"].get("low", 0)
        review.raw_output = result
        review.summary = _build_summary(result)
        pr.status = PRStatus.COMPLETED
        db.commit()

        # Save comments
        for issue in result["issues"]:
            comment = ReviewComment(
                review_id=review.id,
                file_name=issue["file_name"],
                line_number=issue.get("line_number"),
                severity=Severity(issue["severity"].lower()) if issue["severity"].lower() in [s.value for s in Severity] else Severity.INFO,
                category=issue["category"],
                issue=issue["issue"],
                suggestion=issue.get("suggestion", ""),
                code_snippet=issue.get("code_snippet"),
            )
            db.add(comment)
        db.commit()

        # Post GitHub comment
        comment_body = format_review_comment(result, pr.title)
        try:
            await gh.create_pr_review(owner, repo_name, pr.pr_number, comment_body)
        except Exception as e:
            logger.warning("github_comment_failed", error=str(e), pr_id=pr_id)

        logger.info("review_completed", pr_id=pr_id, score=result["score"])

    except Exception as e:
        logger.error("review_processing_error", pr_id=pr_id, error=str(e))
        # Mark as failed
        try:
            if 'review' in locals():
                review.review_status = ReviewStatus.FAILED
                review.error_message = str(e)
                db.commit()
            if 'pr' in locals():
                pr.status = PRStatus.FAILED
                db.commit()
        except Exception:
            pass
        raise
    finally:
        db.close()


def _build_summary(result: dict) -> str:
    score = result["score"]
    total = result["total_issues"]
    critical = result["severity_counts"].get("critical", 0)
    summaries = result.get("summaries", {})

    parts = [f"Overall score: {score}/10. Found {total} issue(s)."]
    if critical:
        parts.append(f"{critical} critical issue(s) require immediate attention.")
    for agent, summary in summaries.items():
        if summary:
            parts.append(f"[{agent.capitalize()}] {summary}")
    return " ".join(parts)
