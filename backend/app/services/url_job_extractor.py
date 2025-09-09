import logging
import requests
import json
import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from datetime import datetime
from bs4 import BeautifulSoup

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
            
            # Step 2: Fetch content using free Jina AI Reader with fallback
            try:
                markdown_content = await self._fetch_with_jina(validated_url)
            except Exception as fetch_error:
                logger.error(f"Content fetching failed: {fetch_error}")
                # Return fallback data with specific error
                return self._create_fallback_job_data(validated_url, f"Content fetching failed: {str(fetch_error)}")
            
            # Step 3: Extract structured data with OpenAI
            try:
                job_details = await self._extract_with_openai(markdown_content, validated_url, user_context)
            except Exception as ai_error:
                logger.error(f"AI extraction failed: {ai_error}")
                # Return fallback data with AI error
                return self._create_fallback_job_data(validated_url, f"AI extraction failed: {str(ai_error)}")
            
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
            'remote.co', 'weworkremotely.com', 'flexjobs.com', 'upwork.com',
            'stripe.com', 'google.com', 'microsoft.com', 'amazon.com',
            'apple.com', 'meta.com', 'netflix.com', 'uber.com', 'airbnb.com'
        ]
        
        # Allow any domain but log if it's not a known job site
        domain = parsed.netloc.lower().replace('www.', '')
        if not any(allowed in domain for allowed in allowed_domains):
            logger.warning(f"Extracting from non-standard job site: {domain}")
        
        return url
    
    async def _fetch_with_jina(self, url: str) -> str:
        """
        Fetch and convert URL to clean markdown using free Jina AI Reader
        Falls back to direct HTML parsing if Jina AI Reader fails
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
            
            # Check if response is HTML (Jina AI Reader might return HTML instead of markdown)
            if content.strip().startswith('<!DOCTYPE') or content.strip().startswith('<html'):
                logger.warning("Jina AI Reader returned HTML instead of markdown, falling back to direct HTML parsing")
                return await self._fetch_direct_html(url)
            
            # Limit content length for OpenAI processing
            if len(content) > self.max_content_length:
                content = content[:self.max_content_length] + "\n... (content truncated)"
            
            logger.info(f"Successfully fetched {len(content)} characters via Jina AI")
            return content
            
        except requests.exceptions.Timeout:
            logger.warning("Jina AI Reader timed out, falling back to direct HTML parsing")
            return await self._fetch_direct_html(url)
        except requests.exceptions.RequestException as e:
            logger.warning(f"Jina AI Reader failed: {str(e)}, falling back to direct HTML parsing")
            return await self._fetch_direct_html(url)
    
    async def _fetch_direct_html(self, url: str) -> str:
        """
        Fallback method: Fetch HTML directly and convert to clean text
        """
        logger.info(f"Fetching content directly from URL: {url}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Special handling for Stripe job pages
            if 'stripe.com/jobs' in url:
                logger.info("Detected Stripe job page, using specialized extraction")
                return self._extract_stripe_job_content(soup)
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Extract text content
            text_content = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = ' '.join(chunk for chunk in chunks if chunk)
            
            if not text_content or len(text_content) < 100:
                raise Exception("Extracted content too short or empty")
            
            # Limit content length for OpenAI processing
            if len(text_content) > self.max_content_length:
                text_content = text_content[:self.max_content_length] + "\n... (content truncated)"
            
            logger.info(f"Successfully fetched {len(text_content)} characters via direct HTML parsing")
            return text_content
            
        except Exception as e:
            logger.error(f"Direct HTML parsing also failed: {str(e)}")
            raise Exception(f"Failed to fetch content from URL: {str(e)}")
    
    def _extract_stripe_job_content(self, soup: BeautifulSoup) -> str:
        """
        Specialized extraction for Stripe job pages
        """
        try:
            # Extract main content sections
            content_parts = []
            
            # Job title (usually in h1)
            title_elem = soup.find('h1')
            if title_elem:
                content_parts.append(f"Job Title: {title_elem.get_text(strip=True)}")
            
            # About Stripe section
            about_section = soup.find('h2', string=lambda text: text and 'About Stripe' in text)
            if about_section:
                about_content = about_section.find_next_sibling()
                if about_content:
                    content_parts.append(f"About Stripe: {about_content.get_text(strip=True)}")
            
            # About the team section
            team_section = soup.find('h2', string=lambda text: text and 'About the team' in text)
            if team_section:
                team_content = team_section.find_next_sibling()
                if team_content:
                    content_parts.append(f"About the team: {team_content.get_text(strip=True)}")
            
            # What you'll do section
            do_section = soup.find('h2', string=lambda text: text and "What you'll do" in text)
            if do_section:
                do_content = do_section.find_next_sibling()
                if do_content:
                    content_parts.append(f"What you'll do: {do_content.get_text(strip=True)}")
            
            # Responsibilities
            resp_section = soup.find('h2', string=lambda text: text and 'Responsibilities' in text)
            if resp_section:
                resp_content = resp_section.find_next_sibling()
                if resp_content:
                    content_parts.append(f"Responsibilities: {resp_content.get_text(strip=True)}")
            
            # Who you are section
            who_section = soup.find('h2', string=lambda text: text and 'Who you are' in text)
            if who_section:
                who_content = who_section.find_next_sibling()
                if who_content:
                    content_parts.append(f"Who you are: {who_content.get_text(strip=True)}")
            
            # Minimum requirements
            min_req_section = soup.find('h2', string=lambda text: text and 'Minimum requirements' in text)
            if min_req_section:
                min_req_content = min_req_section.find_next_sibling()
                if min_req_content:
                    content_parts.append(f"Minimum requirements: {min_req_content.get_text(strip=True)}")
            
            # Preferred qualifications
            pref_qual_section = soup.find('h2', string=lambda text: text and 'Preferred qualifications' in text)
            if pref_qual_section:
                pref_qual_content = pref_qual_section.find_next_sibling()
                if pref_qual_content:
                    content_parts.append(f"Preferred qualifications: {pref_qual_content.get_text(strip=True)}")
            
            # Pay and benefits
            pay_section = soup.find('h2', string=lambda text: text and 'Pay and benefits' in text)
            if pay_section:
                pay_content = pay_section.find_next_sibling()
                if pay_content:
                    content_parts.append(f"Pay and benefits: {pay_content.get_text(strip=True)}")
            
            # Office locations
            office_section = soup.find('h2', string=lambda text: text and 'Office locations' in text)
            if office_section:
                office_content = office_section.find_next_sibling()
                if office_content:
                    content_parts.append(f"Office locations: {office_content.get_text(strip=True)}")
            
            # Team information
            team_info = soup.find('h2', string=lambda text: text and 'Team' in text)
            if team_info:
                team_info_content = team_info.find_next_sibling()
                if team_info_content:
                    content_parts.append(f"Team: {team_info_content.get_text(strip=True)}")
            
            # Job type
            job_type = soup.find('h2', string=lambda text: text and 'Job type' in text)
            if job_type:
                job_type_content = job_type.find_next_sibling()
                if job_type_content:
                    content_parts.append(f"Job type: {job_type_content.get_text(strip=True)}")
            
            # Combine all content
            if content_parts:
                combined_content = '\n\n'.join(content_parts)
                
                # Limit content length for OpenAI processing
                if len(combined_content) > self.max_content_length:
                    combined_content = combined_content[:self.max_content_length] + "\n... (content truncated)"
                
                logger.info(f"Successfully extracted {len(combined_content)} characters from Stripe job page")
                return combined_content
            else:
                # Fallback to general text extraction
                logger.warning("Stripe-specific extraction failed, falling back to general extraction")
                return self._extract_general_content(soup)
                
        except Exception as e:
            logger.error(f"Stripe-specific extraction failed: {e}, falling back to general extraction")
            return self._extract_general_content(soup)
    
    def _extract_general_content(self, soup: BeautifulSoup) -> str:
        """
        General content extraction fallback
        """
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Extract text content
        text_content = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_content = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit content length for OpenAI processing
        if len(text_content) > self.max_content_length:
            text_content = text_content[:self.max_content_length] + "\n... (content truncated)"
        
        return text_content
    
    async def _extract_with_openai(self, markdown_content: str, original_url: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract structured job data using OpenAI GPT-4o-mini
        """
        try:
            logger.info(f"Starting OpenAI extraction for URL: {original_url}")
            logger.info(f"Content length: {len(markdown_content)} characters")
            logger.info(f"Content preview: {markdown_content[:200]}...")
            
            # Check if AI service is properly configured
            if not hasattr(ai_service, 'client') or not ai_service.client:
                logger.error("AI service client not properly initialized")
                raise Exception("AI service not available")
            
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
            
            logger.info("Sending prompt to OpenAI...")
            response = await ai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"OpenAI response received, length: {len(content)} characters")
            logger.info(f"Response preview: {content[:200]}...")
            
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