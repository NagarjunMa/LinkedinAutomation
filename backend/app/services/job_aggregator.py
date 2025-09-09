import asyncio
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from app.models.job import JobListing

logger = logging.getLogger(__name__)

class JobAggregator:
    """
    Job extraction service for extracting job details from URLs
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })
        
    async def extract_job_from_url(self, url: str) -> Optional[JobListing]:
        """
        Extract job information from a direct URL (LinkedIn, Indeed, etc.)
        """
        try:
            logger.info(f"Extracting job from URL: {url}")
            
            # Determine the source type
            source = self._determine_source(url)
            
            if source == "linkedin":
                return await self._extract_linkedin_job(url)
            elif source == "indeed":
                return await self._extract_indeed_job(url)
            else:
                return await self._extract_generic_job(url, source)
                
        except Exception as e:
            logger.error(f"Error extracting job from URL {url}: {e}")
            return None

    def _determine_source(self, url: str) -> str:
        """Determine the job source from URL"""
        if "linkedin.com" in url:
            return "linkedin"
        elif "indeed.com" in url:
            return "indeed"
        elif "glassdoor.com" in url:
            return "glassdoor"
        elif "ziprecruiter.com" in url:
            return "ziprecruiter"
        else:
            return "other"

    async def _extract_linkedin_job(self, url: str) -> Optional[JobListing]:
        """Extract job information from LinkedIn URL"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.session.get, url
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract job title
            title_elem = soup.find('h1', class_='top-card-layout__title') or \
                         soup.find('h1', class_='job-details-jobs-unified-top-card__job-title')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
            
            # Extract company name
            company_elem = soup.find('a', class_='topcard__org-name-link') or \
                          soup.find('span', class_='job-details-jobs-unified-top-card__company-name')
            company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
            
            # Extract location
            location_elem = soup.find('span', class_='topcard__flavor--bullet') or \
                           soup.find('span', class_='job-details-jobs-unified-top-card__bullet')
            location = location_elem.get_text(strip=True) if location_elem else "Unknown Location"
            
            # Extract description
            desc_elem = soup.find('div', class_='description__text') or \
                       soup.find('div', class_='job-details-jobs-unified-top-card__job-description')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Create job listing
            job = JobListing(
                title=title,
                company=company,
                location=location,
                description=description,
                source="linkedin",
                source_url=url,
                extracted_date=datetime.utcnow()
            )
            
            logger.info(f"Successfully extracted LinkedIn job: {title} at {company}")
            return job
            
        except Exception as e:
            logger.error(f"Error extracting LinkedIn job: {e}")
            return None

    async def _extract_indeed_job(self, url: str) -> Optional[JobListing]:
        """Extract job information from Indeed URL"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.session.get, url
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract job title
            title_elem = soup.find('h1', class_='jobsearch-JobInfoHeader-title') or \
                         soup.find('h1', class_='icl-u-xs-mb--xs')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
            
            # Extract company name
            company_elem = soup.find('a', class_='jobsearch-CompanyInfoContainer-companyName') or \
                          soup.find('span', class_='companyName')
            company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
            
            # Extract location
            location_elem = soup.find('div', class_='jobsearch-JobInfoHeader-subtitle') or \
                           soup.find('span', class_='location')
            location = location_elem.get_text(strip=True) if location_elem else "Unknown Location"
            
            # Extract description
            desc_elem = soup.find('div', class_='jobsearch-jobDescriptionText') or \
                       soup.find('div', class_='job-description')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Create job listing
            job = JobListing(
                title=title,
                company=company,
                location=location,
                description=description,
                source="indeed",
                source_url=url,
                extracted_date=datetime.utcnow()
            )
            
            logger.info(f"Successfully extracted Indeed job: {title} at {company}")
            return job
            
        except Exception as e:
            logger.error(f"Error extracting Indeed job: {e}")
            return None

    async def _extract_generic_job(self, url: str, source: str) -> Optional[JobListing]:
        """Extract job information from generic job board URL"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.session.get, url
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find job title in common patterns
            title = "Unknown Title"
            title_selectors = ['h1', 'h2', '.job-title', '.title', '[data-testid*="title"]']
            for selector in title_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    title = elem.get_text(strip=True)
                    break
            
            # Try to find company name
            company = "Unknown Company"
            company_selectors = ['.company', '.employer', '[data-testid*="company"]', '.org-name']
            for selector in company_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    company = elem.get_text(strip=True)
                    break
            
            # Try to find location
            location = "Unknown Location"
            location_selectors = ['.location', '.address', '[data-testid*="location"]']
            for selector in location_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    location = elem.get_text(strip=True)
                    break
            
            # Try to find description
            description = ""
            desc_selectors = ['.description', '.job-description', '.content', '[data-testid*="description"]']
            for selector in desc_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    description = elem.get_text(strip=True)
                    break
            
            # Create job listing
            job = JobListing(
                title=title,
                company=company,
                location=location,
                description=description,
                source=source,
                source_url=url,
                extracted_date=datetime.utcnow()
            )
            
            logger.info(f"Successfully extracted generic job: {title} at {company}")
            return job
            
        except Exception as e:
            logger.error(f"Error extracting generic job: {e}")
            return None 