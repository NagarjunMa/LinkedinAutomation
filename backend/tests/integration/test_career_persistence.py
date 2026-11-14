"""Exercise owner-scoped Career Evidence services against release migrations."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from queue import Queue
from threading import Barrier, Event
from time import monotonic, sleep
from uuid import uuid4

import pytest
from alembic import command
from sqlalchemy import event, inspect, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from app.application.career_service import CareerApplicationService
from app.application.errors import ResourceConflictError, ResourceNotFoundError
from app.models.resume_document import ResumeDocument
from app.schemas.career.persistence import CareerSourceCreate, CareerTargetInput
from app.models.user import User

pytestmark = pytest.mark.postgres


def test_two_accounts_cannot_read_change_or_link_each_others_records(migrated_database):
    engine, config = migrated_database
    command.upgrade(config, "head")
    owner_a, owner_b = str(uuid4()), str(uuid4())
    with Session(engine) as db, db.begin():
        db.add_all([User(user_id=owner_a), User(user_id=owner_b)])
    with Session(engine) as first_session, Session(engine) as second_session:
        a = CareerApplicationService(first_session, owner_a)
        b = CareerApplicationService(second_session, owner_b)
        source_a = a.add_source(CareerSourceCreate(kind="job_description", content="Experience with Python"))
        source_b = b.add_source(CareerSourceCreate(kind="job_description", content="Experience with Ruby"))
        target_a = a.create_target(CareerTargetInput(
            role_family="Backend engineering", seniority="Senior", job_description=source_a.source,
        ))
        target_b = b.create_target(CareerTargetInput(
            role_family="Platform engineering", seniority="Mid-level", job_description=source_b.source,
        ))
        for own, other_source, own_source, other_target, own_target in (
            (a, source_b, source_a, target_b, target_a), (b, source_a, source_b, target_a, target_b),
        ):
            assert own.list_sources() == [own_source]
            assert own.list_targets() == [own_target]
            assert own.get_source(own_source.source) == own_source
            assert own.get_target(own_target.target_id) == own_target
            for service_call, argument in (
                (own.get_source, other_source.source), (own.read_source_content, other_source.source),
                (own.get_target, other_target.target_id), (own.delete_source, other_source.source.source_id),
                (own.archive_target, other_target.target_id), (own.delete_target, other_target.target_id),
            ):
                with pytest.raises(ResourceNotFoundError):
                    service_call(argument)
            with pytest.raises(ResourceNotFoundError):
                own.update_target(other_target.target_id, CareerTargetInput(role_family="Changed", seniority="Senior"))
            with pytest.raises(ResourceNotFoundError):
                own.create_target(CareerTargetInput(
                    role_family="Data engineering", seniority="Senior", job_description=other_source.source,
                ))
            with pytest.raises(ResourceNotFoundError):
                own.add_source(CareerSourceCreate(kind="job_description", content="Foreign revision"), other_source.source)
    with engine.connect() as conn:
        for table in ("career_sources", "career_targets"):
            assert conn.execute(text("SELECT relrowsecurity FROM pg_class WHERE oid = to_regclass(:table)"),
                                {"table": table}).scalar_one()
            assert not conn.execute(text("SELECT has_table_privilege('authenticated', :table, 'SELECT, INSERT, UPDATE, DELETE, TRUNCATE')"),
                                    {"table": table}).scalar_one()


def test_existing_schema_lifecycle_and_rollback(migrated_database):
    engine, config = migrated_database
    previous = "2026_11_11_profile_truncate"
    owner = str(uuid4())
    command.upgrade(config, previous)
    with Session(engine) as db, db.begin():
        db.add(User(user_id=owner))
    command.upgrade(config, "head")
    command.downgrade(config, previous)
    assert not inspect(engine).has_table("career_sources")
    command.upgrade(config, "head")
    with Session(engine) as db:
        career = CareerApplicationService(db, owner)
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        first = career.add_source(CareerSourceCreate(
            kind="job_description", content="Version 1", retention_expires_at=expires,
        ))
        second = career.add_source(
            CareerSourceCreate(kind="job_description", content="Version 2"), first.source,
        )
        assert second.retention_expires_at == expires
        third = career.add_source(CareerSourceCreate(
            kind="job_description", content="Version 3", retention_expires_at=expires + timedelta(days=1),
        ), second.source)
        assert third.retention_expires_at == expires
        assert (second.source.source_id, second.source.source_version) == (first.source.source_id, 2)
        for record, content in ((first, "Version 1"), (second, "Version 2"), (third, "Version 3")):
            assert career.read_source_content(record.source) == content
            assert record.content_sha256 == sha256(content.encode()).hexdigest()
        with pytest.raises(ResourceConflictError):
            career.add_source(CareerSourceCreate(kind="job_description", content="Stale write"), first.source)
        db.rollback()
        target = career.create_target(CareerTargetInput(
            role_family="Engineering", seniority="Senior", job_description=first.source,
        ))
        assert career.get_target(target.target_id).job_description == first.source
        updated = career.update_target(target.target_id, CareerTargetInput(
            role_family="Platform", seniority="Senior", job_description=second.source, desired_work=["APIs"],
        ))
        assert updated.role_family == "Platform" and updated.desired_work == ["APIs"]
        archived = career.archive_target(target.target_id)
        assert archived.status == "archived"
        assert career.archive_target(target.target_id) == archived
        with pytest.raises(ResourceConflictError):
            career.update_target(target.target_id, CareerTargetInput(role_family="Changed", seniority="Senior"))
        db.rollback()

        with pytest.raises(DBAPIError, match="must be preserved"):
            command.downgrade(config, previous)
        with pytest.raises(IntegrityError, match="snapshots are immutable"), engine.begin() as conn:
            conn.execute(text("UPDATE career_sources SET content = 'changed' WHERE user_id = :owner"), {"owner": owner})

        career.delete_source(first.source.source_id)
        assert career.list_sources() == []
        assert career.get_target(target.target_id).job_description is None
        career.delete_target(target.target_id)
        assert career.list_targets() == []


def test_resume_snapshot_follows_resume_deletion(migrated_database):
    engine, config = migrated_database
    command.upgrade(config, "head")
    owner, other = str(uuid4()), str(uuid4())
    with Session(engine) as db, db.begin():
        db.add_all([User(user_id=owner), User(user_id=other)])
        db.flush()
        db.add(ResumeDocument(
            id="synthetic-resume", user_id=owner, original_filename="resume.pdf",
            file_path="synthetic-path", file_type="pdf", parsed_json={}, raw_text="Synthetic résumé",
        ))
    resume = CareerSourceCreate(kind="resume", resume_document_id="synthetic-resume")
    with Session(engine) as db:
        with pytest.raises(ResourceNotFoundError):
            CareerApplicationService(db, other).add_source(resume)
        career = CareerApplicationService(db, owner)
        snapshot = career.add_source(resume)
        assert career.read_source_content(snapshot.source) == "Synthetic résumé"
        db.rollback()
        with engine.begin() as conn:
            conn.exec_driver_sql("UPDATE resume_documents SET storage_status = 'deleting'")
        assert career.list_sources() == []
        with pytest.raises(ResourceNotFoundError):
            career.read_source_content(snapshot.source)
        db.rollback()
        with engine.begin() as conn:
            conn.exec_driver_sql("DELETE FROM resume_documents")
            assert conn.exec_driver_sql("SELECT count(*) FROM career_sources").scalar_one() == 0


def test_browser_grants_and_rls_enforce_two_subjects(migrated_database):
    engine, config = migrated_database
    previous = "2026_11_11_profile_truncate"
    command.upgrade(config, previous)
    with engine.begin() as conn:
        conn.exec_driver_sql("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'anon') THEN
                    CREATE ROLE anon;
                END IF;
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'service_role') THEN
                    CREATE ROLE service_role BYPASSRLS;
                END IF;
            END $$;
            ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE
                ON TABLES TO PUBLIC, anon, authenticated, service_role;
            CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE
                AS 'SELECT nullif(current_setting(''request.jwt.claim.sub'', true), '''')::uuid';
            GRANT USAGE ON SCHEMA auth TO authenticated;
        """)
    command.upgrade(config, "head")
    owners = (str(uuid4()), str(uuid4()))
    with Session(engine) as db, db.begin():
        db.add_all(User(user_id=owner) for owner in owners)
    with Session(engine) as db:
        for owner in owners:
            service = CareerApplicationService(db, owner)
            service.add_source(CareerSourceCreate(kind="job_description", content="Fixture"))
            service.create_target(CareerTargetInput(role_family="Engineering", seniority="Senior"))

    with engine.begin() as conn:
        for table in ("career_sources", "career_targets"):
            for role in ("anon", "authenticated", "service_role"):
                assert not conn.scalar(text("""
                    SELECT has_table_privilege(:role, :table,
                        'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
                """), {"role": role, "table": table})
        # Simulate an accidental CRUD grant inside this disposable database.
        conn.exec_driver_sql("GRANT SELECT, INSERT, UPDATE, DELETE ON career_sources, career_targets TO authenticated")

    for owner, other in (owners, owners[::-1]):
        with engine.begin() as conn:
            conn.exec_driver_sql("SET LOCAL ROLE authenticated")
            assert conn.exec_driver_sql("""
                SELECT rolbypassrls OR rolsuper FROM pg_roles WHERE rolname = current_user
            """).scalar_one() is False
            conn.execute(text("SELECT set_config('request.jwt.claim.sub', :owner, true)"), {"owner": owner})
            for table in ("career_sources", "career_targets"):
                assert conn.exec_driver_sql(f"SELECT user_id FROM {table}").scalars().all() == [owner]
                assert conn.execute(text(f"DELETE FROM {table} WHERE user_id = :other"), {"other": other}).rowcount == 0
            assert conn.execute(text("UPDATE career_targets SET role_family = 'Changed' WHERE user_id = :other"),
                                {"other": other}).rowcount == 0
            with pytest.raises(DBAPIError) as denied, conn.begin_nested():
                _insert_target(conn, other)
            assert denied.value.orig.pgcode == "42501"
            with pytest.raises(DBAPIError) as denied, conn.begin_nested():
                conn.execute(text("UPDATE career_targets SET user_id = :other"), {"other": other})
            assert denied.value.orig.pgcode == "42501"
    with engine.begin() as conn:
        conn.exec_driver_sql("SET LOCAL ROLE authenticated")
        for table in ("career_sources", "career_targets"):
            assert conn.exec_driver_sql(f"SELECT count(*) FROM {table}").scalar_one() == 0


