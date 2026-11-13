import json
import subprocess
import sys

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from app.schemas.career import career_json_schema
from app.schemas.career.evidence import CareerEvidenceItem, EvidenceSourceLink
from app.schemas.career.interview import CareerCoverage
from app.schemas.career.resume import (
    EvidenceSelectionDecision,
    GeneratedClaimLineage,
    ResumeBulletPlan,
    ResumeRenderValidationResult,
    ResumeRequirementFinding,
)
from app.schemas.career.sources import CareerSource, LinkedInDocument, LinkedInReview

VERSION = {"schema_version": 1}
REF = {"evidence_id": "api", "revision": 2}
PDF = {"source_id": "profile-pdf", "source_version": 1}
LINK = {
    "source_id": "interview", "source_version": 1, "relationship": "supports",
    "locator": "message:5", "excerpt": "Built the API.", "extraction": "candidate",
}
ITEM = VERSION | REF | {
    "owner_id": "candidate", "claim": "Built the API.", "category": "action",
    "ownership": "individual", "lifecycle": "confirmed", "support": "candidate_statement",
    "sources": [LINK],
}
REVIEW = VERSION | {
    "document": PDF, "target_id": "backend", "evidence_snapshot_version": 2,
    "parser_version": "parser-v1", "model_manifest_id": "manifest-v1",
    "generated_artifact_ids": ["profile-draft"], "findings": [],
}
PLAN = VERSION | {
    "plan_id": "plan", "evidence_revisions": [REF], "action": "Built the API",
    "ownership": "individual", "method": "FastAPI", "ownership_verbs": ["built"],
    "structure": "achievement", "max_length": 180, "policy_version": "v1",
    "renderer_version": "v1", "outcome": {
        "description": "Reduced review time", "measurement_method": "Pilot timing",
        "measurement_scope": "5 reviewers",
    },
}
METRIC = {"value": 30, "unit": "minutes per day", "estimated": True, "evidence": REF}
RESULT = VERSION | {
    "accepted": False, "rule_version": "v1", "plan_hash": "a" * 64, "used_fallback": True,
}


def test_linkedin_pdf_and_review_keep_fields_and_provenance():
    source = CareerSource.model_validate(VERSION | {
        "source": PDF, "owner_id": "candidate", "kind": "linkedin_profile_pdf",
        "content_sha256": "a" * 64, "created_at": "2026-11-13T12:00:00Z",
    })
    document = LinkedInDocument.model_validate(VERSION | {
        "source": source.source.model_dump(), "coverage": "uploaded_export_only",
        "raw_text": "  Candidate\nEnglish\n",
        "name": "Candidate", "profile_url": "https://www.linkedin.com/in/example/",
        "location": "New York", "contact_links": ["https://example.com/portfolio"],
        "sections": [
            {"name": "languages", "page": 1, "locator": "page:1:lines:2-2", "text": "English"},
            {"name": "unclassified", "page": 2, "locator": "page:2:lines:2-2", "text": "Other text"},
        ],
        "experience": [{
            "title": "Engineer", "company": "Example", "employment_type": "Full-time",
            "start_date": "2024-02", "end_date": "Present", "location": "New York",
            "description": "Built the API.", "page": 2, "locator": "page:2:lines:3-7",
        }],
    })
    assert document.raw_text == "  Candidate\nEnglish\n"
    assert document.experience[0].locator == "page:2:lines:3-7"
    assert [section.name for section in document.sections] == ["languages", "unclassified"]
    assert LinkedInDocument.model_validate_json(document.model_dump_json()) == document
    review = LinkedInReview.model_validate(REVIEW | {"findings": [
        {"kind": "experience_gap", "explanation": "No Kubernetes example.", "target_requirement_id": "k8s"},
        {"kind": "knowledge_gap", "explanation": "Currently learning.", "target_requirement_id": "linux"},
        {"kind": "consistency_question", "explanation": "Confirm dates.",
         "document_locator": "page:2:lines:3-7", "evidence_revisions": [REF]},
    ]})
    restored = LinkedInReview.model_validate_json(review.model_dump_json())
    assert restored == review
    assert restored.evidence_snapshot_version == 2
    assert restored.model_manifest_id == "manifest-v1"
    assert restored.generated_artifact_ids == ["profile-draft"]


def test_linkedin_missing_confirmed_evidence_must_cite_it():
    finding = {"kind": "missing_confirmed_evidence", "explanation": "Add the API work."}
    with pytest.raises(ValidationError, match="evidence revision"):
        LinkedInReview.model_validate(REVIEW | {"findings": [finding]})
    assert LinkedInReview.model_validate(REVIEW | {"findings": [
        finding | {"evidence_revisions": [REF]},
    ]}).findings[0].evidence_revisions[0].revision == 2


