"""
Job extraction strategy coordinator that chooses the best extraction method
based on the target domain and implements fallback logic.
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from urllib.parse import urlparse

from .url_job_extractor import url_job_extractor
from .browser_job_extractor import browser_job_extractor, PLAYWRIGHT_AVAILABLE

logger = logging.getLogger(__name__)

class ExtractionMethod(Enum):
    """Available extraction methods"""
    JINA_AI = "jina_ai_reader"
    PLAYWRIGHT = "browser_playwright"
    DIRECT_HTML = "direct_html_parse"

class ExtractionResult:
    """Wrapper for extraction results with metadata"""
    def __init__(self, data: Dict[str, Any], method: ExtractionMethod, success: bool, error: Optional[str] = None):
        self.data = data
        self.method = method
        self.success = success
        self.error = error

class JobExtractionStrategy:
    """
    Coordinated job extraction using multiple methods with intelligent fallback logic.
    """

    def __init__(self):
        self.problematic_domains = {
            'linkedin.com': 'High anti-bot protection, requires browser',
            'indeed.com': 'Dynamic content loading, JavaScript required',
            'glassdoor.com': 'Authentication walls, complex JS',
            'monster.com': 'Heavy JavaScript, anti-scraping',
            'ziprecruiter.com': 'Dynamic loading, session-based'
        }

        self.reliable_domains = {
            'stripe.com': 'Static content, API-friendly',
            'google.com': 'Well-structured, accessible',
            'microsoft.com': 'Static job pages',
            'amazon.com': 'Structured content',
            'apple.com': 'Clean HTML structure'
        }

    async def extract_job_with_fallback(self, url: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract job details using the most appropriate method with fallback logic.

        Args:
            url: Job posting URL
            user_context: Optional user profile context for better extraction

        Returns:
            Dictionary with extracted job details and metadata
        """
        try:
            logger.info(f"Starting strategic job extraction for URL: {url}")

            domain = self._get_domain(url)
            extraction_plan = self._create_extraction_plan(domain)

            logger.info(f"Domain: {domain}, Extraction plan: {[method.value for method, _ in extraction_plan]}")

            # Try extraction methods in order
            for method, extractor_func in extraction_plan:
                try:
                    logger.info(f"Attempting extraction with method: {method.value}")

                    result = await self._execute_extraction(method, extractor_func, url, user_context)

                    if self._is_successful_extraction(result):
                        result.data['extraction_method'] = method.value
                        result.data['extraction_attempts'] = [method.value]
                        result.data['domain_classification'] = self._classify_domain(domain)

                        logger.info(f"Successfully extracted job using {method.value}: {result.data.get('title', 'Unknown')} at {result.data.get('company', 'Unknown')}")
                        return result.data
                    else:
                        logger.warning(f"Method {method.value} succeeded but returned low-quality data")

                except Exception as e:
                    logger.warning(f"Method {method.value} failed for {url}: {str(e)}")
                    continue

            # All methods failed - create comprehensive fallback
            logger.error(f"All extraction methods failed for {url}")
            return self._create_comprehensive_fallback(url, domain, [method.value for method, _ in extraction_plan])

        except Exception as e:
            logger.error(f"Strategic extraction completely failed for {url}: {str(e)}")
            return self._create_error_fallback(url, str(e))

    def _create_extraction_plan(self, domain: str) -> List[tuple]:
        """
        Create an extraction plan based on domain characteristics.

        Returns list of (ExtractionMethod, extractor_function) tuples in priority order.
        """
        plan = []

        if domain in self.problematic_domains:
            # Start with browser automation for problematic sites
            if PLAYWRIGHT_AVAILABLE and browser_job_extractor:
                plan.append((ExtractionMethod.PLAYWRIGHT, browser_job_extractor.extract_job_details))

            # Fallback to Jina AI (might work sometimes)
            plan.append((ExtractionMethod.JINA_AI, url_job_extractor.extract_job_details))

            # Last resort: direct HTML
            plan.append((ExtractionMethod.DIRECT_HTML, self._extract_with_direct_html))

        elif domain in self.reliable_domains:
            # Start with fast methods for reliable sites
            plan.append((ExtractionMethod.JINA_AI, url_job_extractor.extract_job_details))

            # Browser as backup if needed
            if PLAYWRIGHT_AVAILABLE and browser_job_extractor:
                plan.append((ExtractionMethod.PLAYWRIGHT, browser_job_extractor.extract_job_details))

            # Direct HTML fallback
            plan.append((ExtractionMethod.DIRECT_HTML, self._extract_with_direct_html))

        else:
            # Unknown domain - try all methods starting with least resource-intensive
            plan.append((ExtractionMethod.JINA_AI, url_job_extractor.extract_job_details))

            if PLAYWRIGHT_AVAILABLE and browser_job_extractor:
                plan.append((ExtractionMethod.PLAYWRIGHT, browser_job_extractor.extract_job_details))

            plan.append((ExtractionMethod.DIRECT_HTML, self._extract_with_direct_html))

        # Filter out None extractors
        plan = [(method, func) for method, func in plan if func is not None]

        if not plan:
            logger.error("No extraction methods available!")
            raise Exception("No extraction methods available")

        return plan

    async def _execute_extraction(self, method: ExtractionMethod, extractor_func: Callable, url: str, user_context: Optional[Dict]) -> ExtractionResult:
        """Execute a specific extraction method and return wrapped result"""
        try:
            if method == ExtractionMethod.DIRECT_HTML:
                # Direct HTML method doesn't take user_context
                result = await extractor_func(url)
            else:
                result = await extractor_func(url, user_context)

            success = result.get('extraction_success', False) and result.get('confidence', 0) > 0.5
            return ExtractionResult(result, method, success)

        except Exception as e:
            error_result = self._create_method_error_result(method, url, str(e))
            return ExtractionResult(error_result, method, False, str(e))

    async def _extract_with_direct_html(self, url: str) -> Dict[str, Any]:
        """Wrapper for direct HTML extraction"""
        return await url_job_extractor._fetch_direct_html(url)

    def _is_successful_extraction(self, result: ExtractionResult) -> bool:
        """
        Determine if an extraction was successful based on data quality.
        """
        if not result.success:
            return False

        data = result.data

        # Check for minimum required fields
        title = data.get('title', '').strip()
        company = data.get('company', '').strip()

        if not title or not company:
            return False

        # Check for placeholder values
        if title in ['Not specified', 'Unknown', 'Job from']:
            return False

        if company in ['Not specified', 'Unknown Company', 'Unknown']:
            return False

        # Check confidence score
        confidence = data.get('confidence', 0)
        if confidence < 0.6:
            return False

        # Check content length
        description = data.get('description', '')
        if len(description) < 50:
            return False

        logger.info(f"Extraction quality check passed: title='{title}', company='{company}', confidence={confidence}")
        return True

    def _classify_domain(self, domain: str) -> str:
        """Classify domain for metadata"""
        if domain in self.problematic_domains:
            return "problematic"
        elif domain in self.reliable_domains:
            return "reliable"
        else:
            return "unknown"

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace('www.', '')
            return domain
        except:
            return "unknown"

    def _create_comprehensive_fallback(self, url: str, domain: str, attempted_methods: List[str]) -> Dict[str, Any]:
        """Create a comprehensive fallback result when all methods fail"""
        return {
            "title": f"Job from {domain}",
            "company": "Unknown Company",
            "location": "Location not specified",
            "salary_range": None,
            "job_type": "Not specified",
            "experience_level": "Not specified",
            "remote_policy": None,
            "description": f"Extraction failed using all available methods. Please check the job posting manually at: {url}",
            "minimum_requirements": "See original posting",
            "preferred_qualifications": "See original posting",
            "technical_skills": [],
            "soft_skills": [],
            "benefits": [],
            "compensation_details": None,
            "application_deadline": None,
            "application_url": url,
            "original_url": url,
            "extraction_method": "all_methods_failed",
            "extraction_attempts": attempted_methods,
            "extraction_success": False,
            "extraction_error": f"All {len(attempted_methods)} extraction methods failed",
            "domain": domain,
            "domain_classification": self._classify_domain(domain),
            "confidence": 0.1,
            "fallback_reason": "comprehensive_failure"
        }

    def _create_error_fallback(self, url: str, error_message: str) -> Dict[str, Any]:
        """Create fallback when strategy itself fails"""
        domain = self._get_domain(url)

        return {
            "title": f"Job from {domain}",
            "company": "Unknown Company",
            "location": "Location not specified",
            "salary_range": None,
            "job_type": "Not specified",
            "experience_level": "Not specified",
            "remote_policy": None,
            "description": f"Strategic extraction system error. Please check manually: {url}",
            "minimum_requirements": "See original posting",
            "preferred_qualifications": "See original posting",
            "technical_skills": [],
            "soft_skills": [],
            "benefits": [],
            "compensation_details": None,
            "application_deadline": None,
            "application_url": url,
            "original_url": url,
            "extraction_method": "strategy_error",
            "extraction_attempts": ["strategy_failure"],
            "extraction_success": False,
            "extraction_error": error_message,
            "domain": domain,
            "domain_classification": "error",
            "confidence": 0.0,
            "fallback_reason": "strategy_error"
        }

    def _create_method_error_result(self, method: ExtractionMethod, url: str, error_message: str) -> Dict[str, Any]:
        """Create error result for a specific method failure"""
        domain = self._get_domain(url)

        return {
            "title": f"Job from {domain}",
            "company": "Unknown Company",
            "location": "Location not specified",
            "salary_range": None,
            "job_type": "Not specified",
            "experience_level": "Not specified",
            "remote_policy": None,
            "description": f"Extraction failed with {method.value}: {error_message}",
            "minimum_requirements": "See original posting",
            "preferred_qualifications": "See original posting",
            "technical_skills": [],
            "soft_skills": [],
            "benefits": [],
            "compensation_details": None,
            "application_deadline": None,
            "application_url": url,
            "original_url": url,
            "extraction_method": f"{method.value}_failed",
            "extraction_attempts": [method.value],
            "extraction_success": False,
            "extraction_error": error_message,
            "domain": domain,
            "confidence": 0.1,
            "fallback_reason": f"{method.value}_error"
        }

    def get_domain_info(self, url: str) -> Dict[str, Any]:
        """Get information about a domain's extraction characteristics"""
        domain = self._get_domain(url)

        info = {
            "domain": domain,
            "classification": self._classify_domain(domain),
            "extraction_plan": [method.value for method, _ in self._create_extraction_plan(domain)],
            "playwright_available": PLAYWRIGHT_AVAILABLE
        }

        if domain in self.problematic_domains:
            info["notes"] = self.problematic_domains[domain]
        elif domain in self.reliable_domains:
            info["notes"] = self.reliable_domains[domain]
        else:
            info["notes"] = "Unknown domain, will try all methods"

        return info

# Create singleton instance
job_extraction_strategy = JobExtractionStrategy()