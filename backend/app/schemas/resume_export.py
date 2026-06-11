from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Country(str, Enum):
    US = "US"
    IN = "IN"


class RoleTemplate(str, Enum):
    SWE = "swe"
    DS = "ds"
    PM = "pm"


class ExportRequest(BaseModel):
    # Legacy Phase-2 shape (still supported)
    resume_document_id: Optional[str] = None
    country: Optional[Country] = None
    role_template: Optional[RoleTemplate] = None
    # Apply-flow shape (new)
    resume_version_id: Optional[str] = None
    template_id: Optional[str] = None  # accepts "us-swe" OR "us/swe"
    # Common
    filename: Optional[str] = None


class ExportResponse(BaseModel):
    export_id: str
    download_url: str
    expires_at: datetime
    country: Country
    role_template: RoleTemplate
    filename: Optional[str] = None
