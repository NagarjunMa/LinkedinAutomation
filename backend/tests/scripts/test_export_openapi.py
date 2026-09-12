"""Client contract export must be repeatable and independent of live configuration."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.export_openapi import client_routes, export_document


@pytest.fixture(scope="module")
def document():
    return export_document()


def test_exports_client_routes_and_declared_transport_semantics(document):
    assert "/api/v1/resumes/upload" in document.get("paths", {})
    schemas = document["components"]["schemas"]
    assert schemas["EvalRequest"]["properties"]["target_role"]["minLength"] == 2
    assert "email" in schemas["WaitlistCreate"]["required"]
    assert schemas["WaitlistCreate"]["properties"]["consent"]["const"] is True
    assert {"type": "null"} in schemas["WaitlistCreate"]["properties"]["career_stage"]["anyOf"]
    assert "student" in schemas["CareerStage"]["enum"]
    assert document["paths"]["/api/v1/resumes/list"]["get"]["security"]


def test_excludes_operational_admin_and_disabled_routes(document):
    assert document.get("paths"), "An empty export is not a valid client contract"
    assert all(path.startswith("/api/v1/") for path in document["paths"])
    assert not any("/admin/" in path or "/cleanup/" in path for path in document["paths"])
    assert "/api/v1/webhooks/stripe" not in document["paths"]
    assert "/api/v1/jobs/scrape" not in document["paths"]
    assert "CostPerUserResponse" not in document["components"]["schemas"]


def test_export_ignores_ambient_secrets_flags_and_dotenv(document, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for key in ("OPENAI_API_KEY", "SUPABASE_SERVICE_ROLE_KEY", "PROJECT_NAME", "DATABASE_URL"):
        monkeypatch.setenv(key, "ambient-secret-must-not-escape")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ENABLE_BILLING", "true")
    monkeypatch.setenv("ENABLE_LEGACY_JOB_EXTRACTION", "true")
    (tmp_path / ".env").write_text("PROJECT_NAME=dotenv-secret-must-not-escape\n")
    actual = export_document()
    assert actual.get("paths"), "Must export the real contract even in production-like environments"
    assert actual == document
    assert "must-not-escape" not in json.dumps(actual)


def test_admin_dependencies_and_their_private_schemas_are_excluded():
    from fastapi import APIRouter, Depends, FastAPI
    from fastapi.openapi.utils import get_openapi
    from pydantic import BaseModel
    from app.core.auth import require_admin_user

    class InternalReport(BaseModel):
        internal_details: str

    router = APIRouter(dependencies=[Depends(require_admin_user)])

    @router.get("/report", response_model=InternalReport)
    def report():
        raise AssertionError("Schema export must never invoke an endpoint")

    app = FastAPI()
    # Even an admin endpoint inside an otherwise client-facing namespace is excluded.
    app.include_router(router, prefix="/api/v1/jobs")
    exported = get_openapi(title="test", version="1", routes=client_routes(app.routes))
    assert exported["paths"] == {}
    assert "InternalReport" not in exported.get("components", {}).get("schemas", {})


def test_network_guard_blocks_connections_before_io():
    result = subprocess.run(
        [sys.executable, "-c", (
            "import socket, sys; from scripts.export_openapi import deny_network; "
            "sys.addaudithook(deny_network); "
            "socket.socket().connect(('127.0.0.1', 9))"
        )], cwd=Path(__file__).resolve().parents[2],
        capture_output=True, text=True, timeout=5,
    )
    assert result.returncode != 0
    assert "Network access is forbidden" in result.stderr
