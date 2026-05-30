from app.agents.base import BaseAgent, AgentResult, AgentIssue
from app.core.logging import logger

SYSTEM_PROMPT = """You are a code quality expert. Analyze code diffs for quality issues.
Focus on: code duplication, poor naming conventions, SOLID principle violations, excessive complexity,
long methods/functions, missing error handling, tight coupling, low cohesion, and maintainability issues.

Always respond with valid JSON:
{
  "issues": [
    {
      "severity": "critical|high|medium|low|info",
      "file_name": "string",
      "line_number": number_or_null,
      "issue": "description of the quality issue",
      "suggestion": "how to fix it",
      "code_snippet": "relevant code snippet or null"
    }
  ],
  "score": 0-10,
  "summary": "brief quality summary"
}
"""


class QualityAgent(BaseAgent):
    async def analyze(self, diff: str, file_context: list[dict]) -> AgentResult:
        prompt = f"""Analyze the following code diff for code quality issues:

```diff
{diff[:6000]}
```

Return only the JSON response with quality issues found."""

        try:
            raw = await self._query_ollama(prompt, SYSTEM_PROMPT)
            data = self._parse_json_response(raw)

            issues = []
            for item in data.get("issues", []):
                issues.append(AgentIssue(
                    severity=item.get("severity", "low"),
                    category="quality",
                    file_name=item.get("file_name", "unknown"),
                    line_number=item.get("line_number"),
                    issue=item.get("issue", ""),
                    suggestion=item.get("suggestion", ""),
                    code_snippet=item.get("code_snippet"),
                ))

            return AgentResult(
                agent_name="quality",
                issues=issues,
                score=float(data.get("score", 10.0)),
                summary=data.get("summary", "Quality analysis complete."),
            )
        except Exception as e:
            logger.error("quality_agent_failed", error=str(e))
            return AgentResult(
                agent_name="quality",
                error=str(e),
                summary="Quality analysis failed.",
            )
