"""Export declared client contracts without starting the app or using live settings."""

import contextlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


# Passed as the complete child environment, never merged with ambient credentials.
EXPORT_ENV = {
    "ENVIRONMENT": "test",
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    "DATABASE_URL": "sqlite:///:memory:",
    "OPENAI_API_KEY": "test",
    "SUPABASE_URL": "https://test.supabase.co",
    "SUPABASE_ANON_KEY": "test",
    "SUPABASE_SERVICE_ROLE_KEY": "test",
    "ENABLE_BILLING": "false",
    "ENABLE_LEGACY_JOB_EXTRACTION": "false",
    "PRISM_PRO_PUBLIC_PREVIEW_ONLY": "false",
    "PYTHON_DOTENV_DISABLED": "1",
    "PYTHONHASHSEED": "0",
}
CLIENT_PREFIXES = tuple(f"/api/v1/{name}" for name in (
    "resumes", "jd", "credits", "exports", "tailored-resumes", "jobs",
    "user-profiles", "logs", "analytics", "waitlist", "public-preview", "auth",
))


def deny_network(event: str, _args: tuple) -> None:
    """Fail if a future import starts network I/O during offline generation."""
    if event in {"socket.connect", "socket.getaddrinfo", "socket.bind", "socket.sendto"}:
        raise RuntimeError("Network access is forbidden during contract export")


def client_routes(routes):
    from fastapi.routing import APIRoute, iter_route_contexts
    from app.core.auth import require_admin_user

    def is_admin(dependency):
        return dependency.call is require_admin_user or any(
            is_admin(child) for child in dependency.dependencies
        )

    return [route for route in iter_route_contexts(routes) if (
        isinstance(route.original_route, APIRoute)
        and route.include_in_schema
        and any(route.path == prefix or route.path.startswith(prefix + "/")
                for prefix in CLIENT_PREFIXES)
        and not is_admin(route.dependant)
    )]


def _worker() -> dict:
    # -I excludes caller Python paths. Only the verified backend root is added.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    sys.addaudithook(deny_network)
    # Existing imports log to stdout. Keep machine-readable output separate.
    with contextlib.redirect_stdout(sys.stderr):
        from fastapi.openapi.utils import get_openapi
        from app.main import app

        return get_openapi(
            title=app.title, version=app.version, description=app.description,
            openapi_version=app.openapi_version, routes=client_routes(app.routes),
        )


def export_document() -> dict:
    # Empty cwd prevents pydantic-settings from reading a checkout .env; dotenv
    # discovery is separately disabled. Import logging stays in this temp folder.
    with tempfile.TemporaryDirectory(prefix="prismpro-contracts-") as directory:
        result = subprocess.run(
            [sys.executable, "-I", str(Path(__file__).resolve()), "--worker"],
            cwd=directory, env=EXPORT_ENV, capture_output=True, text=True,
            timeout=30, check=True,
        )
    return json.loads(result.stdout)


if __name__ == "__main__":
    document = _worker() if sys.argv[1:] == ["--worker"] else export_document()
    print(json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False))
