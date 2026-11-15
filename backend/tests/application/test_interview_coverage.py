import pytest
from pydantic import ValidationError

from app.application.errors import InvalidOperationError, ResourceConflictError
from app.application.interview_controller import InterviewEvent, transition
from app.application.interview_coverage import TurnPlanningInput, plan_next_turn
from app.schemas.career.interview import CareerSessionState


def session(**changes):
    return CareerSessionState.model_validate({
        "schema_version": 1, "session_id": "session-a", "owner_id": "owner-a", "mode": "foundation",
        "candidate_stage": "experienced_ic", "chapter": "work_project_timeline", "status": "active",
        "state_version": 4, "prompt_version": "interview-v1", "turns_remaining": 4, "tokens_remaining": 500,
        **changes,
    })


def slot(name, status, *evidence):
    return {"slot": name, "status": status, "evidence_revisions": [
        {"evidence_id": item, "revision": 1} for item in evidence
    ]}


def planning(state, slots=(), **changes):
    return TurnPlanningInput.model_validate({
        "coverage": {"schema_version": 1, "session_id": state.session_id, "slots": list(slots)},
        "expected_state_version": state.state_version,
        "budget": {"time_remaining_ms": 30000, "cost_remaining_microusd": 10000},
        **changes,
    })


@pytest.mark.parametrize(("stage", "expected"), (
    ("student", "project_context"),
    ("new_graduate", "project_context"),
    ("experienced_ic", "role_scope"),
    ("manager_or_leader", "role_scope"),
))
def test_same_controller_prioritizes_work_evidence_for_each_stage(stage, expected):
    state = session(candidate_stage=stage)
    coverage = [slot("project_context", "missing"), slot("role_scope", "missing")]
    forward = plan_next_turn(state, planning(state, coverage))
    assert forward == plan_next_turn(state, planning(state, reversed(coverage)))
    assert (forward.action, forward.slot) == ("probe", expected)
    assert forward.question.endswith("?")


@pytest.mark.parametrize("status", ("confirmed", "private", "unavailable"))
def test_resolved_or_excluded_slot_is_never_asked_again(status):
    state = session()
    result = plan_next_turn(state, planning(state, [slot("role_scope", status, "evidence-a")]))
    assert (result.action, result.slot) == ("probe", "project_context")


def test_missing_question_is_not_repeated_and_two_vague_probes_are_distinct():
    state = session()
    initial = plan_next_turn(state, planning(state))
    repeat = plan_next_turn(state, planning(state, progress={"role_scope": {"asked": True}}))
    assert repeat.slot == "project_context"
    questions = [initial.question]
    for attempts in (0, 1):
        decision = plan_next_turn(state, planning(state, progress={
            "role_scope": {"asked": True, "vague_answer": True, "vague_probes": attempts},
        }))
        assert (decision.action, decision.slot) == ("clarify", "role_scope")
        questions.append(decision.question)
    assert len(set(questions)) == 3
    exhausted = planning(state, progress={
        "role_scope": {"asked": True, "vague_answer": True, "vague_probes": 2},
    })
    assert plan_next_turn(state, exhausted).slot == "project_context"


def test_proposed_evidence_gets_at_most_one_confirmation_request():
    state = session()
    coverage = [slot("role_scope", "proposed", "evidence-a")]
    review = plan_next_turn(state, planning(state, coverage))
    assert (review.action, review.slot) == ("confirm_evidence", "role_scope")
    done = planning(state, coverage, progress={"role_scope": {"confirmation_requested": True}})
    assert plan_next_turn(state, done).slot == "project_context"


@pytest.mark.parametrize(("progress", "expected"), (
    ({}, ("probe", "role_scope")),
    ({"asked": True, "vague_answer": True}, ("clarify", "role_scope")),
    ({"asked": True, "vague_answer": True, "vague_probes": 2}, ("probe", "project_context")),
))
def test_proposal_without_revisions_follows_missing_evidence_rules(progress, expected):
    state = session()
    data = planning(state, [slot("role_scope", "proposed")], progress={"role_scope": progress})
    decision = plan_next_turn(state, data)
    assert (decision.action, decision.slot) == expected


