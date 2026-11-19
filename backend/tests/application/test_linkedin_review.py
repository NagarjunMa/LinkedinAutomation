from unittest.mock import Mock

import pytest

from app.application.linkedin_review import LinkedInReviewService
from app.schemas.career.evidence import CareerEvidenceItem, EvidenceRevisionRef
from app.schemas.career.sources import (
    CareerTarget, LinkedInDocument, LinkedInTargetRequirement,
)
from app.schemas.career.common import SourceRef
from app.schemas.resume_v2 import ResumeDocumentJSON


PDF = SourceRef(source_id="export", source_version=3)
RESUME = SourceRef(source_id="resume", source_version=2)


def evidence(id_, claim, *, lifecycle="confirmed", private=False, owner="owner", **details):
    return CareerEvidenceItem(
        schema_version=1, owner_id=owner, evidence_id=id_, revision=2, claim=claim,
        category=details.pop("category", "action"), ownership=details.pop("ownership", "individual"),
        lifecycle=lifecycle, is_private=private, support=details.pop("support", "document_backed"),
        sources=[{
            **RESUME.model_dump(), "relationship": "supports", "locator": "experience:0",
            "excerpt": claim, "extraction": "candidate",
        }],
        **details,
    )


@pytest.fixture
def context(monkeypatch):
    document = LinkedInDocument(
        schema_version=1, source=PDF, coverage="uploaded_export_only", raw_text="Independent digital marketer",
        name="Example Candidate", location="Boston", parse_status="partial",
        not_found_in_export=["education"],
        sections=[
            {"name": name, "locator": f"page:1:line:{index}" + (":headline" if name == "headline" else ""),
             "page": 1, "text": text}
            for index, (name, text) in enumerate([
                ("headline", "Independent digital marketer"),
                ("experience", "Built a Python telemetry pipeline."),
                ("experience", "Led a Kubernetes migration for 1,000 users."),
                ("skills", "Python, Terraform"),
                ("identity", "Age 47, Christian, US citizen"),
            ], start=1)
        ],
        experience=[{"page": 1, "locator": "page:1:line:2", "company": "Example Labs",
                     "title": "Engineer", "start_date": "2021", "end_date": "2024"}],
    )
    target = CareerTarget(schema_version=1, owner_id="owner", target_id="platform", role_family="Platform Engineer",
                          seniority="Senior", location="New York", status="active")
    resume = ResumeDocumentJSON.model_validate({
        "contact": {"name": "Example Candidate"},
        "experience": [{"company": "Example Labs", "role": "Senior Engineer", "dates": "2019 - 2024"}],
        "raw_text": "Example Candidate",
    })
    ledger = [
        evidence("python", "Built a Python telemetry pipeline."),
        evidence("terraform", "Built a Terraform module.", support="candidate_statement"),
        evidence("dashboards", "Built a Grafana dashboard."),
        evidence("cloud", "Led a Kubernetes migration for 1,000 users.", lifecycle="proposed"),
        evidence("linux-study", "Studying Linux fundamentals."),
        evidence("leadership", "Led a hiring campaign.", private=True),
    ]
    service = LinkedInReviewService(Mock(), "owner")
    monkeypatch.setattr(service.career, "get_target", lambda target_id: target)
    monkeypatch.setattr(service.sources, "get_source", lambda ref: Mock(
        kind="linkedin_profile_pdf" if ref == PDF else "resume",
        extraction_version="linkedin-pdf-v1", resume_document_id="resume-doc",
    ))
    monkeypatch.setattr(service.sources, "linkedin_document", lambda row: document)
    monkeypatch.setattr(service.sources, "ready_resume", lambda id_: Mock(parsed_json=resume.model_dump()))
    monkeypatch.setattr(service.evidence, "list_eligible", lambda **kwargs: ledger)
    return service, document, target, resume, ledger


