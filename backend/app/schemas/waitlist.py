"""Strict public contracts for private-preview waitlist submissions."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CareerStage(str, Enum):
    STUDENT = "student"
    NEW_GRADUATE = "new_graduate"
    EARLY_CAREER = "early_career"
    EXPERIENCED_IC = "experienced_ic"
    TECHNICAL_LEADER = "technical_leader"
    CAREER_SWITCHER = "career_switcher"
    RETURNING_PROFESSIONAL = "returning_professional"


class WaitlistCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr = Field(max_length=254)
    career_stage: CareerStage | None = None
    target_role: str | None = Field(default=None, max_length=120)
    communication_challenge: str | None = Field(default=None, max_length=1000)
    consent: Literal[True]
    company_website: str = Field(default="", max_length=200)

    @field_validator("target_role", "communication_challenge", mode="after")
    @classmethod
    def empty_optional_text_becomes_none(cls, value: str | None) -> str | None:
        return value or None


class WaitlistResponse(BaseModel):
    message: str = "You're on the list. We'll be in touch when there is a useful next step."
