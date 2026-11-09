"""Real PostgreSQL first-contact races and scheduled-grant compatibility."""

import importlib.util
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue
from threading import Barrier
from time import monotonic, sleep
from uuid import uuid4

import pytest
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.orm import Session

from app.application.bootstrap import bootstrap_account
from app.application.errors import ResourceConflictError
from app.models.credit_ledger import CreditLedger
from app.models.user import User
from app.services.credits.ledger import debit


@pytest.fixture
def postgres_bootstrap():
    url = os.environ.get("DATABASE_URL", "")
    if "postgres" not in url:
        pytest.skip("requires PostgreSQL for first-contact concurrency")
    # All data and the actual scheduled function live in a disposable schema.
    schema = f"bootstrap_test_{uuid4().hex}"
    admin = create_engine(url)
    with admin.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    try:
        meta = MetaData()
        User.__table__.to_metadata(meta)
        CreditLedger.__table__.to_metadata(meta)
        meta.create_all(engine)
        path = Path(__file__).parents[3] / "migrations/versions/2026_11_09_reconcile_monthly_credits.py"
        spec = importlib.util.spec_from_file_location("monthly_migration", path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        with engine.begin() as conn:
            conn.execute(text(migration.GRANT_FN_SQL.replace("public.", f'"{schema}".')))
        yield engine
    finally:
        engine.dispose()
        with admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


def test_concurrent_bootstrap_and_monthly_job_grant_once(postgres_bootstrap):
    barrier = Barrier(10)
    def run(index):
        with Session(postgres_bootstrap) as db:
            barrier.wait(timeout=10)
            if index < 8:
                bootstrap_account(db, user_id="new", email="new@example.com")
            else:
                db.execute(text("SELECT grant_monthly_credits()"))
                db.commit()
    with ThreadPoolExecutor(max_workers=10) as pool:
        list(pool.map(run, range(10)))
    with Session(postgres_bootstrap) as db:
        db.execute(text("SELECT grant_monthly_credits()"))
        db.commit()
        assert db.query(User).filter_by(user_id="new").count() == 1
        rows = db.query(CreditLedger).filter_by(user_id="new").all()
        assert len(rows) == 1
        assert rows[0].delta == rows[0].balance_after == 90
        assert rows[0].external_ref.endswith(":new")


def test_concurrent_monthly_jobs_and_existing_account_bootstrap(postgres_bootstrap):
    with Session(postgres_bootstrap) as db:
        db.add(User(user_id="existing", email=None))
        db.commit()
    barrier = Barrier(3)
    def run(index):
        with Session(postgres_bootstrap) as db:
            barrier.wait(timeout=10)
            if index == 0:
                bootstrap_account(db, user_id="existing", email=None)
            else:
                db.execute(text("SELECT grant_monthly_credits()"))
                db.commit()
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(run, range(3)))
    with Session(postgres_bootstrap) as db:
        assert db.query(CreditLedger).filter_by(user_id="existing").one().delta == 90


def test_monthly_grant_reads_balance_after_concurrent_debit(postgres_bootstrap):
    with Session(postgres_bootstrap) as db:
        db.add(User(user_id="existing"))
        db.flush()
        db.add(CreditLedger(id="opening", user_id="existing", delta=100, balance_after=100, reason="grant"))
        db.commit()

    job_pid = Queue()

    def run_job():
        with postgres_bootstrap.begin() as conn:
            conn.execute(text("SET LOCAL statement_timeout = '10s'"))
            job_pid.put(conn.scalar(text("SELECT pg_backend_pid()")))
            return conn.scalar(text("SELECT grant_monthly_credits()"))

    with ThreadPoolExecutor(max_workers=1) as pool, Session(postgres_bootstrap) as db:
        assert debit(db, "existing", 10, "test_debit").balance_after == 90
        job = pool.submit(run_job)
        pid = job_pid.get(timeout=5)
        deadline = monotonic() + 5
        while not db.scalar(text("SELECT pg_backend_pid() = ANY(pg_blocking_pids(:pid))"), {"pid": pid}):
            assert monotonic() < deadline, "Monthly grant did not wait on the debit"
            sleep(0.01)
        db.commit()
        assert job.result(timeout=5) == 1

    with Session(postgres_bootstrap) as db:
        monthly = db.query(CreditLedger).filter(CreditLedger.external_ref.is_not(None)).one()
        assert (monthly.delta, monthly.balance_after) == (90, 180)
        assert db.scalar(text("SELECT grant_monthly_credits()")) == 0


def test_monthly_job_preserves_a_previous_grant_for_the_same_period(postgres_bootstrap):
    with Session(postgres_bootstrap) as db:
        db.add_all([User(user_id="already-credited"), User(user_id="due")])
        db.commit()
        db.execute(text("""
            INSERT INTO credit_ledger (id, user_id, delta, reason, balance_after, external_ref)
            VALUES ('legacy', 'already-credited', 20, 'grant', 20,
                'monthly:' || to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM') || ':' || 'already-credited')
        """))
        assert db.scalar(text("SELECT grant_monthly_credits()")) == 1
        assert db.scalar(text("SELECT grant_monthly_credits(90)")) == 0
        entries = db.query(CreditLedger).order_by(CreditLedger.user_id).all()
        assert [(entry.user_id, entry.delta, entry.balance_after) for entry in entries] == [
            ("already-credited", 20, 20),
            ("due", 90, 90),
        ]


def test_concurrent_different_identities_cannot_share_email(postgres_bootstrap):
    barrier = Barrier(2)
    def run(user_id):
        with Session(postgres_bootstrap) as db:
            barrier.wait(timeout=10)
            try:
                bootstrap_account(db, user_id=user_id, email="shared@example.com")
                return "created"
            except ResourceConflictError:
                return "conflict"
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(run, ["alice", "bob"])) == ["conflict", "created"]
    with Session(postgres_bootstrap) as db:
        owner = db.query(User).one()
        grant = db.query(CreditLedger).one()
        assert grant.user_id == owner.user_id
        assert grant.delta == 90
