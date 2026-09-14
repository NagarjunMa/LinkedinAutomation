"""Compatibility and privacy at the PRI-11 prerequisite response boundaries."""

from copy import deepcopy
from unittest.mock import AsyncMock, Mock

import pytest

from app.api.dependencies import get_export_application_service, get_jd_application_service
from app.application.errors import ResourceNotFoundError
from app.application.export_service import PdfDownload
from app.schemas.jd import BulletDiff, DiffPlan, JDExtraction
from scripts.export_openapi import export_document


JD_TEXT = "Synthetic job description for a Python engineer with backend experience."


@pytest.fixture
def analysis_payload():
    return {
        "jd_evaluation_id": "eval-1",
        "extracted_requirements": JDExtraction(
            must_have=[{"skill": "Python", "evidence_from_jd": "Python engineer", "type": "technical"}],
            good_to_have=[], seniority="mid", primary_role_category="SWE", country_hint="US",
        ).model_dump(),
        "diff_plan": DiffPlan(
            match_score=75, must_have_coverage_found=["Python"], must_have_coverage_missing=[],
            good_to_have_coverage_found=[], good_to_have_coverage_missing=[],
            bullets=[BulletDiff(bullet_id="b1", old="Built services", new="Built Python services", reason="Clarify")],
        ).model_dump(),
    }


@pytest.fixture
def jd_service(client, analysis_payload):
    service = Mock(analyze=AsyncMock(return_value=analysis_payload))
    client.app.dependency_overrides[get_jd_application_service] = lambda: service
    yield service
    client.app.dependency_overrides.pop(get_jd_application_service, None)


@pytest.fixture
def export_service(client):
    service = Mock(download=Mock(return_value=PdfDownload(b"%PDF-1.7\nsynthetic\x00\xff", "resume.pdf")))
    client.app.dependency_overrides[get_export_application_service] = lambda: service
    yield service
    client.app.dependency_overrides.pop(get_export_application_service, None)


@pytest.fixture(scope="module")
def exported():
    return export_document()


def analyze(client, auth_headers):
    return client.post("/api/v1/jd/analyze", headers=auth_headers,
                       json={"resume_document_id": "doc-1", "jd_text": JD_TEXT})


@pytest.mark.parametrize("path,method,schema", [
    ("/api/v1/jd/analyze", "post", "JDAnalysisResponse"),
    ("/api/v1/credits/balance", "get", "CreditBalanceResponse"),
])
def test_json_response_has_declared_schema(exported, path, method, schema):
    response = exported["paths"][path][method]["responses"]["200"]
    assert response["content"]["application/json"]["schema"] == {"$ref": f"#/components/schemas/{schema}"}
    assert schema in exported["components"]["schemas"]


def test_analysis_nested_contracts_are_exported(exported):
    schemas = exported["components"]["schemas"]
    assert "JDExtraction" in schemas
    assert "DiffPlan" in schemas
    assert schemas["JDAnalysisResponse"]["required"] == [
        "jd_evaluation_id", "extracted_requirements", "diff_plan",
    ]


def test_analysis_preserves_wire_payload_and_service_arguments(client, auth_headers, jd_service,
                                                              analysis_payload, test_user_id):
    response = analyze(client, auth_headers)
    assert response.status_code == 200
    assert response.json() == analysis_payload
    jd_service.analyze.assert_awaited_once_with(
        resume_document_id="doc-1", jd_text=JD_TEXT, user_id=test_user_id,
    )
    assert response.json()["extracted_requirements"]["company_name"] is None
    assert response.json()["diff_plan"]["skills_reorder"] is None
    assert response.json()["diff_plan"]["bullets"][0]["options"] == []


@pytest.mark.parametrize("field", [
    ("jd_evaluation_id",),
    ("extracted_requirements", "must_have"),
    ("extracted_requirements", "seniority"),
    ("diff_plan", "match_score"),
    ("diff_plan", "bullets", 0, "truth_check"),
])
def test_nested_analysis_corruption_is_private(client, auth_headers, jd_service, analysis_payload,
                                              caplog, field):
    invalid = deepcopy(analysis_payload)
    target = invalid
    for key in field[:-1]:
        target = target[key]
    target[field[-1]] = {"private": "private-jd-sentinel"}
    jd_service.analyze.return_value = invalid
    response = analyze(client, auth_headers)
    assert response.status_code == 500
    assert response.json() == {"detail": "Response could not be processed"}
    assert "private-jd-sentinel" not in response.text + caplog.text
    assert JD_TEXT not in caplog.text
    assert "doc-1" not in caplog.text
    assert "eval-1" not in caplog.text
    assert any(record.message == "Response contract validation failed" for record in caplog.records)
    assert all(record.exc_info is None for record in caplog.records)
    jd_service.analyze.assert_awaited_once()


def test_missing_analysis_fields_fail_instead_of_fabricating_success(client, auth_headers, jd_service):
    jd_service.analyze.return_value = {}
    response = analyze(client, auth_headers)
    assert response.status_code == 500
    assert response.json() == {"detail": "Response could not be processed"}


