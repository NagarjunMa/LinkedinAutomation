"""Select the next career interview question from application-owned evidence coverage."""

from dataclasses import dataclass
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.application.errors import InvalidOperationError, ResourceConflictError
from app.application.interview_controller import FINAL_CHAPTER, INTRODUCTION, InterviewEvent, interview_chapters, transition
from app.schemas.career.common import Count, Identifier, Revision
from app.schemas.career.evidence import EvidenceRevisionRef
from app.schemas.career.interview import CareerCoverage, CareerSessionState, EvidenceSlotCoverage

TurnAction = Literal[
    "inactive", "pause", "confirm_stage", "advance_chapter", "coverage_review",
    "probe", "clarify", "confirm_evidence", "resolve_contradiction",
]
BudgetLimit = Literal["turns", "tokens", "time", "cost"]

# Order breaks priority ties. These topics also provide the fallback question text.
_CHAPTER_SLOTS = {
    "academic_foundation": (("course_project", "a course project"), ("academic_depth", "how you applied what you learned")),
    "work_project_timeline": (("role_scope", "the scope of your role"), ("project_context", "the problem your project addressed")),
    "project_ownership": (("ownership", "your personal contribution"), ("constraints", "a constraint that affected your contribution")),
    "technical_depth": (("technical_decision", "a technical decision you made"), ("validation", "how you checked that your work solved the problem")),
    "outcomes": (("measurement", "how you measured the impact"), ("outcome", "the result you observed")),
    "constraints_recovery": (("recovery", "how you handled a setback"), ("tradeoff", "a trade-off you had to make")),
    "collaboration_leadership": (("collaboration", "how you worked with teammates"), ("cross_team_alignment", "how you aligned people across teams")),
    "learning": (("learning_gap", "a requirement you still need to learn"), ("transferable_skill", "a skill you can apply in the target role")),
    "communication_gaps": (("communication", "a useful example missing from your materials"), ("positioning", "how your experience fits the target role")),
}
_KNOWN_SLOTS = frozenset(slot for slots in _CHAPTER_SLOTS.values() for slot, _ in slots)
_HIDDEN_EVIDENCE = frozenset({"private", "unavailable"})
_PROJECT_PRIORITIES = frozenset({"project_context", "validation", "outcome"})
_STAGE_PRIORITIES = {
    "student": _PROJECT_PRIORITIES,
    "new_graduate": _PROJECT_PRIORITIES,
    "early_career": frozenset({"validation"}),
    "manager_or_leader": frozenset({"cross_team_alignment", "positioning"}),
    "senior_staff_or_founder": frozenset({"cross_team_alignment", "tradeoff"}),
    "career_switcher": frozenset({"transferable_skill", "positioning"}),
    "returning_professional": frozenset({"transferable_skill"}),
}


class SlotProgress(BaseModel):
    """Progress recorded by the application after questions and candidate replies."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    asked: bool = False
    vague_answer: bool = False
    vague_probes: Annotated[int, Field(ge=0, le=2)] = 0
    confirmation_requested: bool = False

    @model_validator(mode="after")
    def validate_attempts(self) -> Self:
        if not self.asked and (self.vague_answer or self.vague_probes):
            raise ValueError("Vague replies and probes require an earlier question")
        return self


class TurnBudget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    time_remaining_ms: Count
    cost_remaining_microusd: Count
    reserved_time_ms: Count = 0
    reserved_cost_microusd: Count = 0
    reserved_tokens: Count = 0


class TurnPlanningInput(BaseModel):
    """A same-version coverage snapshot assembled from owned evidence by the application."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected_state_version: Revision
    coverage: CareerCoverage
    budget: TurnBudget
    progress: dict[Identifier, SlotProgress] = Field(default_factory=dict, max_length=len(_KNOWN_SLOTS))
    # The caller attests that the current owned revision has both visible source sides.
    supported_contradictions: dict[Identifier, EvidenceRevisionRef] = Field(
        default_factory=dict, max_length=len(_KNOWN_SLOTS),
    )
    # Only prior requests for revisions in the current snapshot are needed.
    requested_contradictions: tuple[EvidenceRevisionRef, ...] = Field(default=(), max_length=len(_KNOWN_SLOTS))


@dataclass(frozen=True)
class ChapterReferences:
    chapter: str
    evidence: tuple[EvidenceRevisionRef, ...]


@dataclass(frozen=True)
class TurnDecision:
    action: TurnAction
    slot: str | None = None
    question: str | None = None
    next_chapter: str | None = None
    stop_reason: BudgetLimit | None = None
    completed_chapters: tuple[ChapterReferences, ...] = ()
    contradiction: EvidenceRevisionRef | None = None


