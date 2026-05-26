from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Country(str, Enum):
    US = "US"
    IN = "IN"


class RoleTemplate(str, Enum):
    SWE = "swe"
    DS = "ds"
    PM = "pm"


class ExportRequest(BaseModel):
    resume_document_id: str = Field(..., min_length=1)
    resume_version_id: Optional[str] = None
    country: Country
    role_template: RoleTemplate
    filename: Optional[str] = None


class ExportResponse(BaseModel):
    export_id: str
    download_url: str
    expires_at: datetime
    country: Country
    role_template: RoleTemplate
    filename: Optional[str] = None
