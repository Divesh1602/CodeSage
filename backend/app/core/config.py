from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CodeSage"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = "postgresql://codesage:codesage@localhost:5432/codesage"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # GitHub OAuth
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_WEBHOOK_SECRET: str = "change-me-in-production"
    GITHUB_APP_NAME: str = "codesage"

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Public URL for webhooks (set to ngrok URL in local dev)
    WEBHOOK_BASE_URL: str = ""

    # AI Provider — set GROQ_API_KEY to use Groq (free), leave blank to use Ollama
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Ollama (local dev fallback)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5-coder:1.5b"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
