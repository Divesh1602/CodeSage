from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import httpx
import json
from groq import AsyncGroq
from app.core.config import settings
from app.core.logging import logger


@dataclass
class AgentIssue:
    severity: str  # critical, high, medium, low, info
    category: str
    file_name: str
    line_number: Optional[int]
    issue: str
    suggestion: str
    code_snippet: Optional[str] = None


@dataclass
class AgentResult:
    agent_name: str
    issues: list[AgentIssue] = field(default_factory=list)
    score: float = 10.0
    summary: str = ""
    error: Optional[str] = None


class BaseAgent(ABC):
    def __init__(self):
        self.model = settings.OLLAMA_MODEL
        self.base_url = settings.OLLAMA_BASE_URL

    async def _query_ollama(self, prompt: str, system_prompt: str = "") -> str:
        """Query AI — uses Groq (cloud, free) if GROQ_API_KEY is set, else Ollama (local)."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        if settings.GROQ_API_KEY:
            return await self._query_groq(messages)
        return await self._query_ollama_local(messages)

    async def _query_groq(self, messages: list[dict]) -> str:
        try:
            client = AsyncGroq(api_key=settings.GROQ_API_KEY)
            response = await client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=2048,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("groq_query_failed", error=repr(e), agent=self.__class__.__name__)
            raise

    async def _query_ollama_local(self, messages: list[dict]) -> str:
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": 0.1, "num_predict": 2048},
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data["message"]["content"]
        except Exception as e:
            logger.error("ollama_query_failed", error=repr(e), agent=self.__class__.__name__)
            raise

    def _parse_json_response(self, text: str) -> dict:
        # Extract JSON from markdown code blocks if present
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            text = text[start:end].strip()

        # Find outermost JSON object/array
        for start_char, end_char in [('{', '}'), ('[', ']')]:
            start = text.find(start_char)
            if start != -1:
                end = text.rfind(end_char)
                if end != -1:
                    try:
                        return json.loads(text[start:end + 1])
                    except json.JSONDecodeError:
                        pass
        return {}

    @abstractmethod
    async def analyze(self, diff: str, file_context: list[dict]) -> AgentResult:
        pass
