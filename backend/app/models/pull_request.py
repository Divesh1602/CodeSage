from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database.base import Base


class PRStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    pr_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    author = Column(String(255), nullable=False)
    author_avatar = Column(String(500), nullable=True)
    pr_url = Column(String(500), nullable=True)
    base_branch = Column(String(255), nullable=True)
    head_branch = Column(String(255), nullable=True)
    status = Column(Enum(PRStatus), default=PRStatus.PENDING)
    diff_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    repository = relationship("Repository", back_populates="pull_requests")
    reviews = relationship("Review", back_populates="pull_request", cascade="all, delete-orphan")
