"""
Referral Templates API Endpoints
Handles template generation, feedback collection, and analytics
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import get_authenticated_user_id
from app.models.user import User
from app.services.referral_template_service_sync import referral_template_service

router = APIRouter()

def get_current_user(user_id: str = Depends(get_authenticated_user_id), db: Session = Depends(get_db)) -> User:
    """
    Get the authenticated user from the database, create if doesn't exist
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        # Create new user
        user = User(user_id=user_id, email=user_id, full_name="User")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# Pydantic models for request/response
class ContactInfo(BaseModel):
    name: str = Field(..., description="Contact's full name")
    email: Optional[str] = Field(None, description="Contact's email address")
    company: str = Field(..., description="Contact's company name")
    position: Optional[str] = Field(None, description="Contact's job title")
    company_size: Optional[str] = Field(None, description="startup/medium/enterprise")
    linkedin_url: Optional[str] = Field(None, description="Contact's LinkedIn profile URL")

class JobInfo(BaseModel):
    job_id: Optional[UUID] = Field(None, description="Job ID if applying through our system")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    industry: Optional[str] = Field(None, description="Industry category")
    level: Optional[str] = Field(None, description="Job level: entry_level/mid_level/senior_level/executive")
    description: Optional[str] = Field(None, description="Job description")
    user_background: Optional[str] = Field(None, description="User's relevant background/experience")

class UserPreferences(BaseModel):
    preferred_tone: str = Field(default="professional", description="professional/casual/direct/friendly")
    preferred_length: str = Field(default="medium", description="short/medium/long")
    include_resume: bool = Field(default=True, description="Whether to mention resume attachment")
    include_portfolio: bool = Field(default=False, description="Whether to mention portfolio")

class GenerateTemplateRequest(BaseModel):
    contact_info: ContactInfo
    job_info: JobInfo
    user_preferences: Optional[UserPreferences] = None

class TemplateFeedback(BaseModel):
    got_response: bool = Field(..., description="Whether the contact responded")
    response_type: Optional[str] = Field(None, description="positive_reply/interview_scheduled/referred/no_response/connection_accepted")
    response_quality_score: Optional[int] = Field(None, ge=1, le=5, description="Quality of response (1-5)")
    user_satisfaction_score: Optional[int] = Field(None, ge=1, le=5, description="User satisfaction with template (1-5)")
    feedback_notes: Optional[str] = Field(None, description="Additional feedback notes")

class TemplateResponse(BaseModel):
    template_id: str
    subject_line: str
    email_body: str
    style: str
    personalization_level: str
    confidence_score: float
    suggested_follow_up_days: int

class TemplateListItem(BaseModel):
    id: str
    contact_name: Optional[str]
    contact_company: Optional[str]
    subject_line: str
    template_style: str
    was_sent: bool
    sent_at: Optional[datetime]
    got_response: Optional[bool]
    response_type: Optional[str]
    effectiveness_score: Optional[float]
    created_at: datetime
    user_feedback: Optional[Dict[str, Any]]

class TemplateStats(BaseModel):
    total_templates: int
    sent_count: int
    response_count: int
    response_rate: float
    avg_effectiveness: float
    draft_count: int

@router.post("/generate", response_model=TemplateResponse)
def generate_template(
    request: GenerateTemplateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a personalized referral email template
    """
    try:
        # Check daily limit
        today_count = _get_today_template_count(db, current_user.user_id)
        daily_limit = 20  # You can make this configurable per user

        if today_count >= daily_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily template generation limit ({daily_limit}) reached"
            )

        # Convert request to service format
        contact_info = request.contact_info.dict()
        job_info = request.job_info.dict()
        user_preferences = request.user_preferences.dict() if request.user_preferences else None

        # Generate template
        result = referral_template_service.generate_referral_template(
            db=db,
            user_id=current_user.user_id,
            contact_info=contact_info,
            job_info=job_info,
            user_preferences=user_preferences
        )

        return TemplateResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate template: {str(e)}"
        )

@router.get("/", response_model=List[TemplateListItem])
def get_user_templates(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's referral templates with pagination
    """
    try:
        templates = referral_template_service.get_user_templates(
            db=db,
            user_id=current_user.user_id,
            limit=min(limit, 100),  # Cap at 100
            offset=offset
        )

        return [TemplateListItem(**template) for template in templates]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch templates: {str(e)}"
        )

@router.get("/stats", response_model=TemplateStats)
def get_template_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's template statistics
    """
    try:
        stats = referral_template_service.get_template_stats(
            db=db,
            user_id=current_user.user_id
        )

        return TemplateStats(**stats)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch template stats: {str(e)}"
        )

@router.post("/{template_id}/feedback")
def record_template_feedback(
    template_id: UUID,
    feedback: TemplateFeedback,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Record feedback about template effectiveness
    """
    try:
        # Verify template belongs to user
        _verify_template_ownership(db, template_id, current_user.user_id)

        referral_template_service.record_template_feedback(
            db=db,
            template_id=template_id,
            user_id=current_user.user_id,
            feedback_data=feedback.dict()
        )

        return {"message": "Feedback recorded successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record feedback: {str(e)}"
        )

