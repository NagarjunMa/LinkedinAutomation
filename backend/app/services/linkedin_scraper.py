import asyncio
import logging
import os
import re
from typing import List, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, TimeoutError
from bs4 import BeautifulSoup
from app.core.config import settings
from app.models.job import JobListing
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LinkedInScraper:
    _instance = None
    _browser = None
    _context = None
    _page = None
    _lock = asyncio.Lock()  # Add a class-level lock
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LinkedInScraper, cls).__new__(cls)
        return cls._instance
    
    async def initialize(self):
        async with self._lock:
            if not self._browser:
                logger.info("Initializing browser...")
                try:
                    playwright = await async_playwright().start()
                    self._browser = await playwright.chromium.launch(
                        headless=False,
                        args=['--disable-blink-features=AutomationControlled']
                    )
                    storage_state_path = "linkedin_state.json"
                    if os.path.exists(storage_state_path):
                        logger.info("Loading existing LinkedIn session from storage state.")
                        self._context = await self._browser.new_context(
                            storage_state=storage_state_path,
                            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                            viewport={'width': 1920, 'height': 1080}
                        )
                    else:
                        logger.info("No storage state found. Creating new context.")
                        self._context = await self._browser.new_context(
                            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                            viewport={'width': 1920, 'height': 1080}
                        )
                    self._page = await self._context.new_page()
                    logger.info("Browser initialized successfully")
                except Exception as e:
                    logger.error(f"Exception during browser initialization: {e}", exc_info=True)
                    self._browser = None
                    self._context = None
                    self._page = None
                    raise
    
    async def close(self):
        if self._browser:
            logger.info("Closing browser...")
        try:
            await self._browser.close()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Exception during browser close: {e}", exc_info=True)
        finally:
            self._browser = None
            self._context = None
            self._page = None

    
    async def login(self):
        try:
            if not self._page:
                await self.initialize()
            logger.info("[login] Checking if already authenticated...")
            await self._page.goto("https://www.linkedin.com/", timeout=15000)
            await self._page.wait_for_load_state("domcontentloaded", timeout=10000)
            current_url = self._page.url
            if "feed" in current_url or "jobs" in current_url:
                logger.info("[login] Already authenticated. Skipping login.")
                return True
            logger.info("[login] Not authenticated. Proceeding with login flow...")
            logger.info("[login] Navigating to LinkedIn login page...")
            try:
                await self._page.goto("https://www.linkedin.com/login", timeout=15000)
                logger.info("[login] Successfully navigated to login page.")
            except TimeoutError:
                logger.error("[login] Timeout navigating to LinkedIn login page.", exc_info=True)
                return False
            logger.info("[login] Waiting for login page to load (networkidle)...")
            try:
                await self._page.wait_for_load_state("networkidle", timeout=10000)
                logger.info("[login] Login page loaded (networkidle).")
            except TimeoutError:
                logger.error("[login] Timeout waiting for login page to load.", exc_info=True)
                return False
            await asyncio.sleep(2)
            logger.info("[login] Filling in username...")
            try:
                await self._page.fill("#username", settings.LINKEDIN_EMAIL, timeout=5000)
                logger.info("[login] Username filled.")
            except TimeoutError:
                logger.error("[login] Timeout filling username field.", exc_info=True)
                return False
            await asyncio.sleep(1)
            logger.info("[login] Filling in password...")
            try:
                await self._page.fill("#password", settings.LINKEDIN_PASSWORD, timeout=5000)
                logger.info("[login] Password filled.")
            except TimeoutError:
                logger.error("[login] Timeout filling password field.", exc_info=True)
                return False
            await asyncio.sleep(1)
            logger.info("[login] Clicking login button...")
            try:
                await self._page.click("button[type='submit']", timeout=5000)
                logger.info("[login] Login button clicked.")
            except TimeoutError:
                logger.error("[login] Timeout clicking login button.", exc_info=True)
                return False
            logger.info("[login] Waiting for post-login navigation (networkidle)...")
            try:
                await self._page.wait_for_load_state("networkidle", timeout=20000)
                logger.info("[login] Post-login navigation complete.")
            except TimeoutError:
                logger.warning("[login] Timeout waiting for post-login navigation.", exc_info=True)
            current_url = self._page.url
            logger.info(f"[login] Current URL after login: {current_url}")
            if "feed" in current_url or "jobs" in current_url:
                logger.info("[login] Successfully logged in to LinkedIn. Saving session state.")
                await self._context.storage_state(path="linkedin_state.json")
                return True
            else:
                logger.error(f"[login] Failed to login to LinkedIn. Current URL: {current_url}")
                return False
        except Exception as e:
            logger.error(f"[login] Error during LinkedIn login: {str(e)}", exc_info=True)
            return False
            
    async def search_jobs(self, query: Dict[str, Any]) -> List[JobListing]:
        async with self._lock:
            try:
                if not self._page:
                    await self.initialize()
                # Login first
                if not await self.login():
                    logger.error("Cannot proceed with job search without login")
                    await self.close()
                    return []
                # Construct LinkedIn search URL
                search_url = self._construct_search_url(query)
                logger.info(f"Searching LinkedIn with URL: {search_url}")
                # Navigate to search page
                await self._page.goto(search_url, wait_until="domcontentloaded")
                # Wait for job cards to appear
                await self._page.wait_for_selector(".scaffold-layout__list-item", timeout=20000)
                await asyncio.sleep(2)  # Optional: let the page settle
                # Extract job listings
                jobs = []
                job_cards = await self._page.query_selector_all(".scaffold-layout__list-item")
                logger.info(f"Found {len(job_cards)} job cards")
                for card in job_cards:
                    try:
                        job_data = await self._extract_job_data(card)
                        if job_data:
                            jobs.append(JobListing(**job_data))
                            logger.info(f"Successfully extracted job: {job_data['title']} at {job_data['company']}")
                    except Exception as e:
                        logger.error(f"Error extracting job data: {str(e)}", exc_info=True)
                        continue
                logger.info(f"Successfully extracted {len(jobs)} jobs")
                await self.close()  # Always close browser after scraping
                return jobs
            except Exception as e:
                logger.error(f"Error during LinkedIn job search: {str(e)}", exc_info=True)
                await self.close()
                return []
            
    def _construct_search_url(self, query: Dict[str, Any]) -> str:
        """Construct LinkedIn job search URL from query parameters"""
        base_url = "https://www.linkedin.com/jobs/search/?"
        params = []
        
        if query.get("title"):
            params.append(f"keywords={query['title']}")
        if query.get("location"):
            params.append(f"location={query['location']}")
        if query.get("job_type"):
            params.append(f"f_JT={query['job_type']}")
        if query.get("experience_level"):
            params.append(f"f_E={query['experience_level']}")
        
        # Add date_posted support
        # LinkedIn's f_TP param: 1=24h, 2=week, 3=month
        date_posted_map = {
            "any": None,
            "past_24_hours": 1,
            "past_week": 2,
            "past_month": 3
        }
        date_posted = query.get("date_posted")
        if date_posted:
            mapped = date_posted_map.get(date_posted.lower())
            if mapped:
                params.append(f"f_TP={mapped}")
        
        return base_url + "&".join(params)
        
    def _parse_relative_date(self, text: str) -> str:
        """Convert relative date strings like '2 weeks ago' to ISO date string."""
        text = text.strip().lower()
        now = datetime.utcnow()
        if not text:
            return ""
        match = re.match(r"(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago", text)
        if match:
            value, unit = int(match.group(1)), match.group(2)
            if unit == "second":
                dt = now - timedelta(seconds=value)
            elif unit == "minute":
                dt = now - timedelta(minutes=value)
            elif unit == "hour":
                dt = now - timedelta(hours=value)
            elif unit == "day":
                dt = now - timedelta(days=value)
            elif unit == "week":
                dt = now - timedelta(weeks=value)
            elif unit == "month":
                dt = now - timedelta(days=30*value)
            elif unit == "year":
                dt = now - timedelta(days=365*value)
            else:
                return ""
            return dt.strftime("%Y-%m-%d")
        return ""

    async def _extract_job_data(self, card) -> Dict[str, Any]:
        try:
            # Click the job card to load details in the right pane
            await card.click()
            await asyncio.sleep(1)  # Wait for details to load

            # --- Job Title (from detail pane) ---
            title = await self._get_text(".job-details-jobs-unified-top-card__job-title")
            if not title:
                title_el = await card.query_selector(".job-card-list__title")
                title = (await title_el.text_content()) if title_el else ""

            # --- Company Name ---
            company_el = await card.query_selector(".artdeco-entity-lockup__subtitle span[dir='ltr']")
            company = (await company_el.text_content()) if company_el else ""

            # --- Location & Metadata ---
            location = ""
            try:
                location_el = await card.query_selector(".artdeco-entity-lockup__caption ul.job-card-container__metadata-wrapper li")
                location = (await location_el.text_content()) if location_el else ""
            except Exception:
                pass

            # --- Posted Date ---
            posted_date_raw = await self._get_text("span.tvm__text.tvm__text--low-emphasis")
            posted_date = ""
            if posted_date_raw:
                parsed = self._parse_relative_date(posted_date_raw)
                posted_date = parsed if parsed else ""

            # --- Description ---
            description = await self._get_text(".jobs-box__html-content")
            if not description:
                description = await self._get_text(".jobs-description-content__text--stretch")
            if not description:
                paragraphs = await self._page.query_selector_all("div.mt4 p[dir='ltr']")
                description = " ".join([
                    (await p.text_content() or "").strip() for p in paragraphs
                ]) if paragraphs else ""

            # --- Application URL ---
            application_url = ""
            try:
                link_el = await card.query_selector(".job-card-list__title a")
                application_url = await link_el.get_attribute("href") if link_el else self._page.url
            except Exception:
                application_url = self._page.url  # fallback

            # --- Source URL ---
            source_url = self._page.url

            return {
                "title": title.strip(),
                "company": company.strip(),
                "location": location.strip(),
                "description": description.strip(),
                "job_type": "",  # Add logic if you find a selector for this
                "experience_level": "",  # Add logic if you find a selector for this
                "application_url": application_url,
                "source": "linkedin",
                "source_url": source_url,
                "is_active": True,
                "posted_date": posted_date if posted_date else None,
                "extracted_date": datetime.utcnow(),  # Add extraction timestamp
                "applied": False,  # Default to not applied
            }
        except Exception as e:
            logger.error(f"Error extracting job data from card: {str(e)}", exc_info=True)
            return None
            
    async def _get_text(self, selector: str) -> str:
        """Helper method to get text content from an element"""
        try:
            element = await self._page.query_selector(selector)
            if element:
                return await element.text_content()
            return ""
        except Exception:
            return ""
            
    async def _get_attribute(self, selector: str, attribute: str) -> str:
        """Helper method to get attribute value from an element"""
        try:
            element = await self._page.query_selector(selector)
            if element:
                return await element.get_attribute(attribute)
            return ""
        except Exception:
            return "" 