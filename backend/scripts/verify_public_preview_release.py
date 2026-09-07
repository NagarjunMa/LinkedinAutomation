"""Verify the live PrismPro public-preview release gates.

The default run is read-only. Passing ``--write-smoke`` additionally creates a
unique example.com waitlist record, verifies idempotency and the route limits,
then deletes only that generated record.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import uuid
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError


EXPECTED_ALEMBIC_REVISION = "2026_09_07_waitlist_retention"
RETENTION_JOB_NAME = "prismpro-waitlist-retention-daily"
RETENTION_JOB_SCHEDULE = "17 3 * * *"
MANAGEMENT_API = "https://api.supabase.com/v1/projects/{project_ref}/config/auth"
USER_AGENT = "PrismPro-Release-Verification/1.0"


class GateFailure(RuntimeError):
    """Raised when a production release invariant is not satisfied."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GateFailure(message)


def _origin(value: str, *, allow_http: bool = False) -> str:
    parsed = urlsplit(value)
    allowed_schemes = {"https", "http"} if allow_http else {"https"}
    try:
        port = parsed.port
    except ValueError as exc:
        raise GateFailure(f"Invalid origin: {value}") from exc
    _require(parsed.scheme in allowed_schemes, f"Origin must use HTTPS: {value}")
    _require(bool(parsed.hostname), f"Origin must include a hostname: {value}")
    _require(parsed.username is None and parsed.password is None, "Origin cannot contain credentials")
    _require(parsed.path in ("", "/") and not parsed.query and not parsed.fragment, "Origin must not contain a path, query, or fragment")
    _require("*" not in value, "Origin cannot contain a wildcard")
    _require(not any(character.isspace() for character in value), "Origin cannot contain whitespace")

    hostname = parsed.hostname or ""
    host = f"[{hostname}]" if ":" in hostname else hostname
    default_port = 443 if parsed.scheme == "https" else 80
    port_suffix = f":{port}" if port is not None and port != default_port else ""
    canonical = f"{parsed.scheme}://{host}{port_suffix}"
    _require(value.rstrip("/") == canonical, f"Origin must use canonical form: {value}")
    return canonical


