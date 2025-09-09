import os
import asyncio
import aiohttp
import time
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.utils.logger import get_logger

logger = get_logger(__name__)

class RateLimiter:
    """Rate limiter for Apollo.io API calls"""
    
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self.timestamps = []
    
    async def acquire(self):
        """Acquire permission to make an API call"""
        now = time.time()
        
        # Remove timestamps older than the period
        self.timestamps = [ts for ts in self.timestamps if now - ts < self.period]
        
        if len(self.timestamps) >= self.calls:
            # Wait until we can make another call
            sleep_time = self.period - (now - self.timestamps[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Waiting {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                return await self.acquire()
        
        self.timestamps.append(time.time())
        return True

class DailyUsageTracker:
    """Track daily API usage and limits (simplified without database)"""
    
    def __init__(self, db: Session, limit: int = 600):
        self.db = db
        self.limit = limit
        self.today = date.today().isoformat()
        self.calls_made = 0
        self.last_reset = datetime.utcnow()
    
    def get_usage(self) -> Dict[str, Any]:
        """Get today's usage record (in-memory only)"""
        return {
            "date": self.today,
            "calls_made": self.calls_made,
            "calls_remaining": self.limit - self.calls_made,
            "last_reset": self.last_reset
        }
    
    def can_make_call(self) -> bool:
        """Check if we can make an API call"""
        return (self.limit - self.calls_made) > 0
    
    def record_call(self, calls: float = 1.0):
        """Record an API call"""
        self.calls_made += calls
        self.last_reset = datetime.utcnow()
        
        logger.info(f"Apollo API usage: {self.calls_made}/{self.limit} calls used")
        
        if (self.limit - self.calls_made) < 50:
            logger.warning(f"Low Apollo API calls remaining: {self.limit - self.calls_made}")

class ApolloClient:
    """Apollo.io API client with rate limiting and error handling"""
    
    def __init__(self, db: Session):
        self.api_key = os.getenv('APOLLO_API_KEY')
        if not self.api_key:
            raise ValueError("APOLLO_API_KEY environment variable is required")
        
        self.base_url = 'https://api.apollo.io/v1'
        self.rate_limiter = RateLimiter(calls=50, period=60)  # 50 calls per minute
        self.usage_tracker = DailyUsageTracker(db, limit=600)  # 600 calls per day
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a rate-limited API request to Apollo.io"""
        
        # Check daily usage limit
        if not self.usage_tracker.can_make_call():
            raise Exception("Daily Apollo API limit reached")
        
        # Wait for rate limiter
        await self.rate_limiter.acquire()
        
        # Make the request
        url = f"{self.base_url}/{endpoint}"
        
        # Remove api_key from params and add to headers
        if 'api_key' in params:
            del params['api_key']
        
        headers = {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            async with self.session.post(url, json=params, headers=headers) as response:
                if response.status == 429:
                    # Rate limited, wait and retry
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Apollo API rate limited. Waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(endpoint, params)
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Apollo API error {response.status}: {error_text}")
                    raise Exception(f"Apollo API error: {response.status}")
                
                data = await response.json()
                
                # Record the API call
                self.usage_tracker.record_call()
                
                return data
                
        except aiohttp.ClientError as e:
            logger.error(f"Apollo API request failed: {e}")
            raise Exception(f"Apollo API request failed: {e}")
    
    async def search_people(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for people using Apollo.io API"""
        
        params = {
            "api_key": self.api_key,
            "page": 1,
            "per_page": 25,  # Maximum per page
            **search_params
        }
        
        try:
            response = await self._make_request("people/search", params)
            
            if response.get('status') != 'success':
                logger.error(f"Apollo search failed: {response}")
                return []
            
            people = response.get('people', [])
            logger.info(f"Found {len(people)} people in Apollo search")
            
            return people
            
        except Exception as e:
            logger.error(f"Apollo search error: {e}")
            return []
    
    async def search_people_by_company(
        self, 
        company_name: str, 
        contact_type: str,
        location: Optional[str] = None,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for people at a specific company"""
        
        # Define search templates based on contact type
        if contact_type == 'recruiter':
            search_params = {
                "person_titles": [
                    "Technical Recruiter", "Engineering Recruiter", 
                    "Talent Acquisition", "Senior Recruiter",
                    "Recruiting Manager", "People Operations"
                ],
                "person_seniorities": ["manager", "senior", "director"],
                "organization_name": company_name,
                "organization_departments": ["recruiting", "hr", "talent"]
            }
        elif contact_type == 'engineer':
            search_params = {
                "person_titles": [
                    "Senior Software Engineer", "Staff Software Engineer",
                    "Principal Engineer", "Tech Lead", "Engineering Manager"
                ],
                "person_seniorities": ["senior", "staff", "principal"],
                "organization_name": company_name,
                "organization_departments": ["engineering", "product", "technology"]
            }
        else:
            raise ValueError(f"Invalid contact type: {contact_type}")
        
        # Add location filter if provided
        if location:
            search_params["person_locations"] = [location]
        
        # Execute search
        people = await self.search_people(search_params)
        
        # Limit results
        return people[:limit]
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        usage = self.usage_tracker.get_usage()
        return {
            "date": usage.date,
            "calls_made": usage.calls_made,
            "calls_remaining": usage.calls_remaining,
            "limit": self.usage_tracker.limit,
            "percentage_used": (usage.calls_made / self.usage_tracker.limit) * 100
        } 