from collections import deque
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.middleware.security import RateLimitMiddleware


def test_railway_waitlist_keeps_one_budget_across_edge_peers(caplog):
    app = FastAPI()
    path = "/api/v1/waitlist"

    @app.post(path, status_code=202)
    def waitlist():
        return {"accepted": True}

    app.add_middleware(
        RateLimitMiddleware,
        peer_only_paths={path},
        railway_edge_paths={path},
        public_cors_origins=["https://www.prismpro.live"],
        route_limits={path: {"requests_per_minute": 5, "burst_size": 3}},
    )
    client_ip = "8.8.8.8"
    origin = "https://www.prismpro.live"
    for attempt in range(1, 5):
        client = TestClient(app, client=(f"100.64.0.{attempt}", 50000))
        response = client.post(
            path,
            headers={
                "X-Real-IP": client_ip if attempt != 2 else f"::ffff:{client_ip}",
                "X-Forwarded-For": f"198.51.100.{attempt}",
                "Forwarded": f"for=198.51.100.{attempt}",
                "Authorization": f"Bearer attempt-{attempt}",
                "Origin": origin,
            },
        )
        assert response.status_code == (202 if attempt <= 3 else 429)

    assert response.headers["Retry-After"] == "60"
    assert response.headers["Access-Control-Allow-Origin"] == origin
    assert client_ip not in caplog.text
    denied = client.post(path, headers={"X-Real-IP": client_ip, "Origin": "https://other.example"})
    assert denied.status_code == 429
    assert "Access-Control-Allow-Origin" not in denied.headers
    for header in ("CF-Connecting-IP", "CF-Worker"):
        cloudflare = client.post(path, headers={"X-Real-IP": "1.1.1.1", header: "1.1.1.1"})
        assert cloudflare.status_code == 403
    assert client.post(path, headers={"X-Real-IP": "1.1.1.1"}).status_code == 202


def test_invalid_railway_edge_addresses_share_a_budget():
    app = FastAPI()
    path = "/api/v1/waitlist"

    @app.post(path)
    def waitlist():
        return {"accepted": True}

    app.add_middleware(
        RateLimitMiddleware,
        peer_only_paths={path},
        railway_edge_paths={path},
        burst_size=1,
    )
    assert TestClient(app, client=("100.64.0.1", 50000)).post(path).status_code == 200
    for headers in (
        {"X-Real-IP": "not-an-address"},
        {"X-Real-IP": "192.168.0.4"},
        {"X-Real-IP": "1.1.1.1, 8.8.8.8"},
        [("X-Real-IP", "1.1.1.1"), ("x-real-ip", "8.8.8.8")],
    ):
        assert TestClient(app, client=("100.64.0.2", 50000)).post(path, headers=headers).status_code == 429


def test_preflight_penalty_does_not_block_waitlist_submissions():
    app = FastAPI()
    path = "/api/v1/waitlist"

    @app.options(path)
    @app.post(path)
    def waitlist():
        return {"accepted": True}

    app.add_middleware(
        RateLimitMiddleware, peer_only_paths={path}, railway_edge_paths={path}, burst_size=1
    )
    client = TestClient(app, client=("100.64.0.1", 50000), headers={"X-Real-IP": "8.8.8.8"})
    assert client.options(path).status_code == 200
    for _ in range(6):
        assert client.options(path).status_code == 429

    assert client.post(path).status_code == 200


def test_rate_limit_cleanup_expires_inactive_client_counters():
    middleware = RateLimitMiddleware(FastAPI())
    now = time.time()
    middleware.last_cleanup = now - 600
    middleware.request_counts["expired"] = deque([now - 3700])
    middleware.burst_counts["expired"] = 1
    middleware.request_counts["active"] = deque([now - 1])
    middleware.burst_counts["active"] = 1

    middleware._cleanup_old_requests()

    assert set(middleware.request_counts) == {"active"}
    assert set(middleware.burst_counts) == {"active"}


