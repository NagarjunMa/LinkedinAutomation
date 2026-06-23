from app.schemas.jd import JDExtraction, Requirement, DiffPlan
from app.schemas.resume_v2 import (
    Bullet,
    Contact,
    ExperienceEntry,
    ResumeDocumentJSON,
    Skills,
)
from app.services.resume.content_fit import (
    build_content_budget,
    enrich_diff_plan_with_content_fit,
    score_bullet_fit,
)


def _doc(*bullets: str, raw_text: str = "short resume") -> ResumeDocumentJSON:
    return ResumeDocumentJSON(
        contact=Contact(name="A"),
        experience=[
            ExperienceEntry(
                company="Acme",
                role="Engineer",
                bullets=[
                    Bullet(id=f"b{i}", text=text, raw_text=text)
                    for i, text in enumerate(bullets, start=1)
                ],
            )
        ],
        skills=Skills(hard=["Python", "React", "AWS"]),
        raw_text=raw_text,
    )


def _jd() -> JDExtraction:
    return JDExtraction(
        must_have=[
            Requirement(skill="Python", evidence_from_jd="Build Python services", type="technical"),
            Requirement(skill="React", evidence_from_jd="Frontend React experience", type="technical"),
        ],
        good_to_have=[
            Requirement(skill="AWS", evidence_from_jd="Cloud deployment on AWS", type="technical"),
        ],
        soft_skills=[],
        seniority="mid",
        primary_role_category="SWE",
        country_hint="US",
        red_flags=[],
    )


def test_scores_highly_relevant_bullet_and_flags_noise():
    doc = _doc(
        "Built Python and React services on AWS for customer workflows",
        "Responsible for office coordination and weekly status meetings",
    )

    signals = score_bullet_fit(doc, _jd())
    by_id = {item.bullet_id: item for item in signals}

    assert by_id["b1"].recommendation == "keep"
    assert by_id["b1"].matched_requirements == ["Python", "React", "AWS"]
    assert by_id["b1"].matched_jd_phrases == [
        "Build Python services",
        "Frontend React experience",
        "Cloud deployment on AWS",
    ]
    assert by_id["b1"].source_resume_evidence == [
        "Built Python and React services on AWS for customer workflows"
    ]
    assert by_id["b1"].page_cost == "low"
    assert by_id["b1"].truth_risk == "low"
    assert "directly supports Python, React, AWS" in by_id["b1"].why_stronger
    assert by_id["b2"].recommendation == "consider_trim"
    assert "no_jd_requirement_match" in by_id["b2"].noise_flags
    assert "responsibility_only" in by_id["b2"].noise_flags
    assert by_id["b2"].truth_risk == "high"
    assert by_id["b2"].matched_jd_phrases == []


def test_content_budget_targets_one_page_for_short_resume():
    doc = _doc(*[f"Built Python service {i}" for i in range(10)])

    budget = build_content_budget(doc)

    assert budget.target_max_pages == 1
    assert budget.recommended_bullet_budget == 12
    assert budget.page_fit_risk == "low"


def test_content_budget_allows_two_pages_for_long_source():
    doc = _doc(
        *[f"Built Python service {i}" for i in range(24)],
        raw_text="word " * 1500,
    )

    budget = build_content_budget(doc)

    assert budget.target_max_pages == 2
    assert budget.recommended_bullet_budget == 22
    assert budget.page_fit_risk == "medium"


def test_enriches_diff_plan_with_fit_metadata():
    doc = _doc("Built Python services")
    plan = DiffPlan(
        match_score=70,
        must_have_coverage_found=["Python"],
        must_have_coverage_missing=[],
        good_to_have_coverage_found=[],
        good_to_have_coverage_missing=[],
        bullets=[],
        skills_reorder=None,
        summary_rewrite=None,
        suggested_additions=[],
    )

    enriched = enrich_diff_plan_with_content_fit(doc, _jd(), plan)

    assert enriched.content_budget is not None
    assert enriched.bullet_fit[0].bullet_id == "b1"