@pytest.mark.parametrize(("model", "payload"), [
    (EvidenceSourceLink, {key: value for key, value in LINK.items() if key != "excerpt"}),
    (EvidenceSourceLink, LINK | {"excerpt_sha256": "a" * 64}),
    (EvidenceSourceLink, LINK | {"excerpt": "  \n"}),
    (CareerEvidenceItem, ITEM | {"lifecycle": "private", "is_private": False}),
    (CareerEvidenceItem, ITEM | {"support": "independently_verified"}),
    (CareerEvidenceItem, ITEM | {"sources": [LINK | {"relationship": "contradicts"}]}),
])
def test_export_and_pydantic_reject_the_same_invalid_evidence(model, payload):
    validator = Draft202012Validator(career_json_schema(model.__name__))
    assert validator.is_valid(LINK if model is EvidenceSourceLink else ITEM)
    assert not validator.is_valid(payload)
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_source_hash_can_replace_raw_excerpt():
    link = LINK | {"excerpt": None, "excerpt_sha256": "a" * 64}
    assert Draft202012Validator(career_json_schema("EvidenceSourceLink")).is_valid(link)
    assert EvidenceSourceLink.model_validate(link).excerpt_sha256 == "a" * 64


def test_cli_exports_a_named_validator_and_bundle_root_cannot_validate_instances():
    bundle = career_json_schema()
    assert not Draft202012Validator(bundle).is_valid({"arbitrary": True})
    output = subprocess.check_output(
        [sys.executable, "-m", "app.schemas.career", "CareerEvidenceItem"], text=True,
    )
    schema = json.loads(output)
    Draft202012Validator.check_schema(schema)
    assert Draft202012Validator(schema).is_valid(ITEM)
    assert not Draft202012Validator(schema).is_valid({"arbitrary": True})


@pytest.mark.parametrize(("decision", "reason"), [
    ("selected", "evidence_private"), ("selected", "page_budget_excluded"), ("blocked", "evidence_private"),
])
def test_selection_rejects_an_ineligible_winner(decision, reason):
    payload = VERSION | {
        "target_id": "backend", "artifact_id": "resume", "evidence": REF,
        "decision": decision, "winning_evidence": REF,
        "ordered_criteria": ["must_have_relevance"], "reason_codes": [reason],
    }
    with pytest.raises(ValidationError, match="winner|winning|ineligible"):
        EvidenceSelectionDecision.model_validate(payload)
    if decision == "selected":
        validator = Draft202012Validator(career_json_schema("EvidenceSelectionDecision"))
        assert not validator.is_valid(payload)
        assert validator.is_valid(payload | {"reason_codes": ["must_have_relevance"]})


@pytest.mark.parametrize(("model", "payload"), [
    (ResumeBulletPlan, PLAN),
    (GeneratedClaimLineage, VERSION | {"claim_id": "bullet", "artifact_id": "resume", "artifact_version": 1}),
])
def test_plan_and_lineage_reject_mixed_revisions(model, payload):
    with pytest.raises(ValidationError, match="one revision"):
        model.model_validate(payload | {"evidence_revisions": [REF, REF | {"revision": 1}]})


def test_metric_requires_a_unit_estimate_status_and_matching_evidence():
    with pytest.raises(ValidationError, match="permitted_numbers"):
        ResumeBulletPlan.model_validate(PLAN | {"permitted_numbers": [30]})
    with pytest.raises(ValidationError, match="estimate|estimated"):
        ResumeBulletPlan.model_validate(PLAN | {"permitted_numbers": [
            {key: value for key, value in METRIC.items() if key != "estimated"},
        ]})
    with pytest.raises(ValidationError, match="evidence"):
        ResumeBulletPlan.model_validate(PLAN | {"permitted_numbers": [METRIC | {"evidence": REF | {"revision": 1}}]})
    plan = ResumeBulletPlan.model_validate(PLAN | {"permitted_numbers": [METRIC]})
    assert plan.permitted_numbers[0].model_dump() == METRIC
    assert ResumeBulletPlan.model_validate_json(plan.model_dump_json()) == plan


@pytest.mark.parametrize("reason", ["model_unavailable", "model_timeout"])
def test_unavailable_renderer_cannot_claim_it_received_a_proposal(reason):
    base = RESULT | {"reason_codes": [reason]}
    assert ResumeRenderValidationResult.model_validate(base).proposal_hash is None
    with pytest.raises(ValidationError, match="proposal"):
        ResumeRenderValidationResult.model_validate(base | {"proposal_hash": "b" * 64})
    with pytest.raises(ValidationError, match="proposal|additions"):
        ResumeRenderValidationResult.model_validate(base | {"disallowed_additions": ["Kubernetes"]})


def test_export_enforces_render_result_states():
    validator = Draft202012Validator(career_json_schema("ResumeRenderValidationResult"))
    absent = RESULT | {"reason_codes": ["model_unavailable"]}
    accepted = RESULT | {"accepted": True, "used_fallback": False, "proposal_hash": "b" * 64}
    assert validator.is_valid(absent)
    assert validator.is_valid(accepted)
    for invalid in (
        absent | {"proposal_hash": "b" * 64},
        absent | {"reason_codes": ["model_unavailable", "evidence_private"]},
        accepted | {"used_fallback": True},
        RESULT | {"reason_codes": ["evidence_private"]},
    ):
        assert not validator.is_valid(invalid)
        with pytest.raises(ValidationError):
            ResumeRenderValidationResult.model_validate(invalid)


