# Prism Pro Phase 0 — Code Cleanup & Remodel

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to execute this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aggressive cleanup before Phase 1 development. Remove all deprecated features, dead code, stale docs, lint debt, and unfinished/conflicting scaffolds. Leave only what aligns with the pivot spec (resume polish + JD tailoring + jobs tracking demoted).

**Branch:** `feat/phase-1-resume-backend` (already created and checked out).

**Spec reference:** `docs/superpowers/specs/2026-05-19-prism-pro-pivot-design.md` §3 (non-goals), §11 (migration/cleanup).

**Tech stack touched:** Python (FastAPI backend), TypeScript (Next.js frontend), shell.

**Sequencing:** Execute Phase 0 fully BEFORE Phase 1 (`2026-05-19-prism-pro-resume-backend-phase-1.md`). Cleanup must leave the build green: backend tests pass, frontend builds, type-checks, and lints cleanly.

---

## Resolved kill list (Explore agent survey + grep verification)

**Backend (KILL):**
- `_archived_features/` (entire dir)
- `services/email_service.py`, `services/resend_email_service.py`, `services/sendgrid_email_service.py`, `services/email_templates/`
- `services/simple_referral_service.py`
- `services/apollo_client.py`, `services/contact_discovery.py`
- `services/job_aggregator.py` (verified unused)
- `services/analytics_service.py`, `services/analytics_intelligence.py`
- `services/question_answer_service.py` (defined but not used)
- `services/orchestrator_manager.py` (used only by legacy `resumes.py`; killed alongside the legacy endpoint logic in Phase 1)
- `api/v1/endpoints/activity.py`
- `api/v1/endpoints/simple_referrals.py`
- `models/activity.py`
- `tasks/email_monitoring_tasks.py`, `tasks/email_scanning_tasks.py`, `tasks/analytics_tasks.py`, `tasks/feedback_collector.py` (any that exist — verify before delete)
- One-shot utility scripts at backend root: `check_mock_data.py`, `check_status.py`, `debug_env.py`, `fix_resume_evaluations_schema.py`, `fix_scheduler.py`, `reset_data.py`, `database_optimizations.py`
- `backend/docs/EMAIL_AGENT_SUMMARY.md`, `EMAIL_AUTOMATION_SYSTEM.md`, `REALTIME_EMAIL_MONITORING.md` (if present)

**Backend (KEEP — verified):**
- `services/job_cleanup_service.py` (used by `jobs.py`)
- `services/job_scorer.py` + `services/smart_job_scorer.py` (used by `profiles.py` + `job_extraction.py`)
- `services/url_job_extractor.py` (used by `job_extraction.py`)
- All retained endpoints: `jobs.py`, `job_extraction.py`, `profiles.py`, `user_profiles.py`, `resumes.py` (will evolve), `logs.py`

