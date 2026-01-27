from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean
from datetime import datetime
from app.db.base_class import Base


class ActivityRecord(Base):
    __tablename__ = "activity_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    activity_type = Column(String, index=True, nullable=False)  # 'job_search', 'application', 'email', 'resume', etc.
    activity_subtype = Column(String)  # More specific categorization
    title = Column(String)
    description = Column(Text)
    metadata = Column(JSON)  # Additional flexible data storage
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    duration_seconds = Column(Integer)  # For activities that have duration
    is_automated = Column(Boolean, default=False)
    source = Column(String)  # 'web', 'api', 'email', etc.
    created_at = Column(DateTime, default=datetime.utcnow)