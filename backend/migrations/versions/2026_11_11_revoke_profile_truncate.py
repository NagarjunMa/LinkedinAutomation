"""Remove browser TRUNCATE grants on profiles and future app tables."""

from alembic import op


revision = "2026_11_11_profile_truncate"
down_revision = "2026_11_09_resume_storage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$
        DECLARE
            browser_role record;
        BEGIN
            -- The migration role owns this table and creates future app tables.
            IF NOT EXISTS (
                SELECT FROM pg_class
                WHERE oid = 'public.user_profiles'::regclass
                  AND relowner = current_user::regrole
            ) THEN
                RAISE EXCEPTION 'Run profile grant migration as the user_profiles owner';
            END IF;

            FOR browser_role IN
                SELECT oid, rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated')
            LOOP
                EXECUTE format(
                    'REVOKE TRUNCATE ON TABLE public.user_profiles FROM %I',
                    browser_role.rolname
                );
                EXECUTE format(
                    'ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE TRUNCATE ON TABLES FROM %I',
                    browser_role.rolname
                );

                IF has_table_privilege(browser_role.oid, 'public.user_profiles', 'TRUNCATE') THEN
                    RAISE EXCEPTION 'Effective TRUNCATE remains on user_profiles for %', browser_role.rolname;
                END IF;

                -- Schema defaults cannot override grants from global defaults.
                IF EXISTS (
                    SELECT
                    FROM pg_default_acl d
                    CROSS JOIN LATERAL aclexplode(d.defaclacl) acl
                    WHERE d.defaclrole = current_user::regrole
                      AND d.defaclobjtype = 'r'
                      AND d.defaclnamespace IN (0, 'public'::regnamespace)
                      AND acl.privilege_type = 'TRUNCATE'
                      AND CASE WHEN acl.grantee = 0 THEN true
                               ELSE pg_has_role(browser_role.oid, acl.grantee, 'USAGE') END
                ) THEN
                    RAISE EXCEPTION 'Found effective default TRUNCATE for %', browser_role.rolname;
                END IF;
            END LOOP;
        END
        $$;
    """)


def downgrade() -> None:
    # Application rollback must not restore browser access to TRUNCATE.
    pass
