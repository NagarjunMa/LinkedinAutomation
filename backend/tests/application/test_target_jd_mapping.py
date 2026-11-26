from hashlib import sha256

import pytest

from app.application.errors import InvalidOperationError
from app.application.target_jd_mapping import project_target_jd_mapping
from app.schemas.career.evidence import CareerEvidenceItem
from app.schemas.career.sources import CareerTarget
from app.schemas.jd import JDExtraction, Requirement


@pytest.fixture
def project():
    target = CareerTarget(
        schema_version=1, owner_id="owner", target_id="target", role_family="Engineer",
        seniority="Senior", status="active",
    )
    claim = "Used Python to build a deployment checker."
    evidence = CareerEvidenceItem(
        schema_version=1, evidence_id="python", revision=2, owner_id="owner", claim=claim,
        category="action", ownership="individual", lifecycle="confirmed", support="candidate_statement",
        sources=[{
            "source_id": "record", "source_version": 1, "locator": "fixture", "excerpt": claim,
            "relationship": "supports", "extraction": "candidate",
        }],
    )

    def map_jd(job_description, quote, skill="Python", *, additional_requirements=(), evidence_skill="Python"):
        extraction = JDExtraction(
            must_have=[Requirement(skill=skill, evidence_from_jd=quote, type="technical")],
            good_to_have=[
                Requirement(skill=label, evidence_from_jd=excerpt, type="technical")
                for label, excerpt in additional_requirements
            ],
            seniority="senior", primary_role_category="SWE", country_hint="US",
        )
        matching_evidence = evidence if evidence_skill == "Python" else evidence.model_copy(
            update={"claim": f"Used {evidence_skill} to build a deployment checker."},
        )
        return project_target_jd_mapping(
            target, [matching_evidence], evaluation_id="evaluation", jd_text=job_description,
            jd_text_sha256=sha256(job_description.encode()).hexdigest(), extraction=extraction,
            resume_document_id="resume", resume=None,
        )

    return map_jd