@pytest.mark.parametrize("path", ["/api/v1/waitlist", "/api/v1/public-preview/events"])
@pytest.mark.parametrize("behind_trusted_proxy", [False, True])
def test_public_preview_budget_ignores_untrusted_identity_headers(path, behind_trusted_proxy):
    from app.main import security_config

    app = FastAPI()

    @app.post(path)
    @app.post(f"{path}/")
    @app.options(path)
    def public_route():
        return {"accepted": True}

    options = {
        **security_config["rate_limit"],
        "whitelist_ips": [],
        "route_limits": {
            path: {"requests_per_minute": 2, "requests_per_hour": 10, "burst_size": 2}
        },
    }
    app.add_middleware(RateLimitMiddleware, **options)
    proxy = "192.0.2.254"
    ingress = ProxyHeadersMiddleware(app, trusted_hosts=proxy)
    first_peer = proxy if behind_trusted_proxy else "192.0.2.1"
    second_peer = proxy if behind_trusted_proxy else "192.0.2.2"
    first_headers = {"X-Forwarded-For": "192.0.2.1"} if behind_trusted_proxy else {}
    second_headers = {"X-Forwarded-For": "192.0.2.2"} if behind_trusted_proxy else {}
    spoofed = "198.51.100.1, 192.0.2.1" if behind_trusted_proxy else "198.51.100.1"

    with TestClient(ingress, client=(first_peer, 50000)) as client:
        assert client.options(path, headers=first_headers).status_code == 200
        assert client.options(path, headers=first_headers).status_code == 200
        assert client.options(path, headers=first_headers).status_code == 429
        assert client.post(path, headers=first_headers).status_code == 200
        assert client.post(path, headers={**first_headers, "Authorization": "Bearer first"}).status_code == 200
        response = client.post(
            f"{path}/",
            headers={
                "Authorization": "Bearer second",
                "X-Forwarded-For": spoofed,
                "X-Real-IP": "8.8.8.8",
            },
        )
        assert response.status_code == 429
        assert response.headers["Retry-After"] == "60"

    with TestClient(ingress, client=(second_peer, 50000)) as client:
        assert client.post(path, headers=second_headers).status_code == 200


def test_route_specific_rate_limit_is_stricter_than_global_limit():
    app = FastAPI()

    @app.get("/api/v1/jd/analyze")
    async def expensive_route():
        return {"ok": True}

    @app.get("/api/v1/healthish")
    async def normal_route():
        return {"ok": True}

    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=100,
        requests_per_hour=100,
        burst_size=100,
        route_limits={
            "/api/v1/jd/analyze": {
                "requests_per_minute": 1,
                "requests_per_hour": 10,
                "burst_size": 1,
            }
        },
        rate_limit_by_user=False,
    )

    client = TestClient(app)

    assert client.get("/api/v1/jd/analyze").status_code == 200
    assert client.get("/api/v1/jd/analyze").status_code == 429
    assert client.get("/api/v1/healthish").status_code == 200


def test_x_forwarded_for_spoof_does_not_bypass_route_rate_limit():
    app = FastAPI()

    @app.get("/api/v1/jd/analyze")
    async def expensive_route():
        return {"ok": True}

    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=100,
        requests_per_hour=100,
        burst_size=100,
        route_limits={
            "/api/v1/jd/analyze": {
                "requests_per_minute": 1,
                "requests_per_hour": 10,
                "burst_size": 1,
            }
        },
        rate_limit_by_user=False,
    )

    client = TestClient(app)

    assert client.get("/api/v1/jd/analyze", headers={"X-Forwarded-For": "198.51.100.1"}).status_code == 200
    assert client.get("/api/v1/jd/analyze", headers={"X-Forwarded-For": "198.51.100.2"}).status_code == 429


def test_private_route_preserves_existing_token_partition():
    app = FastAPI()

    @app.get("/api/v1/jd/analyze")
    async def expensive_route():
        return {"ok": True}

    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=100,
        requests_per_hour=100,
        burst_size=100,
        route_limits={
            "/api/v1/jd/analyze": {
                "requests_per_minute": 1,
                "requests_per_hour": 10,
                "burst_size": 1,
            }
        },
        rate_limit_by_user=True,
    )

    client = TestClient(app)

    assert client.get("/api/v1/jd/analyze", headers={"Authorization": "Bearer user-one"}).status_code == 200
    assert client.get("/api/v1/jd/analyze", headers={"Authorization": "Bearer user-one"}).status_code == 429
    assert client.get("/api/v1/jd/analyze", headers={"Authorization": "Bearer user-two"}).status_code == 200
