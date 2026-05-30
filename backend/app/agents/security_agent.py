from app.agents.base import BaseAgent, AgentResult, AgentIssue
from app.core.logging import logger

SYSTEM_PROMPT = """You are a security-focused code reviewer. Analyze code diffs for security vulnerabilities.
Focus on: SQL injection, XSS, CSRF, authentication flaws, authorization issues, exposed secrets,
command injection, path traversal, insecure deserialization, hardcoded credentials, and unsafe functions.

Always respond with valid JSON matching this exact schema:
{
  "issues": [
    {
      "severity": "critical|high|medium|low|info",
      "file_name": "string",
      "line_number": number_or_null,
      "issue": "description of the security issue",
      "suggestion": "how to fix it",
      "code_snippet": "relevant code snippet or null"
    }
  ],
  "score": 0-10,
  "summary": "brief security summary"
}
"""


class SecurityAgent(BaseAgent):
    async def analyze(self, diff: str, file_context: list[dict]) -> AgentResult:
        prompt = f"""Analyze the following code diff for security vulnerabilities:

```diff
{diff[:6000]}
```

Return only the JSON response with security issues found."""

        try:
            raw = await self._query_ollama(prompt, SYSTEM_PROMPT)
            data = self._parse_json_response(raw)

            issues = []
            for item in data.get("issues", []):
                issues.append(AgentIssue(
                    severity=item.get("severity", "medium"),
                    category="security",
                    file_name=item.get("file_name", "unknown"),
                    line_number=item.get("line_number"),
                    issue=item.get("issue", ""),
                    suggestion=item.get("suggestion", ""),
                    code_snippet=item.get("code_snippet"),
                ))

            return AgentResult(
                agent_name="security",
                issues=issues,
                score=float(data.get("score", 10.0)),
                summary=data.get("summary", "Security analysis complete."),
            )
        except Exception as e:
            logger.error("security_agent_failed", error=repr(e))
            return AgentResult(
                agent_name="security",
                error=str(e),
                summary="Security analysis failed.",
            )
