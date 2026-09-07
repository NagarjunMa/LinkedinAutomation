"""PII-free analytics contracts for the public-preview landing page."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator


class PublicPreviewEventName(str, Enum):
    HERO_CTA = "hero_cta"
    FORM_START = "form_start"
    FORM_SUCCESS = "form_success"
    FORM_VALIDATION_FAILURE = "form_validation_failure"
    SCROLL_DEPTH = "scroll_depth"


class PublicPreviewFormLocation(str, Enum):
    HERO = "hero"
    FINAL_CTA = "final_cta"


class PublicPreviewValidationCategory(str, Enum):
    CONSENT = "consent"
    SERVER_VALIDATION = "server_validation"
    RATE_LIMIT = "rate_limit"
    UNAVAILABLE = "unavailable"


class PublicPreviewEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_name: PublicPreviewEventName
    form_location: PublicPreviewFormLocation | None = None
    validation_category: PublicPreviewValidationCategory | None = None
    scroll_depth: Literal[25, 50, 75, 100] | None = None

    @model_validator(mode="after")
    def validate_event_dimensions(self) -> "PublicPreviewEventCreate":
        form_events = {
            PublicPreviewEventName.HERO_CTA,
            PublicPreviewEventName.FORM_START,
            PublicPreviewEventName.FORM_SUCCESS,
            PublicPreviewEventName.FORM_VALIDATION_FAILURE,
        }
        if self.event_name in form_events and self.form_location is None:
            raise ValueError("form_location is required for form events")
        if (
            self.event_name == PublicPreviewEventName.FORM_VALIDATION_FAILURE
            and self.validation_category is None
        ):
            raise ValueError("validation_category is required for validation failures")
        if (
            self.event_name == PublicPreviewEventName.SCROLL_DEPTH
            and self.scroll_depth is None
        ):
            raise ValueError("scroll_depth is required for scroll-depth events")
        return self
