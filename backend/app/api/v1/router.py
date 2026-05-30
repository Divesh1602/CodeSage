from fastapi import APIRouter
from app.api.v1.endpoints import auth, repositories, reviews, webhooks

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(repositories.router)
api_router.include_router(reviews.router)
api_router.include_router(webhooks.router)
