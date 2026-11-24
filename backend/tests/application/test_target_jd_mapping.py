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

    def map_jd(job_description, quote, skill="Python", *, additional_requirements=()):
        extraction = JDExtraction(
            must_have=[Requirement(skill=skill, evidence_from_jd=quote, type="technical")],
            good_to_have=[
                Requirement(skill=label, evidence_from_jd=excerpt, type="technical")
                for label, excerpt in additional_requirements
            ],
            seniority="senior", primary_role_category="SWE", country_hint="US",
        )
        return project_target_jd_mapping(
            target, [evidence], evaluation_id="evaluation", jd_text=job_description,
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
