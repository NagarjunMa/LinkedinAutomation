from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class JobListing(Base):
    __tablename__ = "job_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=False)
    job_type = Column(String(50))  # Full-time, Part-time, Contract, etc.
    experience_level = Column(String(50))  # Entry, Mid, Senior, etc.
    description = Column(Text)
    requirements = Column(Text)
    salary_range = Column(String(100))
    posted_date = Column(DateTime, default=datetime.utcnow)
    application_url = Column(String(512))
    source_url = Column(String(512))
    source = Column(String(50), default="linkedin")  # linkedin, indeed, etc.
    is_active = Column(Boolean, default=True)
    job_metadata = Column(JSON)  # Additional metadata as JSON
    applied = Column(Boolean, default=False)  # Track if job has been applied to
    extracted_date = Column(DateTime, default=datetime.utcnow)  # When the job was scraped
    
    # Relationships
    search_results = relationship("SearchResult", back_populates="job_listing")
    
    def __repr__(self):
        return f"<JobListing {self.title} at {self.company}>"

class SearchQuery(Base):
    __tablename__ = "search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    location = Column(String(255))
    keywords = Column(String(512))
    job_type = Column(String(50))
    experience_level = Column(String(50))
    date_posted = Column(String, nullable=True)
    salary_range = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    schedule = Column(String(50))  # daily, weekly, monthly, etc.
    last_run = Column(DateTime)
    job_metadata = Column(JSON)
    
    # Relationships
    search_results = relationship("SearchResult", back_populates="search_query")
    
    def __repr__(self):
        return f"<SearchQuery {self.title} in {self.location}>"

class SearchResult(Base):
    __tablename__ = "search_results"
    
    id = Column(Integer, primary_key=True, index=True)
    search_query_id = Column(Integer, ForeignKey("search_queries.id"))
    job_listing_id = Column(Integer, ForeignKey("job_listings.id"))
    match_score = Column(Integer)  # Relevance score
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    search_query = relationship("SearchQuery", back_populates="search_results")
    job_listing = relationship("JobListing", back_populates="search_results")
    
    def __repr__(self):
        return f"<SearchResult {self.job_listing_id} for query {self.search_query_id}>" 