@pytest.mark.parametrize("balance", [0, 17, -3])
def test_credit_balance_is_preserved_not_clamped(client, auth_headers, monkeypatch, test_user_id, balance):
    get_balance = Mock(return_value=balance)
    monkeypatch.setattr("app.api.v1.endpoints.credits.get_balance", get_balance)
    response = client.get("/api/v1/credits/balance", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"balance": balance}
    assert get_balance.call_count == 1
    assert get_balance.call_args.args[1] == test_user_id


@pytest.mark.parametrize("balance", [None, 1.5, "private-balance-sentinel"])
def test_malformed_balance_is_not_an_empty_or_zero_success(client, auth_headers, monkeypatch, caplog, balance):
    monkeypatch.setattr("app.api.v1.endpoints.credits.get_balance", Mock(return_value=balance))
    response = client.get("/api/v1/credits/balance", headers=auth_headers)
    assert response.status_code == 500
    assert response.json() == {"detail": "Response could not be processed"}
    assert "private-balance-sentinel" not in response.text + caplog.text
    assert all(record.exc_info is None for record in caplog.records)


def test_pdf_download_is_documented_as_binary_only(exported):
    response = exported["paths"]["/api/v1/exports/{export_id}/download"]["get"]["responses"]["200"]
    assert response["content"] == {"application/pdf": {"schema": {"type": "string", "format": "binary"}}}


def test_pdf_bytes_and_headers_remain_unchanged(client, auth_headers, export_service, test_user_id):
    response = client.get("/api/v1/exports/exp-1/download", headers=auth_headers)
    assert response.status_code == 200
    assert response.content == b"%PDF-1.7\nsynthetic\x00\xff"
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == 'attachment; filename="resume.pdf"'
    assert response.headers["cache-control"] == "private, no-store"
    export_service.download.assert_called_once_with("exp-1", test_user_id)


def test_application_errors_keep_existing_status_and_detail(client, auth_headers, jd_service, export_service):
    jd_service.analyze.side_effect = ResourceNotFoundError("Resume document not found")
    response = analyze(client, auth_headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Resume document not found"}
    export_service.download.side_effect = ResourceNotFoundError("Export not found")
    response = client.get("/api/v1/exports/exp-1/download", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Export not found"}


def test_invalid_request_is_not_misclassified_as_response_failure(client, auth_headers, jd_service):
    response = client.post("/api/v1/jd/analyze", headers=auth_headers,
                           json={"resume_document_id": "doc-1", "jd_text": "short"})
    assert response.status_code == 422
    jd_service.analyze.assert_not_awaited()


def test_non_contract_exceptions_are_not_swallowed(client, auth_headers, jd_service):
    jd_service.analyze.side_effect = RuntimeError("synthetic service failure")
    with pytest.raises(RuntimeError, match="synthetic service failure"):
        analyze(client, auth_headers)


def test_real_analysis_service_payload_matches_persisted_result(
    client, auth_headers, uploaded_resume_doc, user_with_credits, db_session, monkeypatch, analysis_payload,
):
    from app.models.jd_evaluation import JDEvaluation

    monkeypatch.setattr("app.application.jd_service.extract_jd_requirements", AsyncMock(
        return_value=JDExtraction.model_validate(analysis_payload["extracted_requirements"]),
    ))
    monkeypatch.setattr("app.application.jd_service.tailor_resume_to_jd", AsyncMock(
        return_value=DiffPlan.model_validate(analysis_payload["diff_plan"]),
    ))
    response = client.post("/api/v1/jd/analyze", headers=auth_headers,
                           json={"resume_document_id": uploaded_resume_doc.id, "jd_text": JD_TEXT})
    assert response.status_code == 200
    result = response.json()
    saved = db_session.get(JDEvaluation, result["jd_evaluation_id"])
    assert result == {
        "jd_evaluation_id": saved.id,
        "extracted_requirements": saved.extracted_requirements,
        "diff_plan": saved.diff_plan,
    }
    assert result["extracted_requirements"] == analysis_payload["extracted_requirements"]
    assert result["diff_plan"] == analysis_payload["diff_plan"]


@pytest.mark.parametrize("path,method", [
    ("/api/v1/jd/eval-1/apply", "apply"),
    ("/api/v1/jd/eval-1/bullets/b1/options", "regenerate_options"),
])
def test_existing_jd_response_validation_uses_same_private_boundary(client, auth_headers, jd_service,
                                                                 caplog, path, method):
    factory = AsyncMock if method == "regenerate_options" else Mock
    setattr(jd_service, method, factory(return_value={"private": "private-jd-sentinel"}))
    response = client.post(path, headers=auth_headers, json={"accepted_changes": []})
    assert response.status_code == 500
    assert response.json() == {"detail": "Response could not be processed"}
    assert "private-jd-sentinel" not in response.text + caplog.text
    assert all(record.exc_info is None for record in caplog.records)
