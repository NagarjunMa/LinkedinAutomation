from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from fastapi import HTTPException
import logging

from app.models.referral import ReferralContact, ReferralEmailDraft, ReferralEmailSent
from app.models.job import JobListing
from app.models.user import User
from app.schemas.referral import (
    ReferralContactCreate,
    ReferralEmailGenerateRequest,
    ReferralDraftResponse
)
from app.services.referral_email_generator import ReferralEmailGenerator

logger = logging.getLogger(__name__)


class ReferralService:
    """Main service for handling referral operations"""

    def __init__(self, db: Session):
        self.db = db
        self.email_generator = ReferralEmailGenerator(db)

    async def get_or_create_contact(
        self,
        user_id: str,
        contact_info: Dict
    ) -> ReferralContact:
        """Get existing contact or create new one"""
        try:
            # Check if contact already exists
            existing_contact = self.db.query(ReferralContact).filter(
                and_(
                    ReferralContact.user_id == user_id,
                    ReferralContact.contact_email == contact_info['contact_email']
                )
            ).first()

            if existing_contact:
                return existing_contact

            # Create new contact
            contact = ReferralContact(
                user_id=user_id,
                contact_name=contact_info['name'],
                contact_email=contact_info['contact_email'],
                company=contact_info['company'],
                position=contact_info.get('position'),
                contact_relationship=contact_info.get('relationship')
            )

            self.db.add(contact)
            self.db.commit()
            self.db.refresh(contact)

            return contact

        except Exception as e:
            logger.error(f"Error creating/getting contact: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to create contact")

    async def create_referral_request(
        self,
        user_id: str,
        job_id: int,
        contact_info: Dict
    ) -> ReferralDraftResponse:
        """Complete referral email creation workflow"""
        try:
            # Get user profile and job data
            user_profile = await self.email_generator.get_user_profile(user_id)
            job_data = await self.email_generator.get_job_data(job_id)

            # Get or create contact
            contact = await self.get_or_create_contact(user_id, contact_info)

            # Generate email with AI
            email_draft = await self.email_generator.generate_referral_email(
                user_profile,
                job_data,
                contact_info
            )

            # Save draft
            draft = await self.save_draft(
                user_id,
                job_id,
                str(contact.id),
                email_draft
            )

            return ReferralDraftResponse(
                draft=draft,
                contact=contact
            )

        except Exception as e:
            logger.error(f"Error creating referral request: {e}")
            raise HTTPException(status_code=500, detail="Failed to create referral request")

    async def generate_email_only(
        self,
        user_id: str,
        request: ReferralEmailGenerateRequest
    ) -> Dict:
        """Generate email without saving (for preview)"""
        try:
            # Get user profile
            user_profile = await self.email_generator.get_user_profile(user_id)

            # Get job data if job_id provided
            job_data = {}
            if request.job_id:
                job_data = await self.email_generator.get_job_data(request.job_id)

            # Generate email
            email_content = await self.email_generator.generate_referral_email(
                user_profile,
                job_data,
                request.contact_info.dict()
            )

            return email_content

        except Exception as e:
            logger.error(f"Error generating email: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate email")

    async def save_draft(
        self,
        user_id: str,
        job_id: Optional[int],
        contact_id: str,
        email_content: Dict
    ) -> ReferralEmailDraft:
        """Save email draft with version control"""
        try:
            # Get existing drafts for this job-contact pair
            existing_drafts = self.db.query(ReferralEmailDraft).filter(
                and_(
                    ReferralEmailDraft.user_id == user_id,
                    ReferralEmailDraft.job_id == job_id,
                    ReferralEmailDraft.contact_id == contact_id
                )
            ).all()

            version = len(existing_drafts) + 1

            # Mark previous drafts as not primary
            if existing_drafts:
                self.db.query(ReferralEmailDraft).filter(
                    and_(
                        ReferralEmailDraft.user_id == user_id,
                        ReferralEmailDraft.job_id == job_id,
                        ReferralEmailDraft.contact_id == contact_id
                    )
                ).update({'is_primary': False})

            # Create new draft
            draft = ReferralEmailDraft(
                user_id=user_id,
                job_id=job_id,
                contact_id=contact_id,
                subject=email_content['subject'],
                email_body=email_content['body'],
                template_used=email_content['template_used'],
                version=version,
                is_primary=True
            )

            self.db.add(draft)
            self.db.commit()
            self.db.refresh(draft)

            return draft

        except Exception as e:
            logger.error(f"Error saving draft: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save draft")

    async def update_draft(
        self,
        draft_id: str,
        user_id: str,
        updates: Dict
    ) -> ReferralEmailDraft:
        """Update existing draft"""
        try:
            draft = self.db.query(ReferralEmailDraft).filter(
                and_(
                    ReferralEmailDraft.id == draft_id,
                    ReferralEmailDraft.user_id == user_id
                )
            ).first()

            if not draft:
                raise HTTPException(status_code=404, detail="Draft not found")

            # Update fields
            if 'subject' in updates:
                draft.subject = updates['subject']
            if 'email_body' in updates:
                draft.email_body = updates['email_body']

            self.db.commit()
            self.db.refresh(draft)

            return draft

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating draft: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to update draft")

    async def send_referral_email(
        self,
        user_id: str,
        draft_id: str
    ) -> Dict:
        """Record email as sent (actual sending would integrate with email service)"""
        try:
            # Get draft
            draft = self.db.query(ReferralEmailDraft).filter(
                and_(
                    ReferralEmailDraft.id == draft_id,
                    ReferralEmailDraft.user_id == user_id
                )
            ).first()

            if not draft:
                raise HTTPException(status_code=404, detail="Draft not found")

            # Check if already sent
            existing_send = self.db.query(ReferralEmailSent).filter(
                ReferralEmailSent.draft_id == draft_id
            ).first()

            if existing_send:
                raise HTTPException(status_code=400, detail="Email already sent")

            # Record send
            email_sent = ReferralEmailSent(
                user_id=user_id,
                job_id=draft.job_id,
                contact_id=draft.contact_id,
                draft_id=draft_id
            )

            self.db.add(email_sent)
            self.db.commit()
            self.db.refresh(email_sent)

            return {
                "success": True,
                "message": "Email sent successfully",
                "sent_id": str(email_sent.id)
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to send email")

    async def get_user_contacts(self, user_id: str, limit: int = 50, offset: int = 0) -> Dict:
        """Get user's referral contacts"""
        try:
            # Get total count
            total = self.db.query(ReferralContact).filter(
                ReferralContact.user_id == user_id
            ).count()

            # Get contacts with pagination
            contacts = self.db.query(ReferralContact).filter(
                ReferralContact.user_id == user_id
            ).order_by(desc(ReferralContact.created_at)).offset(offset).limit(limit).all()

            return {
                "contacts": contacts,
                "total_count": total,
                "limit": limit,
                "offset": offset
            }

        except Exception as e:
            logger.error(f"Error getting user contacts: {e}")
            raise HTTPException(status_code=500, detail="Failed to get contacts")

    async def get_user_drafts(
        self,
        user_id: str,
        job_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict:
        """Get user's email drafts"""
        try:
            query = self.db.query(ReferralEmailDraft).filter(
                ReferralEmailDraft.user_id == user_id
            )

            if job_id:
                query = query.filter(ReferralEmailDraft.job_id == job_id)

            total = query.count()
            drafts = query.order_by(desc(ReferralEmailDraft.created_at)).offset(offset).limit(limit).all()

            return {
                "drafts": drafts,
                "total_count": total,
                "limit": limit,
                "offset": offset
            }

        except Exception as e:
            logger.error(f"Error getting user drafts: {e}")
            raise HTTPException(status_code=500, detail="Failed to get drafts")

    async def get_referral_analytics(self, user_id: str) -> Dict:
        """Get referral email statistics"""
        try:
            # This week's referrals
            week_ago = datetime.utcnow() - timedelta(days=7)
            this_week_count = self.db.query(ReferralEmailSent).filter(
                and_(
                    ReferralEmailSent.user_id == user_id,
                    ReferralEmailSent.sent_at >= week_ago
                )
            ).count()

            # Total referrals
            total_count = self.db.query(ReferralEmailSent).filter(
                ReferralEmailSent.user_id == user_id
            ).count()

            # Response rate
            responses_query = self.db.query(ReferralEmailSent).filter(
                ReferralEmailSent.user_id == user_id
            )
            total_sent = responses_query.count()
            responded = responses_query.filter(
                ReferralEmailSent.response_received == True
            ).count()

            response_rate = (responded / total_sent * 100) if total_sent > 0 else 0

            # Trend data (last 30 days)
            start_date = datetime.utcnow() - timedelta(days=30)
            trend_data = self.db.query(
                func.date(ReferralEmailSent.sent_at).label('date'),
                func.count().label('count')
            ).filter(
                and_(
                    ReferralEmailSent.user_id == user_id,
                    ReferralEmailSent.sent_at >= start_date
                )
            ).group_by(
                func.date(ReferralEmailSent.sent_at)
            ).order_by('date').all()

            trend_list = [
                {"date": str(row.date), "count": row.count}
                for row in trend_data
            ]

            return {
                "this_week": this_week_count,
                "total_sent": total_count,
                "response_rate": round(response_rate, 1),
                "trend_data": trend_list
            }

        except Exception as e:
            logger.error(f"Error getting referral analytics: {e}")
            raise HTTPException(status_code=500, detail="Failed to get analytics")

    async def mark_response_received(
        self,
        user_id: str,
        sent_id: str,
        response_date: Optional[datetime] = None
    ) -> Dict:
        """Mark that a response was received for a sent email"""
        try:
            email_sent = self.db.query(ReferralEmailSent).filter(
                and_(
                    ReferralEmailSent.id == sent_id,
                    ReferralEmailSent.user_id == user_id
                )
            ).first()

            if not email_sent:
                raise HTTPException(status_code=404, detail="Sent email not found")

            email_sent.response_received = True
            email_sent.response_date = response_date or datetime.utcnow()

            self.db.commit()

            return {"success": True, "message": "Response marked as received"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error marking response: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to mark response")