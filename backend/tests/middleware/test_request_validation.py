import httpx
import pytest
from fastapi import FastAPI, Request

from app.middleware.security import RequestValidationMiddleware


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        RequestValidationMiddleware,
        max_request_size=50 * 1024 * 1024,
        route_size_limits={"/api/v1/waitlist": 8 * 1024},
        streamed_body_paths=["/api/v1/waitlist"],
        blocked_user_agents=[],
        require_user_agent=False,
    )

    @app.post("/api/v1/waitlist")
    async def waitlist(request: Request):
        body = await request.body()
        return {"bytes_received": len(body)}

    return app


async def _chunked_body(size: int):
    yield b"x" * size


@pytest.mark.asyncio
async def test_chunked_body_over_route_limit_is_rejected():
    transport = httpx.ASGITransport(app=_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/waitlist",
            content=_chunked_body(9_000),
            headers={"Content-Type": "application/octet-stream"},
        )

    assert response.status_code == 413
    assert response.json()["max_size"] == 8 * 1024


@pytest.mark.asyncio
async def test_accepted_chunked_body_is_replayed_to_endpoint():
    transport = httpx.ASGITransport(app=_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/waitlist",
            content=_chunked_body(8_000),
            headers={"Content-Type": "application/octet-stream"},
        )

    assert response.status_code == 200
    assert response.json() == {"bytes_received": 8_000}
