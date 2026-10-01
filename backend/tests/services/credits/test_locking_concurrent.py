"""Actual PostgreSQL credit locking; selected by CI's `-k concurrent` gate."""

from concurrent.futures import ThreadPoolExecutor
import os
from threading import Barrier, Event
import time
from uuid import uuid4

import pytest
from sqlalchemy import MetaData, create_engine, event, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.application.credits import paid_operation
from app.application.bootstrap import bootstrap_account
from app.application.errors import ExternalServiceError
from app.models.credit_ledger import CreditLedger
from app.models.user import User
from app.services.credits.ledger import (
    InsufficientCredits, debit, get_balance, grant_monthly, refund,
)

pytestmark = pytest.mark.postgres


@pytest.fixture
def postgres_ledger():
    url = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
    if make_url(url).get_backend_name() != "postgresql":
        pytest.skip("requires PostgreSQL for real credit locks")
    schema = f"credit_lock_test_{uuid4().hex}"
    admin = create_engine(url)
    with admin.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={
        "options": f"-csearch_path={schema} -cstatement_timeout=5000 -clock_timeout=2000",
    })
    try:
        metadata = MetaData()
        User.__table__.to_metadata(metadata)
        CreditLedger.__table__.to_metadata(metadata)
        metadata.create_all(engine)
        with Session(engine) as db:
            db.add_all([User(user_id="alice", email=None), User(user_id="bob", email=None)])
            db.commit()
            grant_monthly(db, "alice", 5)
            grant_monthly(db, "bob", 5)
            db.commit()
        yield engine
    finally:
        engine.dispose()
        with admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


@pytest.mark.parametrize("operation", ["debit", "grant", "refund"])
def test_each_credit_operation_waits_for_its_user_only(postgres_ledger, operation):
    started = Event()
    statements = []
    def record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)
    def run():
        with Session(postgres_ledger) as db:
            event.listen(db.connection(), "before_cursor_execute", record)
            started.set()
            if operation == "grant":
                grant_monthly(db, "alice", 3)
            else:
                {"debit": debit, "refund": refund}[operation](db, "alice", 3, "test")
            db.commit()

    with (
        Session(postgres_ledger) as holder,
        ThreadPoolExecutor(max_workers=1) as pool,
        postgres_ledger.connect() as observer,
    ):
        pid = holder.scalar(text("SELECT pg_backend_pid()"))
        holder.execute(select(User.user_id).where(User.user_id == "alice").with_for_update())
        # Exercise the race where the observer samples activity before the
        # worker opens its connection. Later polls must see the new backend.
        observer.execute(text("SELECT pid FROM pg_stat_activity")).all()
        future = pool.submit(run)
        try:
            assert started.wait(timeout=3)
            deadline = time.monotonic() + 1.5
            while True:
                # Activity snapshots are cached for the observer transaction.
                observer.execute(text("SELECT pg_stat_clear_snapshot()"))
                blocked = observer.scalar(text(
                    "SELECT EXISTS (SELECT 1 FROM pg_stat_activity "
                    "WHERE :pid = ANY(pg_blocking_pids(pid)))"
                ), {"pid": pid})
                if blocked or future.done() or time.monotonic() >= deadline:
                    break
                time.sleep(0.01)
            assert blocked, "credit operation did not wait on its user's row lock"
            assert not future.done()
            # An insert's foreign-key lock also waits on the holder, but is too
            # late to protect the balance read. Require the ledger's early lock.
            assert not any(
                "sum(" in sql.lower() or "insert into credit_ledger" in sql.lower()
                for sql in statements
            ), "balance reads and ledger inserts must wait for the user's lock"
            # A different user's debit must not wait for Alice's lock.
            with Session(postgres_ledger) as other:
                debit(other, "bob", 3, "independent")
                other.commit()
        finally:
            holder.rollback()
        future.result(timeout=5)
    with Session(postgres_ledger) as db:
        assert get_balance(db, "alice") == (2 if operation == "debit" else 8)
        assert get_balance(db, "bob") == 2


def test_simultaneous_debits_cannot_overspend(postgres_ledger):
    barrier = Barrier(6)
    def run(_):
        with Session(postgres_ledger) as db:
            barrier.wait(timeout=5)
            try:
                debit(db, "alice", 3, "race")
                db.commit()
                return "debited"
            except InsufficientCredits:
                db.rollback()
                return "insufficient"
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(run, range(6)))
    assert results.count("debited") == 1
    assert results.count("insufficient") == 5
    with Session(postgres_ledger) as db:
        assert get_balance(db, "alice") == 2
        rows = db.scalars(select(CreditLedger).where(CreditLedger.user_id == "alice")).all()
        assert sorted((r.delta, r.balance_after) for r in rows) == [(-3, 2), (5, 5)]


def test_original_lock_timeout_survives_without_followup_queries(postgres_ledger):
    statements = []
    def record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)
    with Session(postgres_ledger) as holder, Session(postgres_ledger) as blocked:
        holder.execute(select(User.user_id).where(User.user_id == "alice").with_for_update())
        blocked.execute(text("SET LOCAL lock_timeout = '100ms'"))
        event.listen(blocked.connection(), "before_cursor_execute", record)
        with pytest.raises(OperationalError) as failure:
            debit(blocked, "alice", 3, "blocked")
        assert failure.value.orig.pgcode == "55P03"
        assert not any("sum(" in sql.lower() or "INSERT INTO credit_ledger" in sql for sql in statements)
        blocked.rollback()
        assert get_balance(blocked, "alice") == 5


def test_paid_lock_failure_rolls_back_and_can_recover(postgres_ledger):
    with Session(postgres_ledger) as holder, Session(postgres_ledger) as db:
        holder.execute(select(User.user_id).where(User.user_id == "alice").with_for_update())
        db.execute(text("SET LOCAL lock_timeout = '100ms'"))
        db.execute(text("UPDATE users SET full_name='pending' WHERE user_id='bob'"))
        with pytest.raises(ExternalServiceError, match="Credit service unavailable"):
            with paid_operation(db, "alice", 3, "test"):
                pytest.fail("paid work must not start")
        assert db.scalar(select(User.full_name).where(User.user_id == "bob")) is None
        assert get_balance(db, "alice") == 5
        holder.rollback()
        with paid_operation(db, "alice", 3, "test"):
            pass
        assert get_balance(db, "alice") == 2


@pytest.mark.parametrize("isolation", ["REPEATABLE READ", "SERIALIZABLE", "AUTOCOMMIT"])
def test_unsupported_transaction_modes_fail_before_credit_write(postgres_ledger, isolation):
    with Session(postgres_ledger.execution_options(isolation_level=isolation)) as db:
        assert get_balance(db, "alice") == 5
        with pytest.raises(RuntimeError, match="transactional READ COMMITTED"):
            debit(db, "alice", 3, "unsupported")
        db.rollback()
    with Session(postgres_ledger) as db:
        assert get_balance(db, "alice") == 5


@pytest.mark.parametrize("isolation", ["REPEATABLE READ", "AUTOCOMMIT"])
def test_bootstrap_rolls_back_account_when_credit_mode_is_unsupported(postgres_ledger, isolation):
    with Session(postgres_ledger.execution_options(isolation_level=isolation)) as db:
        with pytest.raises(ExternalServiceError):
            bootstrap_account(db, user_id="new", email=None)
        assert db.scalar(select(User.user_id).where(User.user_id == "new")) is None
