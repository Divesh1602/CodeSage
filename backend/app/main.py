from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import configure_logging
from app.api.v1.router import api_router
from app.database.base import Base, engine
import app.models  # ensure models are registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(debug=settings.DEBUG)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered code review platform",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

_origins = {"http://localhost:3000"}
for _o in settings.FRONTEND_URL.split(","):
    _o = _o.strip().rstrip("/")
    if _o:
        _origins.add(_o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
