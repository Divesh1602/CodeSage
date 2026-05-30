from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.base import get_db
from app.services.auth_service import github_oauth_callback
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    name: str
    email: str | None
    github_username: str
    avatar_url: str | None
    created_at: str

    class Config:
        from_attributes = True


@router.get("/github")
async def github_login():
    """Redirect to GitHub OAuth."""
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&scope=repo,read:user,user:email"
        f"&redirect_uri={settings.FRONTEND_URL}/auth/callback"
    )
    return RedirectResponse(url=github_auth_url)


@router.post("/github/callback", response_model=dict)
async def github_callback(code: str, db: Session = Depends(get_db)):
    """Exchange GitHub OAuth code for JWT."""
    result = await github_oauth_callback(code, db)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to authenticate with GitHub",
        )
    user = result["user"]
    return {
        "access_token": result["access_token"],
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "github_username": user.github_username,
            "avatar_url": user.avatar_url,
            "created_at": user.created_at.isoformat(),
        },
    }


@router.get("/me", response_model=dict)
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "github_username": current_user.github_username,
        "avatar_url": current_user.avatar_url,
        "created_at": current_user.created_at.isoformat(),
    }
