import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import re
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.job import JobListing, JobApplication
from app.models.email_models import EmailEvent

logger = logging.getLogger(__name__)

class JobMatcher:
    """Job matching engine for email-driven status updates"""
    
    def __init__(self):
        self.min_confidence_threshold = 0.6
        self.high_confidence_threshold = 0.8
        
    def find_matching_job(
        self, 
        db: Session, 
        user_id: str, 
        company_name: str, 
        job_title: str = None,
        email_received_date: datetime = None
    ) -> Optional[Tuple[int, float]]:
        """
        Find the best matching job for an email
        
        Returns:
            Tuple of (job_id, confidence_score) or None if no good match
        """
        try:
            # Get user's job applications
            user_applications = db.query(JobApplication).filter(
                JobApplication.user_id == user_id,
                JobApplication.application_status.in_(['interested', 'applied', 'interviewed'])
            ).all()
            
            if not user_applications:
                logger.info(f"No job applications found for user {user_id}")
                return None
            
            best_match = None
            best_score = 0.0
            
            for application in user_applications:
                # Get the job listing
                job = db.query(JobListing).filter(JobListing.id == application.job_id).first()
                if not job:
                    continue
                
                score = self._calculate_match_score(
                    job, company_name, job_title, email_received_date
                )
                
                if score > best_score and score >= self.min_confidence_threshold:
                    best_score = score
                    best_match = job.id
            
            if best_match:
                logger.info(f"Found job match: Job ID {best_match} with confidence {best_score:.2f}")
                return (best_match, best_score)
            else:
                logger.info(f"No job match found above threshold {self.min_confidence_threshold}")
                return None
                
        except Exception as e:
            logger.error(f"Error finding matching job: {e}")
            return None
    
    def _calculate_match_score(
        self, 
        job: JobListing, 
        company_name: str, 
        job_title: str = None,
        email_date: datetime = None
    ) -> float:
        """
        Calculate match score between email and job listing
        
        Returns:
            Score between 0.0 and 1.0
        """
        if not company_name:
            return 0.0
        
        scores = []
        weights = []
        
        # 1. Company name matching (40% weight)
        company_score = self._match_company_name(job.company, company_name)
        scores.append(company_score)
        weights.append(0.4)
        
        # 2. Job title matching (30% weight)
        if job_title and job.title:
            title_score = self._match_job_title(job.title, job_title)
            scores.append(title_score)
            weights.append(0.3)
        else:
            scores.append(0.0)
            weights.append(0.3)
        
        # 3. Temporal proximity (20% weight)
        if email_date and job.created_at:
            time_score = self._calculate_temporal_score(job.created_at, email_date)
            scores.append(time_score)
            weights.append(0.2)
        else:
            scores.append(0.0)
            weights.append(0.2)
        
        # 4. Location matching (10% weight)
        if job.location:
            location_score = self._match_location(job.location, company_name)
            scores.append(location_score)
            weights.append(0.1)
        else:
            scores.append(0.0)
            weights.append(0.1)
        
        # Calculate weighted average
        total_score = sum(score * weight for score, weight in zip(scores, weights))
        
        return min(total_score, 1.0)
    
    def _match_company_name(self, job_company: str, email_company: str) -> float:
        """Match company names using various strategies"""
        if not job_company or not email_company:
            return 0.0
        
        # Normalize company names
        job_company_clean = self._normalize_company_name(job_company)
        email_company_clean = self._normalize_company_name(email_company)
        
        # Exact match
        if job_company_clean == email_company_clean:
            return 1.0
        
        # Contains match
        if job_company_clean in email_company_clean or email_company_clean in job_company_clean:
            return 0.9
        
        # Fuzzy match
        similarity = SequenceMatcher(None, job_company_clean, email_company_clean).ratio()
        
        # Domain matching (if email company looks like a domain)
        if '@' in email_company or '.' in email_company:
            domain_score = self._match_domain(job_company, email_company)
            return max(similarity, domain_score)
        
        return similarity
    
    def _normalize_company_name(self, company: str) -> str:
        """Normalize company name for comparison"""
        if not company:
            return ""
        
        # Convert to lowercase
        company = company.lower()
        
        # Remove common suffixes
        suffixes = [' inc', ' corp', ' llc', ' ltd', ' company', ' co', ' & co']
        for suffix in suffixes:
            if company.endswith(suffix):
                company = company[:-len(suffix)]
        
        # Remove special characters
        company = re.sub(r'[^\w\s]', '', company)
        
        # Remove extra whitespace
        company = ' '.join(company.split())
        
        return company
    
    def _match_domain(self, job_company: str, email_company: str) -> float:
        """Match company name against email domain"""
        try:
            # Extract domain from email company
            if '@' in email_company:
                domain = email_company.split('@')[1]
            elif '.' in email_company:
                domain = email_company
            else:
                return 0.0
            
            # Remove .com, .org, etc.
            domain = re.sub(r'\.(com|org|net|edu|gov)$', '', domain)
            
            # Compare with job company
            job_company_clean = self._normalize_company_name(job_company)
            
            if domain in job_company_clean or job_company_clean in domain:
                return 0.8
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _match_job_title(self, job_title: str, email_title: str) -> float:
        """Match job titles"""
        if not job_title or not email_title:
            return 0.0
        
        # Normalize titles
        job_title_clean = job_title.lower()
        email_title_clean = email_title.lower()
        
        # Exact match
        if job_title_clean == email_title_clean:
            return 1.0
        
        # Contains match
        if job_title_clean in email_title_clean or email_title_clean in job_title_clean:
            return 0.9
        
        # Fuzzy match
        similarity = SequenceMatcher(None, job_title_clean, email_title_clean).ratio()
        
        # Keyword matching
        job_words = set(job_title_clean.split())
        email_words = set(email_title_clean.split())
        
        if job_words and email_words:
            common_words = job_words.intersection(email_words)
            keyword_score = len(common_words) / max(len(job_words), len(email_words))
            return max(similarity, keyword_score * 0.8)
        
        return similarity
    
    def _calculate_temporal_score(self, job_date: datetime, email_date: datetime) -> float:
        """Calculate temporal proximity score"""
        if not job_date or not email_date:
            return 0.0
        
        # Calculate days difference
        days_diff = abs((email_date - job_date).days)
        
        # Score based on proximity (higher score for closer dates)
        if days_diff <= 1:
            return 1.0
        elif days_diff <= 7:
            return 0.9
        elif days_diff <= 30:
            return 0.7
        elif days_diff <= 90:
            return 0.5
        else:
            return 0.2
    
    def _match_location(self, job_location: str, company_name: str) -> float:
        """Simple location matching (can be enhanced later)"""
        # For now, return a low score as location matching is complex
        return 0.3
    
    def should_auto_update_status(self, confidence_score: float) -> bool:
        """Determine if status should be auto-updated based on confidence"""
        return confidence_score >= self.high_confidence_threshold
    
    def get_status_update_mapping(self, email_type: str) -> Optional[str]:
        """Map email type to job application status"""
        status_mapping = {
            'application_confirmation': 'applied',
            'application_rejection': 'rejected',
            'interview_invitation': 'interviewed',
            'offer_letter': 'hired'
        }
        
        return status_mapping.get(email_type)
    
    def log_match_attempt(
        self, 
        db: Session, 
        user_id: str, 
        email_event_id: int, 
        matched_job_id: Optional[int], 
        confidence_score: float,
        email_type: str
    ):
        """Log match attempt for analytics"""
        try:
            # This could be enhanced to store in a separate analytics table
            logger.info(
                f"Match attempt - User: {user_id}, Email: {email_event_id}, "
                f"Job: {matched_job_id}, Confidence: {confidence_score:.2f}, "
                f"Type: {email_type}"
            )
        except Exception as e:
            logger.error(f"Error logging match attempt: {e}") 