@pytest.mark.parametrize(("job_description", "quote", "state", "grounded"), [
    ("CPython / python", "Python", "unresolved", False),
    ("We do not require:\n- Python", "Python", "unresolved", True),
    ("We do not require\n- Python", "Python", "unresolved", True),
    ("Required skills:\nOur team uses Python in a legacy product.", "Python", "unresolved", True),
    ("At least three years of\nPython", "Python", "partial", True),
    ("Python?", "Python", "unresolved", True),
    ("Is Python required?", "Python", "unresolved", True),
    ("Python or Java", "Python", "unresolved", True),
    ("Our team uses Python in a legacy product.", "Python", "unresolved", True),
    ("Requirements:\n- Python", "Python", "supported", True),
    ("Required Skills:\nWe do not require these skills\nPython\n\nApply via the careers portal.",
     "Python", "unresolved", True),
    ("Required Skills:\nWe do not require these skills\nJava\nPython\n\nApply via the careers portal.",
     "Python", "unresolved", True),
    ("Requirements:\n- Choose one of these skills:\n  - Python\n  - Java\n\nApply via the careers portal.",
     "Python", "unresolved", True),
    ("Requirements:\n- Choose one of these skills:\n\n  - Python\n  - Java",
     "Python", "unresolved", True),
    ("Required skills:\nWe do not require these skills\n\nPython",
     "Python", "unresolved", True),
    ("Requirements:\n- Choose one of these skills:\n  - Technical skills:\n    - Python\n    - Java",
     "Python", "unresolved", True),
    ("Requirements:\n- Technical skills:\n  - Python\n  - Java",
     "Python", "supported", True),
    ("Requirements:\n- Choose one of these tracks:\n  Technical skills:\n    - Python\n    - Java",
     "Python", "unresolved", True),
    ("Requirements:\nWe do not require these skills:\n  Technical skills:\n  Python\n  Java",
     "Python", "unresolved", True),
    ("Requirements:\n- Python required\n  - Unless you have equivalent Java experience.",
     "Python", "unresolved", True),
    ("Requirements:\n- Python required\n\n  - Unless you have equivalent Java experience.",
     "Python", "unresolved", True),
    ("Requirements:\n- Python required\n\n  unless you have equivalent Java experience.",
     "Python", "unresolved", True),
    ("Requirements:\n- Python required\n\n- Either Go or Java",
     "Python", "supported", True),
    ("Requirements:\n- Python required\n\n  Exceptions:\n  - Unless you have equivalent Java experience.",
     "Python", "unresolved", True),
    ("Requirements:\n- Python required\n\n  ### Exceptions\n  - Unless you have equivalent Java experience.",
     "Python", "unresolved", True),
    ("Requirements:\n- Python required\n\nExceptions:\n- Java",
     "Python", "supported", True),
    ("Requirements:\n  Optional skills:\n  Either Go or Java\n  Technical skills:\n  Python",
     "Python", "supported", True),
    ("Requirements:\n- Either Go or Java\n- Python",
     "Python", "supported", True),
    ("Minimum Requirements:\n- Python", "Python", "supported", True),
    ("Python\nisn't required.", "Python", "unresolved", True),
    ("Python\nisn’t required.", "Python", "unresolved", True),
    ("We do not require these skills\n- Python", "Python", "unresolved", True),
    ("One of these required skills\n- Python\n- Java", "Python", "unresolved", True),
    ("Required skills (choose 1):\n- Python\n- Go", "Python", "unresolved", True),
    ("Python.\nAnd candidates should have three years of experience in Go", "Python", "supported", True),
    ("We don't require:\n- Python", "Python", "unresolved", True),
    ("Python isn’t required", "Python", "unresolved", True),
    ("Python\nis not required.", "Python", "unresolved", True),
    ("Requirements:\n- Python\n  Minimum three years of production experience.", "Python", "partial", True),
    ("Advanced proficiency in:\n- Python", "Python", "partial", True),
    ("One of these required skills:\n- Python\n- Java", "Python", "unresolved", True),
    ("💼\nPython", "Python", "supported", True),
    ("Responsibilities:\n- Python", "Python", "unresolved", True),
    ("At least three years of experience with:\n- Python", "Python", "partial", True),
    ("Python required", "Python", "supported", True),
    ("Requirements:\n- Python required\nunless you have equivalent Java experience.", "Python", "unresolved", True),
    ("Requirements:\n- Python required\n  unless you have equivalent Java experience.", "Python", "unresolved", True),
    ("Requirements:\nPython\n/ Java", "Python", "unresolved", True),
    ("Requirements:\n- Python required\n(unless you have equivalent Java experience).", "Python", "unresolved", True),
    ("Requirements:\n- Python\n— or equivalent Java experience.", "Python", "unresolved", True),
    ("Requirements:\n- Python required\nunless you have:\n- A Java certification", "Python", "unresolved", True),
    ("Requirements:\nPython\nfor production machine learning deployments.", "Python", "partial", True),
])
def test_only_grounded_affirmative_job_requirements_map_to_used_skills(project, job_description, quote, state, grounded):
    result = project(job_description, quote)
    [item] = result.requirements
    assert item.state == state
    if grounded:
        assert job_description[item.requirement.source_start:item.requirement.source_end] == quote
    else:
        assert item.requirement.source_start is None and item.requirement.source_end is None
    if state == "unresolved":
        assert item.evidence is None
    else:
        assert item.evidence.model_dump() == {"evidence_id": "python", "revision": 2}