@router.post("/{template_id}/mark-sent")
def mark_template_sent(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a template as sent
    """
    try:
        # Verify template belongs to user
        _verify_template_ownership(db, template_id, current_user.user_id)

        from sqlalchemy import text
        query = text("""
            UPDATE referral_templates
            SET was_sent = true, sent_at = NOW()
            WHERE id = :template_id AND user_id = :user_id
        """)

        db.execute(query, {
            'template_id': template_id,
            'user_id': current_user.user_id
        })
        db.commit()

        return {"message": "Template marked as sent"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark template as sent: {str(e)}"
        )

@router.get("/{template_id}", response_model=TemplateListItem)
def get_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific template by ID
    """
    try:
        from sqlalchemy import text
        query = text("""
            SELECT rt.id, rt.contact_name, rt.contact_company, rt.subject_line,
                   rt.email_body, rt.template_style, rt.was_sent, rt.sent_at,
                   rt.got_response, rt.response_type, rt.effectiveness_score,
                   rt.created_at,
                   tf.response_quality_score, tf.user_satisfaction_score
            FROM referral_templates rt
            LEFT JOIN template_feedback tf ON rt.id = tf.template_id
            WHERE rt.id = :template_id AND rt.user_id = :user_id
        """)

        result = db.execute(query, {
            'template_id': template_id,
            'user_id': current_user.user_id
        })
        row = result.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        template_data = {
            'id': str(row.id),
            'contact_name': row.contact_name,
            'contact_company': row.contact_company,
            'subject_line': row.subject_line,
            'email_body': row.email_body,
            'template_style': row.template_style,
            'was_sent': row.was_sent,
            'sent_at': row.sent_at,
            'got_response': row.got_response,
            'response_type': row.response_type,
            'effectiveness_score': row.effectiveness_score,
            'created_at': row.created_at,
            'user_feedback': {
                'response_quality_score': row.response_quality_score,
                'user_satisfaction_score': row.user_satisfaction_score
            } if row.response_quality_score else None
        }

        return TemplateListItem(**template_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch template: {str(e)}"
        )

@router.delete("/{template_id}")
def delete_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a template
    """
    try:
        # Verify template belongs to user
        _verify_template_ownership(db, template_id, current_user.user_id)

        from sqlalchemy import text
        query = text("""
            DELETE FROM referral_templates
            WHERE id = :template_id AND user_id = :user_id
        """)

        result = db.execute(query, {
            'template_id': template_id,
            'user_id': current_user.user_id
        })
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        return {"message": "Template deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}"
        )

# Preferences endpoints
@router.get("/preferences/current")
def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's referral preferences
    """
    try:
        from sqlalchemy import text
        query = text("""
            SELECT preferred_tone, preferred_length, include_resume, include_portfolio,
                   auto_follow_up, follow_up_days, max_templates_per_day, learning_enabled
            FROM user_referral_preferences
            WHERE user_id = :user_id
        """)

        result = db.execute(query, {'user_id': current_user.user_id})
        row = result.fetchone()

        if row:
            return {
                'preferred_tone': row.preferred_tone,
                'preferred_length': row.preferred_length,
                'include_resume': row.include_resume,
                'include_portfolio': row.include_portfolio,
                'auto_follow_up': row.auto_follow_up,
                'follow_up_days': row.follow_up_days,
                'max_templates_per_day': row.max_templates_per_day,
                'learning_enabled': row.learning_enabled
            }

        # Return defaults if no preferences set
        return {
            'preferred_tone': 'professional',
            'preferred_length': 'medium',
            'include_resume': True,
            'include_portfolio': False,
            'auto_follow_up': True,
            'follow_up_days': 15,
            'max_templates_per_day': 5,
            'learning_enabled': True
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch preferences: {str(e)}"
        )

@router.put("/preferences")
def update_user_preferences(
    preferences: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's referral preferences
    """
    try:
        from sqlalchemy import text

        # Upsert preferences
        query = text("""
            INSERT INTO user_referral_preferences (
                user_id, preferred_tone, preferred_length, include_resume,
                include_portfolio, auto_follow_up, follow_up_days,
                max_templates_per_day, learning_enabled
            ) VALUES (
                :user_id, :preferred_tone, :preferred_length, :include_resume,
                :include_portfolio, :auto_follow_up, :follow_up_days,
                :max_templates_per_day, :learning_enabled
            )
            ON CONFLICT (user_id) DO UPDATE SET
                preferred_tone = EXCLUDED.preferred_tone,
                preferred_length = EXCLUDED.preferred_length,
                include_resume = EXCLUDED.include_resume,
                include_portfolio = EXCLUDED.include_portfolio,
                auto_follow_up = EXCLUDED.auto_follow_up,
                follow_up_days = EXCLUDED.follow_up_days,
                max_templates_per_day = EXCLUDED.max_templates_per_day,
                learning_enabled = EXCLUDED.learning_enabled,
                updated_at = NOW()
        """)

        db.execute(query, {
            'user_id': current_user.user_id,
            'preferred_tone': preferences.get('preferred_tone', 'professional'),
            'preferred_length': preferences.get('preferred_length', 'medium'),
            'include_resume': preferences.get('include_resume', True),
            'include_portfolio': preferences.get('include_portfolio', False),
            'auto_follow_up': preferences.get('auto_follow_up', True),
            'follow_up_days': preferences.get('follow_up_days', 15),
            'max_templates_per_day': preferences.get('max_templates_per_day', 5),
            'learning_enabled': preferences.get('learning_enabled', True)
        })
        db.commit()

        return {"message": "Preferences updated successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )

# Helper functions
def _verify_template_ownership(db: Session, template_id: UUID, user_id: str):
    """Verify that the template belongs to the user"""
    from sqlalchemy import text
    query = text("SELECT id FROM referral_templates WHERE id = :template_id AND user_id = :user_id")
    result = db.execute(query, {'template_id': template_id, 'user_id': user_id})

    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or access denied"
        )

def _get_today_template_count(db: Session, user_id: str) -> int:
    """Get the number of templates generated today by the user"""
    from sqlalchemy import text
    query = text("""
        SELECT COUNT(*)
        FROM referral_templates
        WHERE user_id = :user_id AND DATE(created_at) = CURRENT_DATE
    """)
    result = db.execute(query, {'user_id': user_id})
    return result.scalar() or 0