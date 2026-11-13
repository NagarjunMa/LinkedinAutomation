"""Shared wire types for Career Evidence version 1."""

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import AfterValidator, AwareDatetime, BaseModel, BeforeValidator, ConfigDict, Field, StringConstraints


def _version(value: object) -> object:
    if type(value) is not int:
        raise ValueError("schema_version must be an integer")
    return value


def _timestamp(value: object) -> object:
    if not isinstance(value, (str, datetime)) or isinstance(value, str) and "T" not in value:
        raise ValueError("timestamp must be an ISO date-time with a time zone")
    return value


def _utc(value: datetime) -> datetime:
    try:
        return value.astimezone(timezone.utc)
    except OverflowError as exc:
        raise ValueError("timestamp outside representable UTC range") from exc


class CareerContract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    schema_version: Annotated[Literal[1], BeforeValidator(_version)]


Identifier = Annotated[str, StringConstraints(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")]
Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200, pattern=r"\S")]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000, pattern=r"\S")]
Sha256 = Annotated[str, StringConstraints(min_length=64, max_length=64, pattern=r"^[0-9a-f]+$")]
Revision = Annotated[int, Field(strict=True, ge=1)]
Count = Annotated[int, Field(strict=True, ge=0)]
Timestamp = Annotated[AwareDatetime, BeforeValidator(_timestamp), AfterValidator(_utc)]
CandidateStage = Literal[
    "student", "new_graduate", "early_career", "experienced_ic",
    "manager_or_leader", "senior_staff_or_founder", "career_switcher", "returning_professional",
]
Ownership = Literal["individual", "shared", "team", "unknown"]


class SourceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: Identifier
    source_version: Revision
