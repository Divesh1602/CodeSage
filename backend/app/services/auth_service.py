from sqlalchemy.orm import Session
from app.models.user import User
from app.github.client import GitHubClient, exchange_code_for_token
from app.core.security import create_access_token
from app.core.logging import logger
from typing import Optional


async def github_oauth_callback(code: str, db: Session) -> Optional[dict]:
    access_token = await exchange_code_for_token(code)
    if not access_token:
        return None

    gh = GitHubClient(access_token)
    gh_user = await gh.get_authenticated_user()

    github_id = str(gh_user["id"])
    user = db.query(User).filter(User.github_id == github_id).first()

    if user:
        user.github_access_token = access_token
        user.name = gh_user.get("name") or gh_user["login"]
        user.avatar_url = gh_user.get("avatar_url")
    else:
        user = User(
            name=gh_user.get("name") or gh_user["login"],
            email=gh_user.get("email"),
            github_id=github_id,
            github_username=gh_user["login"],
            github_access_token=access_token,
            avatar_url=gh_user.get("avatar_url"),
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    jwt_token = create_access_token({"sub": user.id, "github_id": user.github_id})
    return {"access_token": jwt_token, "user": user}