@pytest.mark.parametrize(("jd", "expected"), [
    ("# Qualifications\n## We do not require these skills\n### Technical skills\n- Python", "unresolved"),
    ("# Qualifications\n## Choose one of these tracks\n### Technical skills\n- Python", "unresolved"),
    ("# Qualifications\n## Choose **one** of these tracks\n### Technical skills\n- Python", "unresolved"),
    ("# Qualifications\n## Choose one of these tracks\n1. Technical skills\n   ## Required skills\n   - Python",
     "unresolved"),
    ("# We do not require these skills\n- Technical skills\n  # Required skills\n  - Python", "unresolved"),
    ("## Required skills\n+ Choose one of these tracks\n  ### Technical skills\n  - Python", "unresolved"),
    ("## Required skills\n+ We do not require these skills\n  ### Technical skills\n  - Python", "unresolved"),
    ("# Qualifications\n## We do not require these skills\nTechnical skills:\n- Python", "unresolved"),
    ("  ## We do not require these skills\n### Technical skills\n- Python", "unresolved"),
    ("Requirements:\n- Choose one of these tracks:\n  ### Technical skills\n    - Python", "unresolved"),
    ("# Qualifications\n## Technical skills\n### Required skills\n- Python", "supported"),
    ("# Senior Platform Engineer\n## Technical skills\n- Python", "supported"),
    ("# Engineering role\n## Skills by domain\n### Technical skills\n- Python", "supported"),
    ("# We do not require the following\n## Technical skills\n- Python", "unresolved"),
    ("# Qualifications\n## Experience with Python/Java\n### Technical skills\n- Python", "unresolved"),
    ("# Qualifications\n## Choose one of these tracks\n### Technical skills\n- Java\n"
     "## Required skills\n### Technical skills\n- Python", "supported"),
    ("# Qualifications\n## Requirements\n### Python is not required elsewhere\n- Java\n"
     "### Technical skills\n- Python", "supported"),
    ("# Qualifications\n- Other track\n  ### We do not require these skills\n  - Java\n- Python", "supported"),
    ("# Qualifications\n1. Other track\n   ### We do not require these skills\n   - Java\n\n- Python", "supported"),
    ("# Qualifications\n## We do not require these skills\n1. Technical skills\n   - Java\n\n"
     "  ## Required skills\n  - Python", "supported"),
    ("# Qualifications\n- Technical skills\n  (choose one of these)\n\n  ### Technical skills\n  - Python",
     "unresolved"),
    ("# Qualifications\n- Technical skills\n  We do not require these skills\n\n  ### Technical skills\n  - Python",
     "unresolved"),
    ("# Qualifications\n- Technical skills\n  ### Other skills\n  We do not require Java\n\n"
     "  ### Technical skills\n  - Python", "supported"),
    ("# Qualifications ###\n## We do not require these skills ##\n### Technical skills ###\n- Python", "unresolved"),
    ("# Qualifications\n## We do not require these skills\n### Technical skills\n- Java\n"
     "##\n### Technical skills\n- Python", "supported"),
])
def test_markdown_heading_ancestry_preserves_governing_scope(project, jd, expected):
    quote = "- Python"
    [item] = project(jd, quote).requirements
    assert item.state == expected
    assert (item.evidence is not None) == (expected == "supported")
    assert jd[item.requirement.source_start:item.requirement.source_end] == quote


@pytest.mark.parametrize("jd", [
    "Experience with Python/Java",
    "Experience with Java/Python",
    "Experience with Python／Java",
    "Experience with Java／Python",
    "Experience with Python 3/Java 17",
    "Experience with Python 3／Java 17",
    "Experience with Python v3.11/Java 17",
    "Experience with Python 3.x/Java 17",
    "Experience with Python 3.*/Java 17",
    "Experience with Python >=3.11/Java 17",
    "Experience with Python **v3.11**/Java 17",
    "Experience with Python\n  3.11/Java 17",
    "Experience with Python\n3.11/Java 17",
    "Experience with Python version 3/Java 17",
    "Experience with Python v3.11-beta/Java 17",
    "Experience with Python 3.11–3.12/Java 17",
    "Experience with Python 3.11 (latest)/Java 17",
    "Experience with Python v3.11.0+cpu/Java 17",
    "Experience with Java/experience with Python",
    "Experience with Java／(**experience with** Python)",
    "Experience with Python\n with v3.11/Java 17",
    "Experience with Python\n3.11\n/ Java 17",
    "Experience with **Python**/**Java**",
    "Experience with (Python)/(Java)",
    "Requirements:\nPython\n／ Java",
    "Requirements:\n- Python\n  ／ Java",
    "Requirements:\n- Python\n  **/ Java**",
    "Requirements:\nPython／\nJava",
    "Experience with Java／\nPython",
    "Experience with Java/\nExperience with Python",
    "Proficiency in Java 17／\nProficiency in Python 3.11",
    "Experience with Java／\n- Python",
    "Requirements:\n- Java/\n  - Python",
    "Experience with Python / Java",
])
def test_slash_alternatives_do_not_attach_evidence(project, jd):
    [item] = project(jd, "Python").requirements
    assert item.state == "unresolved"
    assert item.reason_code == "requirement_not_affirmative"
    assert item.evidence is None
    assert jd[item.requirement.source_start:item.requirement.source_end] == "Python"


