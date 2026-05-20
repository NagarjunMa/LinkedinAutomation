import os
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.db.base_class import Base


def _create_sqlite_tables(engine) -> None:
    """Create only the tables whose columns are SQLite-compatible.

    Models that use PostgreSQL-only types (JSONB) cannot be created on SQLite.
    We create only what the credit-ledger and middleware tests actually need:
    ``users`` and ``credit_ledger``.
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

    meta.create_all(bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
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
