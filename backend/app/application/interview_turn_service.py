"""Admit a private interview turn and commit its application-owned result."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from hashlib import sha256
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import func, select

from app.application.career_encryption import career_cipher, open_private_text
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
from app.schemas.career.interview_persistence import (
    MessageInput, MessageView, SessionView, TurnInput, TurnInterrupted, TurnPending, TurnReplayed,
)
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
    model: CareerModel | None = field(default=None, repr=False)


class InterviewTurnService(InterviewService):
    def begin(
        self, session_id: str, data: TurnInput, *, create_model: Callable[[], CareerModel | None] | None = None,
    ) -> AdmittedTurn | TurnPending | TurnInterrupted | TurnReplayed:
        self._lock_owner()
        row = self._owned(session_id, lock=True)
        now = self._now()
        if row.retention_expires_at is not None and row.retention_expires_at <= now:
            raise ResourceNotFoundError("Interview not found")
        previous = self.repo.get_retry(session_id, "user", data.key)
        if previous is not None:
            return self._existing_turn(row, previous, data, now)
        if data.retry or self.repo.get_retry(session_id, "assistant", data.key):
            raise ResourceConflictError("Interview turn cannot be retried")
        if row.status != "active" or row.state_version != data.expected_state_version:
            raise ResourceConflictError("Interview state is no longer current")
        if data.candidate_stage is not None and row.chapter != INTRODUCTION:
            raise InvalidOperationError("Career stage is confirmed during the introduction")

        self._check_admission(now)
        model = create_model() if create_model is not None else None
        expired = self.repo.messages(row.id).where(
            Message.turn_admitted_version.is_not(None), Message.processing_status == "pending",
            Message.turn_lease_expires_at <= now,
        )
        for orphan in self.db.scalars(expired):
            self._settle_interruption(row, orphan)
        if row.prompt_version == "unassigned":
            row.prompt_version = "2"
            row.turns_remaining = SESSION_TURNS
            row.tokens_remaining = SESSION_TOKENS
        if row.turns_remaining == 0 or row.tokens_remaining == 0:
            raise ResourceConflictError("Interview budget is exhausted")

        message = self._new_message(row, data, role="user", now=now)
        message.turn_lease_expires_at = now + TURN_LEASE
        message.turn_admitted_version = row.state_version
        message.turn_candidate_stage = data.candidate_stage
        attempts = min(ATTEMPTS, row.tokens_remaining // ATTEMPT_TOKENS) if model is not None else 0
        message.turn_tokens_reserved = attempts * ATTEMPT_TOKENS
        row.turns_remaining -= 1
        row.tokens_remaining -= message.turn_tokens_reserved
        admitted = self._admitted(row, message, data, reserved=message.turn_tokens_reserved, model=model)
        self.db.commit()
        return admitted

    def _existing_turn(
        self, row: Interview, previous: Message, data: TurnInput, now: datetime,
    ) -> TurnPending | TurnInterrupted | TurnReplayed:
        cipher = career_cipher()
        if (previous.turn_lease_expires_at is None or previous.turn_candidate_stage != data.candidate_stage
                or open_private_text(cipher, previous.content_ciphertext) != data.content):
            raise ResourceConflictError("Interview turn key was reused with a different request")

        if previous.processing_status == "complete":
            reply = self.repo.get_retry(row.id, "assistant", data.key)
            if reply is None or reply.processing_status != "complete":
                raise ResourceConflictError("Interview turn has no saved reply")
            result = TurnReplayed(message=_message_view(reply, open_private_text(cipher, reply.content_ciphertext)),
                                  state=_state(row), recovered=False)
        elif previous.processing_status == "pending" and previous.turn_lease_expires_at > now:
            result = TurnPending(key=previous.key, lease_expires_at=previous.turn_lease_expires_at)
        else:
            self._settle_interruption(row, previous)
            can_retry = (row.status == "active" and row.state_version == previous.turn_admitted_version
                         and row.message_count == previous.position)
            if not data.retry:
                result = TurnInterrupted(key=previous.key, state_version=row.state_version, can_retry=can_retry)
            else:
                if not can_retry or data.expected_state_version != row.state_version:
                    self.db.commit()
                    raise ResourceConflictError("Interview turn state is no longer current")
                admitted = self._admitted(row, previous, data, reserved=0)
                state, planning = _plan_admitted(admitted)
                outcome = CareerTurnOutcome(plan_next_turn(state, planning))
                reply, state = self._finish(row, previous, admitted, outcome, now, refund=0)
                result = TurnReplayed(message=reply, state=state, recovered=True)
        self.db.commit()
        return result

    def _admitted(
        self, row: Interview, message: Message, data: TurnInput, *, reserved: int, model: CareerModel | None = None,
    ) -> AdmittedTurn:
        state = _state(row)
        planning_state = self._confirm_stage(state, data)
        asked_slots = self.repo.messages(row.id).with_only_columns(Message.turn_slot).where(
            Message.turn_slot.is_not(None),
        ).distinct()
        asked = frozenset(self.db.scalars(asked_slots))
        return AdmittedTurn(state, _message_view(message, data.content), message.turn_lease_expires_at,
                            planning_state, asked, reserved, model)

    def validate_admission(self, turn: AdmittedTurn) -> datetime:
        self._lock_owner()
        _, _, now = self._pending(turn)
        self.db.commit()
        return now

    def record_dispatch(self, turn: AdmittedTurn) -> None:
        self._lock_owner()
        _, pending, _ = self._pending(turn)
        if pending.turn_tokens_dispatched + ATTEMPT_TOKENS > pending.turn_tokens_reserved:
            raise ResourceConflictError("Interview token reservation was exceeded")
        # A crash after this commit cannot establish whether the provider received the call.
        pending.turn_tokens_dispatched += ATTEMPT_TOKENS
        self.db.commit()

    def complete(self, turn: AdmittedTurn, outcome: CareerTurnOutcome) -> tuple[MessageView, SessionView]:
        self._lock_owner()
        row, pending, now = self._pending(turn)
        if not 0 <= outcome.tokens_reserved <= pending.turn_tokens_dispatched <= pending.turn_tokens_reserved:
            raise ResourceConflictError("Interview token reservation was exceeded")
        refund = pending.turn_tokens_reserved - outcome.tokens_reserved
        result = self._finish(row, pending, turn, outcome, now, refund=refund)
        self.db.commit()
        return result

    def _finish(
        self, row: Interview, pending: Message, turn: AdmittedTurn, outcome: CareerTurnOutcome,
        now: datetime, *, refund: int,
    ) -> tuple[MessageView, SessionView]:
        decision = outcome.decision
        content = decision.question or _STATUS_MESSAGES.get(decision.action)
        if content is None:
            raise ResourceConflictError("Interview cannot produce a current result")
        row.candidate_stage = turn.planning_state.candidate_stage
        row.chapter = decision.next_chapter or turn.planning_state.chapter
        row.tokens_remaining += refund
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
        return _message_view(message, content), _state(row)

    def interrupt(self, turn: AdmittedTurn) -> None:
        self.db.rollback()
        self._lock_owner()
        row = self.repo.get(turn.state.session_id, lock=True)
        if row is None:
            self.db.rollback()
            return
        pending = self.repo.get_message_at(turn.state.session_id, turn.message.position)
        if (pending is not None and pending.key == turn.message.key
                and pending.turn_lease_expires_at == turn.lease_expires_at):
            self._settle_interruption(row, pending)
        self.db.commit()

    @staticmethod
    def _settle_interruption(row: Interview, message: Message) -> None:
        if message.processing_status == "pending":
            row.tokens_remaining += message.turn_tokens_reserved - message.turn_tokens_dispatched
            message.processing_status = "interrupted"

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


def _plan_admitted(turn: AdmittedTurn, time_budget: int = 1) -> tuple[SessionView, TurnPlanningInput]:
    # Admission has already decremented the turn count. The planner sees capacity for this admitted turn.
    state = turn.planning_state.model_copy(update={
        "turns_remaining": turn.planning_state.turns_remaining + 1,
        "tokens_remaining": turn.planning_state.tokens_remaining + turn.reserved_tokens,
    })
    planning = TurnPlanningInput(
        expected_state_version=state.state_version, coverage=CareerCoverage(schema_version=1,
        session_id=state.session_id, slots=[]), progress={slot: SlotProgress(asked=True) for slot in turn.asked_slots},
        budget=TurnBudget(time_remaining_ms=max(1, time_budget),
                          cost_remaining_microusd=max(1, turn.reserved_tokens // ATTEMPT_TOKENS * ATTEMPT_COST_MICROUSD)),
    )
    return state, planning


async def run_admitted_turn(
    turn: AdmittedTurn, *, now: datetime, before_attempt: Callable[[], Awaitable[None]],
) -> CareerTurnOutcome:
    deadline = min(turn.lease_expires_at, turn.planning_state.retention_expires_at or turn.lease_expires_at)
    time_budget = min(TURN_TIME_MS, max(0, int((deadline - now).total_seconds() * 1000) - 1_000))
    state, planning = _plan_admitted(turn, time_budget)
    model = turn.model
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
    return await execute_career_turn(model, model_state, planning, context, now=now, before_attempt=before_attempt)
