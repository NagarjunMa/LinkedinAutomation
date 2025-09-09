import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Contact, JobListing
from app.services.apollo_client import ApolloClient
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ContactCache:
    """Cache contacts by company to reduce API calls"""
    
    def __init__(self, db: Session, ttl_days: int = 30):
        self.db = db
        self.ttl_days = ttl_days
    
    def get_cached_contacts(self, company: str, contact_type: str) -> List[Contact]:
        """Get cached contacts for a company and type"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.ttl_days)
        
        contacts = self.db.query(Contact).filter(
            and_(
                Contact.company.ilike(f"%{company}%"),
                Contact.type == contact_type,
                Contact.created_at >= cutoff_date
            )
        ).all()
        
        return contacts
    
    def cache_contacts(self, contacts: List[Contact]):
        """Cache contacts in the database"""
        for contact in contacts:
            # Check if contact already exists
            existing = self.db.query(Contact).filter(
                Contact.apollo_id == contact.apollo_id
            ).first()
            
            if not existing:
                self.db.add(contact)
        
        self.db.commit()
        logger.info(f"Cached {len(contacts)} new contacts")

class ContactDiscoveryService:
    """Service for discovering contacts using Apollo.io"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = ContactCache(db, ttl_days=30)
        self.apollo_client = None
    
    async def __aenter__(self):
        self.apollo_client = ApolloClient(self.db)
        await self.apollo_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.apollo_client:
            await self.apollo_client.__aexit__(exc_type, exc_val, exc_tb)
    
    def _apollo_to_contact(self, apollo_person: Dict[str, Any], contact_type: str) -> Contact:
        """Convert Apollo.io person data to Contact model"""
        
        # Extract location
        location_parts = []
        if apollo_person.get('city'):
            location_parts.append(apollo_person['city'])
        if apollo_person.get('state'):
            location_parts.append(apollo_person['state'])
        if apollo_person.get('country'):
            location_parts.append(apollo_person['country'])
        
        location = ", ".join(location_parts) if location_parts else None
        
        # Extract specializations
        specializations = []
        if apollo_person.get('skills'):
            specializations.extend(apollo_person['skills'])
        if apollo_person.get('keywords'):
            specializations.extend(apollo_person['keywords'])
        
        return Contact(
            type=contact_type,
            company=apollo_person.get('organization_name', ''),
            name=apollo_person.get('name', ''),
            title=apollo_person.get('title', ''),
            email=apollo_person.get('email', ''),
            linkedin_url=apollo_person.get('linkedin_url', ''),
            location=location,
            department=apollo_person.get('organization_department', ''),
            seniority=apollo_person.get('seniority', ''),
            specializations=specializations,
            confidence_score=apollo_person.get('confidence_score', 0.0),
            apollo_id=apollo_person.get('id', '')
        )
    
    async def discover_contacts_for_job(
        self, 
        job: JobListing, 
        max_recruiters: int = 3,
        max_engineers: int = 3
    ) -> Dict[str, List[Contact]]:
        """Discover contacts for a specific job posting"""
        
        logger.info(f"Discovering contacts for job: {job.title} at {job.company}")
        
        # Check cache first
        cached_recruiters = self.cache.get_cached_contacts(job.company, 'recruiter')
        cached_engineers = self.cache.get_cached_contacts(job.company, 'engineer')
        
        results = {
            'recruiters': cached_recruiters[:max_recruiters],
            'engineers': cached_engineers[:max_engineers]
        }
        
        # If we have enough cached contacts, return them
        if len(results['recruiters']) >= max_recruiters and len(results['engineers']) >= max_engineers:
            logger.info(f"Using cached contacts for {job.company}")
            return results
        
        # Discover new contacts if needed
        try:
            # Discover recruiters
            if len(results['recruiters']) < max_recruiters:
                needed_recruiters = max_recruiters - len(results['recruiters'])
                new_recruiters = await self._discover_contacts(
                    job.company, 'recruiter', job.location, needed_recruiters
                )
                results['recruiters'].extend(new_recruiters)
            
            # Discover engineers
            if len(results['engineers']) < max_engineers:
                needed_engineers = max_engineers - len(results['engineers'])
                new_engineers = await self._discover_contacts(
                    job.company, 'engineer', job.location, needed_engineers
                )
                results['engineers'].extend(new_engineers)
            
            # Cache new contacts
            all_new_contacts = []
            all_new_contacts.extend([c for c in results['recruiters'] if not c.id])
            all_new_contacts.extend([c for c in results['engineers'] if not c.id])
            
            if all_new_contacts:
                self.cache.cache_contacts(all_new_contacts)
            
        except Exception as e:
            if "API_INACCESSIBLE" in str(e) or "free plan" in str(e).lower():
                logger.warning(f"Apollo.io free plan limitation: {e}")
                logger.info("Contact discovery requires Apollo.io paid plan")
            else:
                logger.error(f"Error discovering contacts for job {job.id}: {e}")
        
        return results
    
    async def _discover_contacts(
        self, 
        company: str, 
        contact_type: str, 
        location: Optional[str] = None,
        limit: int = 3
    ) -> List[Contact]:
        """Discover contacts of a specific type for a company"""
        
        try:
            # Search Apollo.io
            apollo_people = await self.apollo_client.search_people_by_company(
                company, contact_type, location, limit
            )
            
            # Convert to Contact objects
            contacts = []
            for person in apollo_people:
                contact = self._apollo_to_contact(person, contact_type)
                contacts.append(contact)
            
            logger.info(f"Discovered {len(contacts)} {contact_type}s for {company}")
            return contacts
            
        except Exception as e:
            if "API_INACCESSIBLE" in str(e) or "free plan" in str(e).lower():
                logger.warning(f"Apollo.io free plan limitation for {company}: {e}")
                logger.info("Contact discovery requires Apollo.io paid plan")
            else:
                logger.error(f"Error discovering {contact_type}s for {company}: {e}")
            return []
    
    def get_job_contacts(self, job_id: int) -> Dict[str, List[Contact]]:
        """Get all contacts linked to a job"""
        
        # JobContact functionality removed, so this method is no longer relevant
        # For now, it will return empty dictionaries as there's no JobContact model
        return {
            'recruiters': [],
            'engineers': []
        }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get Apollo.io usage statistics"""
        if self.apollo_client:
            return self.apollo_client.get_usage_stats()
        return {}
    
    async def batch_discover_contacts(
        self, 
        jobs: List[JobListing],
        max_jobs_per_batch: int = 10
    ) -> Dict[str, Any]:
        """Discover contacts for multiple jobs in batches"""
        
        logger.info(f"Starting batch contact discovery for {len(jobs)} jobs")
        
        results = {
            'total_jobs': len(jobs),
            'processed_jobs': 0,
            'successful_jobs': 0,
            'failed_jobs': 0,
            'total_contacts_found': 0,
            'errors': []
        }
        
        # Process jobs in batches
        for i in range(0, len(jobs), max_jobs_per_batch):
            batch = jobs[i:i + max_jobs_per_batch]
            
            for job in batch:
                try:
                    results['processed_jobs'] += 1
                    
                    # Discover contacts
                    contacts = await self.discover_contacts_for_job(job)
                    
                    # Link contacts to job (JobContact functionality removed)
                    # self.link_contacts_to_job(job, contacts)
                    
                    # Update stats
                    total_contacts = sum(len(contact_list) for contact_list in contacts.values())
                    results['total_contacts_found'] += total_contacts
                    results['successful_jobs'] += 1
                    
                    logger.info(f"Processed job {job.id}: found {total_contacts} contacts")
                    
                except Exception as e:
                    results['failed_jobs'] += 1
                    error_msg = f"Failed to process job {job.id}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            # Small delay between batches to be respectful to the API
            if i + max_jobs_per_batch < len(jobs):
                await asyncio.sleep(2)
        
        logger.info(f"Batch discovery completed: {results}")
        return results 