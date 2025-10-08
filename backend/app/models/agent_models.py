"""
Database models for agentic resume evaluation system.
"""

from sqlalchemy import Column, String, DateTime, Text, Integer, JSON, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class ResumeEvaluationSession(Base):
    """Track complete resume evaluation sessions."""
    __tablename__ = "resume_evaluation_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    resume_id = Column(String, ForeignKey("resumes.id"), nullable=False)
    evaluation_type = Column(String(50), default="agentic")
    
    # Evaluation results
    overall_score = Column(Integer, nullable=True)
    executive_summary = Column(Text, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    
    # Agent performance
    successful_agents = Column(Integer, default=0)
    total_agents = Column(Integer, default=0)
    confidence_percentage = Column(Float, nullable=True)
    
    # Complete evaluation data
    evaluation_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="evaluation_sessions")
    resume = relationship("Resume", back_populates="evaluation_sessions")
    agent_results = relationship("ResumeAgentResult", back_populates="evaluation_session")
    
    def __repr__(self):
        return f"<ResumeEvaluationSession(id={self.id}, user_id={self.user_id}, score={self.overall_score})>"


class ResumeAgentResult(Base):
    """Store individual agent results for analysis and debugging."""
    __tablename__ = "resume_agent_results"

    id = Column(String, primary_key=True, index=True)
    evaluation_id = Column(String, ForeignKey("resume_evaluation_sessions.id"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    
    # Agent execution results
    agent_results = Column(JSON, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    evaluation_session = relationship("ResumeEvaluationSession", back_populates="agent_results")
    
    def __repr__(self):
        return f"<ResumeAgentResult(id={self.id}, agent={self.agent_name}, success={self.success})>"


class AgentPerformanceMetrics(Base):
    """Track agent performance and optimization."""
    __tablename__ = "agent_performance_metrics"

    agent_name = Column(String(100), primary_key=True)
    total_executions = Column(Integer, default=0)
    success_rate = Column(Float, default=1.0)
    avg_execution_time_ms = Column(Float, nullable=True)
    
    # Timestamps
    last_execution = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AgentPerformanceMetrics(agent={self.agent_name}, success_rate={self.success_rate})>"
