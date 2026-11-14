"""Internal write inputs. Identity and revision numbers are assigned by the service."""
from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from .common import Identifier, Label, SourceRef, Timestamp
from .sources import CareerSourceKind


def _without_null(value: str) -> str:
    if "\x00" in value:
        raise ValueError("text cannot contain a null character")
    return value


StoredLabel = Annotated[Label, AfterValidator(_without_null)]
StoredContent = Annotated[str, Field(min_length=1, max_length=100_000), AfterValidator(_without_null)]


class CareerSourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: CareerSourceKind
    content: StoredContent | None = None
    resume_document_id: Identifier | None = None
    extraction_version: Identifier | None = None
    retention_expires_at: Timestamp | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> Self:
        if self.kind == "resume":
            if self.resume_document_id is None or self.content is not None:
                raise ValueError("resume snapshots require an existing résumé document")
        elif self.resume_document_id is not None or not self.content or not self.content.strip():
            raise ValueError("a non-résumé source requires nonblank content")
        return self


class CareerTargetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_family: StoredLabel
    seniority: StoredLabel
    location: StoredLabel | None = None
    job_description: SourceRef | None = None
    desired_work: list[StoredLabel] = Field(default_factory=list, max_length=20)
    exclusions: list[StoredLabel] = Field(default_factory=list, max_length=20)
