"""Behavioral checks for planning over confirmed evidence and saved requirements."""

from app.application.grounded_tailor import plan_grounded_bullets
from app.schemas.career.evidence import CareerEvidenceItem, EvidenceRevisionRef
from app.schemas.career.jd_mapping import JDRequirementMapping, JDRequirementRef, TargetJDMapping
from app.schemas.career.resume import ResumePolicyProfile


def test_planner_ranks_confirmed_alternatives_and_keeps_all_exact_citations():
    team = contribution("team", "I used Python to review release checks.", ownership="team", scope="release checks")
    individual = contribution("individual", "I used Python to check deployment manifests.")
    private = contribution("private", "I used Python to publish a private finding.", is_private=True)
    ref = EvidenceRevisionRef(evidence_id="team", revision=2)
    requirements = [
        JDRequirementMapping(
            requirement=JDRequirementRef(requirement_id=f"must_have-{index}", revision=str(index) * 64,
                                         source_start=index * 10, source_end=index * 10 + 6),
            priority="must_have", kind="technical", state="communication_gap", reason_code="confirmed_application",
            evidence=ref, follow_up=None,
        ) for index in (1, 2)
    ]
    mapping = TargetJDMapping(
        schema_version=1, policy_version="jd-mapping-v1", target_id="target", jd_evaluation_id="evaluation",
        jd_text_sha256="a" * 64, jd_source=None, resume_document_id="document", resume_comparable=True, requirements=requirements,
    )
    policy = ResumePolicyProfile(
        schema_version=1, profile_id="universal", policy_version="v1", universal_rules_version="v1",
        market_overlay="universal", page_limit=1,
    )
    evidence = [team, individual, private]
    bullets, decisions = plan_grounded_bullets(mapping, evidence, policy, resume_version_id="version")
    assert (bullets, decisions) == plan_grounded_bullets(mapping, evidence[::-1], policy, resume_version_id="version")
    [bullet] = bullets
    assert bullet.plan.evidence_revisions == [EvidenceRevisionRef(evidence_id="individual", revision=2)]
    assert bullet.plan.target_requirement_ids == ["must_have-1", "must_have-2"]
    assert [item.requirement_id for item in bullet.requirements] == ["must_have-1", "must_have-2"]
    assert [(item.evidence.evidence_id, item.decision, item.reason_codes) for item in decisions] == [
        ("individual", "selected", ["must_have_relevance"]),
        ("team", "excluded", ["ownership_clearer"]),
    ]


def contribution(evidence_id, claim, **overrides):
    return CareerEvidenceItem.model_validate({
        "schema_version": 1, "owner_id": "candidate", "evidence_id": evidence_id, "revision": 2,
        "claim": claim, "category": "action", "ownership": "individual",
        "lifecycle": "confirmed", "support": "candidate_statement",
        "sources": [{"source_id": "source", "source_version": 1, "relationship": "supports",
                     "locator": "line one", "excerpt": claim, "extraction": "candidate"}],
        **overrides,
    })


def test_renderer_retains_estimate_and_bounded_team_result():
    from app.application.grounded_tailor import render_contribution

    evidence = contribution(
        "measured", "I used Python to test deployments; result: latency fell about 5%.",
        ownership="team", scope="release checks", qualifiers=["public proof unavailable"],
        measurement={"method": "synthetic replay comparison", "scope": "April baseline and final replay", "estimated": True},
    )
    rendered = render_contribution(evidence)
    assert rendered is not None
    assert rendered.text == (
        "Used Python to test deployments (team contribution: release checks) "
        "(public proof unavailable); team result: latency fell about 5% (April baseline and final replay; synthetic replay comparison)."
    )
    assert rendered.metric and rendered.metric.value == 5 and rendered.metric.estimated
    assert rendered.outcome and rendered.outcome.measurement_scope == "April baseline and final replay"
    assert render_contribution(evidence.model_copy(update={"qualifiers": ["confidential"]})) is None
    assert render_contribution(evidence.model_copy(update={"claim": "Used Python to test deployments."})) is None
    negative = render_contribution(evidence.model_copy(update={
        "claim": "I used Python to test deployments; result: replay delta was −5%.",
    }))
    assert negative and negative.metric and negative.metric.value == -5
    assert "approximately −5%" in negative.text
    small_minus = render_contribution(evidence.model_copy(update={
        "claim": "I used Python to test deployments; result: replay delta was ﹣5%.",
    }))
    assert small_minus and small_minus.metric and small_minus.metric.value == -5
    assert "approximately ﹣5%" in small_minus.text
    assert render_contribution(evidence.model_copy(update={
        "claim": "I used Python to test deployments; result: replay delta was ≤5%.",
    })) is None


async def test_wording_is_accepted_only_when_it_matches_an_approved_variant(monkeypatch):
    import json

    from types import SimpleNamespace
    from unittest.mock import AsyncMock, Mock

    from app.application.grounded_tailor import (
        GroundedTailorBullet, suggest_grounded_wording, validate_grounded_wording, wording_options,
    )
    from app.core.config import settings
    from app.schemas.career.resume import ResumeBulletPlan

    ref = EvidenceRevisionRef(evidence_id="candidate", revision=2)
    bullet = GroundedTailorBullet(requirements=(), plan=ResumeBulletPlan(
        schema_version=1, plan_id="a" * 64, evidence_revisions=[ref], action="test deployments",
        ownership="individual", method="Python", ownership_verbs=["used"], max_length=240,
        structure="technical_contribution", policy_version="v1", renderer_version="v1",
    ), text="Used Python to test deployments.")
    request = {"schema_version": 1, "plan_id": bullet.plan.plan_id, "text": wording_options(bullet)["action_first"]}
    option, validation = validate_grounded_wording(bullet, json.dumps(request))
    assert option == "action_first" and validation.accepted
    for proposal in (None, "null", json.dumps({**request, "extra": 1}),
                     json.dumps({**request, "text": "Led a Python team and increased output 70%."}),
                     json.dumps({**request, "plan_id": "b" * 64})):
        option, validation = validate_grounded_wording(bullet, proposal)
        assert option == "safe" and validation.used_fallback

    proposal = {**request, "text": "To {action}, used {method}."}
    completion = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(proposal)))])
    fake_model = Mock()
    fake_model.manifests = {"tailor": SimpleNamespace(model_snapshot="synthetic")}
    provider = fake_model.single_attempt_client().chat.completions
    provider.create = AsyncMock(return_value=completion)
    monkeypatch.setattr(settings, "ENABLE_AI_FEATURES", False)
    option, validation = await suggest_grounded_wording(bullet, fake_model)
    assert option == "safe" and validation.used_fallback
    provider.create.assert_not_awaited()
    monkeypatch.setattr(settings, "ENABLE_AI_FEATURES", True)
    option, validation = await suggest_grounded_wording(bullet, fake_model)
    assert option == "action_first" and validation.accepted
    provider.create.assert_awaited_once()
    assert provider.create.await_args.kwargs["store"] is False
    assert "deployments" not in str(provider.create.await_args) and "Python" not in str(provider.create.await_args)
