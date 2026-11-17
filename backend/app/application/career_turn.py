"""Bounded execution of a single Career Interview turn."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
from typing import Literal

from app.application.career_model import CareerModel, CareerModelRequest
from app.application.career_turn_context import CareerTurnContext, TurnViolation, prepare_turn, validate_proposal
from app.application.interview_coverage import TurnDecision, TurnPlanningInput, plan_next_turn
from app.schemas.career.evidence import EvidenceProposal
from app.schemas.career.interview import CareerSessionState, ContradictionCandidate
from app.schemas.career.interview_persistence import SessionView
from app.schemas.career.lineage import RunFailure, StoredRun, TurnReason


@dataclass(frozen=True)
class CareerTurnOutcome:
    decision: TurnDecision
    evidence: tuple[EvidenceProposal, ...] = field(default=(), repr=False)
    contradictions: tuple[ContradictionCandidate, ...] = field(default=(), repr=False)
    runs: tuple[StoredRun, ...] = ()
    fallback_reason: RunFailure | TurnReason | Literal[
        "question_repeated", "contradiction_unavailable", "attempt_not_funded",
    ] | None = None
    tokens_reserved: int = 0
    cost_reserved_microusd: int = 0


async def execute_career_turn(
    model: CareerModel, state: CareerSessionState, planning: TurnPlanningInput, context: CareerTurnContext,
    *, now: datetime | None = None, sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    before_attempt: Callable[[], Awaitable[None]] | None = None,
) -> CareerTurnOutcome:
    """Call the injected model within server-owned limits and return only approved output."""
    context.check_session(state)
    context_time = now if now is not None else datetime.now(timezone.utc)
    session_expiry = state.retention_expires_at if isinstance(state, SessionView) else None
    if session_expiry is not None and session_expiry <= context_time:
        return CareerTurnOutcome(TurnDecision("inactive"))
    decision = plan_next_turn(state, planning)
    if decision.question is None:
        return CareerTurnOutcome(decision)
    loop = asyncio.get_running_loop()
    started = loop.time()
    turn = prepare_turn(state, decision, context, planning.coverage, context_time)
    if turn.question_repeated:
        return CareerTurnOutcome(TurnDecision("pause"), fallback_reason="question_repeated")
    if decision.contradiction is not None and turn.contradiction is None:
        return CareerTurnOutcome(TurnDecision("pause"), fallback_reason="contradiction_unavailable")

    manifest = model.manifest
    budget = planning.budget
    expiry = min((value for value in (turn.expires_at, session_expiry) if value is not None), default=None)
    retention_deadline = started + (expiry - context_time).total_seconds() if expiry is not None else math.inf
    deadline = min(started + budget.time_remaining_ms / 1000, retention_deadline)
    attempt_time = max(budget.reserved_time_ms, manifest.timeout_ms) / 1000
    tokens = budget.reserved_tokens
    token_limit = state.tokens_remaining
    cost = budget.reserved_cost_microusd
    calls = 0
    runs: list[StoredRun] = []
    repair: TurnViolation | None = None
    delay = 0.0
    retry_count = 0
    reason = None
    evidence: tuple[EvidenceProposal, ...] = ()
    while True:
        request = CareerModelRequest(owner_id=context.owner_id, context=turn.encode(repair))
        quote = model.quote(request)
        if (quote is None or tokens < max(manifest.max_output_tokens, quote.tokens)
                or cost == 0 or cost < quote.cost_microusd
                or (calls + 1) * tokens > token_limit
                or (calls + 1) * cost > budget.cost_remaining_microusd
                or delay + attempt_time > deadline - loop.time()):
            reason = reason or "attempt_not_funded"
            break
        if delay:
            await sleep(delay)
        if before_attempt is not None:
            await before_attempt()
        if attempt_time > deadline - loop.time():
            reason = reason or "attempt_not_funded"
            break
        # Keep the reservation for attempts whose usage never comes back.
        calls += 1
        try:
            async with asyncio.timeout_at(deadline):
                result = await model.propose(request)
        except TimeoutError:
            reason = "model_timeout"
            break
        if result.run.manifest != manifest:
            reason = "provider_error"
            break
        metadata = result.run.metadata
        failure = metadata.failure
        violation = None
        used_tokens = (metadata.input_tokens or 0) + (metadata.output_tokens or 0)
        if used_tokens > tokens or (metadata.cost_usd is not None and metadata.cost_usd * 1_000_000 > cost):
            violation = TurnViolation("attempt_exceeded_reservation", "usage")
            failure = "proposal_rejected"
        elif failure is None:
            evidence, violation = validate_proposal(result.proposal, decision, turn)
            if violation is not None:
                failure = "schema_invalid" if violation.code == "schema_invalid" else "proposal_rejected"
        elif failure == "schema_invalid":
            violation = TurnViolation("schema_invalid", "proposal")

        reason = violation.code if violation is not None else failure
        codes = list(metadata.reason_codes)
        if violation is not None and violation.code not in codes:
            codes = [*codes[:31], violation.code]
        runs.append(result.run.model_copy(update={"metadata": metadata.model_copy(update={
            "session_id": context.session_id, "failure": failure,
            "retry_count": retry_count, "repair_count": int(repair is not None),
            "reason_codes": codes,
        })}))
        if failure is None or repair is not None or reason == "attempt_exceeded_reservation":
            break
        if violation is not None:
            repair = violation
            delay = 0.0
            continue
        if not result.retryable or failure not in ("model_unavailable", "model_timeout") or retry_count >= 2:
            break

        provider_delay = result.retry_after_seconds
        if provider_delay is not None and (not math.isfinite(provider_delay) or provider_delay < 0):
            break
        delay = max(float(2 ** retry_count), provider_delay or 0.0)
        retry_count += 1

    contradiction = turn.contradiction
    if loop.time() >= retention_deadline:
        evidence = ()
        if session_expiry is not None and session_expiry == expiry:
            decision = TurnDecision("inactive")
            contradiction = None
            reason = "model_unavailable"
        elif contradiction is not None:
            decision = TurnDecision("pause")
            contradiction = None
            reason = "contradiction_unavailable"
    return CareerTurnOutcome(
        decision, evidence, (contradiction,) if contradiction else (), tuple(runs), reason,
        tokens_reserved=calls * tokens, cost_reserved_microusd=calls * cost,
    )
