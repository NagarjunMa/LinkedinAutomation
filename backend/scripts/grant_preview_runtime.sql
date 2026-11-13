-- Run with psql as the application table owner. The operator creates the login separately.
-- psql -v runtime_role=prismpro_preview_runtime -f scripts/grant_preview_runtime.sql
\set ON_ERROR_STOP on
BEGIN;
SET LOCAL lock_timeout = '3s';
SET LOCAL statement_timeout = '10s';

GRANT USAGE ON SCHEMA public TO :"runtime_role";
GRANT SELECT ON public.alembic_version TO :"runtime_role";
GRANT SELECT (id, normalized_email, created_at, updated_at) ON public.waitlist_entries TO :"runtime_role";
GRANT INSERT (id, normalized_email, career_stage, target_role, communication_challenge,
    consent_granted, consent_version, consented_at, source, retention_expires_at)
    ON public.waitlist_entries TO :"runtime_role";

DROP POLICY IF EXISTS preview_runtime_read_revision ON public.alembic_version;
CREATE POLICY preview_runtime_read_revision ON public.alembic_version
    FOR SELECT TO :"runtime_role" USING (true);

DROP POLICY IF EXISTS preview_runtime_read_waitlist ON public.waitlist_entries;
CREATE POLICY preview_runtime_read_waitlist ON public.waitlist_entries
    FOR SELECT TO :"runtime_role" USING (true);

DROP POLICY IF EXISTS preview_runtime_insert_waitlist ON public.waitlist_entries;
CREATE POLICY preview_runtime_insert_waitlist ON public.waitlist_entries
    FOR INSERT TO :"runtime_role" WITH CHECK (
        consent_granted AND source = 'public_preview_landing'
        AND retention_expires_at <= statement_timestamp() + interval '181 days'
    );
COMMIT;