def verify_supabase_auth(
    session: requests.Session,
    *,
    project_ref: str,
    access_token: str,
) -> None:
    _require(
        bool(re.fullmatch(r"[a-z0-9]{20}", project_ref)),
        "Supabase project ref must be exactly 20 lowercase letters or digits",
    )
    response = session.get(
        MANAGEMENT_API.format(project_ref=project_ref),
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    _require(response.status_code == 200, f"Supabase Auth config returned HTTP {response.status_code}")
    config = response.json()
    _require(config.get("disable_signup") is True, "Supabase public signup is still enabled")
    _require(
        config.get("external_anonymous_users_enabled") is False,
        "Supabase anonymous sign-in is still enabled",
    )


def verify_database(engine: Engine) -> None:
    with engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        _require(revision == EXPECTED_ALEMBIC_REVISION, f"Database revision is {revision}, expected {EXPECTED_ALEMBIC_REVISION}")

        row_security = connection.execute(
            text(
                "SELECT relrowsecurity FROM pg_class "
                "WHERE oid = 'public.waitlist_entries'::regclass"
            )
        ).scalar_one()
        _require(row_security is True, "RLS is not enabled on public.waitlist_entries")

        roles = {
            row.rolname
            for row in connection.execute(
                text("SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated')")
            )
        }
        _require(roles == {"anon", "authenticated"}, "Supabase anon/authenticated roles are missing")
        for role in sorted(roles):
            has_access = connection.execute(
                text(
                    "SELECT has_table_privilege(:role, 'public.waitlist_entries', "
                    "'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')"
                ),
                {"role": role},
            ).scalar_one()
            _require(not has_access, f"Role {role} still has waitlist table privileges")

        unique_email = connection.execute(
            text(
                "SELECT EXISTS ("
                "SELECT 1 FROM pg_constraint "
                "WHERE conrelid = 'public.waitlist_entries'::regclass "
                "AND conname = 'uq_waitlist_entries_email' AND contype = 'u')"
            )
        ).scalar_one()
        _require(unique_email is True, "Waitlist email uniqueness constraint is missing")

        retention_index = connection.execute(
            text(
                "SELECT to_regclass('public.ix_waitlist_entries_retention_expires_at') "
                "IS NOT NULL"
            )
        ).scalar_one()
        _require(retention_index is True, "Waitlist retention index is missing")

        cron_enabled = connection.execute(
            text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron')")
        ).scalar_one()
        _require(cron_enabled is True, "pg_cron is not enabled")

        cron_job = connection.execute(
            text(
                "SELECT jobid, schedule, command, active FROM cron.job "
                "WHERE jobname = :job_name"
            ),
            {"job_name": RETENTION_JOB_NAME},
        ).mappings().one_or_none()
        _require(cron_job is not None, "Waitlist retention cron job is missing")
        _require(cron_job["active"] is True, "Waitlist retention cron job is inactive")
        _require(cron_job["schedule"] == RETENTION_JOB_SCHEDULE, "Waitlist retention cron schedule is unexpected")
        normalized_command = " ".join(cron_job["command"].split()).upper()
        _require(
            normalized_command
            == "DELETE FROM PUBLIC.WAITLIST_ENTRIES WHERE RETENTION_EXPIRES_AT <= CURRENT_TIMESTAMP",
            "Waitlist retention cron command is unexpected",
        )

        successful_run = connection.execute(
            text(
                "SELECT EXISTS ("
                "SELECT 1 FROM cron.job_run_details "
                "WHERE jobid = :job_id AND status = 'succeeded' "
                "AND end_time IS NOT NULL)"
            ),
            {"job_id": cron_job["jobid"]},
        ).scalar_one()
        _require(
            successful_run is True,
            "Waitlist retention cron has no recorded successful run",
        )


def _assert_root_redirect(response: requests.Response, *, label: str, frontend_origin: str) -> None:
    _require(response.status_code in {301, 302, 303, 307, 308}, f"{label} returned HTTP {response.status_code}")
    location = response.headers.get("Location", "")
    _require(urljoin(frontend_origin, location) == f"{frontend_origin}/", f"{label} did not redirect to the landing page")
    _require("Set-Cookie" not in response.headers, f"{label} unexpectedly created a session cookie")


def verify_http(
    session: requests.Session,
    *,
    backend_url: str,
    frontend_origin: str,
    allow_http: bool = False,
) -> None:
    backend_url = _origin(backend_url, allow_http=allow_http)
    frontend_origin = _origin(frontend_origin, allow_http=allow_http)
    headers = {"User-Agent": USER_AGENT}

    landing = session.get(f"{frontend_origin}/", headers=headers, timeout=15)
    _require(landing.status_code == 200, f"Landing page returned HTTP {landing.status_code}")
    _require("Join the private preview" in landing.text, "Landing page is missing the preview CTA")

    health = session.get(f"{backend_url}/health", headers=headers, timeout=15)
    _require(health.status_code == 200, f"Backend health returned HTTP {health.status_code}")
    _require("no-store" in health.headers.get("Cache-Control", ""), "Backend health response is cacheable")

    for path in ("/", "/docs", "/redoc", "/openapi.json", "/metrics"):
        blocked_backend_route = session.get(
            f"{backend_url}{path}",
            headers=headers,
            timeout=15,
            allow_redirects=False,
        )
        _require(
            blocked_backend_route.status_code == 403,
            f"Backend route {path} returned HTTP {blocked_backend_route.status_code}, expected 403",
        )

    product = session.get(
        f"{backend_url}/api/v1/resumes",
        headers={**headers, "Authorization": "Bearer release-verification-token"},
        timeout=15,
    )
    _require(product.status_code == 403, f"Product API lockdown returned HTTP {product.status_code}, expected 403")

    for path in ("/login", "/onboarding", "/dashboard", "/dashboard/resume/example"):
        blocked_route = session.get(
            f"{frontend_origin}{path}",
            headers=headers,
            timeout=15,
            allow_redirects=False,
        )
        _assert_root_redirect(
            blocked_route,
            label=f"Public route {path}",
            frontend_origin=frontend_origin,
        )

    callback = session.get(
        f"{frontend_origin}/api/auth/callback?code=release-verification",
        headers=headers,
        timeout=15,
        allow_redirects=False,
    )
    _assert_root_redirect(callback, label="OAuth callback", frontend_origin=frontend_origin)

    confirmation = session.get(
        f"{frontend_origin}/api/auth/confirm?token_hash=release-verification&type=signup",
        headers=headers,
        timeout=15,
        allow_redirects=False,
    )
    _assert_root_redirect(confirmation, label="Auth confirmation", frontend_origin=frontend_origin)

    preflight_headers = {
        **headers,
        "Origin": frontend_origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    allowed = session.options(
        f"{backend_url}/api/v1/waitlist",
        headers=preflight_headers,
        timeout=15,
    )
    _require(allowed.status_code == 200, f"Allowed CORS preflight returned HTTP {allowed.status_code}")
    _require(allowed.headers.get("Access-Control-Allow-Origin") == frontend_origin, "Allowed CORS origin was not echoed exactly")

    denied = session.options(
        f"{backend_url}/api/v1/waitlist",
        headers={**preflight_headers, "Origin": "https://release-verification.invalid"},
        timeout=15,
    )
    _require("Access-Control-Allow-Origin" not in denied.headers, "An unapproved CORS origin was allowed")


def verify_waitlist_write_smoke(
    session: requests.Session,
    *,
    backend_url: str,
    engine: Engine,
    allow_http: bool = False,
) -> None:
    backend_url = _origin(backend_url, allow_http=allow_http)
    smoke_email = f"prismpro-release-smoke-{uuid.uuid4().hex}@example.com"
    payload: dict[str, Any] = {
        "email": smoke_email,
        "career_stage": "experienced_ic",
        "target_role": "Release verification",
        "communication_challenge": "Automated production smoke record",
        "consent": True,
        "company_website": "",
    }
    headers = {
        "User-Agent": USER_AGENT,
        # The middleware hashes this value only to isolate the bounded smoke
        # from live anonymous traffic. The endpoint does not authenticate it.
        "Authorization": f"Bearer prismpro-release-write-{uuid.uuid4().hex}",
    }

    try:
        oversized = session.post(
            f"{backend_url}/api/v1/waitlist",
            headers=headers,
            json={**payload, "communication_challenge": "x" * 9000},
            timeout=15,
        )
        _require(oversized.status_code == 413, f"Waitlist body limit returned HTTP {oversized.status_code}, expected 413")

        first = session.post(
            f"{backend_url}/api/v1/waitlist", headers=headers, json=payload, timeout=15
        )
        duplicate = session.post(
            f"{backend_url}/api/v1/waitlist", headers=headers, json=payload, timeout=15
        )
        _require(first.status_code == duplicate.status_code == 202, "Waitlist new/duplicate responses were not both 202")
        _require(first.json() == duplicate.json(), "Waitlist duplicate response disclosed membership")

        with engine.connect() as connection:
            count = connection.execute(
                text(
                    "SELECT count(*) FROM public.waitlist_entries "
                    "WHERE normalized_email = :email"
                ),
                {"email": smoke_email},
            ).scalar_one()
        _require(count == 1, f"Waitlist write smoke persisted {count} rows, expected one")

        limited = session.post(
            f"{backend_url}/api/v1/waitlist", headers=headers, json=payload, timeout=15
        )
        _require(limited.status_code == 429, f"Waitlist burst limit returned HTTP {limited.status_code}, expected 429")
    finally:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM public.waitlist_entries "
                    "WHERE normalized_email = :email "
                    "AND source = 'public_preview_landing'"
                ),
                {"email": smoke_email},
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-url", required=True)
    parser.add_argument("--frontend-origin", required=True)
    parser.add_argument("--supabase-project-ref", required=True)
    parser.add_argument(
        "--database-url",
        default=os.getenv("SQLALCHEMY_DATABASE_URI"),
        help="Administrative PostgreSQL URL; defaults to SQLALCHEMY_DATABASE_URI.",
    )
    parser.add_argument(
        "--supabase-access-token",
        default=os.getenv("SUPABASE_ACCESS_TOKEN"),
        help="Supabase Management API token; defaults to SUPABASE_ACCESS_TOKEN.",
    )
    parser.add_argument(
        "--write-smoke",
        action="store_true",
        help="Run a bounded waitlist write/dedup/rate-limit smoke and clean it up.",
    )
    parser.add_argument(
        "--allow-http",
        action="store_true",
        help="Allow local HTTP endpoints. Never use this for a production release.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    session = requests.Session()
    engine: Engine | None = None
    try:
        _require(
            bool(args.database_url),
            "--database-url or SQLALCHEMY_DATABASE_URI is required",
        )
        _require(
            bool(args.supabase_access_token),
            "--supabase-access-token or SUPABASE_ACCESS_TOKEN is required",
        )
        engine = create_engine(args.database_url, pool_pre_ping=True)
        verify_supabase_auth(
            session,
            project_ref=args.supabase_project_ref,
            access_token=args.supabase_access_token,
        )
        print("PASS Supabase signup and anonymous sign-in are disabled")
        verify_database(engine)
        print("PASS migration, RLS, privileges, constraints, and retention cron")
        verify_http(
            session,
            backend_url=args.backend_url,
            frontend_origin=args.frontend_origin,
            allow_http=args.allow_http,
        )
        print("PASS health, preview lockdown, auth callbacks, and exact CORS")
        if args.write_smoke:
            verify_waitlist_write_smoke(
                session,
                backend_url=args.backend_url,
                engine=engine,
                allow_http=args.allow_http,
            )
            print("PASS waitlist body limit, idempotency, persistence, cleanup, and rate limit")
        else:
            print("SKIP waitlist write smoke (pass --write-smoke to enable the bounded mutation)")
    except (GateFailure, requests.RequestException, SQLAlchemyError, ValueError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()
        if engine is not None:
            engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
