from app.agents.base import BaseAgent, AgentResult, AgentIssue
from app.core.logging import logger

SYSTEM_PROMPT = """You are a performance optimization expert. Analyze code diffs for performance issues.
Focus on: N+1 queries, inefficient loops, memory leaks, unnecessary API calls, blocking operations,
missing indexes, unoptimized algorithms, excessive object creation, and scalability bottlenecks.

Always respond with valid JSON:
{
  "issues": [
    {
      "severity": "critical|high|medium|low|info",
      "file_name": "string",
      "line_number": number_or_null,
      "issue": "description of the performance issue",
      "suggestion": "how to fix it",
      "code_snippet": "relevant code snippet or null"
    }
  ],
  "score": 0-10,
  "summary": "brief performance summary"
}
"""


class PerformanceAgent(BaseAgent):
    async def analyze(self, diff: str, file_context: list[dict]) -> AgentResult:
        prompt = f"""Analyze the following code diff for performance issues:

```diff
{diff[:6000]}
```

Return only the JSON response with performance issues found."""

        try:
            raw = await self._query_ollama(prompt, SYSTEM_PROMPT)
            data = self._parse_json_response(raw)

            issues = []
            for item in data.get("issues", []):
                issues.append(AgentIssue(
                    severity=item.get("severity", "medium"),
                    category="performance",
                    file_name=item.get("file_name", "unknown"),
                    line_number=item.get("line_number"),
                    issue=item.get("issue", ""),
                    suggestion=item.get("suggestion", ""),
                    code_snippet=item.get("code_snippet"),
                ))

            return AgentResult(
                agent_name="performance",
                issues=issues,
                score=float(data.get("score", 10.0)),
                summary=data.get("summary", "Performance analysis complete."),
            )
        except Exception as e:
            logger.error("performance_agent_failed", error=str(e))
            return AgentResult(
                agent_name="performance",
                error=str(e),
                summary="Performance analysis failed.",
            )
