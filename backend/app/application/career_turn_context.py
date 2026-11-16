"""Build and validate the application-owned view of an interview turn."""

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.application.career_model import MAX_CAREER_CONTEXT_CHARS
from app.application.errors import InvalidOperationError, ResourceConflictError
from app.application.interview_coverage import TurnDecision
from app.schemas.career.common import Count, Identifier, Label, Ownership, Revision
from app.schemas.career.evidence import EvidenceCategory, EvidenceProposal, EvidenceRevisionRef, EvidenceSourceLink
from app.schemas.career.interview import CareerCoverage, CareerSessionState, CareerTurnProposal, ContradictionCandidate
from app.schemas.career.interview_persistence import MessageView
from app.schemas.career.lineage import TurnReason
from app.schemas.career.sources import CareerSource, CareerTarget


class TurnExcerpt(BaseModel):
    """A source span projected by the application. A category attests an extractable fact."""

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)
    source: CareerSource = Field(repr=False)
    current_source_version: Revision
    slot: Identifier
    start: Count
    text: Annotated[str, Field(min_length=1, max_length=800)] = Field(repr=False)
    visibility: Literal["visible", "private", "unavailable"] = "visible"
    lifecycle: Literal["candidate", "confirmed", "proposed", "contradicted", "rejected"] = "candidate"
    category: EvidenceCategory | None = None
    qualifiers: tuple[Label, ...] = Field(default=(), max_length=20, repr=False)
    ownership: Ownership = "unknown"
    evidence_revision: EvidenceRevisionRef | None = None
    relationship: Literal["supports", "contradicts"] = "supports"

    @property
    def locator(self) -> str:
        return f"chars:{self.start}-{self.start + len(self.text)}"

    @property
    def key(self) -> tuple[str, int, str]:
        return self.source.source.source_id, self.source.source.source_version, self.locator

    def citation(self) -> dict:
        return {**self.source.source.model_dump(), "locator": self.locator,
                "relationship": self.relationship, "extraction": "model", "excerpt": self.text}


class TurnMessage(BaseModel):
    """Recent transcript projected by the application after the same eligibility checks."""

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)
    owner_id: Identifier = Field(repr=False)
    session_id: Identifier
    view: MessageView = Field(repr=False)
    source: CareerSource = Field(repr=False)
    current_source_version: Revision
    visibility: Literal["visible", "private", "unavailable"] = "visible"


class CareerTurnContext(BaseModel):
    """Bounded context projected for an authenticated owner and exact session version."""

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)
    owner_id: Identifier = Field(repr=False)
    session_id: Identifier
    state_version: Revision
    target: CareerTarget | None = Field(default=None, repr=False)
    excerpts: tuple[TurnExcerpt, ...] = Field(default=(), max_length=24, repr=False)
    messages: tuple[TurnMessage, ...] = Field(default=(), max_length=10, repr=False)

    def check_session(self, state: CareerSessionState) -> None:
        if (self.owner_id, self.session_id) != (state.owner_id, state.session_id):
            raise InvalidOperationError("Career turn context belongs to another owner or session")
        if self.state_version != state.state_version:
            raise ResourceConflictError("Career turn context is stale")
        if self.target is not None and (
            self.target.owner_id != state.owner_id or self.target.target_id != state.target_id
            or self.target.status != "active"
        ):
            raise InvalidOperationError("Career turn target is unavailable")

_QUESTION_POLICY = {
    "probe": ("probe", "continue"),
    "clarify": ("clarify", "clarify"),
    "confirm_evidence": ("review", "continue"),
    "resolve_contradiction": ("resolve_contradiction", "clarify"),
}


@dataclass(frozen=True)
class TurnViolation:
    code: TurnReason
    path: str


def _encode(body: dict) -> str:
    return json.dumps(body, ensure_ascii=False, separators=(",", ":"))


