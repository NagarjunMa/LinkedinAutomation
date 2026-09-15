"""FastAPI dependency adapters for application services."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.export_service import ExportApplicationService
from app.application.jd_service import JDTailoringApplicationService
from app.application.job_service import JobApplicationService
from app.application.profile_service import ProfileApplicationService
from app.application.resume_service import ResumeApplicationService
from app.application.tailored_resume_service import TailoredResumeApplicationService
from app.db.session import get_db
from app.core.openai_client import ModelRuntime, get_model_runtime


def get_resume_application_service(
    db: Session = Depends(get_db),
    runtime: ModelRuntime = Depends(get_model_runtime),
) -> ResumeApplicationService:
    return ResumeApplicationService(db, runtime=runtime)


def get_jd_application_service(
    db: Session = Depends(get_db),
    runtime: ModelRuntime = Depends(get_model_runtime),
) -> JDTailoringApplicationService:
    return JDTailoringApplicationService(db, runtime=runtime)


def get_job_application_service(
    db: Session = Depends(get_db),
) -> JobApplicationService:
    return JobApplicationService(db)


def get_profile_application_service(
    db: Session = Depends(get_db),
) -> ProfileApplicationService:
    return ProfileApplicationService(db)


def get_export_application_service(
    db: Session = Depends(get_db),
) -> ExportApplicationService:
    return ExportApplicationService(db)


def get_tailored_resume_application_service(
    db: Session = Depends(get_db),
) -> TailoredResumeApplicationService:
    return TailoredResumeApplicationService(db)
