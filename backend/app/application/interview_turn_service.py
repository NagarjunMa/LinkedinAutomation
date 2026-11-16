"""Admit a private interview turn and commit its application-owned result."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from hashlib import sha256
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import func, select

from app.application.career_model import CareerModel
from app.application.career_turn import CareerTurnOutcome, execute_career_turn
from app.application.career_turn_context import CareerTurnContext, TurnMessage
from app.application.errors import (
    ExternalServiceError, InvalidOperationError, ResourceBusyError, ResourceConflictError, ResourceNotFoundError,
)
from app.application.interview_controller import INTRODUCTION, InterviewEvent, transition
from app.application.interview_coverage import SlotProgress, TurnBudget, TurnPlanningInput, plan_next_turn
from app.application.interview_service import InterviewService, _message_view, _state
from app.application.lineage_service import LineageService
from app.db.transactions import is_transactional_read_committed
from app.models.interview import InterviewMessageRow as Message, InterviewSessionRow as Interview
from app.models.user import User
from app.schemas.career.common import SourceRef
from app.schemas.career.interview import CareerCoverage
from app.schemas.career.interview_persistence import MessageInput, MessageView, SessionView, TurnInput
from app.schemas.career.sources import CareerSource

ATTEMPT_TOKENS = 20_000
ATTEMPT_COST_MICROUSD = 60_000
ATTEMPTS = 4  # Initial attempt, two transient retries, and one repair.
TURN_TIME_MS = 35_000
TURN_LEASE = timedelta(seconds=60)
SESSION_TURNS = 40
SESSION_TOKENS = SESSION_TURNS * ATTEMPT_TOKENS
SHORT_LIMIT = 3
DAILY_LIMIT = 8

_STATUS_MESSAGES = {
    "confirm_stage": "Which career stage best describes you?",
    "advance_chapter": "Let's move to the next topic.",
    "coverage_review": "This interview is ready for an evidence review.",
    "pause": "Let's pause this interview here.",
}


@dataclass(frozen=True)
class AdmittedTurn:
    state: SessionView = field(repr=False)
    message: MessageView = field(repr=False)
    lease_expires_at: datetime
    planning_state: SessionView = field(repr=False)
    asked_slots: frozenset[str]
    reserved_tokens: int


class InterviewTurnService(InterviewService):
    def begin(self, session_id: str, data: TurnInput, *, model_enabled: bool) -> AdmittedTurn:
        self._lock_owner()
        row = self._owned(session_id, lock=True)
        if row.status != "active" or row.state_version != data.expected_state_version:
            raise ResourceConflictError("Interview state is no longer current")
        if self.repo.get_retry(session_id, "user", data.key) or self.repo.get_retry(session_id, "assistant", data.key):
            raise ResourceConflictError("Interview turn key has already been used")
        if data.candidate_stage is not None and row.chapter != INTRODUCTION:
            raise InvalidOperationError("Career stage is confirmed during the introduction")

        now = self._now()
        self._check_admission(now)
        if row.retention_expires_at is not None and row.retention_expires_at <= now:
            raise ResourceNotFoundError("Interview not found")
        if row.prompt_version == "unassigned":
            row.prompt_version = "2"
            row.turns_remaining = SESSION_TURNS
            row.tokens_remaining = SESSION_TOKENS
        if row.turns_remaining == 0 or row.tokens_remaining == 0:
            raise ResourceConflictError("Interview budget is exhausted")

        message = self._new_message(row, data, role="user", now=now)
        message.turn_lease_expires_at = now + TURN_LEASE
        row.turns_remaining -= 1
        planning_state = self._confirm_stage(_state(row), data)
        funded_attempts = min(ATTEMPTS, row.tokens_remaining // ATTEMPT_TOKENS) if model_enabled else 0
        reserved = funded_attempts * ATTEMPT_TOKENS
        row.tokens_remaining -= reserved
        asked_slots = self.repo.messages(session_id).with_only_columns(Message.turn_slot).where(
            Message.turn_slot.is_not(None),
        ).distinct()
        asked = frozenset(self.db.scalars(asked_slots))
        admitted = AdmittedTurn(_state(row), _message_view(message, data.content), message.turn_lease_expires_at,
                                planning_state, asked, reserved)
        self.db.commit()
        return admitted

    def validate_admission(self, turn: AdmittedTurn) -> datetime:
        self._lock_owner()
        _, _, now = self._pending(turn)
        self.db.commit()
        return now

    def complete(self, turn: AdmittedTurn, outcome: CareerTurnOutcome) -> tuple[MessageView, SessionView]:
        self._lock_owner()
        row, pending, now = self._pending(turn)
        if not 0 <= outcome.tokens_reserved <= turn.reserved_tokens:
            raise ResourceConflictError("Interview token reservation was exceeded")
        decision = outcome.decision
        content = decision.question or _STATUS_MESSAGES.get(decision.action)
        if content is None:
            raise ResourceConflictError("Interview cannot produce a current result")
        row.candidate_stage = turn.planning_state.candidate_stage
        row.chapter = decision.next_chapter or turn.planning_state.chapter
        row.tokens_remaining += turn.reserved_tokens - outcome.tokens_reserved
        if decision.action == "pause":
            row.status = "paused"
        pending.processing_status = "complete"
        message = self._new_message(row, MessageInput(key=turn.message.key, content=content),
                                    role="assistant", now=now)
        message.turn_slot = decision.slot
        lineage = LineageService(self.db, self.owner)
        start = f"{turn.state.status}:{turn.state.chapter}:v{turn.state.state_version}"
        end = f"{row.status}:{row.chapter}:v{row.state_version}"
        for run in outcome.runs:
            if run.metadata.session_id != row.id:
                raise ResourceConflictError("Interview run is no longer current")
            metadata = run.metadata.model_copy(update={"start_state": start, "end_state": end})
            lineage.stage_run(run.model_copy(update={"metadata": metadata}))
        result = _message_view(message, content), _state(row)
        self.db.commit()
        return result

    def interrupt(self, turn: AdmittedTurn) -> None:
        # Keep the admitted cost and token reservation when provider usage is unknown.
        self.db.rollback()
        self._lock_owner()
        if self.repo.get(turn.state.session_id, lock=True) is None:
            self.db.rollback()
            return
        pending = self.repo.get_message_at(turn.state.session_id, turn.message.position)
        if (pending is not None and pending.processing_status == "pending" and pending.key == turn.message.key
                and pending.turn_lease_expires_at == turn.lease_expires_at):
            pending.processing_status = "interrupted"
        self.db.commit()

    def _pending(self, turn: AdmittedTurn) -> tuple[Interview, Message, datetime]:
        state = turn.state
        row = self._owned(state.session_id, lock=True)
        pending = self.repo.get_message_at(state.session_id, turn.message.position)
        now = self._now()
        if row.retention_expires_at is not None and row.retention_expires_at <= now:
            raise ResourceNotFoundError("Interview not found")
        if (row.state_version != state.state_version or row.status != "active"
                or pending is None or pending.processing_status != "pending" or pending.key != turn.message.key
                or pending.turn_lease_expires_at != turn.lease_expires_at or turn.lease_expires_at <= now):
            raise ResourceConflictError("Interview turn is no longer current")
        return row, pending, now

    def _lock_owner(self) -> None:
        if self.db.get_bind().dialect.name != "postgresql" or not is_transactional_read_committed(self.db.connection()):
            raise ExternalServiceError("Career turns require transactional PostgreSQL READ COMMITTED")
        # FOR NO KEY UPDATE serializes admissions while keeping the owner-before-session lock order.
        owner = select(User.user_id).where(User.user_id == self.owner).with_for_update(key_share=True)
        if self.db.scalar(owner) is None:
            raise ResourceNotFoundError("Interview not found")

    def _now(self) -> datetime:
        return self.db.scalar(select(func.clock_timestamp()))

    def _check_admission(self, now: datetime) -> None:
        daily, minute, busy = self.db.execute(select(
            func.count(),
            func.count().filter(Message.created_at > now - timedelta(minutes=1)),
            func.count().filter(Message.processing_status == "pending", Message.turn_lease_expires_at > now),
        ).where(Message.user_id == self.owner, Message.turn_lease_expires_at.is_not(None),
                Message.created_at > now - timedelta(days=1))).one()
        # Every admitted turn counts at its full possible cost, even after a disconnect or a missing usage report.
        if daily >= DAILY_LIMIT or minute >= SHORT_LIMIT or busy:
            raise ResourceBusyError("Interview turn limit reached")

    @staticmethod
    def _confirm_stage(state: SessionView, data: TurnInput) -> SessionView:
        stage = data.candidate_stage or state.candidate_stage
        if state.chapter != INTRODUCTION or stage is None:
            return state
        confirmed = transition(state, InterviewEvent(session_id=state.session_id,
                               expected_state_version=state.state_version, kind="confirm_stage", candidate_stage=stage))
        return confirmed.model_copy(update={"state_version": state.state_version})


async def run_admitted_turn(
    turn: AdmittedTurn, model: CareerModel | None, *, now: datetime, before_retry: Callable[[], Awaitable[None]],
) -> CareerTurnOutcome:
    state = turn.planning_state
    # Admission has already decremented the turn count. The planner sees capacity for this admitted turn.
    state = state.model_copy(update={"turns_remaining": state.turns_remaining + 1})
    deadline = min(turn.lease_expires_at, state.retention_expires_at or turn.lease_expires_at)
    time_budget = min(TURN_TIME_MS, max(0, int((deadline - now).total_seconds() * 1000) - 1_000))
    planning = TurnPlanningInput(
        expected_state_version=state.state_version, coverage=CareerCoverage(schema_version=1,
        session_id=state.session_id, slots=[]), progress={slot: SlotProgress(asked=True) for slot in turn.asked_slots},
        budget=TurnBudget(time_remaining_ms=max(1, time_budget),
                          cost_remaining_microusd=max(1, turn.reserved_tokens // ATTEMPT_TOKENS * ATTEMPT_COST_MICROUSD)),
    )
    if model is None or turn.reserved_tokens == 0 or time_budget < model.manifest.timeout_ms:
        return CareerTurnOutcome(plan_next_turn(state, planning))
    planning = planning.model_copy(update={"budget": planning.budget.model_copy(update={
        "reserved_tokens": ATTEMPT_TOKENS, "reserved_cost_microusd": ATTEMPT_COST_MICROUSD,
    })})
    model_state = state.model_copy(update={"tokens_remaining": turn.reserved_tokens})
    # Scope the first projection to the explicitly submitted message. Existing sources do not have
    # a durable transcript-to-source privacy binding and cannot attest new exact evidence excerpts here.
    message = turn.message
    source = CareerSource(
        schema_version=1, owner_id=state.owner_id, kind="interview_message",
        source=SourceRef(source_id=str(uuid5(NAMESPACE_URL, f"prismpro:interview:{state.session_id}:{message.position}")),
                         source_version=1),
        content_sha256=sha256(message.content.encode()).hexdigest(),
        created_at=message.created_at, retention_expires_at=state.retention_expires_at,
    )
    context = CareerTurnContext(
        owner_id=state.owner_id, session_id=state.session_id, state_version=state.state_version,
        messages=(TurnMessage(owner_id=state.owner_id, session_id=state.session_id, source=source,
                   current_source_version=1, view=message),),
    )
    return await execute_career_turn(model, model_state, planning, context, now=now, before_retry=before_retry)