@pytest.mark.parametrize("reason", ["evidence_revision_stale", "evidence_private"])
def test_rejected_proposal_can_report_eligibility_failure(reason):
    result = ResumeRenderValidationResult.model_validate(RESULT | {
        "proposal_hash": "b" * 64, "reason_codes": [reason],
    })
    assert result.used_fallback


def test_equivalent_source_timestamps_serialize_to_the_same_bytes():
    payload = VERSION | {
        "source": PDF, "owner_id": "candidate", "kind": "interview_message", "content_sha256": "a" * 64,
    }
    utc = CareerSource.model_validate(payload | {"created_at": "2026-11-13T12:00:00Z"})
    offset = CareerSource.model_validate(payload | {"created_at": "2026-11-13T07:00:00-05:00"})
    assert offset.model_dump_json() == utc.model_dump_json()
    assert json.loads(utc.model_dump_json())["created_at"] == "2026-11-13T12:00:00Z"


def test_export_rejects_missing_linkedin_finding_citations():
    schema = Draft202012Validator(career_json_schema("LinkedInReview"))
    finding = {"kind": "communication_gap", "explanation": "Add the API work."}
    assert schema.is_valid(REVIEW | {"findings": [finding | {"evidence_revisions": [REF]}]})
    assert not schema.is_valid(REVIEW | {"findings": [finding]})
    assert not schema.is_valid(REVIEW | {"findings": [
        {"kind": "unsupported_claim", "explanation": "Check the claim.", "document_locator": "  "},
    ]})


def test_export_rejects_metrics_without_measurement():
    schema = Draft202012Validator(career_json_schema("ResumeBulletPlan"))
    assert schema.is_valid(PLAN | {"permitted_numbers": [METRIC]})
    assert not schema.is_valid(PLAN | {"permitted_numbers": [METRIC], "outcome": {"description": "Outcome"}})
    assert not schema.is_valid(PLAN | {
        "permitted_numbers": [METRIC], "outcome": PLAN["outcome"] | {"measurement_method": "  "},
    })


def test_export_rejects_evidence_proposal_with_contradictory_source():
    turn = VERSION | {
        "question": "What did you build?", "question_intent": "probe",
        "target_evidence_slot": "action", "recommended_action": "continue",
    }
    proposal = {"claim": "Built the API.", "category": "action", "sources": [LINK]}
    validator = Draft202012Validator(career_json_schema("CareerTurnProposal"))
    assert validator.is_valid(turn | {"evidence_proposals": [proposal]})
    bad_link = LINK | {"relationship": "contradicts"}
    assert not validator.is_valid(turn | {"evidence_proposals": [proposal | {"sources": [bad_link]}]})


@pytest.mark.parametrize("timestamp", ["0001-01-01T00:00:00+01:00", "9999-12-31T23:59:59-01:00"])
def test_source_utc_normalization_rejects_out_of_range_timestamps(timestamp):
    with pytest.raises(ValidationError, match="UTC"):
        CareerSource.model_validate(VERSION | {
            "source": PDF, "owner_id": "candidate", "kind": "interview_message",
            "content_sha256": "a" * 64, "created_at": timestamp,
        })



@pytest.mark.parametrize(("model", "valid", "change"), [
    (CareerSource, VERSION | {
        "source": PDF, "owner_id": "candidate", "kind": "resume", "resume_document_id": "resume",
        "content_sha256": "a" * 64, "created_at": "2026-11-13T12:00:00Z",
    }, {"resume_document_id": None}),
    (CareerSource, VERSION | {
        "source": PDF, "owner_id": "candidate", "kind": "interview_message",
        "content_sha256": "a" * 64, "created_at": "2026-11-13T12:00:00Z",
    }, {"resume_document_id": "resume"}),
    (CareerCoverage, VERSION | {
        "session_id": "session", "slots": [{"slot": "action", "status": "confirmed", "evidence_revisions": [REF]}],
    }, {"slots": [{"slot": "action", "status": "confirmed"}]}),
    (ResumeRequirementFinding, VERSION | {
        "finding_id": "finding", "category": "evidence", "severity": "warning", "blocking": False,
        "reason_code": "evidence_not_confirmed", "policy_profile_id": "policy", "rule_version": "v1",
        "source": PDF, "source_locator": "page:1", "explanation": "Clarify ownership.", "next_action": "Ask candidate.",
    }, {"source_locator": None, "evidence_revisions": [REF]}),
])
def test_named_wire_contracts_reject_inconsistent_references(model, valid, change):
    validator = Draft202012Validator(career_json_schema(model.__name__))
    assert validator.is_valid(valid)
    assert not validator.is_valid(valid | change)
    with pytest.raises(ValidationError):
        model.model_validate(valid | change)
