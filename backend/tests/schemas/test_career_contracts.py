import json

import pytest
from pydantic import ValidationError

from app.schemas.career import career_json_schema
from app.schemas.career.evidence import CareerEvidenceItem
from app.schemas.career.interview import CareerTurnProposal
from app.schemas.career.resume import (
    EvidenceSelectionDecision,
    GeneratedClaimLineage,
    ResumeBulletPlan,
    ResumeBulletRenderProposal,
    ResumeRenderValidationResult,
)
from app.schemas.career.sources import CareerSource, LinkedInReview


@pytest.fixture
def contribution():
    return {
        "schema_version": 1,
        "evidence_id": "api",
        "revision": 1,
        "owner_id": "candidate",
        "claim": "Built the FastAPI endpoint and wrote tests for ambiguous shorthand.",
        "category": "action",
        "ownership": "individual",
        "lifecycle": "confirmed",
        "support": "candidate_statement",
        "sources": [
            {
                "source_id": "interview-turn-5",
                "source_version": 1,
                "relationship": "supports",
                "locator": "message:5",
                "excerpt": "I built the FastAPI endpoint and wrote those tests.",
                "extraction": "candidate",
            }
        ],
    }


@pytest.fixture
def plan(contribution):
    return {
        "schema_version": 1,
        "plan_id": "backend-plan",
        "target_requirement_ids": ["api-testing"],
        "evidence_revisions": [{"evidence_id": contribution["evidence_id"], "revision": 1}],
        "action": "Built a FastAPI endpoint and regression tests",
        "ownership": "individual",
        "method": "Expand underwriting shorthand",
        "skills": ["FastAPI", "API testing"],
        "ownership_verbs": ["built", "tested"],
        "structure": "technical_contribution",
        "max_length": 200,
        "policy_version": "1.0",
        "renderer_version": "1.0",
    }


def test_candidate_statement_and_bullet_lineage_round_trip(contribution, plan):
    item = CareerEvidenceItem.model_validate(contribution)
    draft = ResumeBulletPlan.model_validate(plan)
    lineage = GeneratedClaimLineage(
        schema_version=1, claim_id="bullet-1", artifact_id="resume", artifact_version=1,
        evidence_revisions=draft.evidence_revisions,
    )
    assert item.lifecycle == "confirmed"
    assert item.support == "candidate_statement"
    assert draft.permitted_numbers == []
    assert draft.outcome is None
    assert CareerEvidenceItem.model_validate_json(item.model_dump_json()) == item
    assert GeneratedClaimLineage.model_validate_json(lineage.model_dump_json()) == lineage
    assert lineage.evidence_revisions[0].revision == item.revision


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"lifecycle": "private"}, "private"),
        ({"lifecycle": "contradicted"}, "contradict"),
        ({"support": "independently_verified"}, "verification"),
        ({"sources": []}, "sources"),
        ({"schema_version": True}, "schema_version"),
        ({"revision": "1"}, "revision"),
    ],
)
def test_invalid_evidence_states_fail(contribution, changes, reason):
    with pytest.raises(ValidationError, match=reason):
        CareerEvidenceItem.model_validate(contribution | changes)


def test_source_requires_version_and_evidence_excerpt(contribution):
    source = contribution["sources"][0]
    del source["source_version"]
    del source["excerpt"]
    with pytest.raises(ValidationError, match="source_version"):
        CareerEvidenceItem.model_validate(contribution)
    source["source_version"] = 1
    with pytest.raises(ValidationError, match="excerpt"):
        CareerEvidenceItem.model_validate(contribution)


def test_model_turn_proposes_evidence_without_confirmation_authority(contribution):
    payload = {
        "schema_version": 1,
        "question": "How did you test the ambiguous shorthand?",
        "question_intent": "probe",
        "target_evidence_slot": "validation",
        "recommended_action": "continue",
        "evidence_proposals": [
            {
                "claim": contribution["claim"], "category": "action",
                "sources": contribution["sources"],
            }
        ],
    }
    assert CareerTurnProposal.model_validate(payload).evidence_proposals[0].claim
    payload["evidence_proposals"][0]["lifecycle"] = "confirmed"
    with pytest.raises(ValidationError, match="lifecycle"):
        CareerTurnProposal.model_validate(payload)


