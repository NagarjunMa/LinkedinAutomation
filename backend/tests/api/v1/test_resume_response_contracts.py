"""HTTP compatibility and declaration tests for the resume transport boundary."""

from copy import deepcopy
from unittest.mock import AsyncMock, Mock

import pytest

from app.api.dependencies import get_resume_application_service
from scripts.export_openapi import export_document
from tests.fixtures.resume_doc_json import make_resume


CASES = [
    ("upload", "post", "/upload", 201, "ResumeUploadResponse"),
    ("list", "get", "/list", 200, "ResumeListResponse"),
    ("get", "get", "/doc-1", 200, "ResumeDetailResponse"),
    ("evaluate", "post", "/doc-1/evaluate", 200, "ResumeEvaluationResponse"),
    ("rewrite", "post", "/doc-1/rewrite/b1", 200, "RewriteResult"),
    ("create_version", "post", "/doc-1/versions", 201, "ResumeVersionResponse"),
]


@pytest.fixture
def payloads():
    evaluation = {
        "overall_score": 75, "readiness_label": "minor_edits",
        "score_breakdown": {"content_quality": 80, "role_fit": 75,
                            "evidence_strength": 70, "recruiter_readability": 75},
        "score_explanation": [{"category": "role_fit", "score": 75, "reason": "Test",
                               "evidence": [], "before_applying_action": "Review"}],
        "top_actions_before_applying": [], "parser_confidence": "medium",
        "bullet_flags": [], "format_issues": [],
    }
    saved = {
        **evaluation, "id": "eval-1", "resume_id": "doc-1", "resume_document_id": "doc-1",
        "ats_score": 85, "ats_compliance_score": 85, "content_quality_score": 80,
        "experience_points_score": 70, "job_relevance_score": 75, "quality_checks_score": 75,
        "strengths": [], "improvements": [], "ats_compatibility": "good",
        "detailed_feedback": None, "keyword_analysis": {"relevant": [], "missing": [], "score": 75},
        "created_at": "2026-09-13T12:34:56.123456",
    }
    row = {
        "id": "doc-1", "resume_document_id": "doc-1", "filename": "r.pdf",
        "original_filename": "r.pdf", "file_size": 0, "file_type": "pdf",
        "uploaded_at": None, "evaluation_status": "completed", "is_primary": True,
        "evaluation_result": saved,
    }
    return {
        "upload": {"resume_document_id": "doc-1", **make_resume().model_dump()},
        "list": {"resumes": [row], "total_count": 1, "totalCount": 1},
        "get": {"resume": row, "evaluation": saved},
        "evaluate": {**evaluation, "evaluation_id": "eval-1", "summary_critique": None,
                     "ats_parseability": 85, "ats_raw_text": "Synthetic resume"},
        "rewrite": {"rewritten": "Built a service", "placeholders": [], "applied_changes": []},
        "create_version": {"version_id": "ver-1"},
    }


@pytest.fixture
def stub_service(client, payloads):
    service = Mock()
    for name, payload in payloads.items():
        factory = AsyncMock if name in {"upload", "evaluate", "rewrite"} else Mock
        setattr(service, name, factory(return_value=payload))
    client.app.dependency_overrides[get_resume_application_service] = lambda: service
    yield service
    client.app.dependency_overrides.pop(get_resume_application_service, None)


def request(client, method, path, headers):
    options = {"headers": headers}
    if path == "/upload":
        options["files"] = {"file": ("r.pdf", b"synthetic", "application/pdf")}
    elif path.endswith("/evaluate") or "/rewrite/" in path:
        options["json"] = {"target_role": "Engineer"}
    elif path.endswith("/versions"):
        options["json"] = {"change_set": []}
    return client.request(method, "/api/v1/resumes" + path, **options)


@pytest.fixture(scope="module")
def exported():
    return export_document()


@pytest.mark.parametrize("name,method,path,status,schema", CASES)
def test_openapi_declares_each_json_response(exported, name, method, path, status, schema):
    path = path.replace("doc-1", "{resume_document_id}").replace("/b1", "/{bullet_id}")
    response = exported["paths"]["/api/v1/resumes" + path][method]["responses"][str(status)]
    assert response["content"]["application/json"]["schema"] == {
        "$ref": f"#/components/schemas/{schema}"
    }


@pytest.mark.parametrize("name,method,path,status,schema", CASES)
def test_response_preserves_complete_wire_payload(client, auth_headers, stub_service, payloads,
                                                  name, method, path, status, schema):
    response = request(client, method, path, auth_headers)
    assert response.status_code == status
    assert response.json() == payloads[name]


