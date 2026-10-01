"""Response header and credentialed CORS behavior at the ASGI boundary."""

from fastapi.testclient import TestClient
import pytest

from app.main import credentialed_cors_origins


def test_configured_wildcard_is_rejected_before_creating_credentialed_cors():
    with pytest.raises(ValueError, match="Credentialed CORS requires explicit origins"):
        credentialed_cors_origins(["*"])


def _preflight(client: TestClient, origin: str):
    return client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )


def test_development_credentialed_cors_uses_exact_local_origins(client: TestClient):
    for origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
        response = _preflight(client, origin)
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
        assert response.headers["access-control-allow-credentials"] == "true"

    for origin in ("http://localhost:3001", "https://untrusted.example"):
        response = _preflight(client, origin)
        assert response.status_code == 400
        assert "access-control-allow-origin" not in response.headers


def test_early_workflow_errors_keep_exact_cors_and_current_security_headers(client: TestClient):
    allowed = client.post(
        "/api/v1/resumes/upload",
        content=b"",
        headers={
            "Origin": "http://localhost:3000",
            "Content-Length": str(12 * 1024 * 1024),
        },
    )
    assert allowed.status_code == 413
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert allowed.headers["x-content-type-options"] == "nosniff"
    assert allowed.headers["x-frame-options"] == "DENY"
    assert "x-xss-protection" not in allowed.headers

    denied = client.post(
        "/api/v1/resumes/upload",
        content=b"",
        headers={
            "Origin": "https://untrusted.example",
            "Content-Length": str(12 * 1024 * 1024),
        },
    )
    assert denied.status_code == 413
    assert "access-control-allow-origin" not in denied.headers
