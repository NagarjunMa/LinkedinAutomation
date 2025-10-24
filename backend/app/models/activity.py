from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.db.base_class import Base

class ActivityRecord(Base):
    __tablename__ = "activity_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    activity_type = Column(String, nullable=False)  # 'job_extraction' or 'referral_email'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    activity_metadata = Column(JSON, nullable=True)  # Store additional data like job title, company, etc.
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "activity_type": self.activity_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.activity_metadata or {}
        }
