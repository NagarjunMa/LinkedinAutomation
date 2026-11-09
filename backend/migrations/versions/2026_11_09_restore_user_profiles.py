"""Bring the Alembic-created user_profiles table up to the profile API schema."""

import sqlalchemy as sa
from alembic import op


revision = "2026_11_09_user_profiles"
down_revision = "2026_11_09_monthly_credits"
branch_labels = None
depends_on = None


PROFILE_COLUMNS = {
    "full_name": "character varying(255)",
    "email": "character varying(255)",
    "phone": "character varying(50)",
    "location": "character varying(255)",
    "work_authorization": "character varying(100)",
    "years_of_experience": "double precision",
    "career_level": "character varying(50)",
    "professional_summary": "text",
    "programming_languages": "json",
    "frameworks_libraries": "json",
    "tools_platforms": "json",
    "soft_skills": "json",
    "job_titles": "json",
    "companies": "json",
    "industries": "json",
    "experience_descriptions": "json",
    "degrees": "json",
    "institutions": "json",
    "graduation_years": "json",
    "relevant_coursework": "json",
    "desired_roles": "json",
    "preferred_locations": "json",
    "salary_range_min": "integer",
    "salary_range_max": "integer",
    "job_types": "json",
    "company_size_preference": "json",
    "ai_profile_summary": "text",
    "ai_strengths": "json",
    "ai_improvement_areas": "json",
    "ai_career_advice": "text",
    "created_at": "timestamp without time zone",
    "updated_at": "timestamp without time zone",
    "last_resume_upload": "timestamp without time zone",
}


def upgrade() -> None:
    connection = op.get_bind()
    columns = {
        name: (sql_type, not_null)
        for name, sql_type, not_null in connection.execute(sa.text("""
            SELECT attname, format_type(atttypid, atttypmod), attnotnull
            FROM pg_attribute
            WHERE attrelid = 'public.user_profiles'::regclass AND attnum > 0 AND NOT attisdropped
        """))
    }
    for name, sql_type in PROFILE_COLUMNS.items():
        if name in columns and columns[name] != (sql_type, False):
            raise RuntimeError(f"Incompatible existing user_profiles column: {name}")

    missing_columns = [
        f"ADD COLUMN {name} {sql_type}"
        for name, sql_type in PROFILE_COLUMNS.items()
        if name not in columns
    ]
    has_unique_owner = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = i.indkey[0]
            WHERE i.indrelid = 'public.user_profiles'::regclass AND a.attname = 'user_id'
              AND i.indisunique AND i.indisvalid AND i.indisready
              AND i.indnkeyatts = 1 AND i.indpred IS NULL AND i.indexprs IS NULL
        )
    """)).scalar_one()

    if missing_columns:
        op.execute("LOCK TABLE public.user_profiles IN ACCESS EXCLUSIVE MODE NOWAIT")
        op.execute("ALTER TABLE public.user_profiles " + ", ".join(missing_columns))

    if not has_unique_owner:
        if not missing_columns:
            op.execute("LOCK TABLE public.user_profiles IN SHARE ROW EXCLUSIVE MODE NOWAIT")
        # Block concurrent inserts while checking for duplicates. Keep owner IDs out of errors.
        op.execute("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM public.user_profiles GROUP BY user_id HAVING count(*) > 1) THEN
                    RAISE EXCEPTION 'user_profiles has duplicate owners; reconcile before retrying';
                END IF;
            END;
            $$;
        """)
        op.execute("CREATE UNIQUE INDEX ix_user_profiles_user_id ON public.user_profiles (user_id)")


def downgrade() -> None:
    # The previous app also uses these columns. Keep profile data on rollback.
    pass
