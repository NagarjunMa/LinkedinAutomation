"""
Migration to add Apollo.io contact intelligence models
"""

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

def add_apollo_contact_models():
    """Add Apollo.io contact models to the database"""
    
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    
    with engine.connect() as conn:
        try:
            # Create contacts table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    type VARCHAR(20) NOT NULL CHECK (type IN ('recruiter', 'engineer')),
                    company VARCHAR(255) NOT NULL,
                    name VARCHAR(255),
                    title VARCHAR(255),
                    email VARCHAR(255),
                    linkedin_url VARCHAR(500),
                    location VARCHAR(255),
                    department VARCHAR(255),
                    seniority VARCHAR(50),
                    specializations JSONB,
                    confidence_score FLOAT DEFAULT 0.0,
                    apollo_id VARCHAR(255) UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create indexes for contacts table
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(company)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_contacts_type ON contacts(type)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_contacts_apollo_id ON contacts(apollo_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_contacts_created_at ON contacts(created_at)"))
            
            # Create job_contacts relationship table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS job_contacts (
                    job_id INTEGER REFERENCES job_listings(id) ON DELETE CASCADE,
                    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
                    relevance_score FLOAT DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (job_id, contact_id)
                )
            """))
            
            # Create indexes for job_contacts table
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_job_contacts_job_id ON job_contacts(job_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_job_contacts_contact_id ON job_contacts(contact_id)"))
            
            # Create apollo_usage tracking table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS apollo_usage (
                    date VARCHAR(10) PRIMARY KEY,
                    calls_made FLOAT DEFAULT 0,
                    calls_remaining FLOAT DEFAULT 600,
                    last_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create trigger to update updated_at timestamp
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql'
            """))
            
            # Add triggers for updated_at
            conn.execute(text("""
                DROP TRIGGER IF EXISTS update_contacts_updated_at ON contacts;
                CREATE TRIGGER update_contacts_updated_at
                    BEFORE UPDATE ON contacts
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column()
            """))
            
            conn.execute(text("""
                DROP TRIGGER IF EXISTS update_apollo_usage_updated_at ON apollo_usage;
                CREATE TRIGGER update_apollo_usage_updated_at
                    BEFORE UPDATE ON apollo_usage
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column()
            """))
            
            conn.commit()
            logger.info("Successfully created Apollo.io contact models")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating Apollo.io contact models: {e}")
            raise

if __name__ == "__main__":
    add_apollo_contact_models() 