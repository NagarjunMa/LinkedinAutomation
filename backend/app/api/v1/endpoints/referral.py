from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.services.referral_service import ReferralService
from app.schemas.referral import (
    ReferralEmailGenerateRequest,
    ReferralEmailGenerateResponse,
    ReferralRequestCreate,
    ReferralDraftResponse,
    ReferralEmailDraftUpdate,
    ReferralEmailDraft,
    ReferralContact,
    ContactListResponse,
    ReferralAnalytics,
    ReferralStatsResponse,
    ReferralEmailSentCreate,
    ReferralDetailedInfo,
    ReferralDetailedListResponse
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def get_current_user_mock(db: Session = Depends(get_db)) -> User:
    """
    Temporary mock for user authentication
    Replace with your actual authentication dependency
    """
    # For now, get the first user in the database
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No users found")
    return user


@router.post("/generate-email", response_model=ReferralEmailGenerateResponse)
async def generate_referral_email(
    request: ReferralEmailGenerateRequest,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Generate a referral email without saving it
    """
    try:
        service = ReferralService(db)
        email_content = await service.generate_email_only(current_user.user_id, request)

        return ReferralEmailGenerateResponse(
            subject=email_content['subject'],
            body=email_content['body'],
            template_used=email_content['template_used']
        )
    except Exception as e:
        logger.error(f"Email generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate email: {str(e)}")


@router.post("/create-request", response_model=ReferralDraftResponse)
async def create_referral_request(
    request: ReferralRequestCreate,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Create a complete referral request (contact + draft)
    """
    try:
        service = ReferralService(db)
        result = await service.create_referral_request(
            current_user.user_id,
            request.job_id,
            request.contact_info.dict()
        )

        return result
    except Exception as e:
        logger.error(f"Referral request creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create referral request: {str(e)}")


@router.put("/drafts/{draft_id}", response_model=ReferralEmailDraft)
async def update_draft(
    draft_id: str,
    updates: ReferralEmailDraftUpdate,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Update an existing email draft
    """
    try:
        service = ReferralService(db)
        updated_draft = await service.update_draft(
            draft_id,
            current_user.user_id,
            updates.dict(exclude_unset=True)
        )

        return updated_draft
    except Exception as e:
        logger.error(f"Draft update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update draft: {str(e)}")


@router.post("/send/{draft_id}")
async def send_referral_email(
    draft_id: str,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Send a referral email (mark as sent)
    """
    try:
        service = ReferralService(db)
        result = await service.send_referral_email(current_user.user_id, draft_id)

        return result
    except Exception as e:
        logger.error(f"Email send failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.get("/contacts", response_model=ContactListResponse)
async def get_user_contacts(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Get user's referral contacts
    """
    try:
        service = ReferralService(db)
        result = await service.get_user_contacts(current_user.user_id, limit, offset)

        return ContactListResponse(
            contacts=result['contacts'],
            total_count=result['total_count']
        )
    except Exception as e:
        logger.error(f"Get contacts failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get contacts: {str(e)}")


@router.get("/drafts")
async def get_user_drafts(
    job_id: Optional[int] = Query(None),
    limit: int = Query(20, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Get user's email drafts
    """
    try:
        service = ReferralService(db)
        result = await service.get_user_drafts(current_user.user_id, job_id, limit, offset)

        return result
    except Exception as e:
        logger.error(f"Get drafts failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get drafts: {str(e)}")


@router.get("/analytics", response_model=ReferralAnalytics)
async def get_referral_analytics(
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Get referral analytics for the user
    """
    try:
        service = ReferralService(db)
        analytics = await service.get_referral_analytics(current_user.user_id)

        return ReferralAnalytics(
            this_week=analytics['this_week'],
            total_sent=analytics['total_sent'],
            response_rate=analytics['response_rate'],
            trend_data=analytics['trend_data']
        )
    except Exception as e:
        logger.error(f"Get analytics failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/stats", response_model=ReferralStatsResponse)
async def get_referral_stats(
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Get quick referral stats for dashboard
    """
    try:
        service = ReferralService(db)
        analytics = await service.get_referral_analytics(current_user.user_id)

        # Get contacts count
        contacts = await service.get_user_contacts(current_user.user_id, limit=1)

        # Calculate monthly stats
        monthly_sent = analytics['this_week'] * 4  # Rough estimate

        return ReferralStatsResponse(
            total_contacts=contacts['total_count'],
            emails_sent_this_month=monthly_sent,
            response_rate=analytics['response_rate'],
            pending_responses=max(0, analytics['total_sent'] - int(analytics['total_sent'] * analytics['response_rate'] / 100))
        )
    except Exception as e:
        logger.error(f"Get stats failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/responses/{sent_id}/mark-received")
async def mark_response_received(
    sent_id: str,
    response_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Mark that a response was received for a sent referral
    """
    try:
        service = ReferralService(db)
        result = await service.mark_response_received(
            current_user.user_id,
            sent_id,
            response_date
        )

        return result
    except Exception as e:
        logger.error(f"Mark response failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to mark response: {str(e)}")


@router.get("/templates")
async def get_available_templates():
    """
    Get available email templates and their categories
    """
    try:
        from app.services.referral_email_generator import ReferralEmailGenerator

        templates = {}
        for template_name, template_data in ReferralEmailGenerator.TEMPLATES.items():
            templates[template_name] = {
                'name': template_name.replace('_', ' ').title(),
                'focus': template_data['focus'],
                'value_prop': template_data['value_prop'],
                'keywords': template_data['keywords']
            }

        return {
            'templates': templates,
            'default': 'software_engineering'
        }
    except Exception as e:
        logger.error(f"Get templates failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")


@router.delete("/contacts/{contact_id}")
async def delete_contact(
    contact_id: str,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Delete a referral contact
    """
    try:
        from app.models.referral import ReferralContact
        from sqlalchemy import and_

        contact = db.query(ReferralContact).filter(
            and_(
                ReferralContact.id == contact_id,
                ReferralContact.user_id == current_user.user_id
            )
        ).first()

        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

        db.delete(contact)
        db.commit()

        return {"success": True, "message": "Contact deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete contact failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete contact: {str(e)}")


@router.delete("/drafts/{draft_id}")
async def delete_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Delete an email draft
    """
    try:
        from app.models.referral import ReferralEmailDraft
        from sqlalchemy import and_

        draft = db.query(ReferralEmailDraft).filter(
            and_(
                ReferralEmailDraft.id == draft_id,
                ReferralEmailDraft.user_id == current_user.user_id
            )
        ).first()

        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")

        db.delete(draft)
        db.commit()

        return {"success": True, "message": "Draft deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete draft failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete draft: {str(e)}")


@router.get("/sent", response_model=ReferralDetailedListResponse)
async def get_sent_referrals(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    company_filter: Optional[str] = Query(None, description="Filter by company name"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    current_user: User = Depends(get_current_user_mock),
    db: Session = Depends(get_db)
):
    """
    Get all sent referrals with detailed information including:
    - Contact name, email, company, position
    - Email subject, content, template used
    - Job title and company (if applicable)
    - Date sent and response status
    """
    try:
        from app.models.referral import ReferralEmailSent, ReferralContact, ReferralEmailDraft
        from app.models.job import JobListing
        from sqlalchemy import and_, desc
        from sqlalchemy.orm import joinedload

        # Calculate offset
        offset = (page - 1) * page_size

        # Build base query with joins
        query = db.query(ReferralEmailSent).filter(
            ReferralEmailSent.user_id == current_user.user_id
        ).options(
            joinedload(ReferralEmailSent.contact),
            joinedload(ReferralEmailSent.draft),
            joinedload(ReferralEmailSent.job)
        )

        # Apply filters
        if company_filter:
            query = query.join(ReferralContact).filter(
                ReferralContact.company.ilike(f"%{company_filter}%")
            )

        if date_from:
            query = query.filter(ReferralEmailSent.sent_at >= date_from)

        if date_to:
            query = query.filter(ReferralEmailSent.sent_at <= date_to)

        # Get total count
        total_count = query.count()

        # Apply pagination and ordering
        sent_referrals = query.order_by(desc(ReferralEmailSent.sent_at)).offset(offset).limit(page_size).all()

        # Transform to response format
        referrals = []
        for sent in sent_referrals:
            referral_info = ReferralDetailedInfo(
                # Sent email info
                sent_id=sent.id,
                sent_at=sent.sent_at,
                response_received=sent.response_received,
                response_date=sent.response_date,

                # Contact information
                contact_name=sent.contact.contact_name,
                contact_email=sent.contact.contact_email,
                company=sent.contact.company,
                position=sent.contact.position,
                contact_relationship=sent.contact.contact_relationship,

                # Email content
                email_subject=sent.draft.subject if sent.draft else None,
                email_body=sent.draft.email_body if sent.draft else None,
                template_used=sent.draft.template_used if sent.draft else None,

                # Job information (if applicable)
                job_title=sent.job.title if sent.job else None,
                job_company=sent.job.company if sent.job else None,
                job_id=sent.job.id if sent.job else None
            )
            referrals.append(referral_info)

        return ReferralDetailedListResponse(
            referrals=referrals,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Get sent referrals failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sent referrals: {str(e)}")