**Frontend (KILL):**
- `src/app/dashboard/activity/` (entire route)
- `src/app/dashboard/referrals/` (entire route)
- `src/app/dashboard/resume-evaluation/` (7-line stub; replaced by Phase 1's `/dashboard/resume/[id]/edit`)
- `src/app/lib/api/email.ts` (if present)
- `src/app/lib/api/referral.ts` (if present)
- Any components under `src/components/` whose only consumers are the killed routes (audit via grep)
- Email/referrals tabs/settings in `dashboard/settings/` (if present)
- Frontend doc files: `AUTHENTICATION_SETUP.md`, `AUTH_DEBUG_GUIDE.md`, `BUILD_STATUS.md`, `DARK_THEME_UPDATE.md`, `LANDING_PAGE_SETUP.md`, `RAILWAY_BUILD_FIX.md`, `RAILWAY_BUILD_FIX_COMPLETE.md`, `ROOT_CAUSE_ANALYSIS.md`, `STRICT_LINTING.md`, `STRICT_LINT_TRACKER.md`, `auth-test-instructions.md`, `clear-auth-data.html`

**Frontend (KEEP — verified):**
- `src/app/dashboard/applications/` (718-line job-applications view, used)
- `src/app/dashboard/jobs/`, `/profile`, `/settings`, top-level layout/loading
- `src/types/stats.ts` (used by `contexts/dashboard-context.tsx` + `lib/api/jobs.ts`)

**Root-level (KILL):**
- `PRIORITY_2_COMPLETION_SUMMARY.md`, `PRODUCTION_ENV_GUIDE.md`, `RAILWAY_ENV_VARS.md`, `SECURITY_IMPLEMENTATION.md`

**Root-level (KEEP):**
- `README.md` (update to reflect pivot)
- `CLAUDE.md` (update)
- `DEPLOYMENT.md`
- `Dockerfile`, `docker-compose.yml`, env files

---

### Task A: Delete `_archived_features/`

**Files:**
- Delete: `backend/_archived_features/` (entire directory)

- [ ] **Step 1: Verify dir exists**

```bash
ls /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/backend/_archived_features
```

- [ ] **Step 2: Delete recursively**

```bash
git -C /Users/nagarjunmallesh/Desktop/projects/linkedin-automation rm -rf backend/_archived_features
```

- [ ] **Step 3: Commit**

```bash
git commit -m "chore(cleanup): delete backend/_archived_features (5 stale modules)"
```

---

### Task B: Delete one-shot utility scripts

**Files:**
- Delete: `backend/check_mock_data.py`, `backend/check_status.py`, `backend/debug_env.py`, `backend/fix_resume_evaluations_schema.py`, `backend/fix_scheduler.py`, `backend/reset_data.py`, `backend/database_optimizations.py`

- [ ] **Step 1: Verify none are imported by app code**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && grep -rn "check_mock_data\|check_status\|fix_resume_evaluations_schema\|fix_scheduler\|reset_data\|database_optimizations" backend/app/ 2>&1 | grep -v "Binary file"
```

Expected: empty. If anything imports them, STOP and report.

- [ ] **Step 2: Delete**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  git rm backend/check_mock_data.py backend/check_status.py backend/debug_env.py \
    backend/fix_resume_evaluations_schema.py backend/fix_scheduler.py backend/reset_data.py \
    backend/database_optimizations.py
```

- [ ] **Step 3: Commit**

```bash
git commit -m "chore(cleanup): delete 7 one-shot utility scripts at backend root"
```

---

### Task C: Delete stale root + frontend + backend doc files

**Files:**
- Delete (root): `PRIORITY_2_COMPLETION_SUMMARY.md`, `PRODUCTION_ENV_GUIDE.md`, `RAILWAY_ENV_VARS.md`, `SECURITY_IMPLEMENTATION.md`
- Delete (frontend): `frontend/AUTHENTICATION_SETUP.md`, `frontend/AUTH_DEBUG_GUIDE.md`, `frontend/BUILD_STATUS.md`, `frontend/DARK_THEME_UPDATE.md`, `frontend/LANDING_PAGE_SETUP.md`, `frontend/RAILWAY_BUILD_FIX.md`, `frontend/RAILWAY_BUILD_FIX_COMPLETE.md`, `frontend/ROOT_CAUSE_ANALYSIS.md`, `frontend/STRICT_LINTING.md`, `frontend/STRICT_LINT_TRACKER.md`, `frontend/auth-test-instructions.md`, `frontend/clear-auth-data.html`
- Delete (backend/docs): any of `EMAIL_AGENT_SUMMARY.md`, `EMAIL_AUTOMATION_SYSTEM.md`, `REALTIME_EMAIL_MONITORING.md` that exist

- [ ] **Step 1: Delete root MDs**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  git rm PRIORITY_2_COMPLETION_SUMMARY.md PRODUCTION_ENV_GUIDE.md RAILWAY_ENV_VARS.md SECURITY_IMPLEMENTATION.md
```

- [ ] **Step 2: Delete frontend MDs**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  git rm frontend/AUTHENTICATION_SETUP.md frontend/AUTH_DEBUG_GUIDE.md frontend/BUILD_STATUS.md \
    frontend/DARK_THEME_UPDATE.md frontend/LANDING_PAGE_SETUP.md frontend/RAILWAY_BUILD_FIX.md \
    frontend/RAILWAY_BUILD_FIX_COMPLETE.md frontend/ROOT_CAUSE_ANALYSIS.md frontend/STRICT_LINTING.md \
    frontend/STRICT_LINT_TRACKER.md frontend/auth-test-instructions.md frontend/clear-auth-data.html
```

- [ ] **Step 3: Delete backend doc MDs if present**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  for f in backend/docs/EMAIL_AGENT_SUMMARY.md backend/docs/EMAIL_AUTOMATION_SYSTEM.md backend/docs/REALTIME_EMAIL_MONITORING.md; do \
    [ -f "$f" ] && git rm "$f"; \
  done
```

- [ ] **Step 4: Commit**

```bash
git commit -m "chore(docs): delete 4 stale root + 12 frontend + 3 backend docs"
```

---

### Task D: Delete backend email services

**Files:**
- Delete: `backend/app/services/email_service.py`, `resend_email_service.py`, `sendgrid_email_service.py`, `email_templates/` (entire subdir)

- [ ] **Step 1: Grep imports**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  grep -rn "from app.services.email_service\|from app.services.resend_email_service\|from app.services.sendgrid_email_service\|from app.services.email_templates" backend/app/ 2>&1 | grep -v "^Binary"
```

- [ ] **Step 2: Remove every import + dependent code**

For each import found in step 1, edit the file: delete the `import` line AND remove any reference to the imported symbols downstream. If a function becomes empty, delete the function. If an endpoint becomes empty, delete the endpoint route. Show diffs in commit.

- [ ] **Step 3: Delete the service files**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  git rm backend/app/services/email_service.py backend/app/services/resend_email_service.py \
    backend/app/services/sendgrid_email_service.py && \
  [ -d backend/app/services/email_templates ] && git rm -r backend/app/services/email_templates || true
```

- [ ] **Step 4: Run backend tests — verify nothing broke**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/backend && \
  python -m pytest tests/ -x --ignore=tests/golden 2>&1 | tail -30
```

Expected: PASS (any failures must be triaged before commit).

- [ ] **Step 5: Commit**

```bash
git commit -m "chore(cleanup): remove email services + all callers"
```

---

### Task E: Delete backend referral + contact services

**Files:**
- Delete: `backend/app/services/simple_referral_service.py`, `apollo_client.py`, `contact_discovery.py`
- Delete endpoint: `backend/app/api/v1/endpoints/simple_referrals.py`
- Modify: `backend/app/api/v1/api.py` (remove referrals router include)

- [ ] **Step 1: Grep imports**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  grep -rn "simple_referral_service\|apollo_client\|contact_discovery\|simple_referrals" backend/app/ 2>&1 | grep -v "^Binary"
```

- [ ] **Step 2: Remove router include in `api.py`**

Edit `backend/app/api/v1/api.py`: delete the line `from app.api.v1.endpoints import simple_referrals` and any `api_router.include_router(simple_referrals.router)` line.

- [ ] **Step 3: Delete files**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  git rm backend/app/services/simple_referral_service.py backend/app/services/apollo_client.py \
    backend/app/services/contact_discovery.py backend/app/api/v1/endpoints/simple_referrals.py
```

- [ ] **Step 4: Run backend tests**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/backend && \
  python -m pytest tests/ -x --ignore=tests/golden 2>&1 | tail -30
```

- [ ] **Step 5: Commit**

```bash
git commit -m "chore(cleanup): remove referrals + contact-discovery services and endpoint"
```

---

### Task F: Delete activity endpoint + model

**Files:**
- Delete: `backend/app/api/v1/endpoints/activity.py`
- Delete: `backend/app/models/activity.py`
- Modify: `backend/app/api/v1/api.py` (remove activity router include)
- Modify: `backend/app/models/__init__.py` (remove `from app.models.activity import ...`)

- [ ] **Step 1: Grep**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  grep -rn "from app.models.activity\|from app.api.v1.endpoints import activity\|api_router.include_router(activity" backend/app/ 2>&1 | grep -v "^Binary"
```

- [ ] **Step 2: Remove imports + router include**

Edit `backend/app/api/v1/api.py` and `backend/app/models/__init__.py` per the grep results.

- [ ] **Step 3: Delete files**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  git rm backend/app/api/v1/endpoints/activity.py backend/app/models/activity.py
```

- [ ] **Step 4: Tests**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/backend && \
  python -m pytest tests/ -x --ignore=tests/golden 2>&1 | tail -20
```

- [ ] **Step 5: Commit**

```bash
git commit -m "chore(cleanup): remove activity endpoint + model"
```

---

### Task G: Delete analytics + misc unused services

**Files:**
- Delete: `backend/app/services/analytics_service.py`, `analytics_intelligence.py`, `job_aggregator.py`, `question_answer_service.py`

- [ ] **Step 1: Grep**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  grep -rn "analytics_service\|analytics_intelligence\|job_aggregator\|question_answer_service\|QuestionAnswerService" backend/app/ 2>&1 | grep -v "^Binary"
```

- [ ] **Step 2: Strip residual usages**

For any caller found, remove the import + any function calls. If the only function in a route file used these, the route may be deletable — flag in PR.

For `app/core/rate_limiter.py:156` ("question_answering" key) — leave the dict entry; harmless. Or remove cleanly if isolated.

- [ ] **Step 3: Delete files**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  git rm backend/app/services/analytics_service.py backend/app/services/analytics_intelligence.py \
    backend/app/services/job_aggregator.py backend/app/services/question_answer_service.py
```

- [ ] **Step 4: Tests**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/backend && \
  python -m pytest tests/ -x --ignore=tests/golden 2>&1 | tail -20
```

- [ ] **Step 5: Commit**

```bash
git commit -m "chore(cleanup): remove analytics, job_aggregator, question_answer services"
```

---

### Task H: Delete backend tasks for removed features

**Files:**
- Delete (if present): `backend/app/tasks/email_monitoring_tasks.py`, `email_scanning_tasks.py`, `analytics_tasks.py`, `feedback_collector.py`

- [ ] **Step 1: List + grep**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  ls backend/app/tasks/ 2>&1 && \
  grep -rn "email_monitoring_tasks\|email_scanning_tasks\|analytics_tasks\|feedback_collector" backend/app/ 2>&1 | grep -v "^Binary"
```

- [ ] **Step 2: Remove imports + scheduler registrations**

If Celery beat schedule or scheduler config references these tasks (likely in `core/celery_app.py` or similar), remove those entries.

- [ ] **Step 3: Delete files (only those that exist)**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  for f in backend/app/tasks/email_monitoring_tasks.py backend/app/tasks/email_scanning_tasks.py \
           backend/app/tasks/analytics_tasks.py backend/app/tasks/feedback_collector.py; do \
    [ -f "$f" ] && git rm "$f"; \
  done
```

- [ ] **Step 4: Tests + commit**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/backend && \
  python -m pytest tests/ -x --ignore=tests/golden 2>&1 | tail -10 && \
  cd .. && git commit -m "chore(cleanup): remove email/analytics/feedback Celery tasks"
```

---

### Task I: Delete frontend routes — activity, referrals, resume-evaluation

**Files:**
- Delete: `frontend/src/app/dashboard/activity/`, `frontend/src/app/dashboard/referrals/`, `frontend/src/app/dashboard/resume-evaluation/`

- [ ] **Step 1: Confirm presence**

```bash
ls /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend/src/app/dashboard/activity \
   /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend/src/app/dashboard/referrals \
   /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend/src/app/dashboard/resume-evaluation
```

- [ ] **Step 2: Delete**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  git rm -r frontend/src/app/dashboard/activity \
    frontend/src/app/dashboard/referrals \
    frontend/src/app/dashboard/resume-evaluation
```

- [ ] **Step 3: Update navigation**

Find the dashboard nav config (likely `frontend/src/components/dashboard/sidebar.tsx` or `nav.tsx`) and remove any nav items pointing to `/dashboard/activity`, `/dashboard/referrals`, `/dashboard/resume-evaluation`. Use:

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend && \
  grep -rn "/dashboard/activity\|/dashboard/referrals\|/dashboard/resume-evaluation" src/components/ 2>&1 | head -20
```

For each hit, open and remove the entry.

- [ ] **Step 4: Add redirects in `next.config.mjs`** (optional but safer)

Append to the `redirects` config:

```js
async redirects() {
  return [
    { source: "/dashboard/activity", destination: "/dashboard", permanent: false },
    { source: "/dashboard/referrals", destination: "/dashboard", permanent: false },
    { source: "/dashboard/resume-evaluation", destination: "/dashboard", permanent: false },
  ];
}
```

- [ ] **Step 5: Frontend build**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend && npm run build 2>&1 | tail -30
```

Expected: build succeeds. Fix any import-broken errors.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "chore(cleanup): delete frontend routes activity, referrals, resume-evaluation + nav + redirects"
```

---

### Task J: Delete frontend API modules + dead components

**Files:**
- Delete (if present): `frontend/src/app/lib/api/email.ts`, `frontend/src/app/lib/api/referral.ts`
- Modify: `frontend/src/app/lib/api/index.ts` (remove barrels exports)
- Modify: `frontend/src/app/lib/api/types.ts` (remove orphaned Email/Referral/Activity types)
- Delete: any `*referral*`, `*activity-calendar*`, `*email-tab*` components no longer imported

- [ ] **Step 1: Inventory dead frontend modules**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend && \
  ls src/app/lib/api/ && \
  grep -rln "from.*api/email\|from.*api/referral" src/ 2>&1 | head -20 && \
  find src/components -type f \( -iname "*referral*" -o -iname "*activity*calendar*" -o -iname "*email-tab*" \)
```

- [ ] **Step 2: Delete API modules**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  [ -f frontend/src/app/lib/api/email.ts ] && git rm frontend/src/app/lib/api/email.ts || true && \
  [ -f frontend/src/app/lib/api/referral.ts ] && git rm frontend/src/app/lib/api/referral.ts || true
```

- [ ] **Step 3: Update barrels (`lib/api/index.ts`)**

Open file, delete `export * from './email'` and `export * from './referral'` lines.

- [ ] **Step 4: Prune `types.ts`**

Open `frontend/src/app/lib/api/types.ts`. Remove any `Referral*`, `Email*`, `Activity*` type/interface definitions and their dependent type unions. Keep `Job*`, `Resume*`, `Profile*`, `User*` types.

- [ ] **Step 5: Delete unreferenced components**

For each component file found in Step 1 inventory:

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend && \
  grep -rln "ComponentName" src/ | grep -v "the file itself"
```

If zero remaining imports, `git rm` the file.

- [ ] **Step 6: Build + commit**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend && npm run build 2>&1 | tail -30
cd .. && git add -A && git commit -m "chore(cleanup): delete frontend email/referral API + dead components + types"
```

---

### Task K: Strip settings/notifications tabs for killed features

**Files:**
- Modify: `frontend/src/app/dashboard/settings/page.tsx` and child components (tabs)

- [ ] **Step 1: Inventory**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend && \
  ls src/app/dashboard/settings/ && \
  grep -rn "notifications-tab\|email-tab" src/app/dashboard/settings/ 2>&1
```

- [ ] **Step 2: Decide per tab**

For each settings tab/component:
- If it manages email notifications, automation rules, or referral templates → delete the component file + remove its tab trigger and content from the parent tabs page.
- If it manages account/profile/security → keep.

- [ ] **Step 3: Delete + edit**

```bash
# Example, adapt to actual files found:
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation && \
  git rm frontend/src/app/dashboard/settings/email-tab.tsx 2>/dev/null || true
```

Then edit `settings/page.tsx` (or tabs index) to remove the `<TabsTrigger>` and `<TabsContent>` for killed tabs.

- [ ] **Step 4: Build**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend && npm run build 2>&1 | tail -20
```

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "chore(cleanup): strip email + referral tabs from settings"
```

---

### Task L: Fix all frontend lint debt

**Files:**
- Modify: any frontend TSX/TS file with lint violations

- [ ] **Step 1: Baseline run**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend && npm run lint 2>&1 | tee /tmp/lint-before.log | tail -50
```

Capture the count of errors and warnings.

- [ ] **Step 2: Auto-fix what's auto-fixable**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend && npm run lint -- --fix 2>&1 | tail -30
```

- [ ] **Step 3: Re-run and triage remaining**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend && npm run lint 2>&1 | tee /tmp/lint-after.log | tail -80
```

Categories to fix manually:
- `@typescript-eslint/no-explicit-any` → replace `any` with concrete types from `lib/api/types.ts` or `unknown` with type guards
- `react-hooks/exhaustive-deps` → add missing deps OR refactor to remove the dep (whichever preserves intent; prefer correctness)
- `react/no-unescaped-entities` → use `&apos;` / `&quot;`
- `@typescript-eslint/no-unused-vars` → delete; if intentional, prefix `_`
- `prefer-const` → change `let` to `const`

Fix file by file. Build + lint after each batch.

- [ ] **Step 4: Verify zero lint errors**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend && npm run lint 2>&1 | tail -5
```

Expected: 0 errors. Warnings allowed if justified.

- [ ] **Step 5: Type-check**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend && npx tsc --noEmit 2>&1 | tail -20
```

Expected: 0 errors.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "chore(lint): resolve all STRICT_LINT_TRACKER violations across frontend"
```

(If the diff is large, split into 2-3 logical commits: types-only fix, hooks fix, JSX fix.)

---

### Task M: Update README.md + CLAUDE.md for pivot

**Files:**
- Modify: `README.md` (root)
- Modify: `CLAUDE.md` (root)

- [ ] **Step 1: Update root `README.md`**

Replace the features section with the new pivot description: AI-powered resume polish + JD-driven tailoring. List the 6 new API endpoints (from Phase 1 plan). Link to spec. Remove obsolete claims (browser extension, email automation, full-suite resume tracker).

- [ ] **Step 2: Update `CLAUDE.md`**

Replace the "Recent Specific Updates (February 2026)" + features sections with current pivot scope:
- Resume polish + JD tailoring as primary
- Jobs tracking demoted (kept)
- Voice interview deferred
- Browser extension deferred
- USA + India MVP, SWE/DS/PM templates
- Single-agent + specialized passes architecture (not multi-agent)
- Reference the umbrella spec path

- [ ] **Step 3: Commit**

```bash
git add README.md CLAUDE.md && \
  git commit -m "docs: rewrite README + CLAUDE.md to reflect pivot (resume polish + JD tailoring)"
```

---

### Task N: Final verification

- [ ] **Step 1: Backend tests**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/backend && \
  python -m pytest tests/ --ignore=tests/golden -v 2>&1 | tail -40
```

Expected: ALL PASS.

- [ ] **Step 2: Frontend build + lint + types**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend && \
  npm run build && npm run lint && npx tsc --noEmit 2>&1 | tail -30
```

Expected: build succeeds, 0 lint errors, 0 type errors.

- [ ] **Step 3: Quick smoke — backend boots**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/backend && \
  python -c "from app.main import app; print('routes:', len(app.routes))" 2>&1
```

Expected: prints route count without ImportError.

- [ ] **Step 4: Quick smoke — frontend dev server starts**

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend && \
  timeout 30 npm run dev 2>&1 | grep -E "Ready|error" | head -5
```

Expected: "Ready in ..." line.

- [ ] **Step 5: Push branch**

```bash
git push -u origin feat/phase-1-resume-backend
```

- [ ] **Step 6: Commit marker (if any uncommitted changes from verification)**

```bash
git status
# If clean, no action. Otherwise commit the noted issues.
```

---

## Self-Review Summary

**Coverage of user's δ scope:**
- Backend route reduction → Tasks D, E, F, G (services + endpoints), Task H (tasks) ✓
- Frontend prune → Tasks I, J, K ✓
- Dead code purge → Tasks A, B (archived + utilities) ✓
- Lint debt → Task L ✓
- Docs consolidation → Task C, M ✓
- Final verification → Task N ✓

**Risk:** Tasks D–H change shared `api/v1/api.py` and `models/__init__.py`. If subagents run sequentially (skill default), merges are fine. If parallelized, conflicts. Subagent-driven-development is strictly sequential per task — safe.

**No placeholders.** Every step has concrete commands. Final verification (Task N) is the safety net.

**After Phase 0:** Switch to `2026-05-19-prism-pro-resume-backend-phase-1.md` and execute Phase 1 tasks 0-24.
