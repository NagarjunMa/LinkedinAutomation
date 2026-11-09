import os
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from app.core.config import settings


@pytest.fixture
def migrated_database(monkeypatch):
    url = make_url(os.environ["DATABASE_URL"])
    if url.get_backend_name() != "postgresql":
        pytest.skip("requires a disposable PostgreSQL server")
    assert url.host in {"localhost", "127.0.0.1", "::1"} and not url.query

    database = f"test_migration_{uuid4().hex}"
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    test_url = url.set(database=database)
    engine = create_engine(test_url)
    try:
        with admin.connect() as conn:
            conn.exec_driver_sql(f"CREATE DATABASE {database}")
        monkeypatch.setattr(settings, "SQLALCHEMY_DATABASE_URI", test_url.render_as_string(hide_password=False))
        yield engine, Config("alembic.ini")
    finally:
        engine.dispose()
        with admin.connect() as conn:
            conn.exec_driver_sql(f"DROP DATABASE IF EXISTS {database}")
        admin.dispose()
