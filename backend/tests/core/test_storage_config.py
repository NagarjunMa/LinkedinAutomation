from app.core.config import settings, validate_production_config


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


def test_production_validation_requires_admin_allowlist(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_USER_IDS", "")

    assert "ADMIN_USER_IDS is required" in validate_production_config()


def test_production_validation_does_not_require_resend_for_mvp(monkeypatch):
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")

    assert "RESEND_API_KEY is recommended for email functionality" not in validate_production_config()