@pytest.mark.parametrize("separator", [" ", "\n"])
def test_version_release_label_can_precede_a_slash_alternative(project, separator):
    jd = f"Experience with Java{separator}17 LTS/Kotlin 2"
    [item] = project(jd, "Java", "Java", evidence_skill="Java").requirements
    assert item.state == "unresolved"
    assert item.reason_code == "requirement_not_affirmative"
    assert item.evidence is None


def test_literal_compound_skill_can_be_supported(project):
    [item] = project("Experience with CI/CD", "CI/CD", "CI/CD", evidence_skill="CI/CD").requirements
    assert item.state == "supported"
    assert item.evidence is not None


def test_unknown_slash_label_is_ambiguous_even_with_an_exact_evidence_label(project):
    [item] = project("Experience with Python/Java", "Python/Java", "Python/Java", evidence_skill="Python/Java").requirements
    assert item.state == "unresolved"
    assert item.reason_code == "requirement_not_affirmative" and item.evidence is None


def test_slash_at_end_of_separate_list_item_does_not_block_next_requirement(project):
    jd = "Requirements:\n- Read the documentation at https://example.test/\n- Python"
    [item] = project(jd, "Python").requirements
    assert item.state == "supported"


def test_trailing_url_slash_does_not_continue_into_next_requirement(project):
    jd = "Read the documentation at https://example.test/\nExperience with Python"
    [item] = project(jd, "Python").requirements
    assert item.state == "supported"


def test_blank_line_ends_wrapped_slash_context(project):
    jd = "Experience with Java/\n\nExperience with Python"
    [item] = project(jd, "Python").requirements
    assert item.state == "supported"
    assert item.evidence is not None


@pytest.mark.parametrize("slash", ["/", "／"])
def test_slash_on_a_list_item_does_not_merge_its_peer(project, slash):
    [item] = project(f"Requirements:\n- Experience with Java{slash}\n- Python", "Python").requirements
    assert item.state == "supported"
    assert item.evidence is not None


@pytest.mark.parametrize("marker", ["1.", "+"])
def test_requirement_list_markers_use_the_same_affirmative_context(project, marker):
    jd = f"# Qualifications\n## Required skills\n{marker} Python"
    [item] = project(jd, "Python").requirements
    assert item.state == "supported"
    assert item.evidence is not None


@pytest.mark.parametrize("heading", ["Hands-on production experience required", "Production experience only"])
def test_ancestor_scope_qualification_preserves_partial_state(project, heading):
    jd = f"# Qualifications\n## {heading}\n### Technical skills\n- Python"
    [item] = project(jd, "Python").requirements
    assert item.state == "partial"
    assert item.reason_code == "additional_qualification_unverified"


def test_wrapped_alternative_is_unresolved_when_the_quote_spans_both_lines(project):
    jd = "Experience with Java／\n- Python"
    [item] = project(jd, jd).requirements
    assert item.state == "unresolved"
    assert item.reason_code == "requirement_not_affirmative" and item.evidence is None
    assert item.requirement.source_start == 0 and item.requirement.source_end == len(jd)


@pytest.mark.parametrize(("job_description", "label"), [
    ("A synthetic long-copy JD includes Paris and sample private text.",
     "A synthetic long-copy JD includes Paris and sample private text."),
    ("A synthetic" + " " * 180 + "job description includes private text.",
     "A synthetic job description includes private text."),
    ("A synthetic JD mentions private data." + " " * 30,
     "A synthetic JD mentions private data."),
])
def test_saved_extraction_cannot_echo_the_entire_job_description_as_a_skill(project, job_description, label):
    with pytest.raises(InvalidOperationError, match="invalid requirement label"):
        project(job_description, job_description, skill=label)


def test_saved_extraction_cannot_serialize_job_description_fragments(project):
    first = "Sample Labs. Hire Dana via Recruiting."
    second = "Contact recruiting@example.test and cite this private posting."
    jd = f"{first}\n{second}"
    result = project(jd, first, first, additional_requirements=[(second, second)])

    assert [item.requirement.requirement_id for item in result.requirements] == ["must_have-1", "preferred-1"]
    assert len({item.requirement.revision for item in result.requirements}) == 2
    assert all("skill" not in item.model_dump() for item in result.requirements)
    payload = result.model_dump_json()
    assert first not in payload and second not in payload