def test_render_proposal_cannot_supply_facts(plan):
    proposal = {"schema_version": 1, "plan_id": plan["plan_id"], "text": "Built a FastAPI endpoint."}
    assert ResumeBulletRenderProposal.model_validate(proposal).plan_id == plan["plan_id"]
    with pytest.raises(ValidationError, match="evidence_revisions"):
        ResumeBulletRenderProposal.model_validate(proposal | {"evidence_revisions": []})
    with pytest.raises(ValidationError, match="outcome"):
        ResumeBulletPlan.model_validate(plan | {"structure": "achievement"})


def test_rejected_render_requires_reason_and_fallback():
    payload = {
        "schema_version": 1,
        "accepted": False,
        "rule_version": "1.0",
        "plan_hash": "a" * 64,
        "proposal_hash": "b" * 64,
        "reason_codes": ["ownership_upgrade"],
        "used_fallback": True,
    }
    assert ResumeRenderValidationResult.model_validate(payload).used_fallback is True
    with pytest.raises(ValidationError, match="fallback"):
        ResumeRenderValidationResult.model_validate(payload | {"used_fallback": False})
    with pytest.raises(ValidationError, match="proposal hash"):
        ResumeRenderValidationResult.model_validate(payload | {"proposal_hash": None})
    unavailable = ResumeRenderValidationResult.model_validate(
        payload | {"proposal_hash": None, "reason_codes": ["model_unavailable"]}
    )
    assert unavailable.used_fallback is True


def test_linkedin_export_coverage_and_review_require_cited_sources():
    assert "document" in LinkedInReview.model_json_schema()["required"]
    assert "source" in CareerSource.model_json_schema()["required"]


