from app.agents.base import BaseAgent, AgentResult, AgentIssue
from app.core.logging import logger

SYSTEM_PROMPT = """You are a testing expert. Analyze code diffs and suggest missing tests.
Focus on: uncovered edge cases, missing unit tests, missing integration tests, boundary conditions,
error/exception scenarios, and null/empty input handling.

Always respond with valid JSON:
{
  "issues": [
    {
      "severity": "medium|low|info",
      "file_name": "string",
      "line_number": number_or_null,
      "issue": "description of missing test coverage",
      "suggestion": "suggested test case to write",
      "code_snippet": "example test code or null"
    }
  ],
  "score": 0-10,
  "summary": "brief testing summary"
}
"""


class TestAgent(BaseAgent):
    async def analyze(self, diff: str, file_context: list[dict]) -> AgentResult:
        prompt = f"""Analyze the following code diff and suggest missing test cases:

```diff
{diff[:6000]}
```

Return only the JSON response with testing suggestions."""

        try:
            raw = await self._query_ollama(prompt, SYSTEM_PROMPT)
            data = self._parse_json_response(raw)

            issues = []
            for item in data.get("issues", []):
                issues.append(AgentIssue(
                    severity=item.get("severity", "info"),
                    category="testing",
                    file_name=item.get("file_name", "unknown"),
                    line_number=item.get("line_number"),
                    issue=item.get("issue", ""),
                    suggestion=item.get("suggestion", ""),
                    code_snippet=item.get("code_snippet"),
                ))

            return AgentResult(
                agent_name="testing",
                issues=issues,
                score=float(data.get("score", 10.0)),
                summary=data.get("summary", "Test coverage analysis complete."),
            )
        except Exception as e:
            logger.error("test_agent_failed", error=str(e))
            return AgentResult(
                agent_name="testing",
                error=str(e),
                summary="Test analysis failed.",
            )
