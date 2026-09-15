"""Protocol and denial-path tests without a database or external provider."""

import asyncio
from uuid import UUID

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, Response

from app.middleware.error_contracts import WorkflowErrorMiddleware
from app.middleware.public_preview import PublicPreviewAccessMiddleware
from app.middleware.security import RateLimitMiddleware, RequestValidationMiddleware


CORS = dict(allow_origins=["https://frontend.example"], allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"], allow_credentials=True,
            expose_headers=["X-Request-ID"])


def make_app(*, preview=False, rate=False, validation=False):
    app = FastAPI()
    app.add_middleware(CORSMiddleware, **CORS)
    if rate:
        app.add_middleware(RateLimitMiddleware, requests_per_minute=1, requests_per_hour=1, burst_size=1, whitelist_ips=[])
    if validation:
        app.add_middleware(RequestValidationMiddleware, max_request_size=16)
    app.add_middleware(PublicPreviewAccessMiddleware, enabled=preview)
    app.add_middleware(WorkflowErrorMiddleware, cors_options=CORS)

    @app.api_route("/api/v1/resumes", methods=["GET", "POST"])
    def resumes(request: Request):
        return {"request_id": request.state.request_id}

    @app.get("/api/v1/resumes/error")
    def error():
        return JSONResponse({"private": "private-sentinel"}, status_code=409,
                            headers={"ETag": "private-sentinel", "Content-Disposition": "private-sentinel", "Content-Range": "private-sentinel", "X-Frame-Options": "DENY"})

    @app.delete("/api/v1/resumes/doc")
    def delete():
        return Response(status_code=204)

    @app.get("/api/v1/resumes/pdf")
    def pdf():
        return Response(b"%PDF-synthetic\x00\xff", media_type="application/pdf")

    @app.get("/api/v1/resumes-legacy")
    def legacy():
        return JSONResponse({"detail": "Legacy error"}, status_code=422)

    return app


@pytest.mark.parametrize("origin", ["https://frontend.example", "https://untrusted.example"])
@pytest.mark.parametrize("method", ["GET", "OPTIONS"])
def test_preview_denial_cannot_be_bypassed_by_cors(origin, method):
    client = TestClient(make_app(preview=True))
    response = client.request(method, "/api/v1/resumes", headers={"Origin": origin, "Access-Control-Request-Method": "GET"})
    assert response.status_code == 403
    assert response.json()["code"] == "access_denied"
    assert response.json()["request_id"] == response.headers["x-request-id"]
    assert "no-store" in response.headers["cache-control"]
    assert "noindex" in response.headers["x-robots-tag"]
    if origin == "https://frontend.example":
        assert response.headers["access-control-allow-origin"] == origin
        assert response.headers["access-control-allow-credentials"] == "true"
    else:
        assert "access-control-allow-origin" not in response.headers


def test_rate_limit_rejection_keeps_retry_headers_and_correlation():
    client = TestClient(make_app(rate=True))
    first = client.get("/api/v1/resumes")
    assert first.json()["request_id"] == first.headers["x-request-id"]
    second = client.get("/api/v1/resumes")
    assert second.status_code == 429
    assert second.json()["code"] == "rate_limited"
    assert second.headers["retry-after"] == "60"
    assert second.json()["request_id"] == second.headers["x-request-id"]


def test_body_limit_remains_enforced():
    response = TestClient(make_app(validation=True)).post("/api/v1/resumes", content=b"x" * 17)
    assert response.status_code == 413
    assert response.json()["code"] == "request_too_large"


def test_success_bytes_empty_body_and_legacy_contract_are_unchanged():
    client = TestClient(make_app())
    assert client.delete("/api/v1/resumes/doc").content == b""
    assert client.get("/api/v1/resumes/pdf").content == b"%PDF-synthetic\x00\xff"
    response = client.get("/api/v1/resumes-legacy")
    assert response.json() == {"detail": "Legacy error"}
    assert "x-request-id" not in response.headers
    error = client.get("/api/v1/resumes/error")
    assert "private-sentinel" not in error.text + str(error.headers)
    assert error.headers["x-frame-options"] == "DENY"


def test_preflight_policy_is_preserved_and_failure_is_correlated():
    client = TestClient(make_app())
    for origin, status in [("https://frontend.example", 200), ("https://untrusted.example", 400)]:
        response = client.options("/api/v1/resumes", headers={"Origin": origin, "Access-Control-Request-Method": "POST"})
        assert response.status_code == status
        assert UUID(response.headers["x-request-id"]).version == 4
        if status == 400:
            assert response.json()["code"] == "invalid_request"
            assert "access-control-allow-origin" not in response.headers


@pytest.mark.asyncio
async def test_interrupted_success_does_not_silently_complete_or_leak_exception():
    async def partial(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"part", "more_body": True})
        raise RuntimeError("private-sentinel")

    sent = []
    async def send(message):
        sent.append(message)
    async def receive():
        return {"type": "http.request", "body": b""}
    with pytest.raises(RuntimeError, match="Workflow response interrupted") as error:
        await WorkflowErrorMiddleware(partial, cors_options=CORS)(
            {"type": "http", "method": "GET", "path": "/api/v1/resumes", "headers": []}, receive, send)
    assert error.value.__suppress_context__
    assert len([m for m in sent if m["type"] == "http.response.start"]) == 1


@pytest.mark.asyncio
async def test_concurrent_requests_have_isolated_state():
    async def endpoint(scope, receive, send):
        await asyncio.sleep(0)
        await JSONResponse({"id": scope["state"]["request_id"]})(scope, receive, send)
    middleware = WorkflowErrorMiddleware(endpoint, cors_options=CORS)
    async def call():
        sent = []
        async def send(message):
            sent.append(message)
        async def receive():
            return {"type": "http.request", "body": b""}
        scope = {"type": "http", "method": "GET", "path": "/api/v1/jd", "headers": []}
        await middleware(scope, receive, send)
        return scope["state"]["request_id"]
    ids = await asyncio.gather(*(call() for _ in range(20)))
    assert len(set(ids)) == 20
