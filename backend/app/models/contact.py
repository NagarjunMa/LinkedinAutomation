# This file is deprecated - Apollo contact discovery has been removed
# Keeping minimal Contact model for future use if needed

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from app.db.base_class import Base

class Contact(Base):
    """Basic contact model for future use"""
    __tablename__ = "contacts"
    
    id = Column(String(255), primary_key=True)
    name = Column(String(255))
    email = Column(String(255))
    company = Column(String(255))
    title = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Contact {self.name} at {self.company}>" 