@dataclass(frozen=True)
class PreparedTurn:
    request_body: dict = field(repr=False)
    excerpts: dict[tuple[str, int, str], TurnExcerpt] = field(repr=False)
    contradiction: ContradictionCandidate | None = field(repr=False)
    expires_at: datetime | None
    question_repeated: bool

    def encode(self, violation: TurnViolation | None = None) -> str:
        if violation is None:
            return _encode(self.request_body)
        return _encode({**self.request_body, "violations": [{"code": violation.code, "path": violation.path}]})


def _available(source: CareerSource, current_version: int, owner: str, now: datetime) -> bool:
    return (source.owner_id == owner and source.kind != "job_description"
            and source.source.source_version == current_version
            and (source.retention_expires_at is None or source.retention_expires_at > now))


def prepare_turn(
    state: CareerSessionState, decision: TurnDecision, data: CareerTurnContext, coverage: CareerCoverage, now: datetime,
) -> PreparedTurn:
    intent, action = _QUESTION_POLICY[decision.action]
    body = {
        "chapter": state.chapter, "stage": state.candidate_stage,
        "plan": {"question": decision.question, "question_intent": intent,
                 "target_evidence_slot": decision.slot, "recommended_action": action},
        "sources": [], "recent_messages": [], "prior_evidence": [],
    }
    withdrawn = set()
    withdrawn_evidence = {ref.evidence_id for slot in coverage.slots if slot.status in ("private", "unavailable")
                          for ref in slot.evidence_revisions}
    contradicted_evidence = {ref.evidence_id for slot in coverage.slots if slot.status == "contradicted"
                             for ref in slot.evidence_revisions}
    current_versions: dict[str, int] = {}
    evidence_versions: dict[str, int] = {}
    evidence_expiries: dict[str, datetime] = {}
    for slot in coverage.slots:
        for ref in slot.evidence_revisions:
            if evidence_versions.setdefault(ref.evidence_id, ref.revision) != ref.revision:
                withdrawn_evidence.add(ref.evidence_id)
    for item in data.excerpts:
        if item.source.owner_id != state.owner_id:
            continue
        source_id = item.source.source.source_id
        current_version = current_versions.setdefault(source_id, item.current_source_version)
        hidden = item.visibility != "visible" or item.lifecycle == "rejected"
        if hidden or current_version != item.current_source_version:
            withdrawn.add(source_id)
        ref = item.evidence_revision
        if ref is not None:
            current_revision = evidence_versions.setdefault(ref.evidence_id, ref.revision)
            if (hidden or current_revision != ref.revision
                    or not _available(item.source, item.current_source_version, state.owner_id, now)):
                withdrawn_evidence.add(ref.evidence_id)
            expiry = item.source.retention_expires_at
            if expiry is not None:
                evidence_expiries[ref.evidence_id] = min(expiry, evidence_expiries.get(ref.evidence_id, expiry))
    for message in data.messages:
        if (message.owner_id, message.session_id) != (state.owner_id, state.session_id):
            continue
        source_id = message.source.source.source_id
        current_version = current_versions.setdefault(source_id, message.current_source_version)
        if (message.visibility != "visible" or current_version != message.current_source_version
                or not _available(message.source, message.current_source_version, state.owner_id, now)):
            withdrawn.add(source_id)
    for item in data.excerpts:
        ref = item.evidence_revision
        if item.source.owner_id == state.owner_id and ref is not None and item.key[0] in withdrawn:
            withdrawn_evidence.add(ref.evidence_id)
    withdrawn_sources = withdrawn | {
        item.key[0] for item in data.excerpts if item.source.owner_id == state.owner_id
        and item.evidence_revision is not None and item.evidence_revision.evidence_id in withdrawn_evidence
    }
    withdrawn_transcripts = withdrawn_sources | {
        item.key[0] for item in data.excerpts if item.source.owner_id == state.owner_id
        and item.evidence_revision is not None and item.evidence_revision.evidence_id in contradicted_evidence
    }
    withdrawn_text = _withdrawn_fragments(data, withdrawn_sources, now)
    withdrawn_transcript_text = _withdrawn_fragments(data, withdrawn_transcripts, now)
    if data.target is not None and not _contains_withdrawn_text(
        withdrawn_text, data.target.role_family, data.target.seniority,
    ):
        body["target"] = {"role_family": data.target.role_family, "seniority": data.target.seniority}
    sources: dict[tuple[str, int, str], TurnExcerpt] = {}
    visible_refs = set()
    expiries = []
    for item in data.excerpts:
        expiry = item.source.retention_expires_at
        ref = item.evidence_revision
        if (item.key[0] in withdrawn
                or not _available(item.source, item.current_source_version, state.owner_id, now)
                or item.text != item.text.strip()
                or _contains_withdrawn_text(withdrawn_text, item.text, *item.qualifiers)):
            continue
        if ref is not None and ref.evidence_id in withdrawn_evidence:
            continue
        if ref is not None and ref.evidence_id in contradicted_evidence and item.lifecycle != "contradicted":
            continue
        if ref is not None and item.lifecycle == "confirmed":
            visible_refs.add((ref.evidence_id, ref.revision))
        if item.slot != decision.slot:
            continue
        if item.lifecycle == "contradicted":
            if decision.contradiction is None or item.evidence_revision != decision.contradiction:
                continue
        elif item.relationship != "supports" or decision.contradiction is not None:
            continue
        if item.key in sources:
            if item != sources[item.key]:
                raise InvalidOperationError("Conflicting Career source projections")
            continue
        projected = {**item.citation(), "lifecycle": item.lifecycle}
        if item.category is not None and item.lifecycle != "contradicted":
            projected.update(category=item.category, qualifiers=item.qualifiers)
        if _append_bounded(body, "sources", projected):
            sources[item.key] = item.model_copy(deep=True)
            if ref is not None:
                expiry = evidence_expiries.get(ref.evidence_id, expiry)
            if expiry is not None:
                expiries.append(expiry)

    sides = {item.relationship: item for item in reversed(tuple(sources.values()))}
    contradiction = None
    if decision.contradiction is not None and len(sides) == 2:
        contradiction = ContradictionCandidate(supports=sides["supports"].citation(),
                                               contradicts=sides["contradicts"].citation())
    for chapter in decision.completed_chapters:
        for ref in chapter.evidence:
            key = (ref.evidence_id, ref.revision)
            if key in visible_refs and _append_bounded(body, "prior_evidence", {"chapter": chapter.chapter, **ref.model_dump()}):
                expiry = evidence_expiries.get(ref.evidence_id)
                if expiry is not None:
                    expiries.append(expiry)
    repeated = False
    question = " ".join((decision.question or "").casefold().split())
    for item in sorted(data.messages, key=lambda item: item.view.position, reverse=True):
        message = item.view
        if ((item.owner_id, item.session_id) != (state.owner_id, state.session_id)
                or item.source.source.source_id in withdrawn_transcripts or message.processing_status == "interrupted"
                or item.source.kind != "interview_message"
                or _contains_withdrawn_text(withdrawn_transcript_text, message.content)
                or sha256(message.content.encode()).hexdigest() != item.source.content_sha256):
            continue
        if message.role == "assistant" and message.processing_status == "complete":
            repeated = repeated or " ".join(message.content.casefold().split()) == question
        if _append_bounded(body, "recent_messages", {"role": message.role, "content": message.content}):
            if item.source.retention_expires_at is not None:
                expiries.append(item.source.retention_expires_at)
    body["recent_messages"].reverse()
    return PreparedTurn(body, sources, contradiction, min(expiries, default=None), repeated)


