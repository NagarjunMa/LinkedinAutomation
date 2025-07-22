import asyncio
import logging
import requests
import feedparser
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus, urljoin
import re
from bs4 import BeautifulSoup
from app.core.config import settings
from app.models.job import JobListing

logger = logging.getLogger(__name__)

class JobAggregator:
    """
    Production-ready job aggregation service using RSS.app and Indeed public APIs
    """
    
    def __init__(self):
        self.rss_app_base_url = "https://rss.app/feeds"
        self.indeed_base_url = "https://www.indeed.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })
        
    async def search_jobs(self, query: Dict[str, Any]) -> List[JobListing]:
        """
        Main job search method that aggregates from multiple sources:
        1. RSS.app feeds (175 jobs)
        2. Indeed RSS feeds (additional jobs)
        3. Other job board RSS feeds (additional jobs)
        """
        logger.info(f"Starting job aggregation from multiple sources for query: {query}")
        
        all_jobs = []
        
        # Check if enhanced search mode is enabled (ignore location for more jobs)
        enhanced_mode = query.get("enhanced_search", False)
        if enhanced_mode:
            logger.info("Enhanced search mode enabled - searching all locations for maximum job volume")
            # Temporarily remove location filter for broader search
            enhanced_query = {k: v for k, v in query.items() if k != "location"}
        else:
            enhanced_query = query
        
        # Fetch from RSS.app feeds (primary source)
        try:
            rss_jobs = await self._fetch_rss_app_jobs(enhanced_query)
            all_jobs.extend(rss_jobs)
            logger.info(f"Fetched {len(rss_jobs)} jobs from RSS.app feeds")
        except Exception as e:
            logger.error(f"Error fetching RSS.app jobs: {e}")
        
        # Fetch from Indeed RSS feeds (secondary source)
        try:
            indeed_jobs = await self._fetch_indeed_jobs(enhanced_query)
            all_jobs.extend(indeed_jobs)
            logger.info(f"Fetched {len(indeed_jobs)} jobs from Indeed RSS feeds")
        except Exception as e:
            logger.error(f"Error fetching Indeed jobs: {e}")
        
        # Fetch from other job board RSS feeds (tertiary source)
        try:
            board_jobs = await self._fetch_job_board_feeds(enhanced_query)
            all_jobs.extend(board_jobs)
            logger.info(f"Fetched {len(board_jobs)} jobs from job board feeds")
        except Exception as e:
            logger.error(f"Error fetching job board feeds: {e}")
        
        # Remove duplicates and filter
        unique_jobs = self._deduplicate_jobs(all_jobs)
        
        # Apply original query filters (including location) for final filtering
        filtered_jobs = self._filter_jobs(unique_jobs, query)
        
        logger.info(f"Total jobs from all sources: {len(all_jobs)}")
        logger.info(f"Unique jobs after deduplication: {len(unique_jobs)}")
        logger.info(f"Final filtered jobs: {len(filtered_jobs)}")
        return filtered_jobs
    
    async def _fetch_rss_app_jobs(self, query: Dict[str, Any]) -> List[JobListing]:
        """
        Fetch jobs using RSS.app feeds (JSON format) with feed health monitoring
        """
        jobs = []
        
        # Get RSS.app feed URLs for different states
        rss_feeds = self._get_rss_app_feeds(query)
        
        # Track feed health
        from app.db.session import SessionLocal
        from app.models.job import RSSFeedConfiguration
        
        db = SessionLocal()
        
        for state_name, feed_url in rss_feeds.items():
            try:
                logger.info(f"Fetching RSS.app feed for {state_name}")
                
                # Fetch JSON feed (RSS.app v1.1 format)
                response = self.session.get(feed_url, timeout=30)
                response.raise_for_status()
                
                feed_data = response.json()
                items = feed_data.get('items', [])
                
                logger.info(f"Found {len(items)} items in {state_name} feed")
                
                # Update feed health in database
                try:
                    feed_config = db.query(RSSFeedConfiguration).filter(
                        RSSFeedConfiguration.feed_url == feed_url
                    ).first()
                    
                    if feed_config:
                        feed_config.last_refresh = datetime.now(timezone.utc)
                        feed_config.last_job_count = len(items)
                        db.commit()
                        logger.debug(f"Updated feed health for {feed_config.name}: {len(items)} jobs")
                        
                except Exception as e:
                    logger.warning(f"Could not update feed health for {state_name}: {e}")
                
                for item in items[:25]:  # Increase to 25 jobs per state (max available)
                    job_data = self._parse_json_feed_item(item, state_name)
                    if job_data:
                        jobs.append(JobListing(**job_data))
                        
            except Exception as e:
                logger.error(f"Error processing RSS.app feed {state_name}: {e}")
                
                # Mark feed as having issues
                try:
                    feed_config = db.query(RSSFeedConfiguration).filter(
                        RSSFeedConfiguration.feed_url == feed_url
                    ).first()
                    
                    if feed_config:
                        feed_config.last_refresh = datetime.now(timezone.utc)
                        feed_config.last_job_count = 0  # Indicates failure
                        db.commit()
                        
                except Exception as db_error:
                    logger.warning(f"Could not update failed feed status: {db_error}")
                
                continue
        
        db.close()
        return jobs
    
    def _get_rss_app_feeds(self, query: Dict[str, Any]) -> Dict[str, str]:
        """
        Get RSS.app feed URLs from database configuration instead of hardcoded values
        """
        from app.db.session import SessionLocal
        from app.models.job import RSSFeedConfiguration
        
        db = SessionLocal()
        try:
            # Get all active RSS feeds from database
            active_feeds = db.query(RSSFeedConfiguration).filter(
                RSSFeedConfiguration.is_active == True,
                RSSFeedConfiguration.source_type == "rss_app"
            ).all()
            
            feeds = {}
            for feed_config in active_feeds:
                # Use the feed name as key (converted to lowercase with underscores)
                feed_key = feed_config.name.lower().replace(' ', '_').replace('state_', '').replace('software_engineers', '')
                feeds[feed_key] = feed_config.feed_url
                
                # Update last_refresh time
                feed_config.last_refresh = datetime.now(timezone.utc)
                
            db.commit()
            logger.info(f"Loaded {len(feeds)} RSS feeds from database configuration")
            
        except Exception as e:
            logger.error(f"Error loading RSS feeds from database: {e}")
            # Fallback to previous hardcoded feeds if database fails
            feeds = {
                "washington": "https://rss.app/feeds/v1.1/4oDo6ldXWx91XJRL.json",
                "texas": "https://rss.app/feeds/v1.1/sRqFCmJl3DGe41OF.json",
                "california": "https://rss.app/feeds/v1.1/SJQIBYMNoFgqDSS4.json",
                "florida": "https://rss.app/feeds/v1.1/i2MS3pCQpXWvXotd.json",
                "illinois": "https://rss.app/feeds/v1.1/xywk3mYJjoUFfmtN.json",
                "boston": "https://rss.app/feeds/v1.1/zYrb2zVQRwlCfNOE.json",
                "michigan": "https://rss.app/feeds/v1.1/KYIvySiyWFnoS6Oz.json",
                "newyork": "https://rss.app/feeds/v1.1/13X05pZ4QYIImTC2.json"
            }
            logger.warning("Using fallback hardcoded feeds")
        finally:
            db.close()
        
        # Filter feeds based on query location if specified
        query_location = query.get("location", "").lower()
        if query_location:
            # If specific location requested, try to match feeds
            location_matches = {
                "washington": ["washington", "seattle", "wa"],
                "texas": ["texas", "austin", "dallas", "houston", "tx"],
                "california": ["california", "san francisco", "los angeles", "ca"],
                "florida": ["florida", "miami", "orlando", "fl"],
                "illinois": ["illinois", "chicago", "il"],
                "boston": ["boston", "massachusetts", "ma"],
                "michigan": ["michigan", "detroit", "mi"],
                "newyork": ["new york", "ny", "nyc", "manhattan"]
            }
            
            matched_feeds = {}
            for state, feed_url in feeds.items():
                # Extract state name from feed key
                state_name = state.split('_')[0] if '_' in state else state
                if any(loc in query_location for loc in location_matches.get(state_name, [])):
                    matched_feeds[state] = feed_url
            
            # If matches found, use only those; otherwise use all feeds for broader coverage
            if matched_feeds:
                # For better job volume, also include nearby states for major locations
                if query_location in ['texas', 'tx']:
                    # Include neighboring states and major tech hubs for Texas searches
                    matched_feeds.update({k: v for k, v in feeds.items() 
                                        if k in ['california', 'newyork', 'washington']})
                elif query_location in ['california', 'ca']:
                    # Include major tech states for California searches  
                    matched_feeds.update({k: v for k, v in feeds.items() 
                                        if k in ['washington', 'newyork']})
                
                return matched_feeds
        
        return feeds
    
    async def _fetch_indeed_jobs(self, query: Dict[str, Any]) -> List[JobListing]:
        """
        Indeed RSS feeds are blocked (403 Forbidden), so we'll use alternative sources
        """
        logger.info("Indeed RSS feeds are currently blocked, skipping Indeed source")
        return []
    
    async def _fetch_job_board_feeds(self, query: Dict[str, Any]) -> List[JobListing]:
        """
        Fetch jobs from various working job board RSS feeds
        """
        jobs = []
        
        # Working job board RSS feeds (verified as accessible)
        job_board_feeds = {
            "remoteok": "https://remoteok.io/remote-jobs.rss",
            "weworkremotely": "https://weworkremotely.com/remote-jobs.rss",
            "ycombinator": "https://news.ycombinator.com/jobs.rss",
            "dice": "https://www.dice.com/jobs/rss",
            "authentic_jobs": "https://authenticjobs.com/rss",
            "flexjobs": "https://www.flexjobs.com/rss",
            # Alternative tech job feeds
            "angel_list": "https://angel.co/jobs.rss",
            "startup_jobs": "https://startup.jobs/rss",
            "tech_jobs": "https://techjobs.com/rss",
        }
        
        for board_name, feed_url in job_board_feeds.items():
            try:
                logger.info(f"Fetching {board_name} RSS feed")
                
                # Parse RSS feed with timeout
                import socket
                socket.setdefaulttimeout(10)
                feed = feedparser.parse(feed_url)
                
                if feed.bozo:
                    logger.warning(f"{board_name} RSS feed has parsing issues: {feed.bozo_exception}")
                    continue
                
                logger.info(f"Found {len(feed.entries)} entries in {board_name} RSS feed")
                
                # Process entries (limit to 15 per board to get variety)
                for entry in feed.entries[:15]:
                    try:
                        job_data = self._parse_rss_entry(entry, board_name)
                        if job_data and self._matches_query(job_data, query):
                            jobs.append(JobListing(**job_data))
                    except Exception as e:
                        logger.debug(f"Error parsing {board_name} RSS entry: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Error fetching {board_name} feed: {e}")
                continue
        
        logger.info(f"Total job board jobs fetched: {len(jobs)}")
        return jobs
    
    def _build_indeed_search_url(self, query: Dict[str, Any]) -> str:
        """
        Build Indeed RSS feed URL with location-specific searches
        """
        base_url = "https://www.indeed.com/rss"
        
        # Build search query
        keywords = []
        if query.get("title"):
            keywords.append(query["title"])
        if query.get("keywords"):
            keywords.append(query["keywords"])
        
        search_term = " ".join(keywords) if keywords else "Software Engineer"
        
        # Get location from query or default to major tech hubs
        location = query.get("location", "")
        if not location:
            # Default to Texas since that's what LinkedIn shows
            location = "Texas"
        
        params = [
            f"q={quote_plus(search_term)}",
            f"l={quote_plus(location)}",
            "sort=date",
            "limit=100"  # Increase limit to get more jobs
        ]
        
        return f"{base_url}?" + "&".join(params)
    
    def _parse_indeed_job_card(self, card) -> Optional[Dict[str, Any]]:
        """
        Parse Indeed job card HTML into job data
        """
        try:
            # Extract title
            title_elem = card.find('h2', class_='jobTitle') or card.find('a', {'data-jk': True})
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract company
            company_elem = card.find('span', class_='companyName') or card.find('a', {'data-testid': 'company-name'})
            company = company_elem.get_text(strip=True) if company_elem else ""
            
            # Extract location
            location_elem = card.find('div', class_='companyLocation') or card.find('[data-testid="job-location"]')
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Extract job URL
            link_elem = card.find('h2', class_='jobTitle')
            if link_elem:
                link = link_elem.find('a')
                job_url = urljoin(self.indeed_base_url, link.get('href')) if link else ""
            else:
                job_url = ""
            
            # Extract summary/description
            summary_elem = card.find('div', class_='summary') or card.find('[data-testid="job-snippet"]')
            description = summary_elem.get_text(strip=True) if summary_elem else ""
            
            # Extract posted date
            posted_elem = card.find('span', class_='date')
            posted_text = posted_elem.get_text(strip=True) if posted_elem else ""
            posted_date = self._parse_relative_date(posted_text)
            
            if not title or not company:
                return None
            
            return {
                "title": title,
                "company": company,
                "location": location or "Not specified",
                "description": description[:2000],  # Limit description
                "job_type": "Full-time",  # Default
                "experience_level": "Not specified",
                "application_url": job_url,
                "source": "indeed",
                "source_url": job_url,
                "is_active": True,
                "posted_date": posted_date,
                "extracted_date": datetime.now(timezone.utc),
                "applied": False,
            }
            
        except Exception as e:
            logger.error(f"Error parsing Indeed job card: {e}")
            return None
    
    def _parse_json_feed_item(self, item: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
        """
        Parse RSS.app JSON feed item into job data
        """
        try:
            title = item.get('title', '').strip()
            
            # Extract content
            content_text = item.get('content_text', '') or item.get('content_html', '')
            
            # Parse title to extract company and position
            # Format: "Company hiring Position in Location"
            company = ""
            job_title = title
            location = ""
            
            if " hiring " in title:
                parts = title.split(" hiring ")
                company = parts[0].strip()
                if len(parts) > 1:
                    remainder = parts[1].strip()
                    if " in " in remainder:
                        job_parts = remainder.split(" in ")
                        job_title = job_parts[0].strip()
                        location = job_parts[1].strip()
                    else:
                        job_title = remainder
            
            # Extract salary from content
            salary_range = self._extract_salary_from_content(content_text)
            
            # Get job URL
            job_url = item.get('url', '')
            
            # Parse date
            published_date = None
            if item.get('date_published'):
                try:
                    from dateutil.parser import parse
                    from datetime import timezone
                    published_date = parse(item['date_published'])
                    # Ensure timezone awareness
                    if published_date.tzinfo is None:
                        published_date = published_date.replace(tzinfo=timezone.utc)
                except:
                    pass
            
            if not title or not company:
                return None
            
            return {
                "title": job_title,
                "company": company,
                "location": location or f"{source.title()} area",
                "description": content_text[:2000] if content_text else "",
                "job_type": "Full-time",  # Default, could be extracted from content
                "experience_level": "Not specified",
                "salary_range": salary_range,
                "application_url": job_url,
                "source": f"rss_app_{source}",
                "source_url": job_url,
                "is_active": True,
                "posted_date": published_date,
                "extracted_date": datetime.now(timezone.utc),
                "applied": False,
            }
            
        except Exception as e:
            logger.error(f"Error parsing JSON feed item: {e}")
            return None
    
    def _extract_salary_from_content(self, content: str) -> str:
        """
        Extract salary information from job content
        """
        if not content:
            return ""
        
        # Common salary patterns
        salary_patterns = [
            r'\$[\d,]+(?:\.\d{2})?\s*(?:-|to)\s*\$[\d,]+(?:\.\d{2})?',  # $70,000 - $90,000
            r'\$[\d,]+(?:\.\d{2})?(?:/year|/yr|annually)',  # $80,000/year
            r'\$[\d,]+(?:\.\d{2})?K?',  # $80K, $80,000
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ""
    
    def _parse_rss_entry(self, entry, source: str) -> Optional[Dict[str, Any]]:
        """
        Parse RSS feed entry into job data
        """
        try:
            title = entry.get('title', '').strip()
            
            # Extract company from title or summary
            company = self._extract_company_from_entry(entry, source)
            
            # Get description
            description = ""
            if hasattr(entry, 'summary'):
                description = BeautifulSoup(entry.summary, 'html.parser').get_text()
            elif hasattr(entry, 'content'):
                description = BeautifulSoup(entry.content[0].value, 'html.parser').get_text()
            
            # Get location
            location = self._extract_location_from_entry(entry)
            
            # Get published date
            published_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_date = datetime(*entry.published_parsed[:6])
            
            # Get job URL
            job_url = entry.get('link', '')
            
            if not title:
                return None
            
            return {
                "title": title,
                "company": company or f"{source.title()} Job",
                "location": location or "Remote",
                "description": description[:2000],
                "job_type": "Full-time",
                "experience_level": "Not specified",
                "application_url": job_url,
                "source": source,
                "source_url": job_url,
                "is_active": True,
                "posted_date": published_date,
                "extracted_date": datetime.now(timezone.utc),
                "applied": False,
            }
            
        except Exception as e:
            logger.error(f"Error parsing RSS entry: {e}")
            return None
    
    def _extract_company_from_entry(self, entry, source: str) -> str:
        """
        Extract company name from RSS entry
        """
        # Try different methods based on source
        if source == "weworkremotely":
            # WeWorkRemotely format: "Company: Job Title"
            title = entry.get('title', '')
            if ':' in title:
                return title.split(':')[0].strip()
        
        # Try to extract from tags or categories
        if hasattr(entry, 'tags'):
            for tag in entry.tags:
                if 'company' in tag.term.lower():
                    return tag.term
        
        # Default fallback
        return ""
    
    def _extract_location_from_entry(self, entry) -> str:
        """
        Extract location from RSS entry
        """
        # Check summary for location patterns
        text = entry.get('summary', '') + ' ' + entry.get('title', '')
        
        # Common location patterns
        location_patterns = [
            r'(?:in|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z]{2,})?)',
            r'([A-Z][a-z]+,\s*[A-Z]{2,})',
            r'(Remote)',
            r'(Worldwide)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return "Remote"
    
    def _matches_query(self, job_data: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """
        Check if job matches the search query
        """
        # Check title keywords
        if query.get("title"):
            title_lower = job_data.get("title", "").lower()
            query_title = query["title"].lower()
            if query_title not in title_lower:
                return False
        
        # Check additional keywords
        if query.get("keywords"):
            text = f"{job_data.get('title', '')} {job_data.get('description', '')}".lower()
            keywords = query["keywords"].lower().split(",")
            if not any(keyword.strip() in text for keyword in keywords):
                return False
        
        # Check location
        if query.get("location"):
            job_location = job_data.get("location", "").lower()
            query_location = query["location"].lower()
            if query_location not in job_location and job_location != "remote":
                return False
        
        return True
    
    def _deduplicate_jobs(self, jobs: List[JobListing]) -> List[JobListing]:
        """
        Remove duplicate jobs based on title, company, and location
        """
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # Create a unique key based on title, company, and location
            title_clean = re.sub(r'[^\w\s]', '', job.title.lower().strip())
            company_clean = re.sub(r'[^\w\s]', '', job.company.lower().strip())
            location_clean = re.sub(r'[^\w\s]', '', job.location.lower().strip())
            
            key = f"{title_clean}|{company_clean}|{location_clean}"
            
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
            else:
                logger.debug(f"Duplicate job filtered: {job.title} at {job.company}")
        
        logger.info(f"Deduplicated {len(jobs)} jobs to {len(unique_jobs)} unique jobs")
        return unique_jobs
    
    def _filter_jobs(self, jobs: List[JobListing], query: Dict[str, Any]) -> List[JobListing]:
        """
        Filter jobs based on query criteria
        """
        filtered = []
        
        for job in jobs:
            # Filter by date if specified
            if query.get("date_posted") and job.posted_date:
                cutoff_date = self._get_date_cutoff(query["date_posted"])
                if cutoff_date:
                    # Ensure both dates are timezone-aware for comparison
                    job_date = job.posted_date
                    if job_date.tzinfo is None:
                        job_date = job_date.replace(tzinfo=timezone.utc)
                    if job_date < cutoff_date:
                        continue
            
            filtered.append(job)
        
        return filtered  # Return all filtered jobs without artificial limit
    
    def _get_date_cutoff(self, date_posted: str) -> Optional[datetime]:
        """
        Get cutoff date for filtering
        """
        from datetime import timezone
        now = datetime.now(timezone.utc)
        
        if date_posted == "past_24_hours":
            return now - timedelta(days=1)
        elif date_posted == "past_week":
            return now - timedelta(days=7)
        elif date_posted == "past_month":
            return now - timedelta(days=30)
        
        return None
    
    def _parse_relative_date(self, text: str) -> Optional[datetime]:
        """
        Parse relative date strings like '2 days ago'
        """
        if not text:
            return None
        
        text = text.strip().lower()
        now = datetime.utcnow()
        
        # Pattern: "X days ago", "X hours ago", etc.
        match = re.match(r"(\d+)\s+(second|minute|hour|day|week|month)s?\s+ago", text)
        if match:
            value, unit = int(match.group(1)), match.group(2)
            
            if unit == "second":
                return now - timedelta(seconds=value)
            elif unit == "minute":
                return now - timedelta(minutes=value)
            elif unit == "hour":
                return now - timedelta(hours=value)
            elif unit == "day":
                return now - timedelta(days=value)
            elif unit == "week":
                return now - timedelta(weeks=value)
            elif unit == "month":
                return now - timedelta(days=30*value)
        
        # Handle "today", "yesterday"
        if "today" in text:
            return now
        elif "yesterday" in text:
            return now - timedelta(days=1)
        
        return None 