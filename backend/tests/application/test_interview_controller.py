import pytest
from pydantic import ValidationError

from app.application.errors import InvalidOperationError, ResourceConflictError
from app.application.interview_controller import InterviewEvent, transition
from app.schemas.career.interview import CareerSessionState, CareerTurnProposal


MODE_CHAPTERS = (
    ("foundation", "student", (
        "academic_foundation", "work_project_timeline", "project_ownership", "technical_depth",
        "outcomes", "constraints_recovery", "collaboration_leadership", "learning", "communication_gaps",
    )),
    ("foundation", "experienced_ic", (
        "work_project_timeline", "project_ownership", "technical_depth", "outcomes", "constraints_recovery",
        "collaboration_leadership", "learning", "communication_gaps",
    )),
    ("target_calibration", "early_career", (
        "work_project_timeline", "project_ownership", "technical_depth", "learning", "communication_gaps",
    )),
    ("application_gap", "new_graduate", (
        "communication_gaps", "work_project_timeline", "project_ownership", "outcomes", "learning",
    )),
    ("career_refresh", "manager_or_leader", (
        "work_project_timeline", "project_ownership", "technical_depth", "outcomes", "constraints_recovery",
        "collaboration_leadership",
    )),
)


def state(**overrides) -> CareerSessionState:
    return CareerSessionState.model_validate({
        "schema_version": 1,
        "session_id": "session-a",
        "owner_id": "owner-a",
        "target_id": "target-a",
        "mode": "foundation",
        "status": "active",
        "chapter": "introduction",
        "state_version": 7,
        "prompt_version": "interview-v1",
        "turns_remaining": 12,
        "tokens_remaining": 3000,
        **overrides,
    })


def event(session: CareerSessionState, kind: str, **overrides) -> InterviewEvent:
    return InterviewEvent.model_validate({
        "session_id": session.session_id,
        "expected_state_version": session.state_version,
        "kind": kind,
        **overrides,
    })


@pytest.mark.parametrize(("mode", "stage", "chapters"), MODE_CHAPTERS)
def test_replay_is_deterministic_and_selects_each_mode_chapter(mode, stage, chapters):
    initial = state(mode=mode)
    steps = [("confirm_stage", {"candidate_stage": stage})]
    steps += [("chapter_reviewed", {})] * len(chapters)
    steps += [("complete", {})]
    events = [event(initial, kind, expected_state_version=initial.state_version + i, **values)
              for i, (kind, values) in enumerate(steps)]

    def replay():
        current = initial
        snapshots = []
        for step in events:
            current = transition(current, step)
            snapshots.append(current)
        return snapshots

    history = replay()
    assert replay() == history
    assert [item.chapter for item in history] == [*chapters, "evidence_confirmation", "evidence_confirmation"]
    assert [item.status for item in history] == ["active"] * (len(history) - 1) + ["completed"]
    assert [item.state_version for item in history] == list(range(8, 8 + len(history)))
    for item in history:
        assert item.candidate_stage == stage
        assert item.model_dump(exclude={"state_version", "status", "chapter", "candidate_stage"}) == (
            initial.model_dump(exclude={"state_version", "status", "chapter", "candidate_stage"})
        )
    assert initial == state(mode=mode)


@pytest.mark.parametrize("chapter", ("introduction", "project_ownership", "evidence_confirmation"))
def test_pause_and_resume_keep_the_current_chapter(chapter):
    initial = state(chapter=chapter, candidate_stage="experienced_ic")
    paused = transition(initial, event(initial, "pause"))
    resumed = transition(paused, event(paused, "resume"))
    assert paused == initial.model_copy(update={"status": "paused", "state_version": 8})
    assert resumed == initial.model_copy(update={"state_version": 9})