def _withdrawn_fragments(data: CareerTurnContext, source_ids: set[str], now: datetime) -> set[str]:
    excerpts = (item.text for item in data.excerpts
                if item.source.owner_id == data.owner_id and (
                    item.key[0] in source_ids or (
                        item.source.kind != "job_description"
                        and not _available(item.source, item.current_source_version, data.owner_id, now)
                    )
                ))
    messages = (item.view.content for item in data.messages
                if (item.owner_id, item.session_id) == (data.owner_id, data.session_id)
                and item.source.source.source_id in source_ids)
    return {fragment.strip() for fragment in (*excerpts, *messages) if fragment.strip()}


def _contains_withdrawn_text(fragments: set[str], *fields: str) -> bool:
    return any(fragment in value for value in fields for fragment in fragments)


def _append_bounded(body: dict, field_name: str, value: dict) -> bool:
    body[field_name].append(value)
    if len(_encode(body).encode("utf-8")) <= MAX_CAREER_CONTEXT_CHARS - 512:
        return True
    body[field_name].pop()
    return False


def _source_for_link(link: EvidenceSourceLink, turn: PreparedTurn) -> TurnExcerpt | None:
    item = turn.excerpts.get((link.source_id, link.source_version, link.locator))
    if item is None or item.relationship != link.relationship or link.extraction != "model":
        return None
    if link.excerpt is not None:
        return item if link.excerpt == item.text else None
    return item if sha256(item.text.encode()).hexdigest() == link.excerpt_sha256 else None