def _insert_target(conn, owner, jd_owner=None, source=None, version=None):
    conn.execute(text("""
        INSERT INTO career_targets (user_id, id, role_family, seniority, desired_work, exclusions,
                                    jd_user_id, jd_source_id, jd_source_version, jd_source_kind)
        VALUES (:owner, :id, 'Platform', 'Senior', '[]', '[]', :jd_owner, :source, :version,
                CASE WHEN :source IS NULL THEN NULL ELSE 'job_description' END)
    """), {"owner": owner, "id": str(uuid4()), "jd_owner": jd_owner, "source": source, "version": version})


def test_database_rejects_mismatched_links_and_cascades_account_deletion(migrated_database):
    engine, config = migrated_database
    command.upgrade(config, "head")
    owner, other = str(uuid4()), str(uuid4())
    with Session(engine) as db, db.begin():
        db.add_all([User(user_id=owner), User(user_id=other)])
    with Session(engine) as db:
        service = CareerApplicationService(db, owner)
        intro = service.add_source(CareerSourceCreate(kind="candidate_introduction", content="I wrote API tests"))
        jd = service.add_source(CareerSourceCreate(kind="job_description", content="Hiring for API engineering"))
        service.create_target(CareerTargetInput(role_family="Engineering", seniority="Senior", job_description=jd.source))
        CareerApplicationService(db, other).create_target(CareerTargetInput(role_family="Design", seniority="Senior"))
    for ownership, linked_owner, source in (
        (other, owner, jd.source),
        (other, other, jd.source),
        (owner, owner, intro.source),
    ):
        with pytest.raises(IntegrityError), engine.begin() as conn:
            _insert_target(conn, ownership, linked_owner, source.source_id, source.source_version)
    with pytest.raises(IntegrityError), engine.begin() as conn:
        _insert_target(conn, owner, owner)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM users WHERE user_id = :owner"), {"owner": owner})
        assert conn.exec_driver_sql("SELECT user_id FROM career_sources").scalars().all() == []
        assert conn.exec_driver_sql("SELECT user_id FROM career_targets").scalars().all() == [other]