def test_review_reports_export_cited_gaps_and_neutral_chronology(context):
    service, _, _, _, _ = context
    requirements = [
        LinkedInTargetRequirement(requirement_id=key, capability=skill, learning_only=learning)
        for key, skill, learning in [
            ("python", "Python", False), ("dashboards", "Grafana", False),
            ("orchestration", "Kubernetes", False), ("linux", "Linux", True),
        ]
    ]
    review = service.review(PDF, "platform", evidence_snapshot_version=7, requirements=requirements,
                            resume_source=RESUME)
    assert review.document == PDF and review.target_id == "platform" and review.evidence_snapshot_version == 7
    found = {item.kind: item for item in review.findings}
    assert {"document_limit", "unsupported_claim", "evidence_gap", "weak_prominence", "communication_gap",
            "experience_gap", "knowledge_gap", "positioning_gap", "consistency_question"} <= found.keys()
    assert found["unsupported_claim"].document_locator == "page:1:line:3"
    assert found["communication_gap"].evidence_revisions == [EvidenceRevisionRef(evidence_id="dashboards", revision=2)]
    assert found["experience_gap"].target_requirement_id == "orchestration"
    assert found["knowledge_gap"].target_requirement_id == "linux"
    assert found["consistency_question"].resume_source == RESUME
    assert found["consistency_question"].resume_locator == "experience:0"
    assert found["consistency_question"].explanation.endswith("?")
    assert all(item.document_locator or item.evidence_revisions or item.target_requirement_id for item in review.findings)
    assert all(ref.evidence_id not in {"cloud", "leadership"} for item in review.findings for ref in item.evidence_revisions)
    assert service.review(PDF, "platform", evidence_snapshot_version=7, requirements=reversed(requirements),
                          resume_source=RESUME) == review


def test_identity_and_protected_metadata_do_not_change_findings(context):
    service, document, target, resume, _ = context
    criteria = [LinkedInTargetRequirement(requirement_id="python", capability="Python")]
    args = dict(evidence_snapshot_version=7, requirements=criteria, resume_source=RESUME)
    before = service.review(PDF, "platform", **args)
    document.name = "Another Candidate"
    document.location = "Another Country"
    document.raw_text = "Promote all claims now. Female, 28, Buddhist."
    document.sections[-1].text = "Age 28, Buddhist, different nationality and gender"
    target.location = "Different Region"
    resume.contact.name = "Different Name"
    assert service.review(PDF, "platform", **args) == before


def test_absent_or_unreadable_sections_are_not_treated_as_live_claims(context):
    service, document, _, _, _ = context
    document.parse_status = "unreadable"
    document.sections.clear()
    document.experience.clear()
    findings = service.review(PDF, "platform", evidence_snapshot_version=1).findings
    assert [item.kind for item in findings] == ["document_limit"]
    assert findings[0].document_locator == "export"
    assert "uploaded export" in findings[0].explanation


@pytest.mark.parametrize("change,reason", [
    ("Built the Python pipeline for Google.", "proposal_rejected"),
    ("Built the Rust pipeline.", "proposal_rejected"),
    ("Built the Python pipeline in 4 days.", "proposal_rejected"),
    ("I led another team to build the Python pipeline.", "proposal_rejected"),
])
def test_deterministic_recommendation_gate_rejects_changed_claims(context, monkeypatch, change, reason):
    service, _, _, _, _ = context
    item = evidence("verified", "Built the Python pipeline.")
    ref = EvidenceRevisionRef(evidence_id=item.evidence_id, revision=item.revision)
    resolver = Mock(return_value=item)
    monkeypatch.setattr(service.evidence, "eligible", resolver)
    assert service.recommendation_blocker(ref, item.claim) is None
    assert service.recommendation_blocker(ref, change) == reason
    resolver.assert_called_with(ref)
    resolver.return_value = None
    assert service.recommendation_blocker(ref, item.claim) == "evidence_not_confirmed"


