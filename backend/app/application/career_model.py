"""Application boundary for a single untrusted interview proposal."""

from dataclasses import dataclass, field
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.career.common import Identifier
from app.schemas.career.interview import CareerTurnProposal
from app.schemas.career.lineage import CareerRunManifest, StoredRun


class CareerModelRequest(BaseModel):
    """The caller provides the authenticated owner and a filtered context projection."""

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)
    owner_id: Identifier = Field(repr=False)
    context: str = Field(min_length=1, max_length=16000, repr=False)


@dataclass(frozen=True)
class CareerModelResult:
    run: StoredRun
    proposal: CareerTurnProposal | None = field(default=None, repr=False)
    retryable: bool = False


class CareerModel(Protocol):
    @property
    def manifest(self) -> CareerRunManifest: ...

    async def propose(self, request: CareerModelRequest) -> CareerModelResult: ...