@pytest.mark.parametrize("other_status", ("private", "unavailable", "confirmed", "contradicted"))
def test_proposed_confirmation_skips_ineligible_references(other_status):
    state = session()
    other = slot("ownership", other_status, "evidence-a")
    if other_status == "confirmed":
        other["evidence_revisions"][0]["revision"] = 2
    coverage = [slot("role_scope", "proposed", "evidence-a"), other]
    decision = plan_next_turn(state, planning(state, coverage))
    assert (decision.action, decision.slot) == ("probe", "project_context")


def test_partial_proposal_gets_two_narrower_probes_after_vague_reply():
    state = session()
    coverage = [slot("role_scope", "proposed", "evidence-a")]
    questions = []
    for attempts in (0, 1):
        data = planning(state, coverage, progress={
            "role_scope": {"asked": True, "vague_answer": True, "vague_probes": attempts,
                           "confirmation_requested": True},
        })
        decision = plan_next_turn(state, data)
        assert (decision.action, decision.slot) == ("clarify", "role_scope")
        questions.append(decision.question)
    assert len(set(questions)) == 2
    exhausted = planning(state, coverage, progress={
        "role_scope": {"asked": True, "vague_answer": True, "vague_probes": 2, "confirmation_requested": True},
    })
    assert plan_next_turn(state, exhausted).slot == "project_context"


def test_contradiction_in_an_earlier_chapter_precedes_a_normal_question_and_is_not_repeated():
    state = session(chapter="technical_depth")
    coverage = [slot("ownership", "contradicted", "revision-a", "revision-b")]
    supported = {"ownership": {"evidence_id": "revision-a", "revision": 1}}
    decision = plan_next_turn(state, planning(state, coverage, supported_contradictions=supported))
    assert (decision.action, decision.slot) == ("resolve_contradiction", "ownership")
    assert decision.contradiction.model_dump() == supported["ownership"]
    assert decision.next_chapter is None
    asked = planning(state, coverage, supported_contradictions=supported,
                     requested_contradictions=[supported["ownership"]])
    assert plan_next_turn(state, asked).slot == "technical_decision"


def test_same_contradiction_is_not_repeated_when_it_covers_two_slots():
    state = session(chapter="technical_depth")
    ref = {"evidence_id": "revision-a", "revision": 1}
    coverage = [
        slot("role_scope", "contradicted", "revision-a"),
        slot("project_context", "contradicted", "revision-a"),
    ]
    supported = {"role_scope": ref, "project_context": ref}
    assert plan_next_turn(state, planning(state, coverage, supported_contradictions=supported)).slot == "role_scope"
    decision = plan_next_turn(state, planning(
        state, coverage, supported_contradictions=supported, requested_contradictions=[ref],
    ))
    assert (decision.action, decision.slot) == ("probe", "technical_decision")


def test_old_question_does_not_suppress_a_new_contradicted_revision():
    state = session()
    old = {"evidence_id": "revision-a", "revision": 1}
    current = {**old, "revision": 2}
    coverage = [{"slot": "role_scope", "status": "contradicted", "evidence_revisions": [current]}]
    decision = plan_next_turn(state, planning(
        state, coverage, supported_contradictions={"role_scope": current}, requested_contradictions=[old],
    ))
    assert (decision.action, decision.slot) == ("resolve_contradiction", "role_scope")
    assert decision.contradiction.model_dump() == current


@pytest.mark.parametrize(("coverage", "supported"), (
    ([slot("ownership", "contradicted")], {}),
    ([slot("ownership", "contradicted", "revision-a")], {}),
    ([slot("ownership", "contradicted", "revision-a")],
     {"ownership": {"evidence_id": "revision-a", "revision": 2}}),
    ([slot("ownership", "contradicted", "revision-a"), slot("role_scope", "private", "revision-a")],
     {"ownership": {"evidence_id": "revision-a", "revision": 1}}),
    ([slot("ownership", "contradicted", "revision-a"), slot("role_scope", "unavailable", "revision-a")],
     {"ownership": {"evidence_id": "revision-a", "revision": 1}}),
))
def test_unverified_or_hidden_contradiction_does_not_trigger_a_question(coverage, supported):
    state = session(chapter="technical_depth")
    data = planning(state, coverage, supported_contradictions=supported)
    decision = plan_next_turn(state, data)
    assert (decision.action, decision.slot) == ("probe", "technical_decision")


