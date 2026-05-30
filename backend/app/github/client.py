import hmac
import hashlib
from typing import Optional
import httpx
from app.core.config import settings
from app.core.logging import logger


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(self, access_token: str):
        self.token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_authenticated_user(self) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/user", headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def list_repositories(self, page: int = 1, per_page: int = 30) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/user/repos",
                headers=self.headers,
                params={"page": page, "per_page": per_page, "sort": "updated", "type": "owner"},
            )
            resp.raise_for_status()
            return resp.json()

    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}",
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_pr_files(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        files = []
        page = 1
        async with httpx.AsyncClient() as client:
            while True:
                resp = await client.get(
                    f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files",
                    headers=self.headers,
                    params={"page": page, "per_page": 100},
                )
                resp.raise_for_status()
                batch = resp.json()
                if not batch:
                    break
                files.extend(batch)
                if len(batch) < 100:
                    break
                page += 1
        return files

    async def create_pr_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        comments: Optional[list[dict]] = None,
        event: str = "COMMENT",
    ) -> dict:
        payload: dict = {"body": body, "event": event}
        if comments:
            payload["comments"] = comments
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
                headers=self.headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def create_webhook(self, owner: str, repo: str, webhook_url: str) -> dict:
        payload = {
            "name": "web",
            "active": True,
            "events": ["pull_request"],
            "config": {
                "url": webhook_url,
                "content_type": "json",
                "secret": settings.GITHUB_WEBHOOK_SECRET,
                "insecure_ssl": "0",
            },
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/repos/{owner}/{repo}/hooks",
                headers=self.headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def delete_webhook(self, owner: str, repo: str, hook_id: int) -> None:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{self.BASE_URL}/repos/{owner}/{repo}/hooks/{hook_id}",
                headers=self.headers,
            )
            resp.raise_for_status()


def verify_webhook_signature(payload_bytes: bytes, signature_header: str) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()
    provided = signature_header[len("sha256="):]
    return hmac.compare_digest(expected, provided)


async def exchange_code_for_token(code: str) -> Optional[str]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("access_token")