@pytest.mark.parametrize("name,method,path,status,schema", CASES)
def test_invalid_response_fails_without_disclosing_payload(client, auth_headers, stub_service,
                                                          caplog, name, method, path, status, schema):
    # A sentinel stands for a resume or ID; it must never reach logs or the caller.
    getattr(stub_service, name).return_value = {"private": "private-resume-sentinel"}
    response = request(client, method, path, auth_headers)
    assert response.status_code == 500
    assert response.json() == {
        "code": "internal_error", "message": "Request failed. Please try again when ready.",
        "detail": "Request failed. Please try again when ready.", "retryable": False,
        "request_id": response.headers["x-request-id"],
    }
    assert "private-resume-sentinel" not in caplog.text + response.text
    assert any(record.message == "Resume response contract validation failed" for record in caplog.records)
    assert all(record.exc_info is None for record in caplog.records)


def test_nullable_evaluation_and_empty_list_remain_valid(client, auth_headers, stub_service, payloads):
    stub_service.list.return_value = {"resumes": [], "total_count": 0, "totalCount": 0}
    assert request(client, "get", "/list", auth_headers).json() == stub_service.list.return_value
    detail = deepcopy(payloads["get"])
    detail["evaluation"] = None
    detail["resume"].update(evaluation_status="pending", evaluation_result=None)
    stub_service.get.return_value = detail
    assert request(client, "get", "/doc-1", auth_headers).json() == detail


def test_delete_has_no_body_or_response_schema(client, auth_headers, stub_service, exported):
    response = request(client, "delete", "/doc-1", auth_headers)
    assert response.status_code == 204
    assert response.content == b""
    operation = exported["paths"]["/api/v1/resumes/{resume_document_id}"]["delete"]
    assert "content" not in operation["responses"]["204"]


@pytest.mark.parametrize("name,method,path,field", [
    ("upload", "post", "/upload", ("experience", 0, "bullets", 0, "text")),
    ("list", "get", "/list", ("resumes", 0, "evaluation_result", "score_breakdown", "role_fit")),
    ("get", "get", "/doc-1", ("resume", "id")),
    ("evaluate", "post", "/doc-1/evaluate", ("score_explanation", 0, "evidence")),
    ("rewrite", "post", "/doc-1/rewrite/b1", ("placeholders",)),
    ("create_version", "post", "/doc-1/versions", ("version_id",)),
])
def test_malformed_field_is_not_accepted(client, auth_headers, stub_service, payloads,
                                       name, method, path, field):
    invalid = deepcopy(payloads[name])
    target = invalid
    for key in field[:-1]:
        target = target[key]
    target[field[-1]] = None
    getattr(stub_service, name).return_value = invalid
    response = request(client, method, path, auth_headers)
    assert response.status_code == 500
    assert response.json() == {
        "code": "internal_error", "message": "Request failed. Please try again when ready.",
        "detail": "Request failed. Please try again when ready.", "retryable": False,
        "request_id": response.headers["x-request-id"],
    }


def test_saved_legacy_evaluation_preserves_service_fallbacks(
    client, auth_headers, db_session, uploaded_resume_doc, test_user_id
):
    from app.application.resume_service import ResumeApplicationService
    from app.models.resume_evaluation_v2 import ResumeEvaluationV2

    row = ResumeEvaluationV2(
        id="legacy-evaluation", resume_document_id=uploaded_resume_doc.id,
        user_id=test_user_id, overall_score=65, bullet_flags=[], format_issues=[],
        ats_parseability=80, ats_raw_text="Synthetic legacy resume", model_version="test",
        score_breakdown={}, score_explanation=[], top_actions_before_applying=[],
    )
    db_session.add(row)
    db_session.commit()
    service = ResumeApplicationService(db_session)
    detail = request(client, "get", f"/{uploaded_resume_doc.id}", auth_headers)
    assert detail.status_code == 200
    assert detail.json() == service.get(uploaded_resume_doc.id, test_user_id)
    saved = detail.json()["evaluation"]
    assert saved["score_breakdown"] == {
        "content_quality": 65, "role_fit": 65, "evidence_strength": 65, "recruiter_readability": 65,
    }
    assert saved["readiness_label"] == "needs_work"
    assert saved["parser_confidence"] == "medium"
    assert saved["detailed_feedback"] is None
    listing = request(client, "get", "/list", auth_headers)
    assert listing.status_code == 200
    assert listing.json() == service.list(test_user_id)
    assert listing.json()["totalCount"] == listing.json()["total_count"] == 1
