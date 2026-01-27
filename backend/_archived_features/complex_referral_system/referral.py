from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base


class ReferralContact(Base):
    __tablename__ = "referral_contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String)
    linkedin_url = Column(String)
    company = Column(String)
    position = Column(String)
    relationship_strength = Column(String)  # 'strong', 'medium', 'weak'
    last_contacted = Column(DateTime)
    notes = Column(Text)
    tags = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReferralEmailDraft(Base):
    __tablename__ = "referral_email_drafts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    contact_id = Column(Integer, ForeignKey("referral_contacts.id"))
    job_id = Column(Integer, ForeignKey("job_listings.id"))
    subject = Column(String)
    body = Column(Text)
    template_used = Column(String)
    ai_generated = Column(Boolean, default=False)
    personalization_notes = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contact = relationship("ReferralContact", backref="email_drafts")


class ReferralEmailSent(Base):
    __tablename__ = "referral_emails_sent"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    draft_id = Column(Integer, ForeignKey("referral_email_drafts.id"))
    contact_id = Column(Integer, ForeignKey("referral_contacts.id"))
    sent_at = Column(DateTime, default=datetime.utcnow)
    email_message_id = Column(String)
    opened = Column(Boolean, default=False)
    clicked = Column(Boolean, default=False)
    replied = Column(Boolean, default=False)
    response_received_at = Column(DateTime)
    outcome = Column(String)  # 'referral_given', 'meeting_scheduled', 'no_response', etc.
    notes = Column(Text)

    draft = relationship("ReferralEmailDraft", backref="sent_emails")
    contact = relationship("ReferralContact", backref="sent_emails")