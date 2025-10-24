from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class ReferralContact(Base):
    """Referral contacts for users"""
    __tablename__ = "referral_contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    contact_name = Column(String, nullable=False)
    contact_email = Column(String, nullable=False)
    company = Column(String, nullable=False)
    position = Column(String, nullable=True)
    contact_relationship = Column(String, nullable=True)  # colleague, alumni, friend, linkedin_connection
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="referral_contacts")
    email_drafts = relationship("ReferralEmailDraft", back_populates="contact", cascade="all, delete-orphan")
    emails_sent = relationship("ReferralEmailSent", back_populates="contact", cascade="all, delete-orphan")


class ReferralEmailDraft(Base):
    """Referral email drafts with version control"""
    __tablename__ = "referral_email_drafts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("job_listings.id"), nullable=True, index=True)
    contact_id = Column(Integer, ForeignKey("referral_contacts.id"), nullable=False, index=True)
    subject = Column(String, nullable=True)
    email_body = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_primary = Column(Boolean, default=True, nullable=False)
    template_used = Column(String, nullable=True)  # software_engineering, frontend, backend, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="referral_email_drafts")
    job = relationship("JobListing", back_populates="referral_email_drafts")
    contact = relationship("ReferralContact", back_populates="email_drafts")
    emails_sent = relationship("ReferralEmailSent", back_populates="draft")


class ReferralEmailSent(Base):
    """Track sent referral emails"""
    __tablename__ = "referral_emails_sent"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("job_listings.id"), nullable=True, index=True)
    contact_id = Column(Integer, ForeignKey("referral_contacts.id"), nullable=False, index=True)
    draft_id = Column(Integer, ForeignKey("referral_email_drafts.id"), nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    response_received = Column(Boolean, default=False, nullable=False)
    response_date = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="referral_emails_sent")
    job = relationship("JobListing", back_populates="referral_emails_sent")
    contact = relationship("ReferralContact", back_populates="emails_sent")
    draft = relationship("ReferralEmailDraft", back_populates="emails_sent")