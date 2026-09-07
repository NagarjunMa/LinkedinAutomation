import os
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
# Must be set BEFORE app.core.config is imported so Session uses SQLite
os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
# Minimal stub values expected by Settings validators
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("PRISM_PRO_PUBLIC_PREVIEW_ONLY", "false")

import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, JSON
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool


def _create_sqlite_tables(engine) -> None:
    """Create only the tables whose columns are SQLite-compatible.

    Models that use PostgreSQL-only types (JSONB) cannot be created on SQLite.
    We create what the tests actually need, using JSON (not JSONB) for
    SQLite-compatible columns.
    """
    # Import models so they register on Base.metadata
    from app.models.user import User  # noqa: F401
    from app.models.credit_ledger import CreditLedger  # noqa: F401

    # Build a minimal metadata with only the compatible tables.
    meta = sa.MetaData()

    sa.Table(
        "users",
        meta,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("email", sa.String(255), unique=True),
        sa.Column("full_name", sa.String(255)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )

    sa.Table(
        "credit_ledger",
        meta,
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("user_id", sa.String, sa.ForeignKey("users.user_id"), nullable=False, index=True),
        sa.Column("delta", sa.Integer, nullable=False),
        sa.Column("reason", sa.String, nullable=False),
        sa.Column("balance_after", sa.Integer, nullable=False),
        sa.Column("external_ref", sa.String, nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    sa.Table(
        "waitlist_entries",
        meta,
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("normalized_email", sa.String(254), nullable=False, unique=True),
        sa.Column("career_stage", sa.String(40)),
        sa.Column("target_role", sa.String(120)),
        sa.Column("communication_challenge", sa.Text),
        sa.Column("consent_granted", sa.Boolean, nullable=False),
        sa.Column("consent_version", sa.String(32), nullable=False),
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("retention_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Phase-1 resume tables — using JSON instead of JSONB for SQLite compatibility
    sa.Table(
        "resume_documents",
        meta,
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("user_id", sa.String, sa.ForeignKey("users.user_id"), nullable=False, index=True),
        sa.Column("original_filename", sa.String, nullable=False),
        sa.Column("file_path", sa.String, nullable=False),
        sa.Column("storage_path", sa.String, nullable=True),
        sa.Column("storage_status", sa.String(16), nullable=False, server_default="ready"),
        sa.Column("file_type", sa.String, nullable=False),
        sa.Column("parsed_json", JSON, nullable=False),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    sa.Table(
        "resume_evaluations_v2",
        meta,
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("resume_document_id", sa.String, sa.ForeignKey("resume_documents.id"), nullable=False, index=True),
        sa.Column("user_id", sa.String, sa.ForeignKey("users.user_id"), nullable=False, index=True),
        sa.Column("overall_score", sa.Integer, nullable=False),
        sa.Column("bullet_flags", JSON, nullable=False),
        sa.Column("format_issues", JSON, nullable=False),
        sa.Column("readiness_label", sa.String, nullable=False, server_default="needs_work"),
        sa.Column("score_breakdown", JSON, nullable=False, server_default="{}"),
        sa.Column("score_explanation", JSON, nullable=False, server_default="[]"),
        sa.Column("top_actions_before_applying", JSON, nullable=False, server_default="[]"),
        sa.Column("parser_confidence", sa.String, nullable=False, server_default="medium"),
        sa.Column("summary_critique", sa.Text, nullable=True),
        sa.Column("ats_parseability", sa.Integer, nullable=False),
        sa.Column("ats_raw_text", sa.Text, nullable=False),
        sa.Column("model_version", sa.String, nullable=False),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    sa.Table(
        "resume_versions",
        meta,
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("resume_document_id", sa.String, sa.ForeignKey("resume_documents.id"), nullable=False, index=True),
        sa.Column("parent_version_id", sa.String, nullable=True),
        sa.Column("change_set", JSON, nullable=False),
        sa.Column("parsed_json", JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("jd_evaluation_id", sa.String, sa.ForeignKey("jd_evaluations.id"), nullable=True, index=True),
        sa.Column("accepted_at", sa.DateTime, nullable=True),
        sa.Column("template_id", sa.String, nullable=True),
        sa.Column("company_name", sa.String, nullable=True),
        sa.Column("target_role_title", sa.String, nullable=True),
        sa.Column("role_category", sa.String, nullable=True),
        sa.Column("seniority", sa.String, nullable=True),
        sa.Column("country_hint", sa.String, nullable=True),
        sa.Column("match_score", sa.Integer, nullable=True),
        sa.Column("source_jd_text", sa.Text, nullable=True),
    )

    sa.Table(
        "jd_evaluations",
        meta,
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("user_id", sa.String, sa.ForeignKey("users.user_id"), nullable=False, index=True),
        sa.Column("resume_document_id", sa.String, sa.ForeignKey("resume_documents.id"), nullable=False),
        sa.Column("jd_text", sa.Text, nullable=False),
        sa.Column("extracted_requirements", JSON, nullable=False),
        sa.Column("diff_plan", JSON, nullable=False),
        sa.Column("match_score", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    sa.Table(
        "resume_exports",
        meta,
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("user_id", sa.String, sa.ForeignKey("users.user_id"), nullable=False, index=True),
        sa.Column("resume_document_id", sa.String, sa.ForeignKey("resume_documents.id"), nullable=False, index=True),
        sa.Column("resume_version_id", sa.String, nullable=True),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("role_template", sa.String(8), nullable=False),
        sa.Column("storage_path", sa.String, nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="succeeded"),
        sa.Column("render_ms", sa.Integer, nullable=True),
        sa.Column("file_size_bytes", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Legacy AI-extracted profile table (used by user-profiles endpoint).
    # All columns are SQLite-compatible (JSON, not JSONB).
    sa.Table(
        "user_profiles",
        meta,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("full_name", sa.String(255)),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(50)),
        sa.Column("location", sa.String(255)),
        sa.Column("work_authorization", sa.String(100)),
        sa.Column("years_of_experience", sa.Float, default=0.0),
        sa.Column("career_level", sa.String(50)),
        sa.Column("professional_summary", sa.Text),
        sa.Column("programming_languages", JSON),
        sa.Column("frameworks_libraries", JSON),
        sa.Column("tools_platforms", JSON),
        sa.Column("soft_skills", JSON),
        sa.Column("job_titles", JSON),
        sa.Column("companies", JSON),
        sa.Column("industries", JSON),
        sa.Column("experience_descriptions", JSON),
        sa.Column("degrees", JSON),
        sa.Column("institutions", JSON),
        sa.Column("graduation_years", JSON),
        sa.Column("relevant_coursework", JSON),
        sa.Column("desired_roles", JSON),
        sa.Column("preferred_locations", JSON),
        sa.Column("salary_range_min", sa.Integer),
        sa.Column("salary_range_max", sa.Integer),
        sa.Column("job_types", JSON),
        sa.Column("company_size_preference", JSON),
        sa.Column("ai_profile_summary", sa.Text),
        sa.Column("ai_strengths", JSON),
        sa.Column("ai_improvement_areas", JSON),
        sa.Column("ai_career_advice", sa.Text),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
        sa.Column("last_resume_upload", sa.DateTime),
    )

    sa.Table(
        "profile_settings",
        meta,
        sa.Column(
            "user_id",
            sa.String(100),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            primary_key=True,
            index=True,
        ),
        sa.Column("email_notifications", JSON),
        sa.Column("notification_frequency", sa.String),
        sa.Column("email_forwarding_enabled", sa.String),
        sa.Column("forwarding_address", sa.String),
        sa.Column("last_email_check", sa.DateTime),
        sa.Column("data_retention_days", sa.Integer),
        sa.Column("analytics_enabled", sa.String),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    sa.Table(
        "profile_change_history",
        meta,
        sa.Column("id", sa.String, primary_key=True),
        sa.Column(
            "user_id",
            sa.String(100),
            sa.ForeignKey("users.user_id"),
            nullable=False,
            index=True,
        ),
        sa.Column("field_changed", sa.String, nullable=False),
        sa.Column("old_value", sa.Text),
        sa.Column("new_value", sa.Text),
        sa.Column("changed_at", sa.DateTime, server_default=sa.func.now()),
    )

    sa.Table(
        "job_listings",
        meta,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("company", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255)),
        sa.Column("description", sa.Text),
        sa.Column("requirements", sa.Text),
        sa.Column("job_type", sa.String(50)),
        sa.Column("experience_level", sa.String(50)),
        sa.Column("salary_range", sa.String(100)),
        sa.Column("skills", JSON),
        sa.Column("application_url", sa.Text),
        sa.Column("source", sa.String(50)),
        sa.Column("source_url", sa.Text),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("posted_date", sa.DateTime),
        sa.Column("extracted_date", sa.DateTime),
        sa.Column("applied", sa.Boolean, default=False),
        sa.Column("applied_date", sa.DateTime),
        sa.Column("application_status", sa.String(50), default="pending"),
        sa.Column("application_notes", sa.Text),
        sa.Column("application_context", sa.Text),
        sa.Column("compatibility_score", sa.Float),
        sa.Column("ai_insights", sa.Text),
    )

    sa.Table(
        "job_applications",
        meta,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(100), nullable=False, index=True),
        sa.Column("job_id", sa.Integer, sa.ForeignKey("job_listings.id"), nullable=False, index=True),
        sa.Column("application_status", sa.String(50), default="interested", index=True),
        sa.Column("application_source", sa.String(100)),
        sa.Column("application_date", sa.DateTime),
        sa.Column("external_application_id", sa.String(255)),
        sa.Column("application_url", sa.String(1000)),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("extraction_metadata", JSON),
        sa.Column("user_notes", sa.Text),
        sa.Column("follow_up_date", sa.Date),
        sa.Column("interview_date", sa.DateTime),
        sa.Column("company_response", sa.Boolean, default=False),
        sa.Column("response_date", sa.DateTime),
        sa.Column("rejection_reason", sa.String(500)),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )

    meta.create_all(bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Session:
    # StaticPool ensures all connections reuse the same underlying SQLite
    # connection, so in-memory tables created at setup are visible throughout
    # the test (even after session.commit() releases the connection).
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    _create_sqlite_tables(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def test_user_id(db_session: Session) -> str:
    from app.models.user import User
    u = User(user_id="test-user-1", email="t@t.com")
    db_session.add(u)
    db_session.commit()
    return u.user_id


def _make_sqlite_engine():
    """Return a SQLite in-memory engine using StaticPool for connection reuse."""
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture
def client(db_session: Session, test_user_id: str):
    """FastAPI TestClient with DB and auth overrides.

    Strategy to handle two obstacles:
    1. ``app.db.session`` calls ``create_engine`` with PG-only pool kwargs
       (pool_size, max_overflow) which are invalid for SQLite.
       → We patch ``app.db.session`` so both its ``engine`` and ``get_db``
         point to the per-test ``db_session``.
    2. ``app.main`` calls ``Base.metadata.create_all(bind=engine)`` at module
       level with JSONB columns that SQLite can't compile.
       → We patch ``create_all`` to a no-op for the import phase.
    """
    from unittest.mock import patch, MagicMock

    # --- Build a stub session module that uses db_session ---
    # We patch app.db.session BEFORE importing app.main so that when
    # session.py's module-level code runs it sees a stub engine.
    # If session.py is already imported (subsequent tests), we replace the
    # attributes in-place.

    import sqlalchemy.sql.schema as _schema_mod

    _original_create_all = _schema_mod.MetaData.create_all

    def _noop_create_all(self, bind=None, tables=None, checkfirst=False):
        # Skip JSONB-bearing tables; the test's db_session already has them.
        pass

    # Patch create_all for the duration of the import (or if already imported,
    # this is effectively a no-op since create_all already ran at startup).
    with patch.object(_schema_mod.MetaData, "create_all", _noop_create_all):
        from fastapi.testclient import TestClient
        from app.main import app

    import app.db.session as _session_mod
    from app.core.auth import get_current_user_id, get_authenticated_user_id
    from app.db.session import get_db

    # Override engine to one that matches db_session's engine.
    _original_engine = _session_mod.engine
    _original_session_local = _session_mod.SessionLocal

    # We can't replace the in-memory engine with db_session's engine directly
    # (they're different in-memory DBs).  Instead, just override get_db.
    def _override_get_db():
        yield db_session

    def _override_get_current_user_id():
        return test_user_id

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user_id] = _override_get_current_user_id
    app.dependency_overrides[get_authenticated_user_id] = _override_get_current_user_id

    # Phase 4: mock Supabase Storage so tests never hit the real bucket.
    # Also reset the module-level singleton so each test gets a fresh mock.
    import app.services.storage.supabase_storage as _storage_mod
    from pathlib import Path as _Path
    _original_singleton = _storage_mod._client_instance
    _resume_fixture_bytes = (_Path(__file__).parent / "fixtures/resumes/simple.pdf").read_bytes()
    _mock_storage = MagicMock()
    def _storage_path(user_id, file_id, filename):
        return f"{user_id}/{file_id}.{filename.rsplit('.', 1)[-1].lower()}"

    def _upload(user_id, file_id, content, filename):
        return _storage_path(user_id, file_id, filename)

    _mock_storage.path_for.side_effect = _storage_path
    _mock_storage.upload.side_effect = _upload
    _mock_storage.download.return_value = _resume_fixture_bytes
    _mock_storage.signed_url.return_value = "https://storage.example/file?token=test"
    _storage_mod._client_instance = _mock_storage

    with TestClient(app) as tc:
        yield tc

    # Restore overrides
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user_id, None)
    app.dependency_overrides.pop(get_authenticated_user_id, None)
    # Restore storage singleton
    _storage_mod._client_instance = _original_singleton


@pytest.fixture
def auth_headers() -> dict:
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def user_with_credits(db_session, test_user_id):
    from app.services.credits.ledger import grant_monthly
    grant_monthly(db_session, test_user_id, 20)
    db_session.commit()
    return test_user_id


@pytest.fixture
def uploaded_resume_doc(db_session, test_user_id):
    """A persisted ResumeDocument owned by the test user, for export tests."""
    import uuid
    from app.models.resume_document import ResumeDocument
    from tests.fixtures.resume_doc_json import make_resume
    doc_json = make_resume()
    row = ResumeDocument(
        id=str(uuid.uuid4()),
        user_id=test_user_id,
        original_filename="r.pdf",
        file_path="/tmp/ignored.pdf",
        file_type="pdf",
        parsed_json=doc_json.model_dump(),
        raw_text=doc_json.raw_text,
    )
    db_session.add(row)
    db_session.commit()
    return row


@pytest.fixture
def mock_pdf_render():
    from unittest.mock import patch
    with patch("app.application.export_service.render_pdf_from_doc", return_value=b"%PDF-stub-content"):
        yield


@pytest.fixture
def mock_pdf_render_timeout():
    from unittest.mock import patch
    from app.services.pdf.renderer import PdfRenderTimeout
    with patch("app.application.export_service.render_pdf_from_doc", side_effect=PdfRenderTimeout("simulated")):
        yield


@pytest.fixture
def mock_supabase_upload():
    from unittest.mock import patch
    with patch("app.application.export_service.upload_pdf", return_value="user-1/exp-1.pdf") as m:
        yield m


@pytest.fixture
def mock_signed_url():
    from unittest.mock import patch
    with patch("app.application.export_service.signed_url", return_value="https://supabase.example/file.pdf?token=abc") as m:
        yield m
