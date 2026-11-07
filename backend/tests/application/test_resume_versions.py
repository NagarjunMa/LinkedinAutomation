"""Version-aware model operations must validate ownership before side effects."""
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.application.errors import OperationRejectedError, ResourceNotFoundError
from app.application.resume_service import ResumeApplicationService
from app.models.resume_document import ResumeVersion
from app.schemas.resume_v2 import BulletFlag, EvaluationReport, FormatIssue
from tests.fixtures.resume_doc_json import make_resume
from tests.services.resume.test_evaluator import evaluation_content


@pytest.fixture
def workflow(monkeypatch):
    original = make_resume()
    edited = original.model_copy(deep=True)
    edited.experience[0].bullets[0].text = "Implemented the revised API"
    source = SimpleNamespace(id="doc-1", parsed_json=original.model_dump(),
                             storage_path="source.pdf", original_filename="source.pdf")
    version = SimpleNamespace(resume_document_id="doc-1", parsed_json=edited.model_dump())
    service = ResumeApplicationService(Mock())
    service.resumes = Mock()
    service.resumes.get_owned_ready.return_value = source
    service.resumes.get_version.return_value = version
    evaluator = AsyncMock(return_value=EvaluationReport.model_validate(evaluation_content()))
    rewriter = AsyncMock(return_value=SimpleNamespace(model_dump=lambda: {"rewritten": "Revised"}))
    paid = Mock(return_value=nullcontext())
    storage = Mock()
    monkeypatch.setattr("app.application.resume_service.evaluate_resume", evaluator)
    monkeypatch.setattr("app.application.resume_service.rewrite_bullet", rewriter)
    monkeypatch.setattr("app.application.resume_service.paid_operation", paid)
    monkeypatch.setattr("app.application.resume_service.get_storage", lambda: storage)
    source_issue = FormatIssue(type="layout", location="Uploaded PDF", fix_hint="Use one column.")
    monkeypatch.setattr("app.application.resume_service.simulate_ats", lambda *a, **k: SimpleNamespace(
        format_issues=[source_issue], parseability_score=90, raw_text="Uploaded source text"))
    return SimpleNamespace(service=service, source=source, version=version,
                           evaluator=evaluator, rewriter=rewriter, paid=paid)


@pytest.mark.asyncio
async def test_models_use_selected_version_without_stale_raw_text(workflow):
    service = workflow.service
    await service.evaluate("doc-1", "Engineer", "owner", version_id="v1")
    content = workflow.evaluator.call_args.args[0]
    assert content.experience[0].bullets[0].text == "Implemented the revised API"
    assert content.experience[0].bullets[0].raw_text == "Implemented the revised API"
    assert content.raw_text == ""
    await service.rewrite(resume_document_id="doc-1", bullet_id="b1", target_role="Engineer",
                          country="US", jd_context=None, user_id="owner", version_id="v1")
    assert workflow.rewriter.call_args.kwargs["original"] == "Implemented the revised API"


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid", ["missing", "other_resume", "other_owner"])
async def test_invalid_versions_fail_before_model_or_credit_work(workflow, invalid):
    if invalid == "missing":
        workflow.service.resumes.get_version.return_value = None
    elif invalid == "other_resume":
        workflow.version.resume_document_id = "another-document"
    else:
        workflow.service.resumes.get_owned_ready.return_value = None
    for operation in (
        lambda: workflow.service.evaluate("doc-1", "Engineer", "owner", version_id="v1"),
        lambda: workflow.service.rewrite(resume_document_id="doc-1", bullet_id="b1",
            target_role="Engineer", country="US", jd_context=None, user_id="owner", version_id="v1"),
    ):
        with pytest.raises(ResourceNotFoundError):
            await operation()
    workflow.evaluator.assert_not_called()
    workflow.rewriter.assert_not_called()
    workflow.paid.assert_not_called()
    workflow.service.session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_legacy_evaluation_keeps_original_source(workflow):
    await workflow.service.evaluate("doc-1", "Engineer", "owner")
    assert workflow.evaluator.call_args.args[0].model_dump() == workflow.source.parsed_json


@pytest.mark.asyncio
@pytest.mark.parametrize(("version_id", "expected_locations"), [
    ("v1", ["Uploaded PDF"]),
    (None, ["Evaluated content", "Uploaded PDF"]),
])
async def test_version_document_checks_only_include_uploaded_file_diagnostics(workflow, version_id, expected_locations):
    workflow.evaluator.return_value.format_issues = [
        FormatIssue(type="structure", location="Evaluated content", fix_hint="Review section order."),
    ]
    result = await workflow.service.evaluate("doc-1", "Engineer", "owner", version_id=version_id)
    assert [issue["location"] for issue in result["format_issues"]] == expected_locations


@pytest.mark.asyncio
async def test_findings_for_another_bullet_never_reach_the_model(workflow):
    with pytest.raises(OperationRejectedError):
        await workflow.service.rewrite(resume_document_id="doc-1", bullet_id="b1",
            target_role="Engineer", country="US", jd_context=None, user_id="owner",
            findings=[BulletFlag(bullet_id="b2", severity="warning", category="clarity", reason="Wrong bullet")])
    workflow.rewriter.assert_not_called()


def test_consecutive_version_requests_persist_both_changes(client, db_session, auth_headers, uploaded_resume_doc):
    path = f"/api/v1/resumes/{uploaded_resume_doc.id}/versions"
    first = client.post(path, headers=auth_headers, json={"change_set": [
        {"type": "bullet_update", "bullet_id": "b1", "new_text": "Updated first contribution"},
    ]})
    assert first.status_code == 201
    second = client.post(path, headers=auth_headers, json={
        "parent_version_id": first.json()["version_id"],
        "change_set": [{"type": "bullet_update", "bullet_id": "b2", "new_text": "Updated second contribution"}],
    })
    assert second.status_code == 201
    saved = db_session.get(ResumeVersion, second.json()["version_id"])
    assert [bullet["text"] for bullet in saved.parsed_json["experience"][0]["bullets"]] == [
        "Updated first contribution", "Updated second contribution",
    ]
