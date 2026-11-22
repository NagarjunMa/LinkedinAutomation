from app.application.target_coverage import project_target_coverage
from app.schemas.career.evidence import CareerEvidenceItem
from app.schemas.career.sources import CareerTarget


def evidence(evidence_id, claim, *, category="action", **overrides):
    return CareerEvidenceItem.model_validate({
        "schema_version": 1, "evidence_id": evidence_id, "revision": 3, "owner_id": "owner",
        "claim": claim, "category": category, "ownership": "individual",
        "lifecycle": "confirmed", "support": "candidate_statement",
        "sources": [{
            "source_id": "source", "source_version": 1, "locator": "chars:0-14", "excerpt": claim,
            "relationship": "supports", "extraction": "candidate",
        }],
        **overrides,
    })


def target(*focus):
    return CareerTarget(
        schema_version=1, owner_id="owner", target_id="platform", role_family="Platform Engineer",
        seniority="Senior", status="active", desired_work=list(focus),
    )


def test_coverage_separates_application_scope_learning_and_missing_evidence():
    chosen = target("Python", "python.", "Ruby", "Go", "Docker", "Terraform", "Rust", "Java", "JavaScript",
                    "Learning Analytics", "Analytics")
    ledger = [
        evidence("z-python", "Used Python to deploy a service."),
        evidence("a-python", "Used Python to write tests."),
        evidence("ruby", "Ruby", category="skill"),
        evidence("go", "I am studying Go.", category="skill"),
        evidence("docker", "Used Docker to make test images.", ownership="team", scope="Team effort"),
        evidence("terraform", "I used Terraform to configure the network module.", ownership="shared"),
        evidence("rust", "Used Rust to build a CLI.", lifecycle="proposed"),
        evidence("java-private", "Used Java to build a report.", is_private=True),
        evidence("java-foreign", "Used Java to build a service.", owner_id="other"),
        evidence("mention", "Built a tutorial about using JavaScript."),
        evidence("analytics", "Learning Analytics", category="skill"),
    ]
    snapshot = [entry.model_dump() for entry in ledger]
    actual = project_target_coverage(chosen, ledger)
    assert project_target_coverage(chosen, reversed(ledger)) == actual
    assert [entry.model_dump() for entry in ledger] == snapshot
    assert [field.label for field in actual.focus] == [
        "Python", "Ruby", "Go", "Docker", "Terraform", "Rust", "Java", "JavaScript", "Learning Analytics", "Analytics",
    ]
    assert [(f.state, f.reason_code, f.evidence.evidence_id if f.evidence else None) for f in actual.focus] == [
        ("supported", "confirmed_application", "a-python"),
        ("evidence_gap", "skill_without_application", "ruby"),
        ("knowledge_gap", "learning_only", "go"),
        ("evidence_gap", "application_scope_unclear", "docker"),
        ("supported", "confirmed_application", "terraform"),
        ("experience_gap", "no_matching_confirmed_evidence", None),
        ("experience_gap", "no_matching_confirmed_evidence", None),
        ("experience_gap", "no_matching_confirmed_evidence", None),
        ("evidence_gap", "skill_without_application", "analytics"),
        ("experience_gap", "no_matching_confirmed_evidence", None),
    ]
    assert actual.focus[0].evidence.revision == 3
    assert actual.focus[0].evidence_support == "candidate_statement"
    assert actual.focus[5].evidence_support is None


def test_target_summary_ignores_prestige_and_personal_metadata():
    chosen = target("Python")
    original = [evidence("candidate", "Used Python to deploy a service.")]
    variant = [evidence("candidate", "Used Python to deploy a service at a prestigious employer.",
                        qualifiers=["identity metadata"], confidence="high")]
    altered = chosen.model_copy(update={"role_family": "Executive", "seniority": "Principal", "location": "London"})
    assert project_target_coverage(chosen, original) == project_target_coverage(altered, variant)
    empty = project_target_coverage(target(), original)
    assert empty.focus == [] and empty.positioning_reason == "target_focus_missing"


def test_generic_team_scope_cannot_upgrade_coverage():
    claim = "Used Python to deploy a service."
    baseline = evidence("candidate", claim, ownership="team")
    with_prestige = evidence("candidate", claim, ownership="team", scope="Prestigious Employer")
    assert project_target_coverage(target("Python"), [baseline]) == project_target_coverage(
        target("Python"), [with_prestige],
    )


def test_learning_analytics_is_a_literal_skill_label():
    view = project_target_coverage(target("Learning Analytics", "Analytics"), [
        evidence("learning-analytics", "Learning Analytics", category="skill"),
    ])
    assert [area.reason_code for area in view.focus] == [
        "skill_without_application", "no_matching_confirmed_evidence",
    ]