def plan_next_turn(state: CareerSessionState, data: TurnPlanningInput) -> TurnDecision:
    """Choose a plan. The application owns progress writes and budget reservations."""
    if not isinstance(data, TurnPlanningInput) or data.coverage.session_id != state.session_id:
        raise InvalidOperationError("Expected application coverage for this interview session")
    if data.expected_state_version != state.state_version:
        raise ResourceConflictError("Interview coverage no longer matches the state version")
    coverage = {item.slot: item for item in data.coverage.slots}
    if set(coverage).union(data.progress, data.supported_contradictions) - _KNOWN_SLOTS:
        raise InvalidOperationError("Interview coverage contains an unknown evidence slot")
    chapters = interview_chapters(state)
    if state.status != "active":
        return TurnDecision("inactive")
    reason = _stopping_limit(state, data.budget)
    if reason is not None:
        return TurnDecision("pause", stop_reason=reason)
    if state.chapter == INTRODUCTION:
        return TurnDecision("confirm_stage")

    ineligible = _evidence_ids(coverage, _HIDDEN_EVIDENCE) | _mixed_revisions(coverage)
    excluded = ineligible | _evidence_ids(coverage, {"contradicted"})
    summaries = _completed_chapters(chapters[:chapters.index(state.chapter)], coverage, excluded)
    for chapter in chapters:
        for name, topic in _CHAPTER_SLOTS.get(chapter, ()):
            ref = data.supported_contradictions.get(name)
            item = coverage.get(name)
            if (ref is not None and item is not None and item.status == "contradicted"
                    and ref.evidence_id not in ineligible and ref in item.evidence_revisions
                    and ref not in data.requested_contradictions):
                return TurnDecision(
                    "resolve_contradiction", name, f"Which account of {topic} can you support?",
                    completed_chapters=summaries, contradiction=ref,
                )
    if state.chapter == FINAL_CHAPTER:
        return TurnDecision("coverage_review", completed_chapters=summaries)

    preferred = _STAGE_PRIORITIES.get(state.candidate_stage, ())
    slots = sorted(_CHAPTER_SLOTS[state.chapter], key=lambda slot: slot[0] not in preferred)
    for name, topic in slots:
        item = coverage.get(name)
        status = item.status if item is not None else "missing"
        if item is not None and status == "proposed":
            if not item.evidence_revisions:
                status = "missing"
            elif all(ref.evidence_id in excluded for ref in item.evidence_revisions):
                continue
        progress = data.progress.get(name, _UNASKED)
        question = _question(status, progress, topic)
        if question is not None:
            action, prompt = question
            return TurnDecision(action, name, prompt, completed_chapters=summaries)

    next_state = transition(state, InterviewEvent(
        kind="chapter_reviewed", session_id=state.session_id, expected_state_version=state.state_version,
    ))
    return TurnDecision("advance_chapter", next_chapter=next_state.chapter, completed_chapters=summaries)


_UNASKED = SlotProgress()


def _stopping_limit(state: CareerSessionState, budget: TurnBudget) -> BudgetLimit | None:
    if state.turns_remaining == 0:
        return "turns"
    if state.tokens_remaining < max(1, budget.reserved_tokens):
        return "tokens"
    if budget.time_remaining_ms < max(1, budget.reserved_time_ms):
        return "time"
    if budget.cost_remaining_microusd < max(1, budget.reserved_cost_microusd):
        return "cost"
    return None


def _question(status: str, progress: SlotProgress, topic: str) -> tuple[TurnAction, str] | None:
    if status in ("missing", "proposed") and progress.vague_answer:
        if progress.vague_probes == 0:
            return "clarify", f"What did you personally do in that example of {topic}?"
        if progress.vague_probes == 1:
            return "clarify", f"What concrete detail can you verify about {topic}?"
    if status == "proposed" and not progress.confirmation_requested:
        return "confirm_evidence", f"What can you confirm about {topic}?"
    if status == "missing" and not progress.asked:
        return "probe", f"Can you share a specific example of {topic}?"
    return None


def _evidence_ids(coverage: dict[str, EvidenceSlotCoverage], statuses: set[str] | frozenset[str]) -> set[str]:
    return {ref.evidence_id for item in coverage.values() if item.status in statuses
            for ref in item.evidence_revisions}


def _mixed_revisions(coverage: dict[str, EvidenceSlotCoverage]) -> set[str]:
    revisions: dict[str, int] = {}
    mixed = set()
    for item in coverage.values():
        for ref in item.evidence_revisions:
            if revisions.setdefault(ref.evidence_id, ref.revision) != ref.revision:
                mixed.add(ref.evidence_id)
    return mixed


def _completed_chapters(
    chapters: tuple[str, ...], coverage: dict[str, EvidenceSlotCoverage], excluded: set[str],
) -> tuple[ChapterReferences, ...]:
    summaries = []
    for chapter in chapters:
        keys = {(ref.evidence_id, ref.revision) for name, _ in _CHAPTER_SLOTS.get(chapter, ())
                if name in coverage and coverage[name].status == "confirmed"
                for ref in coverage[name].evidence_revisions if ref.evidence_id not in excluded}
        if keys:
            references = tuple(EvidenceRevisionRef(evidence_id=id_, revision=revision) for id_, revision in sorted(keys))
            summaries.append(ChapterReferences(chapter, references))
    return tuple(summaries)