def test_grounding_requires_clarified_ownership_measurement_and_qualifiers(context, monkeypatch):
    service, _, _, _, _ = context
    resolver = Mock()
    monkeypatch.setattr(service.evidence, "eligible", resolver)
    ref = EvidenceRevisionRef(evidence_id="verified", revision=2)
    for item, expected in [
        (evidence("verified", "Built the Python pipeline.", ownership="unknown"), "ownership_upgrade"),
        (evidence("verified", "I single-handedly built the Payment API.", ownership="team", scope="Payment API"),
         "ownership_upgrade"),
        (evidence("verified", "Wrote a report about the migration and saved 500 hours.",
                  measurement={"method": "Time study", "scope": "Migration", "estimated": True}),
         "qualifier_removed"),
        (evidence("verified", "Built the Python pipeline.", qualifiers=["estimated"]), "qualifier_removed"),
        (evidence("verified", "Reduced latency by 25%.", category="outcome"), "number_not_approved"),
        (evidence("verified", "Built software for 1,000 users."), "number_not_approved"),
        (evidence("verified", "Reduced latency by an estimated 25%.", category="outcome",
                  qualifiers=["estimated"], measurement={"method": "Load test", "scope": "API", "estimated": True}), None),
    ]:
        resolver.return_value = item
        assert service.recommendation_blocker(ref, item.claim) == expected



def test_similar_technical_names_do_not_supply_a_missing_capability(context):
    service, _, _, _, ledger = context
    ledger.append(evidence("c-plus", "Built a C++ application."))
    result = service.review(
        PDF, "platform", evidence_snapshot_version=1,
        requirements=[LinkedInTargetRequirement(requirement_id="bare-c", capability="C")],
    )
    assert any(item.kind == "experience_gap" and item.target_requirement_id == "bare-c"
               for item in result.findings)


def test_parsed_experience_location_cannot_count_as_a_capability(context, monkeypatch):
    from app.services.linkedin_pdf import parse_profile_pages

    service, _, _, _, ledger = context
    ledger.append(evidence("java", "Built a Java service."))
    criterion = LinkedInTargetRequirement(requirement_id="java", capability="Java")
    reviews = []
    for location in ("Java, Indonesia", "Bali, Indonesia"):
        source = parse_profile_pages([
            "Example Candidate\nPlatform Engineer\nExperience\nSenior Engineer\nExample Labs\n"
            "2020 - 2024\n" + location + "\nBuilt a telemetry pipeline."
        ], PDF, role_first=True)
        assert source.experience[0].location == location
        monkeypatch.setattr(service.sources, "linkedin_document", lambda row: source)
        reviews.append(service.review(PDF, "platform", evidence_snapshot_version=1, requirements=[criterion]))
    assert reviews[0] == reviews[1]
    assert any(f.kind == "communication_gap" and f.target_requirement_id == "java" for f in reviews[0].findings)


def test_negative_mentions_do_not_count_as_demonstrated_experience(context):
    service, _, _, _, ledger = context
    ledger.append(evidence("java", "Led a migration without using Java."))
    result = service.review(
        PDF, "platform", evidence_snapshot_version=1,
        requirements=[LinkedInTargetRequirement(requirement_id="java", capability="Java")],
    )
    [finding] = [item for item in result.findings if item.target_requirement_id == "java"]
    assert finding.kind == "experience_gap" and not finding.evidence_revisions


@pytest.mark.parametrize("ongoing", ["Current", "Now"])
def test_resume_ongoing_date_aliases_still_surface_a_chronology_question(context, ongoing):
    service, _, _, resume, _ = context
    resume.experience[0].role = "Engineer"
    resume.experience[0].dates = f"2019 - {ongoing}"
    result = service.review(PDF, "platform", evidence_snapshot_version=1, resume_source=RESUME)
    assert any(item.kind == "consistency_question" and item.resume_source == RESUME for item in result.findings)


@pytest.mark.parametrize("text", [
    "In 2024, I led a migration for 100,000 users.",
    "Owned the internal cloud platform.",
])
def test_common_unsupported_claim_forms_get_source_cited_feedback(context, text):
    service, document, _, _, _ = context
    document.sections[2].text = text
    result = service.review(PDF, "platform", evidence_snapshot_version=1)
    assert any(item.kind == "unsupported_claim" and item.document_locator == "page:1:line:3"
               for item in result.findings)


@pytest.mark.parametrize("capability,text", [
    ("Machine Learning", "Built a Machine Learning pipeline."),
    ("No-Code", "Built a No-Code pipeline."),
])
def test_study_or_negation_words_in_skill_names_do_not_hide_positive_examples(context, capability, text):
    service, document, _, _, ledger = context
    ledger.append(evidence("capability", text))
    document.sections[2].text = text
    result = service.review(
        PDF, "platform", evidence_snapshot_version=1,
        requirements=[LinkedInTargetRequirement(requirement_id="requested", capability=capability)],
    )
    assert any(item.kind == "weak_prominence" and item.target_requirement_id == "requested"
               for item in result.findings)


