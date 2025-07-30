import logging
import requests
import json
import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from datetime import datetime

from app.core.ai_service import ai_service

logger = logging.getLogger(__name__)

class URLJobExtractor:
    """
    Extract job details from URLs using:
    1. Free Jina AI Reader (https://r.jina.ai/) for web scraping
    2. OpenAI GPT-4o-mini for structured data extraction
    """
    
    def __init__(self):
        self.jina_base_url = "https://r.jina.ai/"
        self.timeout = 30
        self.max_content_length = 10000  # Limit content for OpenAI
        
    async def extract_job_details(self, url: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main method to extract job details from URL
        
        Args:
            url: Job posting URL
            user_context: Optional user profile context for better extraction
            
        Returns:
            Dictionary with extracted job details and metadata
        """
        try:
            logger.info(f"Starting job extraction for URL: {url}")
            
            # Step 1: Validate URL
            validated_url = self._validate_url(url)
            
            # Step 2: Fetch content using free Jina AI Reader
            markdown_content = await self._fetch_with_jina(validated_url)
            
            # Step 3: Extract structured data with OpenAI
            job_details = await self._extract_with_openai(markdown_content, validated_url, user_context)
            
            # Step 4: Add extraction metadata
            job_details.update({
                "original_url": validated_url,
                "extraction_method": "jina_ai_reader_openai",
                "extracted_at": datetime.utcnow().isoformat(),
                "content_length": len(markdown_content),
                "extraction_success": True
            })
            
            logger.info(f"Successfully extracted job: {job_details.get('title', 'Unknown')} at {job_details.get('company', 'Unknown')}")
            return job_details
            
        except Exception as e:
            logger.error(f"Failed to extract job details from {url}: {str(e)}")
            
            # Return fallback data for graceful degradation
            return self._create_fallback_job_data(url, str(e))
    
    def _validate_url(self, url: str) -> str:
        """
        Validate and normalize URL
        """
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")
        
        url = url.strip()
        
        # Add https:// if no protocol specified
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Parse and validate
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValueError("Invalid URL format")
        
        # Check for common job sites (optional validation)
        allowed_domains = [
            'linkedin.com', 'indeed.com', 'glassdoor.com', 'monster.com',
            'ziprecruiter.com', 'careerbuilder.com', 'simplyhired.com',
            'dice.com', 'stackoverflow.com', 'angel.co', 'wellfound.com',
            'remote.co', 'weworkremotely.com', 'flexjobs.com', 'upwork.com'
        ]
        
        # Allow any domain but log if it's not a known job site
        domain = parsed.netloc.lower().replace('www.', '')
        if not any(allowed in domain for allowed in allowed_domains):
            logger.warning(f"Extracting from non-standard job site: {domain}")
        
        return url
    
    async def _fetch_with_jina(self, url: str) -> str:
        """
        Fetch and convert URL to clean markdown using free Jina AI Reader
        """
        jina_url = f"{self.jina_base_url}{url}"
        
        logger.info(f"Fetching content via Jina AI Reader: {jina_url}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'text/plain, text/html, application/json',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            response = requests.get(jina_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            content = response.text
            
            if not content or len(content) < 100:
                raise Exception("Content too short or empty")
            
            # Limit content length for OpenAI processing
            if len(content) > self.max_content_length:
                content = content[:self.max_content_length] + "\n... (content truncated)"
            
            logger.info(f"Successfully fetched {len(content)} characters via Jina AI")
            return content
            
        except requests.exceptions.Timeout:
            raise Exception("Request timed out while fetching job content")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch job content: {str(e)}")
    
    async def _extract_with_openai(self, markdown_content: str, original_url: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract structured job data using OpenAI GPT-4o-mini
        """
        try:
            # Build context-aware prompt
            context_info = ""
            if user_context:
                context_info = f"""
User Context (to help with extraction):
- Skills: {', '.join(user_context.get('skills', [])[:5])}
- Experience Level: {user_context.get('experience_level', 'Not specified')}
- Preferred Locations: {', '.join(user_context.get('locations', [])[:3])}

"""

            prompt = f"""Extract job posting details from the content below and return ONLY a valid JSON object.

{context_info}Instructions:
1. Extract all relevant job information
2. Normalize salary ranges (e.g., "120k-150k", "$80,000 - $100,000")
3. Extract key skills as an array
4. Provide confidence score (0.0-1.0) based on extraction quality
5. If information is missing, use null (not empty strings)

Required JSON format:
{{
    "title": "Software Engineer",
    "company": "Tech Corp Inc",
    "location": "San Francisco, CA",
    "salary_range": "$120,000 - $150,000",
    "job_type": "Full-time",
    "experience_level": "Mid",
    "remote_policy": "Hybrid",
    "description": "Job description summary (max 500 chars)",
    "requirements": "Key requirements (max 300 chars)",
    "skills": ["Python", "React", "AWS"],
    "benefits": ["Health insurance", "401k"],
    "application_deadline": null,
    "confidence": 0.95
}}

Job posting content:
{markdown_content}

Return ONLY the JSON object (no explanation):"""
            
            response = await ai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up response (remove code blocks if present)
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            
            content = content.strip()
            
            # Parse JSON response
            job_data = json.loads(content)
            
            # Validate required fields
            required_fields = ["title", "company"]
            for field in required_fields:
                if not job_data.get(field):
                    job_data[field] = "Not specified"
            
            # Ensure confidence is set
            if "confidence" not in job_data:
                job_data["confidence"] = 0.7
            
            # Add application URL
            job_data["application_url"] = original_url
            
            logger.info(f"OpenAI extraction successful with confidence: {job_data.get('confidence', 0)}")
            return job_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI JSON response: {e}")
            logger.error(f"Raw response: {content[:500]}...")
            raise Exception("Failed to parse job details from AI response")
        
        except Exception as e:
            logger.error(f"OpenAI extraction failed: {str(e)}")
            raise Exception(f"AI extraction failed: {str(e)}")
    
    def _create_fallback_job_data(self, url: str, error_message: str) -> Dict[str, Any]:
        """
        Create fallback job data when extraction fails
        """
        domain = urlparse(url).netloc.replace('www.', '')
        
        return {
            "title": f"Job from {domain}",
            "company": "Unknown Company",
            "location": "Location not specified",
            "salary_range": None,
            "job_type": "Not specified",
            "experience_level": "Not specified",
            "remote_policy": None,
            "description": f"Failed to extract job details. Please check manually: {url}",
            "requirements": "See original posting",
            "skills": [],
            "benefits": [],
            "application_deadline": None,
            "application_url": url,
            "original_url": url,
            "extraction_method": "fallback",
            "extracted_at": datetime.utcnow().isoformat(),
            "content_length": 0,
            "extraction_success": False,
            "extraction_error": error_message,
            "confidence": 0.1
        }
    
    async def extract_multiple_jobs(self, urls: list, user_context: Optional[Dict] = None) -> list:
        """
        Extract job details from multiple URLs (batch processing)
        """
        results = []
        
        for i, url in enumerate(urls[:10]):  # Limit to 10 URLs to prevent abuse
            try:
                logger.info(f"Processing URL {i+1}/{len(urls)}: {url}")
                job_data = await self.extract_job_details(url, user_context)
                results.append(job_data)
                
            except Exception as e:
                logger.error(f"Failed to process URL {url}: {e}")
                fallback_data = self._create_fallback_job_data(url, str(e))
                results.append(fallback_data)
        
        return results

# Create singleton instance
url_job_extractor = URLJobExtractor() 