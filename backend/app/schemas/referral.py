from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


# Base schemas
class ReferralContactBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    contact_email: EmailStr
    company: str = Field(..., min_length=1, max_length=255)
    position: Optional[str] = Field(None, max_length=255)
    relationship: Optional[str] = Field(None, description="colleague, alumni, friend, linkedin_connection")


class ReferralContactCreate(ReferralContactBase):
    pass


class ReferralContactUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_email: Optional[EmailStr] = None
    company: Optional[str] = Field(None, min_length=1, max_length=255)
    position: Optional[str] = Field(None, max_length=255)
    relationship: Optional[str] = None


class ReferralContact(ReferralContactBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# Email Draft schemas
class ReferralEmailDraftBase(BaseModel):
    subject: Optional[str] = Field(None, max_length=255)
    email_body: Optional[str] = None
    template_used: Optional[str] = Field(None, description="Template category used for generation")


class ReferralEmailDraftCreate(ReferralEmailDraftBase):
    job_id: Optional[int] = None
    contact_id: UUID


class ReferralEmailDraftUpdate(BaseModel):
    subject: Optional[str] = Field(None, max_length=255)
    email_body: Optional[str] = None


class ReferralEmailDraft(ReferralEmailDraftBase):
    id: UUID
    user_id: UUID
    job_id: Optional[int]
    contact_id: UUID
    version: int
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Email Sent schemas
class ReferralEmailSentBase(BaseModel):
    response_received: bool = False
    response_date: Optional[datetime] = None


class ReferralEmailSentCreate(BaseModel):
    draft_id: UUID


class ReferralEmailSent(ReferralEmailSentBase):
    id: UUID
    user_id: UUID
    job_id: Optional[int]
    contact_id: UUID
    draft_id: UUID
    sent_at: datetime

    class Config:
        from_attributes = True


# Request/Response schemas
class ReferralEmailGenerateRequest(BaseModel):
    job_id: Optional[int] = None
    contact_info: ReferralContactBase


class ReferralEmailGenerateResponse(BaseModel):
    subject: str
    body: str
    template_used: str


class ReferralRequestCreate(BaseModel):
    job_id: Optional[int] = None
    contact_info: ReferralContactCreate


class ReferralDraftResponse(BaseModel):
    draft: ReferralEmailDraft
    contact: ReferralContact


class ReferralAnalytics(BaseModel):
    """Referral analytics data"""
    this_week: int = Field(..., description="Referrals sent this week")
    total_sent: int = Field(..., description="Total referrals sent")
    response_rate: float = Field(..., description="Response rate percentage")
    trend_data: List[dict] = Field(..., description="Trend data for charts")


class ReferralTrendDataPoint(BaseModel):
    """Single data point for referral trends"""
    date: str
    count: int


# Contact list response
class ContactListResponse(BaseModel):
    contacts: List[ReferralContact]
    total_count: int


# Dashboard integration
class ReferralStatsResponse(BaseModel):
    """Quick stats for dashboard cards"""
    total_contacts: int
    emails_sent_this_month: int
    response_rate: float
    pending_responses: int


# Detailed referral information
class ReferralDetailedInfo(BaseModel):
    """Complete referral information including contact, email content, and job details"""
    # Sent email info
    sent_id: int
    sent_at: datetime
    response_received: bool
    response_date: Optional[datetime]

    # Contact information
    contact_name: str
    contact_email: str
    company: str
    position: Optional[str]
    contact_relationship: Optional[str]

    # Email content
    email_subject: Optional[str]
    email_body: Optional[str]
    template_used: Optional[str]

    # Job information (if applicable)
    job_title: Optional[str]
    job_company: Optional[str]
    job_id: Optional[int]

    class Config:
        from_attributes = True


class ReferralDetailedListResponse(BaseModel):
    """Response for detailed referral list"""
    referrals: List[ReferralDetailedInfo]
    total_count: int
    page: int
    page_size: int