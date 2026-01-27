"""
Browser-based job extraction using Playwright for LinkedIn, Indeed, and other job sites
that have anti-bot measures or require JavaScript rendering.
"""

import logging
import json
import asyncio
import random
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from datetime import datetime

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not available. Browser extraction will be disabled.")

from app.core.ai_service import ai_service

logger = logging.getLogger(__name__)

class BrowserJobExtractor:
    """
    Browser-based job extraction using Playwright for sites with anti-bot measures.
    """

    def __init__(self):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is required for browser job extraction. Install with: pip install playwright")

        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        ]
        self.timeout = 30000  # 30 seconds
        self.max_content_length = 20000

    async def extract_job_details(self, url: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract job details using browser automation
        """
        try:
            logger.info(f"Starting browser extraction for URL: {url}")

            # Validate URL
            validated_url = self._validate_url(url)
            domain = self._get_domain(validated_url)

            async with async_playwright() as playwright:
                browser = await self._launch_browser(playwright)
                context = await self._create_context(browser)
                page = await context.new_page()

                try:
                    # Navigate to page with realistic behavior
                    await self._navigate_to_page(page, validated_url)

                    # Extract content based on domain
                    content = await self._extract_content_by_domain(page, domain)

                    if not content or len(content) < 100:
                        raise Exception("Insufficient content extracted")

                    # Process with AI
                    job_details = await self._extract_with_openai(content, validated_url, user_context)

                    # Add metadata
                    job_details.update({
                        "original_url": validated_url,
                        "extraction_method": "browser_playwright",
                        "extracted_at": datetime.utcnow().isoformat(),
                        "content_length": len(content),
                        "extraction_success": True,
                        "domain": domain
                    })

                    logger.info(f"Successfully extracted job via browser: {job_details.get('title', 'Unknown')} at {job_details.get('company', 'Unknown')}")
                    return job_details

                finally:
                    await browser.close()

        except Exception as e:
            logger.error(f"Browser extraction failed for {url}: {str(e)}")
            return self._create_fallback_job_data(url, str(e))

    async def _launch_browser(self, playwright) -> Browser:
        """Launch browser with stealth settings"""
        return await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-default-apps'
            ]
        )

    async def _create_context(self, browser: Browser) -> BrowserContext:
        """Create browser context with realistic settings"""
        return await browser.new_context(
            user_agent=random.choice(self.user_agents),
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
        )

    async def _navigate_to_page(self, page: Page, url: str):
        """Navigate to page with human-like behavior"""
        # Set additional page properties to avoid detection
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)

        # Navigate to page
        await page.goto(url, wait_until='networkidle', timeout=self.timeout)

        # Human-like delay
        await self._human_delay()

        # Scroll to simulate reading
        await self._simulate_reading(page)

    async def _simulate_reading(self, page: Page):
        """Simulate human reading behavior"""
        # Scroll down slowly to simulate reading
        for i in range(3):
            await page.evaluate(f"window.scrollTo(0, {i * 300})")
            await asyncio.sleep(random.uniform(0.5, 1.5))

    async def _human_delay(self):
        """Random delay to simulate human behavior"""
        await asyncio.sleep(random.uniform(2.0, 4.0))

    async def _extract_content_by_domain(self, page: Page, domain: str) -> str:
        """Extract content based on the domain"""
        if 'linkedin.com' in domain:
            return await self._extract_linkedin_content(page)
        elif 'indeed.com' in domain:
            return await self._extract_indeed_content(page)
        else:
            return await self._extract_generic_content(page)

    async def _extract_linkedin_content(self, page: Page) -> str:
        """Extract content from LinkedIn job pages"""
        try:
            # Wait for job details to load
            await page.wait_for_selector('h1', timeout=10000)

            content_parts = []

            # Job title
            try:
                title = await page.query_selector('h1')
                if title:
                    title_text = await title.inner_text()
                    content_parts.append(f"Job Title: {title_text}")
            except:
                pass

            # Company name
            try:
                company_selectors = [
                    '.job-details-jobs-unified-top-card__company-name a',
                    '.job-details-jobs-unified-top-card__company-name',
                    '[data-automation-id="job-detail-company-name"]',
                    '.jobs-unified-top-card__company-name'
                ]

                for selector in company_selectors:
                    company_elem = await page.query_selector(selector)
                    if company_elem:
                        company_text = await company_elem.inner_text()
                        content_parts.append(f"Company: {company_text}")
                        break
            except:
                pass

            # Job description
            try:
                description_selectors = [
                    '.job-details-jobs-unified-top-card__job-description',
                    '.jobs-box__html-content',
                    '.job-details-module',
                    '.jobs-description__content',
                    '[data-automation-id="job-detail-description"]'
                ]

                for selector in description_selectors:
                    desc_elem = await page.query_selector(selector)
                    if desc_elem:
                        desc_text = await desc_elem.inner_text()
                        if len(desc_text) > 100:  # Only use if substantial content
                            content_parts.append(f"Description: {desc_text}")
                            break
            except:
                pass

            # Location
            try:
                location_selectors = [
                    '.job-details-jobs-unified-top-card__bullet',
                    '[data-automation-id="job-detail-location"]',
                    '.jobs-unified-top-card__bullet'
                ]

                for selector in location_selectors:
                    location_elem = await page.query_selector(selector)
                    if location_elem:
                        location_text = await location_elem.inner_text()
                        content_parts.append(f"Location: {location_text}")
                        break
            except:
                pass

            # Employment type and other details
            try:
                details_elements = await page.query_selector_all('.job-details-jobs-unified-top-card__job-insight span')
                for elem in details_elements:
                    text = await elem.inner_text()
                    if text and len(text.strip()) > 0:
                        content_parts.append(f"Detail: {text}")
            except:
                pass

            combined_content = '\n\n'.join(content_parts)

            # If we didn't get much content, try generic extraction
            if len(combined_content) < 200:
                logger.warning("LinkedIn-specific extraction yielded little content, trying generic")
                return await self._extract_generic_content(page)

            logger.info(f"LinkedIn extraction successful, {len(combined_content)} characters")
            return combined_content

        except Exception as e:
            logger.warning(f"LinkedIn-specific extraction failed: {e}, trying generic")
            return await self._extract_generic_content(page)

    async def _extract_indeed_content(self, page: Page) -> str:
        """Extract content from Indeed job pages"""
        try:
            # Wait for job details to load
            await page.wait_for_selector('h1', timeout=10000)

            content_parts = []

            # Job title
            try:
                title_selectors = ['h1[data-testid="job-title"]', 'h1', '.jobsearch-JobInfoHeader-title']
                for selector in title_selectors:
                    title = await page.query_selector(selector)
                    if title:
                        title_text = await title.inner_text()
                        content_parts.append(f"Job Title: {title_text}")
                        break
            except:
                pass

            # Company name
            try:
                company_selectors = [
                    '[data-testid="company-name"]',
                    '.jobsearch-InlineCompanyRating-companyHeader a',
                    '.jobsearch-CompanyInfoWithoutHeaderImage .jobsearch-JobInfoHeader-title'
                ]

                for selector in company_selectors:
                    company_elem = await page.query_selector(selector)
                    if company_elem:
                        company_text = await company_elem.inner_text()
                        content_parts.append(f"Company: {company_text}")
                        break
            except:
                pass

            # Location
            try:
                location_selectors = [
                    '[data-testid="job-location"]',
                    '.jobsearch-JobInfoHeader-subtitle div'
                ]

                for selector in location_selectors:
                    location_elem = await page.query_selector(selector)
                    if location_elem:
                        location_text = await location_elem.inner_text()
                        content_parts.append(f"Location: {location_text}")
                        break
            except:
                pass

            # Job description
            try:
                description_selectors = [
                    '[data-testid="job-description"]',
                    '.jobsearch-jobDescriptionText',
                    '.jobsearch-JobComponent-description'
                ]

                for selector in description_selectors:
                    desc_elem = await page.query_selector(selector)
                    if desc_elem:
                        desc_text = await desc_elem.inner_text()
                        if len(desc_text) > 100:
                            content_parts.append(f"Description: {desc_text}")
                            break
            except:
                pass

            # Salary and benefits
            try:
                salary_selectors = [
                    '[data-testid="salary-estimate-range"]',
                    '.jobsearch-JobMetadataHeader-item'
                ]

                for selector in salary_selectors:
                    salary_elem = await page.query_selector(selector)
                    if salary_elem:
                        salary_text = await salary_elem.inner_text()
                        content_parts.append(f"Salary: {salary_text}")
                        break
            except:
                pass

            combined_content = '\n\n'.join(content_parts)

            if len(combined_content) < 200:
                logger.warning("Indeed-specific extraction yielded little content, trying generic")
                return await self._extract_generic_content(page)

            logger.info(f"Indeed extraction successful, {len(combined_content)} characters")
            return combined_content

        except Exception as e:
            logger.warning(f"Indeed-specific extraction failed: {e}, trying generic")
            return await self._extract_generic_content(page)

    async def _extract_generic_content(self, page: Page) -> str:
        """Generic content extraction for any job site"""
        try:
            # Remove common non-content elements
            await page.evaluate("""
                const elementsToRemove = document.querySelectorAll('script, style, nav, header, footer, aside, .navigation, .menu, .sidebar, .ads, .advertisement');
                elementsToRemove.forEach(el => el.remove());
            """)

            # Get main content
            body_text = await page.evaluate("document.body.innerText")

            # Clean up the text
            lines = [line.strip() for line in body_text.splitlines() if line.strip()]
            clean_content = '\n'.join(lines)

            # Limit content length
            if len(clean_content) > self.max_content_length:
                clean_content = clean_content[:self.max_content_length] + "\n... (content truncated)"

            logger.info(f"Generic extraction successful, {len(clean_content)} characters")
            return clean_content

        except Exception as e:
            logger.error(f"Generic content extraction failed: {e}")
            raise Exception("Failed to extract any content from page")

    def _validate_url(self, url: str) -> str:
        """Validate and normalize URL"""
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")

        url = url.strip()

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValueError("Invalid URL format")

        return url

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = urlparse(url)
        return parsed.netloc.lower().replace('www.', '')

    async def _extract_with_openai(self, content: str, original_url: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Extract structured job data using OpenAI"""
        try:
            logger.info(f"Starting OpenAI extraction for browser content")

            if not hasattr(ai_service, 'client') or not ai_service.client:
                raise Exception("AI service not available")

            context_info = ""
            if user_context:
                context_info = f"""
User Context (to help with extraction):
- Skills: {', '.join(user_context.get('skills', [])[:5])}
- Experience Level: {user_context.get('experience_level', 'Not specified')}
- Preferred Locations: {', '.join(user_context.get('locations', [])[:3])}

"""

            prompt = f"""Extract job posting details from browser-extracted content and return ONLY a valid JSON object.

{context_info}Instructions:
1. Focus on actionable information for job preparation
2. Separate minimum requirements from preferred qualifications
3. Extract specific skills, technologies, and tools mentioned
4. Capture salary, benefits, and compensation details clearly
5. Provide confidence score (0.0-1.0) based on extraction quality

Required JSON format:
{{
    "title": "Software Engineer",
    "company": "Tech Corp Inc",
    "location": "San Francisco, CA",
    "salary_range": "$120,000 - $150,000",
    "job_type": "Full-time",
    "experience_level": "Mid-Senior",
    "remote_policy": "Hybrid",
    "description": "Concise role overview focusing on day-to-day responsibilities",
    "minimum_requirements": "Must-have qualifications: education, experience, required skills",
    "preferred_qualifications": "Nice-to-have qualifications: additional skills or experience",
    "technical_skills": ["Python", "React", "AWS"],
    "soft_skills": ["Communication", "Leadership"],
    "benefits": ["Health insurance", "401k", "Remote work"],
    "compensation_details": "Additional compensation beyond base salary",
    "application_deadline": null,
    "confidence": 0.95
}}

Job posting content:
{content}

Return ONLY the JSON object (no explanation):"""

            response = await ai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=3000,
                temperature=0.1
            )

            response_content = response.choices[0].message.content.strip()

            # Clean up response
            if response_content.startswith('```json'):
                response_content = response_content[7:]
            if response_content.startswith('```'):
                response_content = response_content[3:]
            if response_content.endswith('```'):
                response_content = response_content[:-3]

            response_content = response_content.strip()

            # Parse JSON
            job_data = json.loads(response_content)

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

            logger.info(f"Browser OpenAI extraction successful with confidence: {job_data.get('confidence', 0)}")
            return job_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI JSON response: {e}")
            raise Exception("Failed to parse job details from AI response")

        except Exception as e:
            logger.error(f"Browser OpenAI extraction failed: {str(e)}")
            raise Exception(f"AI extraction failed: {str(e)}")

    def _create_fallback_job_data(self, url: str, error_message: str) -> Dict[str, Any]:
        """Create fallback job data when extraction fails"""
        domain = self._get_domain(url)

        return {
            "title": f"Job from {domain}",
            "company": "Unknown Company",
            "location": "Location not specified",
            "salary_range": None,
            "job_type": "Not specified",
            "experience_level": "Not specified",
            "remote_policy": None,
            "description": f"Browser extraction failed. Please check manually: {url}",
            "requirements": "See original posting",
            "skills": [],
            "benefits": [],
            "application_deadline": None,
            "application_url": url,
            "original_url": url,
            "extraction_method": "browser_playwright_failed",
            "extracted_at": datetime.utcnow().isoformat(),
            "content_length": 0,
            "extraction_success": False,
            "extraction_error": error_message,
            "confidence": 0.1
        }


# Create singleton instance (only if Playwright is available)
if PLAYWRIGHT_AVAILABLE:
    browser_job_extractor = BrowserJobExtractor()
else:
    browser_job_extractor = None