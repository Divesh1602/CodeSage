import asyncio
from typing import Optional
from app.agents.base import AgentResult
from app.agents.security_agent import SecurityAgent
from app.agents.performance_agent import PerformanceAgent
from app.agents.quality_agent import QualityAgent
from app.agents.test_agent import TestAgent
from app.core.logging import logger


class ReviewOrchestrator:
    """Runs all specialized agents in parallel and aggregates results."""

    def __init__(self):
        self.agents = [
            SecurityAgent(),
            PerformanceAgent(),
            QualityAgent(),
            TestAgent(),
        ]

    async def run_review(self, diff: str, file_context: list[dict]) -> dict:
        tasks = [agent.analyze(diff, file_context) for agent in self.agents]
        results: list[AgentResult] = await asyncio.gather(*tasks, return_exceptions=True)

        aggregated_issues = []
        scores = []
        summaries = {}

        for result in results:
            if isinstance(result, Exception):
                logger.error("agent_exception", error=str(result))
                continue
            if result.error:
                logger.warning("agent_error", agent=result.agent_name, error=result.error)
                continue
            aggregated_issues.extend(result.issues)
            scores.append(result.score)
            summaries[result.agent_name] = result.summary

        overall_score = round(sum(scores) / len(scores), 1) if scores else 0.0

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for issue in aggregated_issues:
            sev = issue.severity.lower()
            if sev in severity_counts:
                severity_counts[sev] += 1

        return {
            "score": overall_score,
            "total_issues": len(aggregated_issues),
            "severity_counts": severity_counts,
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "file_name": i.file_name,
                    "line_number": i.line_number,
                    "issue": i.issue,
                    "suggestion": i.suggestion,
                    "code_snippet": i.code_snippet,
                }
                for i in aggregated_issues
            ],
            "summaries": summaries,
            "security_score": next(
                (r.score for r in results if not isinstance(r, Exception) and r.agent_name == "security"), None
            ),
            "performance_score": next(
                (r.score for r in results if not isinstance(r, Exception) and r.agent_name == "performance"), None
            ),
            "quality_score": next(
                (r.score for r in results if not isinstance(r, Exception) and r.agent_name == "quality"), None
            ),
        }
