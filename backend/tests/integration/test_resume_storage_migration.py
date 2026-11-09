"""Exercise bucket-specific RLS against a production-shaped Storage policy."""

import pytest
from alembic import command
from sqlalchemy.exc import DBAPIError


pytestmark = pytest.mark.postgres
PREVIOUS_HEAD = "2026_11_09_user_profiles"
OWNER = "00000000-0000-4000-8000-000000000075"
OTHER = "00000000-0000-4000-8000-000000000076"


def _browser_checks(engine):
    with engine.begin() as conn:
        run = conn.exec_driver_sql
        run("SET LOCAL ROLE authenticated")
        run(f"SELECT set_config('request.jwt.claim.sub', '{OWNER}', true)")
        assert run("SELECT name FROM storage.objects WHERE bucket_id='resume'").scalars().all() == [
            f"{OWNER}/original.pdf",
        ]
        for bucket, path in (("resume", f"{OWNER}/direct.pdf"), ("resume", f"{OTHER}/direct.pdf")):
            with pytest.raises(DBAPIError, match="row-level security"), conn.begin_nested():
                run("INSERT INTO storage.objects VALUES (%s, %s)", (bucket, path))
        assert run("UPDATE storage.objects SET name=%s WHERE bucket_id='resume'", (f"{OWNER}/replace.pdf",)).rowcount == 0
        assert run("DELETE FROM storage.objects WHERE bucket_id='resume'").rowcount == 0
        assert run("INSERT INTO storage.objects VALUES ('other', 'unchanged')").rowcount == 1
        with pytest.raises(DBAPIError, match="row-level security"), conn.begin_nested():
            run("UPDATE storage.objects SET bucket_id='resume', name=%s WHERE bucket_id='other'", (f"{OWNER}/moved.pdf",))
        assert run("DELETE FROM storage.objects WHERE bucket_id='other'").rowcount == 1
    with engine.begin() as conn:
        conn.exec_driver_sql("SET LOCAL ROLE anon")
        conn.exec_driver_sql(f"SELECT set_config('request.jwt.claim.sub', '{OWNER}', true)")
        assert conn.exec_driver_sql("SELECT count(*) FROM storage.objects WHERE bucket_id='resume'").scalar_one() == 0
        with pytest.raises(DBAPIError, match="row-level security"), conn.begin_nested():
            conn.exec_driver_sql("INSERT INTO storage.objects VALUES ('resume', 'anonymous.pdf')")
        conn.exec_driver_sql("INSERT INTO storage.objects VALUES ('other', 'anonymous.txt')")
        assert conn.exec_driver_sql("UPDATE storage.objects SET name='renamed.txt'").rowcount == 1
        assert conn.exec_driver_sql("DELETE FROM storage.objects").rowcount == 1


@pytest.mark.parametrize("legacy_policy", [False, True])
def test_resume_storage_backend_only_writes_and_rollback(migrated_database, legacy_policy):
    engine, config = migrated_database
    command.upgrade(config, PREVIOUS_HEAD)
    with engine.begin() as conn:
        conn.exec_driver_sql("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='anon') THEN CREATE ROLE anon; END IF;
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='service_role') THEN
                    CREATE ROLE service_role BYPASSRLS;
                END IF;
            END
            $$;
            CREATE SCHEMA storage;
            CREATE FUNCTION storage.foldername(text) RETURNS text[] LANGUAGE sql IMMUTABLE
                AS $$ SELECT string_to_array($1, '/') $$;
            CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE
                AS $$ SELECT nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
            CREATE TABLE storage.objects (bucket_id text NOT NULL, name text NOT NULL, PRIMARY KEY (bucket_id, name));
            ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;
            GRANT USAGE ON SCHEMA storage, auth TO anon, authenticated, service_role;
            GRANT SELECT, INSERT, UPDATE, DELETE ON storage.objects TO anon, authenticated, service_role;
            CREATE POLICY existing_other_bucket ON storage.objects FOR ALL TO anon, authenticated
                USING (bucket_id='other');
        """)
        if legacy_policy:
            conn.exec_driver_sql("""
                CREATE POLICY legacy_resume_browser ON storage.objects FOR ALL TO anon, authenticated
                    USING (bucket_id='resume');
            """)
        conn.exec_driver_sql("INSERT INTO storage.objects VALUES ('resume', %s), ('resume', %s)",
                             (f"{OWNER}/original.pdf", f"{OTHER}/original.pdf"))
    command.upgrade(config, "head")
    _browser_checks(engine)
    with engine.begin() as conn:
        conn.exec_driver_sql("SET LOCAL ROLE service_role")
        assert conn.exec_driver_sql("INSERT INTO storage.objects VALUES ('resume', 'backend.pdf')").rowcount == 1
        assert conn.exec_driver_sql("DELETE FROM storage.objects WHERE name='backend.pdf'").rowcount == 1
    command.downgrade(config, PREVIOUS_HEAD)
    _browser_checks(engine)
    command.upgrade(config, "head")
    _browser_checks(engine)
