from app.db.session import engine
from app.models.job import Base  # or from wherever your Base is defined
from app.models.email_models import UserGmailConnection, EmailEvent, EmailSyncLog  # Import email models

if __name__ == "__main__":
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")