def test_export_bundle_is_deterministic_and_contains_versioned_contracts():
    exported = career_json_schema()
    assert exported["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert json.dumps(exported, sort_keys=True) == json.dumps(career_json_schema(), sort_keys=True)
    for name in ("CareerEvidenceItem", "CareerTurnProposal", "ResumeBulletPlan", "GeneratedClaimLineage"):
        schema = exported["$defs"][name]
        assert schema["additionalProperties"] is False
        assert schema["properties"]["schema_version"]["const"] == 1
        assert "schema_version" in schema["required"]


@pytest.mark.parametrize("value", [True, "30", float("inf")])
def test_bullet_plan_numbers_do_not_coerce_or_accept_non_finite_values(plan, value):
    with pytest.raises(ValidationError, match="permitted_numbers"):
        ResumeBulletPlan.model_validate(plan | {"permitted_numbers": [_metric(value)]})


def test_bullet_plan_preserves_large_integer_values(plan):
    number = 2**53 + 1
    draft = ResumeBulletPlan.model_validate(plan | {
        "permitted_numbers": [_metric(number)], "outcome": {
            "description": "Processed records", "measurement_method": "Counter", "measurement_scope": "Pilot",
        }, "structure": "achievement",
    })
    restored = ResumeBulletPlan.model_validate_json(draft.model_dump_json())
    assert type(restored.permitted_numbers[0].value) is int
    assert restored.permitted_numbers[0].value == number


def test_private_correction_keeps_lineage_of_the_old_draft(contribution, plan):
    original = CareerEvidenceItem.model_validate(contribution)
    corrected = CareerEvidenceItem.model_validate(
        contribution | {"revision": 2, "supersedes_revision": 1, "lifecycle": "private", "is_private": True}
    )
    draft = ResumeBulletPlan.model_validate(plan)
    assert corrected.supersedes_revision == draft.evidence_revisions[0].revision == original.revision
    assert corrected.revision != draft.evidence_revisions[0].revision
    with pytest.raises(ValidationError, match="superseded revision"):
        CareerEvidenceItem.model_validate(contribution | {"supersedes_revision": 1})


def test_exact_source_excerpt_keeps_formatting(contribution):
    source = contribution["sources"][0]
    source["excerpt"] = "  Original text\n"
    item = CareerEvidenceItem.model_validate(contribution)
    assert item.sources[0].excerpt == "  Original text\n"
    with pytest.raises(ValidationError, match="excerpt"):
        CareerEvidenceItem.model_validate(contribution | {"sources": [source | {"excerpt_sha256": "a" * 64}]})


def test_accepted_render_cannot_report_rejection():
    with pytest.raises(ValidationError, match="accepted"):
        ResumeRenderValidationResult(
            schema_version=1, accepted=True, rule_version="1",
            reason_codes=["proposal_rejected"], plan_hash="a" * 64, proposal_hash="b" * 64,
            used_fallback=False,
        )


def test_contradiction_requires_distinct_source_sides(contribution):
    source = contribution["sources"][0]
    with pytest.raises(ValidationError, match="distinct"):
        CareerTurnProposal.model_validate({
            "schema_version": 1, "question": "Can you clarify what you built?",
            "question_intent": "resolve_contradiction", "target_evidence_slot": "action",
            "recommended_action": "clarify",
            "contradiction_candidates": [{"supports": source, "contradicts": source | {"relationship": "contradicts"}}],
        })


@pytest.mark.parametrize(
    "changes",
    [
        {"winning_evidence": {"evidence_id": "other", "revision": 1}},
        {"ordered_criteria": ["model_timeout"]},
    ],
)
def test_selected_evidence_matches_winner_and_ranking_criteria(changes):
    revision = {"evidence_id": "api", "revision": 1}
    payload = {
        "schema_version": 1, "target_id": "backend", "artifact_id": "resume",
        "evidence": revision, "decision": "selected", "winning_evidence": revision,
        "ordered_criteria": ["must_have_relevance"], "reason_codes": ["must_have_relevance"],
    }
    assert EvidenceSelectionDecision.model_validate(payload).winning_evidence.evidence_id == "api"
    with pytest.raises(ValidationError):
        EvidenceSelectionDecision.model_validate(payload | changes)


def test_unmeasured_bullet_cannot_allow_metric(plan):
    with pytest.raises(ValidationError, match="measurement"):
        ResumeBulletPlan.model_validate(plan | {"permitted_numbers": [_metric(30)]})


def test_linkedin_claim_finding_requires_locator():
    with pytest.raises(ValidationError, match="locator"):
        LinkedInReview.model_validate({
            "schema_version": 1, "document": {"source_id": "pdf", "source_version": 1},
            "target_id": "backend", "evidence_snapshot_version": 1, "parser_version": "v1",
            "findings": [{"kind": "unsupported_claim", "explanation": "No supporting evidence."}],
        })


def test_source_rejects_numeric_timestamp():
    with pytest.raises(ValidationError, match="created_at"):
        CareerSource.model_validate({
            "schema_version": 1, "source": {"source_id": "message", "source_version": 1},
            "owner_id": "candidate", "kind": "interview_message", "content_sha256": "a" * 64,
            "created_at": 123,
        })


def test_team_result_requires_team_attribution(plan):
    with pytest.raises(ValidationError, match="team contribution"):
        ResumeBulletPlan.model_validate(plan | {
            "structure": "achievement", "ownership": "shared",
            "outcome": {"description": "The team shipped the pilot."},
        })
    shared = plan | {
        "structure": "team_contribution", "ownership": "shared",
        "outcome": {"description": "The team shipped the pilot."},
    }
    with pytest.raises(ValidationError, match="personal ownership scope"):
        ResumeBulletPlan.model_validate(shared)
    attributed = ResumeBulletPlan.model_validate(shared | {"ownership_scope": "API tests"})
    assert attributed.ownership_scope == "API tests"


def test_schema_bundle_contains_resolvable_references():
    bundle = career_json_schema()
    for definition in bundle["$defs"].values():
        for reference in _references(definition):
            assert reference.startswith("#/$defs/")
            assert reference.rsplit("/", 1)[1] in bundle["$defs"]


def _references(node):
    if isinstance(node, dict):
        if "$ref" in node:
            yield node["$ref"]
        for value in node.values():
            yield from _references(value)
    elif isinstance(node, list):
        for value in node:
            yield from _references(value)



def _metric(value):
    return {
        "value": value, "unit": "records", "estimated": False,
        "evidence": {"evidence_id": "api", "revision": 1},
    }