def test_concurrent_append_has_one_winner(migrated_database):
    engine, config = migrated_database
    command.upgrade(config, "head")
    owner = str(uuid4())
    with Session(engine) as db:
        db.add(User(user_id=owner))
        db.commit()
        first = CareerApplicationService(db, owner).add_source(
            CareerSourceCreate(kind="candidate_introduction", content="Version 1"),
        )
    barrier = Barrier(2)

    def append(content):
        with Session(engine) as db:
            db.execute(text("SET LOCAL lock_timeout = '5s'"))
            barrier.wait(timeout=5)
            try:
                return CareerApplicationService(db, owner).add_source(
                    CareerSourceCreate(kind="candidate_introduction", content=content), first.source,
                )
            except ResourceConflictError:
                return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        versions = list(pool.map(append, ["First candidate", "Second candidate"], timeout=10))
    winners = [version for version in versions if version is not None]
    assert len(winners) == 1
    with Session(engine) as db:
        assert CareerApplicationService(db, owner).list_sources() == [winners[0], first]
        assert winners[0].source.source_version == 2


def test_inherited_api_access_fails_migration_atomically(migrated_database):
    engine, config = migrated_database
    previous = "2026_11_11_profile_truncate"
    command.upgrade(config, previous)
    with engine.begin() as conn:
        conn.exec_driver_sql("""
            CREATE ROLE pri32_test_access;
            GRANT pri32_test_access TO authenticated;
            ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO pri32_test_access;
        """)
    try:
        with pytest.raises(DBAPIError, match="Effective API role grant remains"):
            command.upgrade(config, "head")
        assert not inspect(engine).has_table("career_sources")
        assert not inspect(engine).has_table("career_targets")
        with engine.connect() as conn:
            assert conn.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one() == previous
            assert conn.exec_driver_sql(
                "SELECT to_regclass('public.uq_resume_documents_owner_id')",
            ).scalar_one() is None
    finally:
        with engine.begin() as conn:
            conn.exec_driver_sql("""
                ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE SELECT ON TABLES FROM pri32_test_access;
                DROP ROLE pri32_test_access;
            """)


