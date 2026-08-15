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


def test_mvp_public_api_surface_excludes_unsupported_legacy_routes(client: TestClient):
    """Deprecated/demo routes must not be presented as launch-supported APIs."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]

    unsupported_paths = {
        "/api/v1/jobs/extract-from-url",
        "/api/v1/jobs/extract-multiple-urls",
        "/api/v1/jobs/extraction-stats/{user_id}",
        "/api/v1/jobs/domain-info",
        "/api/v1/jobs/test-extraction",
        "/api/v1/jobs/scrape",
        "/api/v1/jobs/cleanup/stats",
        "/api/v1/jobs/cleanup/execute",
        "/api/v1/jobs/cleanup/execute-all",
        "/api/v1/profiles/upload-resume/{user_id}",
        "/api/v1/profiles/profile/{user_id}",
        "/api/v1/profiles/matches/{user_id}",
        "/api/v1/profiles/score-jobs/{user_id}",
        "/api/v1/profiles/parse-text/{user_id}",
        "/api/v1/profiles/users",
        "/api/v1/profiles/preferences/{user_id}",
        "/api/v1/profiles/trigger-scoring/{user_id}",
        "/api/v1/profiles/scoring-status/{user_id}",
        "/api/v1/profiles/clear-scores/{user_id}",
        "/api/v1/profiles/score-new-job/{job_id}",
    }

    assert unsupported_paths.isdisjoint(paths), (
        f"Unsupported legacy routes are still advertised: {sorted(unsupported_paths.intersection(paths))}"
    )
