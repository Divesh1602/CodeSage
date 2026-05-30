from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, BigInteger, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database.base import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    github_repo_id = Column(BigInteger, unique=True, nullable=False)
    repo_name = Column(String(500), nullable=False)
    repo_full_name = Column(String(500), nullable=False)
    repo_url = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    language = Column(String(100), nullable=True)
    is_private = Column(Boolean, default=False)
    enabled = Column(Boolean, default=False)
    webhook_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="repositories")
    pull_requests = relationship("PullRequest", back_populates="repository", cascade="all, delete-orphan")