@pytest.mark.parametrize("status", ("active", "paused"))
def test_failure_is_explicit_and_preserves_stage_and_chapter(status):
    initial = state(status=status, chapter="project_ownership", candidate_stage="experienced_ic")
    assert transition(initial, event(initial, "fail")) == initial.model_copy(
        update={"status": "failed", "state_version": 8}
    )


@pytest.mark.parametrize("status", ("completed", "failed"))
@pytest.mark.parametrize("kind", ("confirm_stage", "chapter_reviewed", "pause", "resume", "complete", "fail"))
def test_terminal_sessions_reject_every_event(status, kind):
    current = state(status=status, chapter="evidence_confirmation", candidate_stage="experienced_ic")
    data = {"candidate_stage": "student"} if kind == "confirm_stage" else {}
    with pytest.raises(ResourceConflictError):
        transition(current, event(current, kind, **data))


@pytest.mark.parametrize(("status", "chapter", "kind"), (
    ("active", "introduction", "chapter_reviewed"),
    ("active", "introduction", "complete"),
    ("active", "introduction", "resume"),
    ("active", "project_ownership", "complete"),
    ("active", "evidence_confirmation", "chapter_reviewed"),
    ("paused", "project_ownership", "chapter_reviewed"),
    ("paused", "project_ownership", "pause"),
    ("paused", "evidence_confirmation", "complete"),
    ("paused", "introduction", "confirm_stage"),
    ("active", "project_ownership", "confirm_stage"),
))
def test_illegal_transitions_leave_the_session_unchanged(status, chapter, kind):
    current = state(status=status, chapter=chapter, candidate_stage="experienced_ic")
    data = {"candidate_stage": "student"} if kind == "confirm_stage" else {}
    with pytest.raises(InvalidOperationError):
        transition(current, event(current, kind, **data))
    assert current == state(status=status, chapter=chapter, candidate_stage="experienced_ic")


def test_candidate_confirmation_overrides_an_initial_suggestion():
    initial = state(candidate_stage="experienced_ic")
    confirmed = transition(initial, event(initial, "confirm_stage", candidate_stage="new_graduate"))
    assert confirmed.candidate_stage == "new_graduate"
    assert confirmed.chapter == "academic_foundation"


@pytest.mark.parametrize("version", (6, 8))
def test_version_mismatch_fails_and_a_replayed_event_cannot_be_reapplied(version):
    current = state()
    with pytest.raises(ResourceConflictError):
        transition(current, event(current, "pause", expected_state_version=version))
    accepted = event(current, "pause")
    with pytest.raises(ResourceConflictError):
        transition(transition(current, accepted), accepted)


def test_foreign_session_and_unknown_or_inconsistent_chapters_fail_closed():
    current = state()
    with pytest.raises(InvalidOperationError):
        transition(current, event(current, "pause", session_id="session-b"))
    for invalid in (
        state(chapter="foreign-chapter"),
        state(chapter="project_ownership"),
        state(chapter="academic_foundation", candidate_stage="experienced_ic"),
    ):
        with pytest.raises(InvalidOperationError):
            transition(invalid, event(invalid, "pause"))


def test_model_proposal_has_no_transition_authority():
    current = state(chapter="evidence_confirmation", candidate_stage="experienced_ic")
    proposal = CareerTurnProposal(
        schema_version=1, question="Which outcomes can you confirm?", question_intent="review",
        target_evidence_slot="outcomes", recommended_action="complete",
    )
    for untrusted in (proposal, proposal.model_dump(), event(current, "complete").model_dump()):
        with pytest.raises(InvalidOperationError):
            transition(current, untrusted)


def test_event_payload_rejects_unexpected_fields_and_stage_changes():
    current = state()
    for kind, fields in (
        ("confirm_stage", {}),
        ("pause", {"candidate_stage": "student"}),
        ("chapter_reviewed", {"chapter": "evidence_confirmation"}),
        ("execute_tool", {}),
        ("complete", {"expected_state_version": True}),
    ):
        with pytest.raises(ValidationError):
            event(current, kind, **fields)
