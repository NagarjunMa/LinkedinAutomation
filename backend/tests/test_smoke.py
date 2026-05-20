"""Phase-1 smoke tests: route registration verification (Task 20)."""
import os
os.environ.setdefault("OPENAI_API_KEY", "test")

from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient):
    """GET /health must return 200 — basic liveness check."""
    resp = client.get("/health")
    assert resp.status_code == 200, f"/health returned {resp.status_code}: {resp.text}"


def test_phase1_routes_registered_in_openapi(client: TestClient):
    """All three Phase-1 route paths must appear in /openapi.json."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, f"/openapi.json returned {resp.status_code}"
    paths = resp.json()["paths"]

    assert "/api/v1/resumes/upload" in paths, (
        f"/api/v1/resumes/upload not found. Available paths: {sorted(paths)}"
    )
    assert "/api/v1/jd/analyze" in paths, (
        f"/api/v1/jd/analyze not found. Available paths: {sorted(paths)}"
    )
    assert "/api/v1/credits/balance" in paths, (
        f"/api/v1/credits/balance not found. Available paths: {sorted(paths)}"
    )


def test_phase2_export_routes_registered_in_openapi(client: TestClient):
    """Phase-2 export endpoints must appear in /openapi.json."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    assert "/api/v1/exports" in paths, (
        f"/api/v1/exports not found. Available paths: {sorted(paths)}"
    )
    assert "/api/v1/exports/{export_id}" in paths, (
        f"/api/v1/exports/{{export_id}} not found. Available paths: {sorted(paths)}"
    )