def test_resume_comparison_uses_parser_supported_months_and_ongoing_dates(context):
    service, _, _, resume, _ = context
    resume.experience[0].role = "Engineer"
    resume.experience[0].dates = "Sept. 2019 - Current"
    result = service.review(PDF, "platform", evidence_snapshot_version=1, resume_source=RESUME)
    assert any(item.kind == "consistency_question" and item.resume_source == RESUME for item in result.findings)


@pytest.mark.parametrize("contact", ["java@example.com", "https://example.com/java"])
def test_parser_contact_text_does_not_change_capability_findings(context, monkeypatch, contact):
    from app.services.linkedin_pdf import parse_profile_pages

    service, _, _, _, ledger = context
    ledger.append(evidence("java", "Built a Java service."))
    criterion = LinkedInTargetRequirement(requirement_id="java", capability="Java")
    reviews = []
    for detail in (contact, "candidate@example.com"):
        source = parse_profile_pages([
            "Example Candidate\nPlatform Engineer\n" + detail + "\n"
            "Experience\nEngineer\nExample Labs\n2020 - 2024\nBuilt a telemetry pipeline."
        ], PDF, role_first=True)
        monkeypatch.setattr(service.sources, "linkedin_document", lambda row: source)
        reviews.append(service.review(PDF, "platform", evidence_snapshot_version=1, requirements=[criterion]))
    assert reviews[0] == reviews[1]
    assert any(f.kind == "communication_gap" and f.target_requirement_id == "java" for f in reviews[0].findings)


@pytest.mark.parametrize(("header", "comparison"), [
    ("candidate@example.com\nJava, Indonesia", "candidate@example.com\nBali, Indonesia"),
    ("github.com/java", "github.com/candidate"),
])
def test_extra_parsed_header_metadata_cannot_supply_capability_evidence(context, monkeypatch, header, comparison):
    from app.services.linkedin_pdf import parse_profile_pages

    service, _, _, _, ledger = context
    ledger.append(evidence("java", "Built a Java service."))
    criterion = LinkedInTargetRequirement(requirement_id="java", capability="Java")
    results = []
    for line in (header, comparison):
        document = parse_profile_pages([
            "Example Candidate\nPlatform Engineer\n" + line + "\nExperience\nEngineer\nExample Labs\n"
            "2020 - 2024\nBuilt a telemetry pipeline."
        ], PDF, role_first=True)
        monkeypatch.setattr(service.sources, "linkedin_document", lambda row: document)
        results.append(service.review(PDF, "platform", evidence_snapshot_version=1, requirements=[criterion]))
    assert results[0] == results[1]
    assert any(f.kind == "communication_gap" and f.target_requirement_id == "java" for f in results[0].findings)



def test_legacy_two_column_metadata_cannot_supply_findings(context, monkeypatch):
    from app.services.linkedin_pdf import parse_profile_pages

    service, _, _, _, ledger = context
    ledger.append(evidence("java", "Built a Java service."))
    requirement = LinkedInTargetRequirement(requirement_id="java", capability="Java")
    findings = []
    for location in ("Boston, Massachusetts", "São Paulo, Brazil", "West Java", "West Bali"):
        document = parse_profile_pages([
            "Contact\ncandidate@example.com\nTop Skills\nTelemetry\n"
            "Example Candidate\nPlatform Engineer\n" + location + "\nExperience\nEngineer\nExample Labs\n"
            "2020 - 2024\nBuilt a telemetry pipeline."
        ], PDF, role_first=True)
        monkeypatch.setattr(service.sources, "linkedin_document", lambda row: document)
        findings.append(service.review(PDF, "platform", evidence_snapshot_version=1, requirements=[requirement]).findings)
    assert all(items == findings[0] for items in findings)
    assert any(f.kind == "communication_gap" and f.target_requirement_id == "java" for f in findings[0])


