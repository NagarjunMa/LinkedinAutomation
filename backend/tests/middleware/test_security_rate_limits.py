from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security import RateLimitMiddleware


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


def test_bearer_token_hash_separates_authenticated_rate_limit_keys():
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
