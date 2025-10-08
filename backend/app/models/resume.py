from sqlalchemy import Column, String, DateTime, Text, Integer, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
from datetime import datetime, timedelta, timezone


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Evaluation results
    evaluation_status = Column(String, default="pending")  # pending, evaluating, completed, failed
    evaluation_result = Column(JSON, nullable=True)
    evaluated_at = Column(DateTime(timezone=True), nullable=True)

    # Status locking mechanism to prevent race conditions
    is_locked = Column(Boolean, default=False)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    locked_by = Column(String, nullable=True)  # process/task identifier
    lock_expires_at = Column(DateTime(timezone=True), nullable=True)

    # AI analysis metadata
    ai_model_version = Column(String, nullable=True)
    processing_time = Column(Integer, nullable=True)  # in seconds
    
    # Relationships
    user = relationship("User", back_populates="resumes")
    evaluations = relationship("ResumeEvaluation", back_populates="resume")
    evaluation_sessions = relationship("ResumeEvaluationSession", back_populates="resume")
    
    def __repr__(self):
        return f"<Resume(id={self.id}, filename={self.filename}, user_id={self.user_id})>"

    def acquire_lock(self, locked_by: str, lock_duration_minutes: int = 10) -> bool:
        """
        Acquire a lock for evaluation processing.
        Returns True if lock was successfully acquired, False otherwise.
        """
        now = datetime.now(timezone.utc)

        # Check if already locked and not expired
        if self.is_locked and self.lock_expires_at and self.lock_expires_at > now:
            return False

        # Acquire lock
        self.is_locked = True
        self.locked_at = now
        self.locked_by = locked_by
        self.lock_expires_at = now + timedelta(minutes=lock_duration_minutes)
        return True

    def release_lock(self):
        """Release the evaluation lock."""
        self.is_locked = False
        self.locked_at = None
        self.locked_by = None
        self.lock_expires_at = None

    def is_lock_expired(self) -> bool:
        """Check if the current lock has expired."""
        if not self.is_locked or not self.lock_expires_at:
            return True
        return datetime.now(timezone.utc) > self.lock_expires_at

    def can_evaluate(self) -> bool:
        """Check if this resume can be evaluated (not locked or lock expired)."""
        return not self.is_locked or self.is_lock_expired()

    def update_evaluation_status(self, status: str, release_lock: bool = True):
        """
        Update evaluation status and optionally release lock.

        Args:
            status: New evaluation status ('pending', 'evaluating', 'completed', 'failed')
            release_lock: Whether to release the lock after status update
        """
        self.evaluation_status = status

        if status == "completed":
            self.evaluated_at = datetime.now(timezone.utc)

        if release_lock:
            self.release_lock()


class ResumeEvaluation(Base):
    __tablename__ = "resume_evaluations"

    id = Column(String, primary_key=True, index=True)
    resume_id = Column(String, ForeignKey("resumes.id"), nullable=False)
    
    # Scoring breakdown (100 points total)
    overall_score = Column(Integer, nullable=False)
    ats_compliance_score = Column(Integer, nullable=False)
    content_quality_score = Column(Integer, nullable=False)
    experience_points_score = Column(Integer, nullable=False)
    job_relevance_score = Column(Integer, nullable=False)
    quality_checks_score = Column(Integer, nullable=False)
    
    # Detailed feedback
    strengths = Column(JSON, nullable=True)  # List of strings
    improvements = Column(JSON, nullable=True)  # List of strings
    detailed_feedback = Column(Text, nullable=True)
    
    # ATS compatibility
    ats_compatibility = Column(String, nullable=False)  # excellent, good, fair, poor
    
    # Keyword analysis
    keyword_analysis = Column(JSON, nullable=True)  # {relevant: [], missing: [], score: float}
    
    # Enhanced evaluation fields
    critical_issues = Column(JSON, nullable=True)  # {immediate_fixes: [], strategic_improvements: [], nice_to_have: []}
    market_positioning = Column(JSON, nullable=True)  # {current_level: str, salary_range: str, target_roles: str, company_fit: {}}
    
    # Evaluation metadata
    evaluated_at = Column(DateTime(timezone=True), server_default=func.now())
    ai_model_version = Column(String, nullable=True)
    evaluation_prompt = Column(Text, nullable=True)
    
    # Relationships
    resume = relationship("Resume", back_populates="evaluations")
    
    def __repr__(self):
        return f"<ResumeEvaluation(id={self.id}, resume_id={self.resume_id}, score={self.overall_score})>"
