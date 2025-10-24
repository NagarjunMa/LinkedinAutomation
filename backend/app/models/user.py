from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    resumes = relationship("Resume", back_populates="user", foreign_keys="Resume.user_id")
    evaluation_sessions = relationship("ResumeEvaluationSession", back_populates="user")
    referral_contacts = relationship("ReferralContact", back_populates="user", cascade="all, delete-orphan")
    referral_email_drafts = relationship("ReferralEmailDraft", back_populates="user", cascade="all, delete-orphan")
    referral_emails_sent = relationship("ReferralEmailSent", back_populates="user", cascade="all, delete-orphan")
    profile_info = relationship("ProfileInfo", back_populates="user", uselist=False, cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.user_id}>" 