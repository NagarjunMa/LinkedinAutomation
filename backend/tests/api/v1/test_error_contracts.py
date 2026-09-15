"""Private workflow errors must be safe, correlated and status-compatible."""

from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.api.dependencies import get_jd_application_service, get_resume_application_service
from app.application.errors import ResourceNotFoundError
from app.core.auth import get_current_user_id


def assert_envelope(response, status, code, retryable=False):
    assert response.status_code == status
    payload = response.json()
    assert payload["code"] == code
    assert payload["retryable"] is retryable
    assert payload["message"] == payload["detail"]
    assert UUID(payload["request_id"]).version == 4
    assert response.headers["x-request-id"] == payload["request_id"]
    assert "private-sentinel" not in response.text
    return payload


@pytest.mark.parametrize("error,status,code", [
    (ResourceNotFoundError("private-sentinel"), 404, "resource_not_found"),
    (HTTPException(401, "private-sentinel", headers={"WWW-Authenticate": "Bearer"}), 401, "authentication_required"),
    (HTTPException(503, "private-sentinel"), 503, "service_unavailable"),
    (HTTPException(402, "private-sentinel"), 402, "insufficient_credits"),
    (HTTPException(415, "private-sentinel"), 415, "unsupported_media_type"),
    (HTTPException(429, "private-sentinel"), 429, "rate_limited"),
    (RuntimeError("private-sentinel"), 500, "internal_error"),
])
def test_application_and_unexpected_errors(client, auth_headers, caplog, error, status, code):
    service = Mock(get=Mock(side_effect=error))
    client.app.dependency_overrides[get_resume_application_service] = lambda: service
    try:
        response = client.get("/api/v1/resumes/doc-1", headers=auth_headers)
        # A failed operation might already have written data: no blanket retry permission.
        assert_envelope(response, status, code)
        if status == 401:
            assert response.headers["www-authenticate"] == "Bearer"
        assert "private-sentinel" not in caplog.text
    finally:
        client.app.dependency_overrides.pop(get_resume_application_service, None)


def test_request_validation_does_not_echo_input(client, auth_headers):
    response = client.post("/api/v1/jd/analyze", json={"resume_document_id": "doc", "jd_text": {"secret": "private-sentinel"}}, headers=auth_headers)
    assert_envelope(response, 422, "invalid_request")


def test_request_ids_are_server_owned_and_available_on_success(client, auth_headers):
    service = Mock(list=Mock(return_value={"resumes": [], "total_count": 0, "totalCount": 0}))
    client.app.dependency_overrides[get_resume_application_service] = lambda: service
    try:
        responses = [client.get("/api/v1/resumes/list", headers={**auth_headers, "X-Request-ID": "private-sentinel"}) for _ in range(2)]
        ids = [r.headers["x-request-id"] for r in responses]
        assert ids[0] != ids[1]
        assert all(UUID(value).version == 4 for value in ids)
        assert all(r.json() == service.list.return_value for r in responses)
    finally:
        client.app.dependency_overrides.pop(get_resume_application_service, None)


def test_jd_failure_keeps_cors_and_safe_diagnostics(client, auth_headers):
    service = Mock(analyze=AsyncMock(side_effect=RuntimeError("private-sentinel")))
    client.app.dependency_overrides[get_jd_application_service] = lambda: service
    try:
        response = client.post("/api/v1/jd/analyze", json={"resume_document_id": "doc", "jd_text": "synthetic role requirements " * 3}, headers={**auth_headers, "Origin": "http://localhost:3000"})
        assert_envelope(response, 500, "internal_error")
        assert response.headers["access-control-allow-origin"] in {"*", "http://localhost:3000"}
        assert "X-Request-ID" in response.headers["access-control-expose-headers"]
        service.analyze.assert_awaited_once()
    finally:
        client.app.dependency_overrides.pop(get_jd_application_service, None)


@pytest.mark.parametrize("status,code", [(401, "authentication_required"), (403, "access_denied"), (503, "service_unavailable")])
def test_auth_dependency_failure_never_reaches_service(client, status, code):
    overrides = client.app.dependency_overrides
    original = overrides[get_current_user_id]
    service = Mock()
    def deny():
        raise HTTPException(status, "private-sentinel")
    overrides[get_current_user_id] = deny
    overrides[get_resume_application_service] = lambda: service
    try:
        response = client.get("/api/v1/resumes/list")
        assert_envelope(response, status, code)
        service.list.assert_not_called()
    finally:
        overrides[get_current_user_id] = original
        overrides.pop(get_resume_application_service, None)


def test_openapi_error_contracts_are_scoped():
    from scripts.export_openapi import export_document
    document = export_document()
    for path, operations in document["paths"].items():
        for operation in operations.values():
            responses = operation["responses"]
            scoped = path.startswith(("/api/v1/resumes/", "/api/v1/jd/"))
            if scoped:
                for status in ("4XX", "422", "5XX"):
                    assert responses[status]["content"]["application/json"]["schema"] == {
                        "$ref": "#/components/schemas/APIErrorEnvelope"
                    }
            else:
                assert "APIErrorEnvelope" not in str(responses)