@pytest.mark.parametrize(("state_change", "budget_change", "reason"), (
    ({"turns_remaining": 0}, {}, "turns"),
    ({"tokens_remaining": 0}, {}, "tokens"),
    ({}, {"time_remaining_ms": 0}, "time"),
    ({}, {"cost_remaining_microusd": 0}, "cost"),
    ({}, {"reserved_tokens": 501}, "tokens"),
    ({}, {"reserved_time_ms": 30001}, "time"),
    ({}, {"reserved_cost_microusd": 10001}, "cost"),
))
def test_budgets_stop_before_questions_or_contradiction_routing(state_change, budget_change, reason):
    state = session(**state_change)
    budget = {"time_remaining_ms": 30000, "cost_remaining_microusd": 10000, **budget_change}
    coverage = [slot("role_scope", "contradicted", "revision-a")]
    supported = {"role_scope": {"evidence_id": "revision-a", "revision": 1}}
    decision = plan_next_turn(state, planning(state, coverage, budget=budget, supported_contradictions=supported))
    assert (decision.action, decision.stop_reason, decision.question, decision.slot) == ("pause", reason, None, None)


def test_exact_positive_reservations_are_allowed():
    state = session()
    budget = {"time_remaining_ms": 250, "reserved_time_ms": 250, "cost_remaining_microusd": 10,
              "reserved_cost_microusd": 10, "reserved_tokens": 500}
    assert plan_next_turn(state, planning(state, budget=budget)).action == "probe"


def test_covered_chapter_advances_using_state_machine_and_final_review_needs_application_event():
    state = session()
    coverage = [slot("role_scope", "confirmed", "evidence-a"), slot("project_context", "unavailable")]
    decision = plan_next_turn(state, planning(state, coverage))
    expected = transition(state, InterviewEvent(
        kind="chapter_reviewed", session_id=state.session_id, expected_state_version=state.state_version,
    ))
    assert (decision.action, decision.next_chapter) == ("advance_chapter", expected.chapter)
    assert state.state_version == 4
    final = session(chapter="evidence_confirmation")
    assert plan_next_turn(final, planning(final)).action == "coverage_review"
    assert final.status == "active"


def test_context_references_are_deduplicated_and_skip_private_current_and_later_chapters():
    state = session(chapter="technical_depth")
    coverage = [
        slot("role_scope", "confirmed", "z-evidence"),
        slot("project_context", "confirmed", "z-evidence", "private-evidence", "a-evidence"),
        slot("ownership", "private", "private-evidence"),
        slot("technical_decision", "confirmed", "current-evidence"),
        slot("measurement", "confirmed", "future-evidence"),
    ]
    decision = plan_next_turn(state, planning(state, coverage))
    assert [(item.chapter, tuple((ref.evidence_id, ref.revision) for ref in item.evidence))
            for item in decision.completed_chapters] == [
        ("work_project_timeline", (("a-evidence", 1), ("z-evidence", 1))),
    ]


def test_context_excludes_conflicting_versions_of_the_same_evidence():
    state = session(chapter="technical_depth")
    first = slot("role_scope", "confirmed", "mixed-version", "current-evidence")
    second = slot("project_context", "confirmed", "mixed-version")
    second["evidence_revisions"][0]["revision"] = 2
    decision = plan_next_turn(state, planning(state, [first, second]))
    assert [(item.chapter, tuple((ref.evidence_id, ref.revision) for ref in item.evidence))
            for item in decision.completed_chapters] == [
        ("work_project_timeline", (("current-evidence", 1),)),
    ]


@pytest.mark.parametrize("status", ("paused", "completed", "failed"))
def test_inactive_sessions_never_schedule_questions(status):
    state = session(status=status)
    assert plan_next_turn(state, planning(state)).action == "inactive"


def test_stage_confirmation_snapshot_and_input_validation():
    state = session(chapter="introduction", candidate_stage=None)
    assert plan_next_turn(state, planning(state)).action == "confirm_stage"
    data = planning(state)
    with pytest.raises(ResourceConflictError):
        plan_next_turn(state, data.model_copy(update={"expected_state_version": 3}))
    with pytest.raises(InvalidOperationError):
        plan_next_turn(state.model_copy(update={"session_id": "session-b"}), data)
    with pytest.raises(InvalidOperationError):
        plan_next_turn(state, planning(state, [slot("employer_prestige", "missing")]))
    with pytest.raises(InvalidOperationError):
        plan_next_turn(session(candidate_stage=None), data)
    with pytest.raises(ValidationError):
        planning(state, employer_prestige="famous employer")
    with pytest.raises(ValidationError):
        planning(state, progress={"role_scope": {"vague_probes": 3}})