def test_downgrade_requires_read_committed(migrated_database):
    engine, config = migrated_database
    command.upgrade(config, "head")
    with engine.begin() as conn:
        owner = conn.exec_driver_sql("SELECT quote_ident(current_user)").scalar_one()
        database = conn.exec_driver_sql("SELECT quote_ident(current_database())").scalar_one()
        conn.exec_driver_sql(f"ALTER ROLE {owner} IN DATABASE {database} SET default_transaction_isolation = 'repeatable read'")
    try:
        with pytest.raises(DBAPIError, match="READ COMMITTED"):
            command.downgrade(config, "2026_11_11_profile_truncate")
        assert inspect(engine).has_table("career_sources")
    finally:
        with engine.begin() as conn:
            conn.exec_driver_sql(f"ALTER ROLE {owner} IN DATABASE {database} RESET default_transaction_isolation")


@pytest.mark.parametrize("write", ["create_target", "append_source"])
@pytest.mark.parametrize("delete_first", [False, True], ids=["write_first", "delete_first"])
def test_owner_deletion_and_career_write_finish_without_deadlock(migrated_database, write, delete_first):
    engine, config = migrated_database
    command.upgrade(config, "head")
    owner, other = str(uuid4()), str(uuid4())
    with Session(engine) as db:
        db.add_all([User(user_id=owner), User(user_id=other)])
        db.commit()
        source = CareerApplicationService(db, owner).add_source(
            CareerSourceCreate(kind="job_description", content="Engineering JD"),
        )
        CareerApplicationService(db, other).create_target(
            CareerTargetInput(role_family="Unrelated role", seniority="Senior"),
        )

    release = Event()
    writer_pid, deleter_pid = Queue(), Queue()

    def write_career_record():
        with Session(engine) as db:
            db.execute(text("SET LOCAL statement_timeout = '10s'"))
            pid = db.scalar(text("SELECT pg_backend_pid()"))

            def pause_before_insert(*_):
                writer_pid.put(pid)
                assert release.wait(6), "Timed out waiting to release the Career write"

            if delete_first:
                writer_pid.put(pid)
            else:
                event.listen(db, "before_flush", pause_before_insert, once=True)
            career = CareerApplicationService(db, owner)
            if write == "create_target":
                return career.create_target(CareerTargetInput(
                    role_family="Platform", seniority="Senior", job_description=source.source,
                ))
            return career.add_source(
                CareerSourceCreate(kind="job_description", content="Revised JD"), source.source,
            )

    def delete_owner():
        with engine.begin() as conn:
            conn.exec_driver_sql("SET LOCAL statement_timeout = '10s'")
            pid = conn.exec_driver_sql("SELECT pg_backend_pid()").scalar_one()
            if not delete_first:
                deleter_pid.put(pid)
            deleted = conn.execute(text("DELETE FROM users WHERE user_id = :owner"), {"owner": owner})
            assert deleted.rowcount == 1
            if delete_first:
                deleter_pid.put(pid)
                assert release.wait(6), "Timed out waiting to commit owner deletion"

    with ThreadPoolExecutor(max_workers=2) as pool:
        try:
            if delete_first:
                deleted = pool.submit(delete_owner)
                blocker = deleter_pid.get(timeout=5)
                written = pool.submit(write_career_record)
                blocked = writer_pid.get(timeout=5)
            else:
                written = pool.submit(write_career_record)
                blocker = writer_pid.get(timeout=5)
                deleted = pool.submit(delete_owner)
                blocked = deleter_pid.get(timeout=5)
            _wait_for_blocking(engine, blocked, blocker)
        finally:
            release.set()
        deleted.result(timeout=10)
        if delete_first:
            with pytest.raises(ResourceNotFoundError):
                written.result(timeout=10)
        else:
            assert written.result(timeout=10).owner_id == owner

    with engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT user_id FROM users").scalars().all() == [other]
        assert conn.exec_driver_sql("SELECT user_id FROM career_sources").scalars().all() == []
        assert conn.exec_driver_sql("SELECT user_id FROM career_targets").scalars().all() == [other]


def _wait_for_blocking(engine, blocked, blocker):
    deadline = monotonic() + 5
    with engine.connect() as conn:
        while monotonic() < deadline:
            if conn.scalar(text("SELECT :blocker = ANY(pg_blocking_pids(:blocked))"),
                           {"blocker": blocker, "blocked": blocked}):
                return
            sleep(0.01)
    pytest.fail("PostgreSQL did not observe the expected lock wait")
