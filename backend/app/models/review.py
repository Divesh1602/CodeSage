from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, Enum, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database.base import Base


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pull_request_id = Column(String, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False)
    review_status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING)
    summary = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    security_score = Column(Float, nullable=True)
    performance_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)
    raw_output = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    pull_request = relationship("PullRequest", back_populates="reviews")
    comments = relationship("ReviewComment", back_populates="review", cascade="all, delete-orphan")


class ReviewComment(Base):
    __tablename__ = "review_comments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    review_id = Column(String, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(500), nullable=False)
    line_number = Column(Integer, nullable=True)
    severity = Column(Enum(Severity), default=Severity.INFO)
    category = Column(String(100), nullable=True)  # security, performance, quality, testing
    issue = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=True)
    code_snippet = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    review = relationship("Review", back_populates="comments")
