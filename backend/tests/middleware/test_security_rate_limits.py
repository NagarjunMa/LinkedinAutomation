import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.middleware.security import RateLimitMiddleware


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
            headers={"Authorization": "Bearer second", "X-Forwarded-For": spoofed},
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
