"""
Simplified Referral API endpoints.
Paste-and-parse functionality for extracting contacts and generating referral messages.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.core.ai_service import get_ai_service
from app.core.auth import get_authenticated_user_id
from app.core.rate_limiter import check_ai_rate_limit
from app.services.simple_referral_service import SimpleReferralService

logger = logging.getLogger(__name__)

router = APIRouter()


class ProfileParseRequest(BaseModel):
    """Request model for parsing LinkedIn profile text."""
    profile_text: str = Field(..., description="LinkedIn profile text to parse")


class ContactInfo(BaseModel):
    """Contact information extracted from profile."""
    name: str
    title: str
    company: str
    location: str
    industry: str
    experience_summary: str
    skills: List[str]
    education: str
    mutual_connections: str
    years_experience: int
    extracted_at: str
    source: str


class ProfileParseResponse(BaseModel):
    """Response model for profile parsing."""
    success: bool
    contact_info: ContactInfo
    extraction_method: str


class MultipleContactsResponse(BaseModel):
    """Response model for multiple contacts extraction."""
    success: bool
    contacts: List[ContactInfo]
    total_extracted: int


class MessageGenerationRequest(BaseModel):
    """Request model for generating referral messages."""
    contact_info: Dict[str, Any] = Field(..., description="Contact information")
    job_info: Optional[Dict[str, Any]] = Field(None, description="Optional job information")
    message_type: str = Field("linkedin", description="Message type: linkedin, email, or informal")


class ReferralMessage(BaseModel):
    """Generated referral message."""
    type: str
    message: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    contact_name: str
    contact_company: str
    character_count: Optional[int] = None
    generated_at: str


class MessageGenerationResponse(BaseModel):
    """Response model for message generation."""
    success: bool
    message_data: ReferralMessage


class MessageTemplatesResponse(BaseModel):
    """Response model for available message templates."""
    templates: Dict[str, Any]
    tips: List[str]


@router.post("/parse-profile", response_model=ProfileParseResponse)
async def parse_linkedin_profile(
    request: ProfileParseRequest,
    db: Session = Depends(get_db),
    ai_service = Depends(get_ai_service),
    user_id: str = Depends(get_authenticated_user_id)
):
    """
    Parse LinkedIn profile text to extract contact information.

    This endpoint takes raw LinkedIn profile text (copied from browser)
    and extracts structured contact information using AI.

    Args:
        request: Contains the profile text to parse
        db: Database session
        ai_service: AI service instance
        user_id: Authenticated user ID

    Returns:
        Extracted contact information
    """
    try:
        if not request.profile_text or len(request.profile_text.strip()) < 20:
            raise HTTPException(
                status_code=400,
                detail="Profile text is too short. Please paste the complete LinkedIn profile."
            )

        if len(request.profile_text) > 10000:
            raise HTTPException(
                status_code=400,
                detail="Profile text is too long. Please paste only the relevant profile section."
            )

        # Check rate limit for profile parsing
        check_ai_rate_limit(user_id, "profile_parsing")

        logger.info(f"Parsing LinkedIn profile for user {user_id}")

        # Initialize service
        service = SimpleReferralService(ai_service)

        # Parse profile
        contact_info = await service.parse_linkedin_profile(request.profile_text)

        return ProfileParseResponse(
            success=True,
            contact_info=ContactInfo(**contact_info),
            extraction_method=contact_info.get("source", "ai_extraction")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to parse profile. Please check the format and try again."
        )


@router.post("/parse-multiple", response_model=MultipleContactsResponse)
async def parse_multiple_contacts(
    request: ProfileParseRequest,
    db: Session = Depends(get_db),
    ai_service = Depends(get_ai_service),
    user_id: str = Depends(get_authenticated_user_id)
):
    """
    Extract multiple contacts from text (search results, company directory).

    This endpoint can parse text containing multiple LinkedIn profiles
    or contact information and extract structured data for each contact.

    Args:
        request: Contains text with multiple profiles
        db: Database session
        ai_service: AI service instance
        user_id: Authenticated user ID

    Returns:
        List of extracted contacts
    """
    try:
        if not request.profile_text or len(request.profile_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Text is too short. Please paste content with multiple profiles."
            )

        if len(request.profile_text) > 20000:
            raise HTTPException(
                status_code=400,
                detail="Text is too long. Please limit to 10-15 profiles maximum."
            )

        logger.info(f"Extracting multiple contacts for user {user_id}")

        # Initialize service
        service = SimpleReferralService(ai_service)

        # Extract multiple contacts
        contacts = service.extract_multiple_contacts(request.profile_text)

        # Convert to response format
        contact_objects = []
        for contact in contacts:
            try:
                contact_objects.append(ContactInfo(**contact))
            except Exception as e:
                logger.warning(f"Skipping invalid contact data: {e}")
                continue

        return MultipleContactsResponse(
            success=True,
            contacts=contact_objects,
            total_extracted=len(contact_objects)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting multiple contacts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to extract contacts. Please check the format and try again."
        )


@router.post("/generate-message", response_model=MessageGenerationResponse)
async def generate_referral_message(
    request: MessageGenerationRequest,
    db: Session = Depends(get_db),
    ai_service = Depends(get_ai_service),
    user_id: str = Depends(get_authenticated_user_id)
):
    """
    Generate a personalized referral message.

    This endpoint creates personalized referral messages using contact info,
    optional job context, and user's professional background.

    Args:
        request: Contains contact info, job info, and message type
        db: Database session
        ai_service: AI service instance
        user_id: Authenticated user ID

    Returns:
        Generated referral message
    """
    try:
        if request.message_type not in ["linkedin", "email", "informal"]:
            raise HTTPException(
                status_code=400,
                detail="Message type must be 'linkedin', 'email', or 'informal'"
            )

        if not request.contact_info:
            raise HTTPException(
                status_code=400,
                detail="Contact information is required"
            )

        # Check rate limit for referral message generation
        check_ai_rate_limit(user_id, "referral_message")

        logger.info(f"Generating {request.message_type} message for user {user_id}")

        # Initialize service
        referral_service = SimpleReferralService(ai_service)

        # Get basic user context (simplified)
        user_context = {
            "current_title": "Professional",
            "years_experience": "Several",
            "skills": []
        }

        # Use simplified user context for message generation
        message_user_context = user_context

        # Generate message
        message_data = await referral_service.generate_referral_message(
            contact_info=request.contact_info,
            job_info=request.job_info,
            user_context=message_user_context,
            message_type=request.message_type
        )

        return MessageGenerationResponse(
            success=True,
            message_data=ReferralMessage(**message_data)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate message. Please try again."
        )


@router.get("/templates", response_model=MessageTemplatesResponse)
async def get_message_templates(
    db: Session = Depends(get_db),
    ai_service = Depends(get_ai_service),
    user_id: str = Depends(get_authenticated_user_id)
):
    """
    Get available message templates and tips.

    This endpoint provides information about available message types,
    their characteristics, and tips for effective referral requests.

    Args:
        db: Database session
        ai_service: AI service instance
        user_id: Authenticated user ID

    Returns:
        Available templates and usage tips
    """
    try:
        logger.info(f"Getting message templates for user {user_id}")

        # Initialize service
        service = SimpleReferralService(ai_service)

        # Get templates
        templates_data = service.get_message_templates()

        return MessageTemplatesResponse(**templates_data)

    except Exception as e:
        logger.error(f"Error getting templates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get templates. Please try again."
        )


@router.post("/parse-and-generate")
async def parse_and_generate_message(
    profile_text: str = Body(..., description="LinkedIn profile text"),
    job_info: Optional[Dict[str, Any]] = Body(None, description="Optional job information"),
    message_type: str = Body("linkedin", description="Message type"),
    db: Session = Depends(get_db),
    ai_service = Depends(get_ai_service),
    user_id: str = Depends(get_authenticated_user_id)
):
    """
    Parse profile and generate message in one step.

    This endpoint combines profile parsing and message generation
    for a streamlined workflow.

    Args:
        profile_text: LinkedIn profile text to parse
        job_info: Optional job information for context
        message_type: Type of message to generate
        db: Database session
        ai_service: AI service instance
        user_id: Authenticated user ID

    Returns:
        Parsed contact info and generated message
    """
    try:
        if not profile_text or len(profile_text.strip()) < 20:
            raise HTTPException(
                status_code=400,
                detail="Profile text is too short. Please paste the complete LinkedIn profile."
            )

        if message_type not in ["linkedin", "email", "informal"]:
            raise HTTPException(
                status_code=400,
                detail="Message type must be 'linkedin', 'email', or 'informal'"
            )

        logger.info(f"Parse and generate workflow for user {user_id}")

        # Initialize services
        referral_service = SimpleReferralService(ai_service)
        context_service = UserContextService(ai_service)

        # Step 1: Parse profile
        contact_info = await referral_service.parse_linkedin_profile(profile_text)

        # Step 2: Get simplified user context
        message_user_context = {
            "current_title": "Professional",
            "years_experience": "Several",
            "skills": []
        }

        # Step 3: Generate message
        message_data = await referral_service.generate_referral_message(
            contact_info=contact_info,
            job_info=job_info,
            user_context=message_user_context,
            message_type=message_type
        )

        return {
            "success": True,
            "contact_info": ContactInfo(**contact_info),
            "message_data": ReferralMessage(**message_data),
            "extraction_method": contact_info.get("source", "ai_extraction")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in parse and generate workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to parse profile and generate message. Please try again."
        )