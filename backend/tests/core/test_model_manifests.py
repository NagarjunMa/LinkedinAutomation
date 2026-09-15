"""Characterize the five existing calls before changing their configuration source."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from dataclasses import FrozenInstanceError
import hashlib
import json
import logging

import pytest
import respx
from pydantic import ValidationError

from app.core.openai_client import DEFAULT_MANIFESTS, ModelManifest, ModelParameters, ModelRuntime, get_model_runtime
from app.services.resume import evaluator, rewriter
from app.services.jd import extractor, tailor
from app.services.jd.extractor import extract_jd_requirements
from app.schemas.jd import BulletDiff, DiffPlan, JDExtraction
from tests.services.resume.test_evaluator import evaluation_content
from tests.fixtures.resume_doc_json import make_resume


@pytest.fixture(autouse=True)
def no_external_http():
    with respx.mock:
        yield


def jd_fixture():
    return JDExtraction(must_have=[], good_to_have=[], seniority="senior",
                        primary_role_category="SWE", country_hint="US")


def plan_fixture():
    return DiffPlan(match_score=50, must_have_coverage_found=[], must_have_coverage_missing=[],
                    good_to_have_coverage_found=[], good_to_have_coverage_missing=[], bullets=[])


def response(parsed=None, content=None):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
        parsed=parsed, content=json.dumps(content),
    ))], usage=None)


def fake_provider(result):
    call = AsyncMock(return_value=result)
    completions = SimpleNamespace(create=call, parse=call)
    chat = SimpleNamespace(completions=completions)
    client = SimpleNamespace(chat=chat, beta=SimpleNamespace(chat=chat))
    client.with_options = Mock(return_value=client)
    return client, call


def case(name):
    doc, jd = make_resume(), jd_fixture()
    doc.raw_text = "PRIVATE-RESUME" + "x" * 12000
    resume_json = doc.model_dump_json(exclude={"raw_text"})
    original = doc.experience[0].bullets[0].text
    if name == "evaluator":
        return (evaluator.evaluate_resume, {"doc": doc, "target_role": "SWE"},
                evaluator.SYSTEM_PROMPT, evaluator.USER_PROMPT_TEMPLATE,
                evaluator.USER_PROMPT_TEMPLATE.format(target_role="SWE", resume_json=resume_json, raw_text=doc.raw_text[:12000]),
                {"type": "json_object"}, response(content=evaluation_content()))
    if name == "rewriter":
        return (rewriter.rewrite_bullet, {"original": original, "target_role": "SWE"},
                rewriter.REWRITER_SYSTEM, rewriter.REWRITER_USER,
                rewriter.REWRITER_USER.format(original=original, target_role="SWE", country="US", jd_context=""),
                {"type": "json_object"}, response(content={"rewritten": original, "placeholders": [], "applied_changes": []}))
    if name == "extractor":
        template = "Job description:\n\n{jd_text}\n\nExtract requirements."
        return (extractor.extract_jd_requirements, {"jd_text": "PRIVATE-JD"},
                extractor.EXTRACTOR_SYSTEM, template, template.format(jd_text="PRIVATE-JD"), JDExtraction, response(parsed=jd))
    if name == "tailor":
        return (tailor.tailor_resume_to_jd, {"doc": doc, "jd": jd},
                tailor.TAILOR_SYSTEM, tailor.TAILOR_USER,
                tailor.TAILOR_USER.format(resume_json=resume_json, jd_json=jd.model_dump_json()),
                DiffPlan, response(parsed=plan_fixture()))
    return (tailor.generate_bullet_options, {"doc": doc, "jd": jd, "bullet_id": "b1", "original": original},
            tailor.OPTIONS_SYSTEM, tailor.OPTIONS_USER,
            tailor.OPTIONS_USER.format(bullet_id="b1", original=original, resume_json=resume_json, jd_json=jd.model_dump_json()),
            BulletDiff, response(parsed=BulletDiff(bullet_id="b1", old=original, new=original, reason="PRIVATE-RESPONSE")))


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["evaluator", "rewriter", "extractor", "tailor", "tailor_options"])
@pytest.mark.parametrize("custom", [False, True])
async def test_call_configuration_and_prompt_compatibility(name, custom, caplog):
    fn, args, system, template, user, output_format, result = case(name)
    client, call = fake_provider(result)
    manifest = DEFAULT_MANIFESTS[name]
    assert manifest.prompt_name == name
    assert manifest.prompt_version == "1"
    assert manifest.provider == "openai"
    assert manifest.schema_version == {
        "evaluator": "EvaluationReport.v1", "rewriter": "RewriteResult.v1",
        "extractor": "JDExtraction.v1", "tailor": "DiffPlan.v1", "tailor_options": "BulletDiff.v1",
    }[name]
    assert manifest.model_snapshot == "gpt-4o-2024-08-06"
    assert manifest.parameters.temperature == {
        "evaluator": 0.2, "rewriter": 0.4, "extractor": 0.1, "tailor": 0.3, "tailor_options": 0.4,
    }[name]
    assert manifest.prompt_hash == hashlib.sha256(json.dumps(
        [system, template], ensure_ascii=False, separators=(",", ":"),
    ).encode()).hexdigest()
    if custom:
        manifest = ModelManifest(**{**manifest.model_dump(), "model_snapshot": "test-snapshot",
                                    "parameters": {"temperature": 0.7}})
    runtime = ModelRuntime(client_factory=lambda: client, manifests={name: manifest})
    with caplog.at_level(logging.INFO, logger="llm"):
        await fn(**args, runtime=runtime)
    call.assert_awaited_once_with(
        model=manifest.model_snapshot, temperature=manifest.parameters.temperature,
        response_format=output_format,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    client.with_options.assert_called_once_with(max_retries=0)
    for sentinel in ("PRIVATE-RESUME", "PRIVATE-JD", "PRIVATE-RESPONSE", system):
        assert sentinel not in caplog.text


def test_runtime_configuration_is_deeply_immutable():
    source = dict(DEFAULT_MANIFESTS)
    runtime = ModelRuntime(manifests=source)
    source.clear()
    assert len(runtime.manifests) == 5
    with pytest.raises(TypeError):
        runtime.manifests["evaluator"] = DEFAULT_MANIFESTS["rewriter"]
    with pytest.raises(FrozenInstanceError):
        runtime.client_factory = lambda: None
    with pytest.raises(ValidationError):
        runtime.manifests["evaluator"].model_snapshot = "changed"
    with pytest.raises(ValidationError):
        runtime.manifests["evaluator"].parameters.temperature = 1


def test_dependency_construction_is_lazy(monkeypatch):
    from app.core import openai_client
    from app.api.dependencies import get_resume_application_service, get_jd_application_service
    def forbidden():
        pytest.fail("Dependency construction must not create a provider client")
    monkeypatch.setattr(openai_client, "get_openai_client", forbidden)
    runtime = get_model_runtime()
    assert get_resume_application_service(db=None, runtime=runtime).runtime is runtime
    assert get_jd_application_service(db=None, runtime=runtime).runtime is runtime


@pytest.mark.parametrize("values", [{"temperature": float("nan")}, {"temperature": 3},
                                    {"temperature": 0.2, "api_key": "private"}])
def test_parameters_reject_invalid_or_extra_configuration(values):
    with pytest.raises(ValidationError):
        ModelParameters(**values)


def test_dependency_override_persists_exact_call_model(
    client, auth_headers, uploaded_resume_doc, user_with_credits, db_session,
):
    from app.main import app
    from app.models.resume_evaluation_v2 import ResumeEvaluationV2
    fake, call = fake_provider(response(content=evaluation_content()))
    manifests = dict(DEFAULT_MANIFESTS)
    manifests["evaluator"] = ModelManifest(**{
        **manifests["evaluator"].model_dump(), "model_snapshot": "injected-evaluator-snapshot",
    })
    runtime = ModelRuntime(client_factory=lambda: fake, manifests=manifests)
    app.dependency_overrides[get_model_runtime] = lambda: runtime
    try:
        result = client.post(f"/api/v1/resumes/{uploaded_resume_doc.id}/evaluate",
                             json={"target_role": "SWE"}, headers=auth_headers)
        assert result.status_code == 200, result.text
        row = db_session.get(ResumeEvaluationV2, result.json()["evaluation_id"])
        assert row.model_version == call.await_args.kwargs["model"] == "injected-evaluator-snapshot"
    finally:
        app.dependency_overrides.pop(get_model_runtime, None)


def test_jd_dependency_override_reaches_analysis_and_options(
    client, auth_headers, uploaded_resume_doc, user_with_credits,
):
    from app.main import app
    original = uploaded_resume_doc.parsed_json["experience"][0]["bullets"][0]["text"]
    fake, call = fake_provider(None)
    call.side_effect = [
        response(parsed=jd_fixture()), response(parsed=plan_fixture()),
        response(parsed=BulletDiff(bullet_id="b1", old=original, new=original, reason="Safe")),
    ]
    manifests = {name: ModelManifest(**{**manifest.model_dump(), "model_snapshot": f"test-{name}"})
                 for name, manifest in DEFAULT_MANIFESTS.items()}
    app.dependency_overrides[get_model_runtime] = lambda: ModelRuntime(
        client_factory=lambda: fake, manifests=manifests,
    )
    try:
        result = client.post("/api/v1/jd/analyze", headers=auth_headers, json={
            "resume_document_id": uploaded_resume_doc.id,
            "jd_text": "Senior software engineer role. Build and maintain reliable Python services.",
        })
        assert result.status_code == 200, result.text
        evaluation_id = result.json()["jd_evaluation_id"]
        options = client.post(f"/api/v1/jd/{evaluation_id}/bullets/b1/options", headers=auth_headers)
        assert options.status_code == 200, options.text
        assert options.json()["old"] == original
        assert [c.kwargs["model"] for c in call.await_args_list] == [
            "test-extractor", "test-tailor", "test-tailor_options",
        ]
    finally:
        app.dependency_overrides.pop(get_model_runtime, None)


def test_rewrite_dependency_override_reaches_provider(client, auth_headers, uploaded_resume_doc):
    from app.main import app
    original = uploaded_resume_doc.parsed_json["experience"][0]["bullets"][0]["text"]
    fake, call = fake_provider(response(content={
        "rewritten": original, "placeholders": [], "applied_changes": [],
    }))
    manifest = ModelManifest(**{**DEFAULT_MANIFESTS["rewriter"].model_dump(), "model_snapshot": "test-rewriter"})
    app.dependency_overrides[get_model_runtime] = lambda: ModelRuntime(
        client_factory=lambda: fake, manifests={"rewriter": manifest},
    )
    try:
        result = client.post(f"/api/v1/resumes/{uploaded_resume_doc.id}/rewrite/b1",
                             headers=auth_headers, json={"target_role": "SWE", "country": "US"})
        assert result.status_code == 200, result.text
        assert call.await_args.kwargs["model"] == "test-rewriter"
    finally:
        app.dependency_overrides.pop(get_model_runtime, None)


@pytest.mark.asyncio
async def test_extractor_accepts_injected_client_and_manifest():
    parsed = JDExtraction(must_have=[], good_to_have=[], seniority="senior",
                          primary_role_category="SWE", country_hint="US")
    parse = AsyncMock(return_value=SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed))], usage=None,
    ))
    fake_client = SimpleNamespace(beta=SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(parse=parse)),
    ))
    fake_client.with_options = Mock(return_value=fake_client)
    manifest = SimpleNamespace(model_snapshot="test-snapshot", parameters=SimpleNamespace(temperature=0.7))
    runtime = ModelRuntime(client_factory=lambda: fake_client, manifests={"extractor": manifest})

    result = await extract_jd_requirements("Private JD fixture", runtime=runtime)

    assert result is parsed
    assert parse.await_args.kwargs["model"] == "test-snapshot"
    assert parse.await_args.kwargs["temperature"] == 0.7
