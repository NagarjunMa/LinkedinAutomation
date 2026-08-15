"""API schemas for the tailored resume library."""

from datetime import datetime

from pydantic import BaseModel


class TailoredResumeListItem(BaseModel):
    version_id: str
    resume_document_id: str
    source_filename: str
    company_name: str | None = None
    target_role_title: str | None = None
    role_category: str | None = None
    seniority: str | None = None
    country_hint: str | None = None
    match_score: int | None = None
    template_id: str | None = None
    accepted_change_count: int
    created_at: datetime | None = None
    accepted_at: datetime | None = None


class TailoredResumeDetail(TailoredResumeListItem):
    resume_json: dict
    source_jd_text: str | None = None
    extracted_requirements: dict
    diff_plan: dict
    accepted_changes: list[dict]


class TailoredDownloadRequest(BaseModel):
    template_id: str | None = None
    filename: str | None = None
