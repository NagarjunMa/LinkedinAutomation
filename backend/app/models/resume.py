from sqlalchemy import Column, String, DateTime, Text, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


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
    
    # AI analysis metadata
    ai_model_version = Column(String, nullable=True)
    processing_time = Column(Integer, nullable=True)  # in seconds
    
    # Relationships
    user = relationship("User", back_populates="resumes")
    evaluations = relationship("ResumeEvaluation", back_populates="resume")
    
    def __repr__(self):
        return f"<Resume(id={self.id}, filename={self.filename}, user_id={self.user_id})>"


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
