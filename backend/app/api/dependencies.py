"""FastAPI dependency adapters for application services."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.export_service import ExportApplicationService
from app.application.jd_service import JDTailoringApplicationService
from app.application.resume_service import ResumeApplicationService
from app.application.tailored_resume_service import TailoredResumeApplicationService
from app.db.session import get_db


def get_resume_application_service(
    db: Session = Depends(get_db),
) -> ResumeApplicationService:
    return ResumeApplicationService(db)


def get_jd_application_service(
    db: Session = Depends(get_db),
) -> JDTailoringApplicationService:
    return JDTailoringApplicationService(db)


def get_export_application_service(
    db: Session = Depends(get_db),
) -> ExportApplicationService:
    return ExportApplicationService(db)


def get_tailored_resume_application_service(
    db: Session = Depends(get_db),
) -> TailoredResumeApplicationService:
    return TailoredResumeApplicationService(db)