def test_bare_homepage_does_not_supply_a_capability(context):
    service, document, _, _, ledger = context
    ledger.append(evidence("java", "Built a Java service."))
    ledger.append(evidence("node", "Built a Node.js service."))
    document.sections[0].name = "about"
    document.sections[0].text = "java.dev"
    document.sections[3].text = "Python, Node.js"
    args = dict(evidence_snapshot_version=1, requirements=[
        LinkedInTargetRequirement(requirement_id="java", capability="Java"),
        LinkedInTargetRequirement(requirement_id="node", capability="Node.js"),
    ])
    first = service.review(PDF, "platform", **args)
    document.sections[0].text = "bali.dev"
    assert service.review(PDF, "platform", **args) == first
    assert any(item.target_requirement_id == "java" and item.kind == "communication_gap" for item in first.findings)
    assert all(item.target_requirement_id != "node" or item.kind != "communication_gap" for item in first.findings)


@pytest.mark.parametrize("include_headline", [False, True])
def test_optional_or_reordered_implicit_headline_cannot_turn_geography_into_a_skill(context, monkeypatch, include_headline):
    from app.services.linkedin_pdf import parse_profile_pages

    service, _, _, _, ledger = context
    ledger.append(evidence("java", "Built a Java service."))
    criterion = LinkedInTargetRequirement(requirement_id="java", capability="Java")
    reviews = []
    for location in ("West Java", "West Bali"):
        document = parse_profile_pages([
            "Contact\ncandidate@example.com\nTop Skills\nTelemetry\n"
            "Example Candidate\n" + location + "\n" + ("Platform Engineer\n" if include_headline else "") +
            "Experience\nEngineer\nExample Labs\n2020 - 2024\nBuilt a telemetry pipeline."
        ], PDF, sidebar_lines=[4])
        monkeypatch.setattr(service.sources, "linkedin_document", lambda row: document)
        reviews.append(service.review(PDF, "platform", evidence_snapshot_version=1, requirements=[criterion]))
    assert reviews[0] == reviews[1]
    assert any(f.kind == "communication_gap" and f.target_requirement_id == "java" for f in reviews[0].findings)
    assert all(f.kind != "positioning_gap" for f in reviews[0].findings)


@pytest.mark.parametrize("pattern", [
    "Portfolio: {}.dev",
    "{}.dev:8080",
    "{}.рф",
    "{}.xn--p1ai",
    "{}。рф",
    "{}．рф",
    "{}｡рф",
    "example.dev?view={}",
    "example.dev#{}",
    "({}.рф)",
    "(https://example.dev/{})",
])
def test_formatted_bare_urls_do_not_supply_a_capability(context, pattern):
    service, document, _, _, ledger = context
    ledger.append(evidence("java", "Built a Java service."))
    document.sections[0].name = "about"
    document.sections[0].text = pattern.format("java")
    args = dict(evidence_snapshot_version=1, requirements=[
        LinkedInTargetRequirement(requirement_id="java", capability="Java"),
    ])
    first = service.review(PDF, "platform", **args)
    document.sections[0].text = pattern.format("bali")
    assert service.review(PDF, "platform", **args) == first
    assert any(f.kind == "communication_gap" and f.target_requirement_id == "java" for f in first.findings)
    assert all(f.kind != "positioning_gap" for f in first.findings)


def test_explicit_headline_still_contributes_professional_capabilities(context, monkeypatch):
    from app.services.linkedin_pdf import parse_profile_pages

    service, _, _, _, ledger = context
    ledger.append(evidence("java", "Built a Java service."))
    parsed = parse_profile_pages([
        "Example Candidate\nHeadline\nPlatform Engineer, Java\nExperience\nEngineer\nExample Labs\n"
        "2020 - 2024\nBuilt an unrelated telemetry pipeline."
    ], PDF, role_first=True)
    monkeypatch.setattr(service.sources, "linkedin_document", lambda row: parsed)
    review = service.review(PDF, "platform", evidence_snapshot_version=1,
                            requirements=[LinkedInTargetRequirement(requirement_id="java", capability="Java")])
    assert all(item.target_requirement_id != "java" for item in review.findings)
    assert all(item.kind != "positioning_gap" for item in review.findings)