def validate_proposal(proposal: object, decision: TurnDecision, turn: PreparedTurn) -> tuple[
    tuple[EvidenceProposal, ...], TurnViolation | None,
]:
    try:
        raw = proposal.model_dump() if isinstance(proposal, CareerTurnProposal) else proposal
        candidate = CareerTurnProposal.model_validate(raw)
    except (ValidationError, RecursionError):
        return (), TurnViolation("schema_invalid", "proposal")
    if candidate.target_evidence_slot != decision.slot:
        return (), TurnViolation("slot_mismatch", "target_evidence_slot")
    intent, action = _QUESTION_POLICY[decision.action]
    if candidate.recommended_action != action:
        return (), TurnViolation("action_not_allowed", "recommended_action")
    if candidate.question != decision.question or candidate.question_intent != intent:
        return (), TurnViolation("question_out_of_scope", "question")

    if len(candidate.contradiction_candidates) > int(turn.contradiction is not None):
        return (), TurnViolation("contradiction_not_approved", "contradiction_candidates")
    for pair in candidate.contradiction_candidates:
        if not _source_for_link(pair.supports, turn) or not _source_for_link(pair.contradicts, turn):
            return (), TurnViolation("contradiction_not_approved", "contradiction_candidates")

    allowed = []
    seen = set()
    for index, proposal in enumerate(candidate.evidence_proposals):
        path = f"evidence_proposals.{index}"
        citations = [_source_for_link(link, turn) for link in proposal.sources]
        if any(item is None for item in citations):
            return (), TurnViolation("citation_not_approved", f"{path}.sources")
        if any(item.lifecycle == "contradicted" or item.category != proposal.category
               or item.text != proposal.claim for item in citations):
            return (), TurnViolation("claim_not_approved", f"{path}.claim")
        if any(tuple(proposal.qualifiers) != item.qualifiers for item in citations):
            return (), TurnViolation("qualifier_not_approved", f"{path}.qualifiers")
        owners = {item.ownership for item in citations}
        keys = {item.key for item in citations}
        if len(owners) != 1 or len(keys) != len(citations) or seen.intersection(keys):
            return (), TurnViolation("citation_not_approved", f"{path}.sources")
        seen.update(keys)
        allowed.append(EvidenceProposal(claim=citations[0].text, category=citations[0].category,
                                        qualifiers=list(citations[0].qualifiers), ownership=owners.pop(),
                                        sources=[item.citation() for item in citations]))
    return tuple(allowed), None
