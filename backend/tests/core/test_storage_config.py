import pytest
from pydantic import ValidationError

from app.core.config import Settings, settings, validate_production_config


def _production_settings(**overrides):
    values = {
        "ENVIRONMENT": "production",
        "SQLALCHEMY_DATABASE_URI": "postgresql://postgres:password@db.example.com/postgres",
        "SUPABASE_URL": "https://abcdefghijklmnopqrst.supabase.co",
        "SUPABASE_ANON_KEY": "publishable-test-key",
        "SUPABASE_SERVICE_ROLE_KEY": "secret-test-key",
        "CORS_ORIGINS": ["https://www.prismpro.live"],
        "PUBLIC_FRONTEND_ORIGIN": "https://www.prismpro.live",
        "PRISM_PRO_PUBLIC_PREVIEW_ONLY": True,
        "BACKEND_REPLICA_COUNT": 1,
        "WEB_CONCURRENCY": 1,
        "OPENAI_API_KEY": "test",
        "ADMIN_USER_IDS": "00000000-0000-0000-0000-000000000000",
        "SECRET_KEY": "x" * 32,
    }
    values.update(overrides)
    return Settings(**values)


def test_production_public_preview_accepts_exact_single_origin_and_process():
    production = _production_settings()

    assert production.PRISM_PRO_PUBLIC_PREVIEW_ONLY is True


def test_production_public_preview_model_validation_fails_closed():
    with pytest.raises(ValidationError, match="one backend replica and one worker"):
        _production_settings(WEB_CONCURRENCY=2)


def test_storage_bucket_defaults_to_launch_bucket():
    assert settings.SUPABASE_STORAGE_BUCKET == "resume"


def test_production_validation_rejects_wrong_storage_bucket(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_STORAGE_BUCKET", "resumes")

    assert "SUPABASE_STORAGE_BUCKET must be 'resume'" in validate_production_config()


def test_production_validation_rejects_sqlite_database(monkeypatch):
    monkeypatch.setattr(settings, "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

    assert "SQLALCHEMY_DATABASE_URI must use PostgreSQL in production" in validate_production_config()


def test_production_validation_rejects_localhost_cors(monkeypatch):
    monkeypatch.setattr(settings, "CORS_ORIGINS", ["https://www.prismpro.live", "http://localhost:3000"])

    assert "CORS_ORIGINS must not include localhost origins in production" in validate_production_config()


def test_public_preview_requires_one_exact_canonical_origin(monkeypatch):
    monkeypatch.setattr(settings, "PRISM_PRO_PUBLIC_PREVIEW_ONLY", True)
    monkeypatch.setattr(settings, "PUBLIC_FRONTEND_ORIGIN", "https://www.prismpro.live")
    monkeypatch.setattr(
        settings,
        "CORS_ORIGINS",
        ["https://www.prismpro.live", "https://prismpro.live"],
    )

    assert (
        "Public preview requires CORS_ORIGINS to contain only "
        "PUBLIC_FRONTEND_ORIGIN"
    ) in validate_production_config()


def test_production_validation_rejects_non_origin_cors_values(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_FRONTEND_ORIGIN", "https://www.prismpro.live")
    monkeypatch.setattr(settings, "CORS_ORIGINS", ["https://www.prismpro.live/api"])

    assert (
        "CORS_ORIGINS must contain exact HTTPS origins without paths, "
        "credentials, queries, fragments, or wildcards"
    ) in validate_production_config()


def test_public_preview_requires_single_process_rate_limiting(monkeypatch):
    monkeypatch.setattr(settings, "PRISM_PRO_PUBLIC_PREVIEW_ONLY", True)
    monkeypatch.setattr(settings, "PUBLIC_FRONTEND_ORIGIN", "https://www.prismpro.live")
    monkeypatch.setattr(settings, "CORS_ORIGINS", ["https://www.prismpro.live"])
    monkeypatch.setattr(settings, "BACKEND_REPLICA_COUNT", 2)
    monkeypatch.setattr(settings, "WEB_CONCURRENCY", 1)

    assert (
        "Public preview requires one backend replica and one worker "
        "while rate limiting is process-local"
    ) in validate_production_config()


def test_production_validation_requires_admin_allowlist(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_USER_IDS", "")

    assert "ADMIN_USER_IDS is required" in validate_production_config()


def test_production_validation_does_not_require_resend_for_mvp(monkeypatch):
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")

    assert "RESEND_API_KEY is recommended for email functionality" not in validate_production_config()
