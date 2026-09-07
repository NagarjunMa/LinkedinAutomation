from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.public_preview import PublicPreviewAccessMiddleware


def _app(*, enabled: bool) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        PublicPreviewAccessMiddleware,
        enabled=enabled,
        allowed_paths={
            "/api/v1/waitlist",
            "/api/v1/public-preview/events",
        },
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/api/v1/waitlist")
    def waitlist():
        return {"accepted": True}

    @app.post("/api/v1/public-preview/events")
    def public_preview_event():
        return {"accepted": True}

    @app.get("/api/v1/resumes")
    def resumes():
        return {"private": True}

    return app


def test_preview_mode_allows_only_health_and_waitlist():
    client = TestClient(_app(enabled=True))

    assert client.get("/health").status_code == 200
    assert client.post("/api/v1/waitlist").status_code == 200
    assert client.post("/api/v1/public-preview/events").status_code == 200

    blocked = client.get(
        "/api/v1/resumes", headers={"Authorization": "Bearer existing-token"}
    )
    assert blocked.status_code == 403
    assert blocked.json() == {
        "detail": "Product access is unavailable during the private preview."
    }
    assert "no-store" in blocked.headers["cache-control"]


def test_explicitly_disabled_preview_preserves_internal_deployment_access():
    client = TestClient(_app(enabled=False))

    response = client.get("/api/v1/resumes")

    assert response.status_code == 200
    assert response.json() == {"private": True}
