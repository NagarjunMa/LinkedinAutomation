import pytest

from app.application.target_defensibility import project_target_defensibility
from app.schemas.career.evidence import CareerEvidenceItem
from app.schemas.career.jd_mapping import TargetJDMapping


@pytest.fixture
def mapping():
    return TargetJDMapping(
        schema_version=1, policy_version="jd-mapping-v1", target_id="target",
        jd_evaluation_id="evaluation", jd_source=None, jd_text_sha256="a" * 64,
        resume_document_id="resume", resume_comparable=True,
        requirements=[{
            "requirement": {
                "requirement_id": "must_have-1", "revision": "b" * 64, "source_start": 0, "source_end": 6,
            },
            "priority": "must_have", "kind": "technical", "state": "supported",
            "reason_code": "confirmed_application", "follow_up": None,
            "evidence": {"evidence_id": "proof", "revision": 2},
        }],
    )


@pytest.fixture
def claim():
    return CareerEvidenceItem(
        schema_version=1, evidence_id="proof", revision=2, owner_id="owner",
        claim="Used Python to test a scheduler.", category="validation", ownership="team",
        lifecycle="confirmed", support="candidate_statement",
        sources=[{
            "source_id": "note", "source_version": 1, "relationship": "supports",
            "locator": "Synthetic School A", "excerpt": "Synthetic candidate A",
            "extraction": "candidate",
        }],
    )


@pytest.mark.parametrize("changes", [
    {"owner_id": "peer"}, {"revision": 3}, {"is_private": True}, {"lifecycle": "proposed"},
])
def test_missing_current_eligible_revision_cannot_display_a_claim(mapping, claim, changes):
    result = project_target_defensibility("owner", mapping, [claim.model_copy(update=changes)])
    assert result.guidance == "review_required_gaps"
    [row] = result.requirements
    assert row.requirement == mapping.requirements[0].requirement
    assert row.state == "unresolved"
    assert row.claim is None
    assert row.unknowns == ["evidence"]


def test_only_cited_facts_affect_guidance_and_questions(mapping, claim):
    report = project_target_defensibility("owner", mapping, [claim])
    other_source = claim.sources[0].model_copy(update={"locator": "Synthetic School B", "excerpt": "Synthetic candidate B"})
    assert report == project_target_defensibility("owner", mapping, [claim.model_copy(update={"sources": [other_source]})])
    assert report.guidance == "prepare_with_evidence"
    [row] = report.requirements
    assert row.claim.evidence == mapping.requirements[0].evidence
    assert row.claim.ownership == "team"
    assert row.claim.support == "candidate_statement"
    assert row.unknowns == ["measurement"]
    assert row.questions == [
        "What did you personally deliver, and who contributed to the rest?",
        "What outcome can you substantiate, and how would you measure it?",
    ]
    assert "Synthetic candidate" not in report.model_dump_json()
