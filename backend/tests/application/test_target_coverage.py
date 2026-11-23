from app.application.target_coverage import project_target_coverage, project_target_resume_coverage
from app.schemas.career.evidence import CareerEvidenceItem
from app.schemas.career.sources import CareerTarget
from app.schemas.resume_v2 import Bullet, Contact, ExperienceEntry, ProjectEntry, ResumeDocumentJSON


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



def test_resume_comparison_accepts_any_displayed_eligible_application_without_changing_the_winner():
    chosen = target("Python", "Go", "Rust")
    ledger = [
        evidence("a-python", "Used Python to deploy a service."),
        evidence("z-python", "Used Python to write tests."),
        evidence("go", "Used Go to build a scoring service."),
        evidence("go-private", "Used Go to build a private service.", is_private=True),
        evidence("rust", "I am learning Rust.", category="skill"),
        evidence("rust-proposed", "Used Rust to build a CLI.", lifecycle="proposed"),
    ]
    resume = ResumeDocumentJSON(
        contact=Contact(name="Synthetic candidate"),
        raw_text="Used Go to build a scoring service.",
        experience=[ExperienceEntry(
            company="Used Go to build a scoring service.", role="Engineer", bullets=[
                Bullet(id="private", text="Used Go to build a private service.", raw_text="Ignored"),
                Bullet(id="proposed", text="Used Rust to build a CLI.", raw_text="Ignored"),
            ],
        )],
        projects=[ProjectEntry(
            name="Testing helper",
            bullets=[Bullet(id="displayed", text="• used PYTHON  to write tests!", raw_text="Ignored")],
        )],
    )

    view = project_target_resume_coverage(chosen, ledger, "resume", resume)
    assert view == project_target_resume_coverage(chosen, reversed(ledger), "resume", resume)
    assert view.coverage == project_target_coverage(chosen, ledger)
    assert view.coverage.focus[0].evidence.evidence_id == "a-python"
    assert view.coverage.focus[2].state == "knowledge_gap"
    [gap] = view.findings
    assert gap.focus_label == "Go" and gap.evidence.evidence_id == "go"


def test_resume_comparison_reports_document_limit_for_punctuation_only_bullets():
    resume = ResumeDocumentJSON(
        contact=Contact(name="Synthetic candidate"),
        raw_text="—",
        experience=[ExperienceEntry(
            company="Example", role="Engineer",
            bullets=[Bullet(id="separator", text="—", raw_text="• —")],
        )],
    )
    view = project_target_resume_coverage(
        target("Python"), [evidence("python", "Used Python to build tests.")], "resume", resume,
    )
    [finding] = view.findings
    assert finding.kind == "document_limit" and finding.evidence is None


def test_scope_calibration_uses_recorded_scope_without_assigning_a_candidate_level():
    chosen = target("Python", "Go", "Rust", "Java")
    ledger = [
        evidence("a", "Used Python to test a component.", scope="Component"),
        evidence("b", "Used Python to coordinate a migration.", scope="Cross-team"),
        evidence("c", "Used Go to ship a change.", scope="Organization"),
        evidence("d", "Used Rust to build a CLI.", scope="Team"),
        evidence("e", "Used Java to write tests.", scope="At an organization of thousands"),
    ]
    view = project_target_coverage(chosen, ledger, required_scope="cross_team")
    assert project_target_coverage(chosen, reversed(ledger), required_scope="cross_team") == view
    assert view.policy_version == "target-coverage-v2"
    assert view.details.target_level == "senior"
    assert view.details.required_scope == "cross_team"
    assert [focus.scope.state for focus in view.details.focus] == [
        "meets_requirement", "meets_requirement", "below_requirement", "unavailable",
    ]
    assert [focus.scope.observed_scope for focus in view.details.focus] == [
        "cross_team", "organization", "team", None,
    ]
    python = view.details.focus[0]
    assert python.selection.selected.evidence_id == view.focus[0].evidence.evidence_id == "b"
    assert python.selection.reason_code == "scope_meets_requirement"
    assert python.selection.alternatives[0].evidence.evidence_id == "a"
    assert python.selection.alternatives[0].reason_code == "scope_meets_requirement"
    assert "At an organization" not in view.model_dump_json()
    legacy = project_target_coverage(chosen, ledger).model_dump(exclude_unset=True)
    assert legacy["policy_version"] == "target-coverage-v1" and "details" not in legacy
    assert legacy["focus"][0]["evidence"]["evidence_id"] == "a"


def test_selection_explanations_describe_priority_and_ties_without_ineligible_references():
    chosen = target("Python", "Go", "Rust")
    ledger = [
        evidence("b", "Used Python to build a CLI.", scope="Team"),
        evidence("a", "Used Python to parse records."),
        evidence("c", "Python", category="skill"),
        evidence("private", "Used Python to deploy a service.", is_private=True),
        evidence("foreign", "Used Python to deploy a service.", owner_id="other"),
        evidence("proposed", "Used Python to deploy a service.", lifecycle="proposed"),
        evidence("same-team", "Used Go to build a CLI.", ownership="team", scope="Organization"),
    ]
    view = project_target_coverage(chosen, ledger, explain=True)
    python, go, rust = view.details.focus
    assert python.scope.state == "requirement_unspecified"
    assert python.selection.selected.model_dump() == {"evidence_id": "a", "revision": 3}
    assert python.selection.reason_code == "stable_id_tiebreak"
    assert [(item.evidence.evidence_id, item.reason_code) for item in python.selection.alternatives] == [
        ("b", "stable_id_tiebreak"), ("c", "coverage_signal_priority"),
    ]
    assert go.selection.reason_code == "only_matching_evidence"
    assert go.scope.observed_scope is None
    assert rust.selection.reason_code == "no_matching_evidence"
    assert rust.selection.selected is None
    for identifier in ("private", "foreign", "proposed"):
        assert f'"{identifier}"' not in view.model_dump_json()


def test_comparison_keeps_other_eligible_bullets_and_explains_only_displayed_competitors():
    chosen = target("Python").model_copy(update={"seniority": "Lead Platform Engineer"})
    ledger = [
        evidence(f"match-{index:02}", "Used Python to build a CLI.", scope="Component")
        for index in range(15)
    ]
    ledger.append(evidence("winner", "Used Python to coordinate releases.", scope="Cross team"))
    resume = ResumeDocumentJSON(
        contact=Contact(name="Synthetic candidate"),
        raw_text="",
        projects=[ProjectEntry(name="CLI", bullets=[
            Bullet(id="cli", text="Used Python to build a CLI.", raw_text="Used Python to build a CLI."),
        ])],
    )
    view = project_target_resume_coverage(chosen, ledger, "resume", resume, required_scope="cross_team")
    assert view.findings == []
    assert view.coverage.details.target_level is None
    [focus] = view.coverage.details.focus
    assert focus.scope.observed_scope == "cross_team"
    assert focus.selection.alternative_count == 15
    assert [option.evidence.evidence_id for option in focus.selection.alternatives] == [
        "match-00", "match-01", "match-02", "match-03", "match-04",
    ]
    assert view.coverage == project_target_coverage(chosen, reversed(ledger), required_scope="cross_team")
