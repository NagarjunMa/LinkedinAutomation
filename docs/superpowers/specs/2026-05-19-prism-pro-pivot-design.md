# Prism Pro — Platform Pivot Design (v2)

**Date:** 2026-05-19
**Status:** Approved umbrella spec. Supersedes v1 of this file (which included voice interview pillar; deferred).
**Author:** brainstorming session
**Scope:** Reposition Prism Pro from US-centric job aggregator into a recruiter-grade resume polishing + JD-driven tailoring platform for South Asian + EU diaspora job seekers. MVP focuses on USA and India markets with three role templates each (SWE / DS / PM). Voice interview practice and browser-extension tracker are deferred to future specs.

---

## 1. Problem Statement

Existing resume tools (Rezi, Teal, Enhancv, Zety) and ATS scanners (Jobscan, ResyMatch) produce output that reads machine-generated: generic verbs, weak structure, and rubric reports that don't translate into edits. None present **what a senior recruiter would actually rewrite** in a way the user can visually act on. Resume content design also varies by country — US 1-page bullet style differs from India's longer CV norm — yet most tools ignore this.

The user's own pain point validates the gap: as a working SWE, the user manually rewrites bullets and skills per JD on every application. That manual work is the product.

## 2. Goals

- Ship a resume product that recruiters would call recruiter-grade, not LLM slop.
- Show users **exactly which bullets are weak**, why, and offer one-click AI rewrites that don't hallucinate impact.
- Make JD-driven tailoring the headline workflow: paste JD → diff → accept → export.
- Show users what an ATS actually parses (raw-text simulator).
- Export to PDF using country + role templates that match recruiter expectations.
- Reuse existing FastAPI + Next.js + Supabase + Google-verified OAuth infrastructure to ship fast.

## 3. Non-Goals

- Voice interview practice (deferred; separate spec).
- Browser extension job tracker (deferred; separate spec).
- Multi-agent agent panel (rejected: own prior product already learned this is theater for resume eval; single sharp GPT-4o with specialized passes beats fan-out).
- WYSIWYG in-app resume editor; the editor is bullet-level only (highlights + rewrite, not free-text editing of arbitrary layout).
- Multi-language. English only at launch.
- Job aggregation as a primary feature.

## 4. Target User

South Asian + EU diaspora across all career stages — students, early-career, mid-career, switchers, returnees. MVP markets: **USA and India**. Other geographies deferred.

## 5. Decisions Locked

| Topic | Choice |
|---|---|
| Product | Resume polish + JD tailoring + PDF export |
| Markets (MVP) | USA + India |
| Roles | SWE / DS / PM (3 templates × 2 countries = 6) |
| Resume input | PDF or DOCX upload |
| Agent design | Single sharp GPT-4o with specialized passes (parse, evaluate, ATS-check, JD-extract, JD-tailor, rewrite). No agent fan-out. |
| Output design | Inline visual highlights (severity-coded) + click-to-rewrite per bullet. No 5-paragraph rubric. |
| Rewrite policy | Placeholder hybrid — placeholders for hard numbers (`[X%]`, `[N users]`, `[$Y]`), full rewrite for verbs/structure |
| JD evaluator | Auto-tailor + diff view + per-change accept. Includes bullet rewrites, skill reorder, summary rewrite |
| ATS | Always-on parseability check + JD-driven keyword score + raw-text ATS-simulator preview |
| PDF render | Puppeteer (HTML + CSS → headless Chrome) |
| Brand | Prism Pro |
| Monetization | Freemium + credits hybrid |
| Architecture | Extend existing FastAPI + Next.js monolith |

## 6. Architecture

```
┌─────────────────────────────────────────────────┐
│  Next.js 14 (Vercel/Railway)                    │
│  Routes: /dashboard/resume                      │
│          /dashboard/resume/[id]/edit            │
│          /dashboard/resume/tailor               │
│          /dashboard/resume/[id]/export          │
│          /dashboard/jobs (kept, demoted)        │
└──────────────┬──────────────────────────────────┘
               │ HTTPS REST
┌──────────────▼──────────────────────────────────┐
│  FastAPI (Railway)                              │
│  ├─ api/resumes.py (extended)                   │
│  ├─ api/jd.py (NEW)                             │
│  ├─ api/exports.py (NEW)                        │
│  ├─ api/credits.py (NEW)                        │
│  ├─ services/resume/                            │
│  │   ├─ parser.py (PDF + DOCX → JSON)           │
│  │   ├─ evaluator.py (weak-bullet flags)        │
│  │   ├─ ats_simulator.py (parseability + raw)   │
│  │   └─ rewriter.py (bullet-level rewrite)      │
│  ├─ services/jd/                                │
│  │   ├─ extractor.py (JD → must/good-to-have)   │
│  │   └─ tailor.py (resume×JD → diff plan)       │
│  ├─ services/pdf/                               │
│  │   ├─ renderer.py (Puppeteer wrapper)         │
│  │   └─ templates/ (6 HTML+CSS files)           │
│  └─ services/_deprecated/                       │
│      referrals, email, activity                 │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│  Supabase (Postgres + Auth + Storage)           │
│  Existing: users, jobs, resumes (legacy)        │
│  NEW: resume_documents, resume_evaluations,     │
│       resume_versions, jd_evaluations,          │
│       credit_ledger                             │
│  Storage: resume uploads (PDF/DOCX), exports    │
└─────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│  External                                        │
│  OpenAI GPT-4o-2024-08-06 (Structured Outputs)  │
│  Headless Chromium (Puppeteer, on Railway)      │
│  Stripe (credit purchases)                      │
└─────────────────────────────────────────────────┘
```

## 7. Components

### 7.1 Resume parser

PDF and DOCX upload pipeline. PDF: PyPDF + pdfplumber for text + structure; fallback `unstructured` for tricky layouts. DOCX: `python-docx` for clean section extraction.

Output: `ResumeDocument` JSON
```
{
  contact: {name, email, phone, links: []},
  summary: string?,
  experience: [{company, role, dates, location, bullets: [{id, text, raw_text}]}],
  education: [{school, degree, dates, gpa?}],
  skills: {hard: [], soft: [], categorized?: {languages, frameworks, ...}},
  projects: [{name, bullets: []}]?,
  certifications: []?,
  raw_text: string  // for ATS sim
}
```

Bullet IDs are stable across versions for diffing.

### 7.2 Resume evaluator (single agent, specialized passes)

One GPT-4o call with a hyper-critical senior-recruiter system prompt. Structured output flags every bullet with severity + reason:

```
{
  overall_score: 0-100,
  bullet_flags: [
    {bullet_id, severity: "critical"|"warning"|"info",
     reason: string,  // "no quantification", "weak verb", "vague impact", "duplicated"
     category: "quantification"|"verb"|"structure"|"clarity"|"redundancy"|"ats"
    }
  ],
  format_issues: [{type, location, fix_hint}],
  summary_critique: string,
  skill_gaps: []
}
```

UI renders bullets with color-coded highlights (red/yellow/blue dots).

### 7.3 ATS simulator

Two outputs:
- **Parseability score** — checks for tables, columns, images, unusual fonts, header/footer text, hidden text. 0-100.
- **Raw-text preview** — strips formatting, shows what a typical ATS parser ingests. User sees their resume the way Workday/Greenhouse would.

Implementation: lightweight Python (pdfminer + heuristics) — no LLM. Heuristic, not perfect, but visceral and accurate enough.

### 7.4 Rewriter (placeholder hybrid)

Per-bullet rewrite endpoint. Inputs: bullet_id, original text, optional JD context, target role. Output:
```
{
  rewritten: string,  // verbs, structure, clarity improved
  placeholders: [
    {token: "[X%]", what: "describe the metric you improved"},
    {token: "[N users]", what: "scale of the impact"}
  ],
  applied_changes: ["strengthened verb", "added XYZ structure"]
}
```

System prompt anchors:
- Google XYZ formula
- 7-second scan optimization
- Never invent numbers/facts the user didn't provide; use placeholders
- Recruiter voice: direct, specific, no buzzword slop ("synergies", "leverage")
- Country-aware tone (US: action-oriented; IN: balance action + scope-of-responsibility)

User sees diff, fills placeholders inline, accepts.

### 7.5 JD extractor

Single GPT-4o call. Input: JD text. Output:
```
{
  must_have: [{skill, evidence_from_jd, type: "technical"|"experience"|"credential"}],
  good_to_have: [{skill, evidence_from_jd, type}],
  soft_skills: [],
  seniority: "junior"|"mid"|"senior"|"staff",
  primary_role_category: "SWE"|"DS"|"PM"|"other",
  country_hint: "US"|"IN"|"other",
  red_flags: []  // e.g. "compensation undisclosed", "vague responsibilities"
}
```

### 7.6 JD tailor (resume × JD → diff plan)

Single GPT-4o call with both resume JSON + JD extraction. Produces a diff plan:
```
{
  match_score: 0-100,
  must_have_coverage: {found: [], missing: []},
  good_to_have_coverage: {found: [], missing: []},
  proposed_changes: {
    bullets: [{bullet_id, old, new, reason, placeholders: []}],
    skills_reorder: {new_order: [], rationale: string},
    summary_rewrite: {old, new, reason},
    suggested_additions: [
      {section: "skills", item: "Kubernetes", reason: "JD requires; user mentioned in projects bullet 3 — promote to skills"}
    ]
  }
}
```

Frontend shows diff view. User accepts/rejects per change. Accepted set saved as new `resume_version`.

### 7.7 PDF renderer + template engine

Puppeteer service inside FastAPI. On export:
1. Load template (6 templates, parameterized by country+role).
2. Inject resume JSON into Handlebars/Jinja-style HTML template.
3. Render via headless Chromium.
4. Save PDF to Supabase Storage; return signed URL.

Template directory:
```
services/pdf/templates/
  us/swe.html, us/ds.html, us/pm.html
  in/swe.html, in/ds.html, in/pm.html
  shared/_base.css, _typography.css, _print.css
```

Templates use shared CSS variables for fonts (Inter for US, Inter+IBM Plex for IN headings), spacing, and section ordering. Country differences (1-page US vs 2-page IN, photo/DOB absent for both, US action-first vs IN scope-aware) are baked into template structure, not runtime config.

### 7.8 Credits + auth

- `credit_ledger` table. Credits are a single fungible counter.
- Per-operation cost: evaluation = 1, JD tailoring = 2 (extract + tailor), bullet rewrite = 0 (rolled into eval/tailor), export = 1.
- Free tier monthly grant: **20 credits** (≈ 4 full standalone polishes-with-export, or ≈ 5 JD tailor-and-exports, or any mix).
- Stripe webhook → top-up.
- Middleware `require_credits(amount)` on relevant endpoints; refund on hard fail.

### 7.9 Frontend components

| Route | Purpose |
|---|---|
| `/dashboard/resume` | Upload + resume library + recent versions |
| `/dashboard/resume/[id]/edit` | Rendered resume with inline severity highlights + bullet click → rewrite modal + ATS-simulator tab + version history |
| `/dashboard/resume/tailor` | Upload + paste JD → JD analysis panel + diff view + per-change accept |
| `/dashboard/resume/[id]/export` | Pick country + role template + preview + download PDF |
| `/dashboard/credits` | Balance, history, Stripe buy |
| `/dashboard/jobs` | Legacy job tracking, kept but in secondary nav |

## 8. Data Flow

### 8.1 Standalone resume polish

```
1. User → POST /api/resumes/upload (PDF/DOCX)
2. Parser → ResumeDocument JSON → persist resume_documents row
3. require_credits(1) → POST /api/resumes/{id}/evaluate
4. Evaluator (GPT-4o, Structured Output) → bullet_flags
5. ATSSimulator → parseability_score + raw_text_preview
6. Persist resume_evaluations row
7. Frontend renders /edit page with highlights + ATS tab
8. User clicks weak bullet → POST /api/resumes/{id}/rewrite/{bullet_id}
   { target_role, jd_context? }
9. Rewriter → rewritten + placeholders
10. User fills placeholders, accepts → POST /api/resumes/{id}/versions
11. New resume_versions row (parent_id + change_set)
12. Export: pick template → POST /api/exports
13. PDF Renderer → signed URL → download
```

### 8.2 JD-driven tailoring

```
1. User → /dashboard/resume/tailor → upload resume + paste JD
2. Parser → ResumeDocument
3. JDExtractor → JD requirements JSON
4. require_credits(2) (extraction + tailoring)
5. JDTailor → diff plan
6. Frontend renders 3 panels:
   - JD analysis (must/good-to-have + match score)
   - ATS simulator tab
   - Diff view: bullet rewrites + skill reorder + summary rewrite
7. User accepts/rejects per change → POST /api/resumes/{id}/apply-diff { accepted_change_ids }
8. New resume_versions row with all accepted changes
9. Export: pick template + country/role auto-suggested from JD analysis → PDF
```

### 8.3 Credit lifecycle (unchanged)

Monthly grant cron + Stripe webhook + per-operation debit + low-balance UI warning.

## 9. Error Handling

| Failure | Response |
|---|---|
| PDF parse fail | Fallback to `unstructured` lib. If still fails, 400 with "Try DOCX format" message. No credit debit. |
| DOCX parse fail | 400 with "File looks corrupt; re-save and retry". No credit debit. |
| Resume too long (>15k tokens) | Truncate experience to top-3 roles for evaluation; warn user. |
| Evaluator schema validation fail | Retry once with stricter prompt; if still fails, return raw evaluation with `degraded: true`. |
| Rewriter hallucinates a number | Detection: regex for unprompted digits not in original bullet AND not in placeholder. Reject + retry once with reinforced instructions. |
| JD parse empty/garbled | 400 before debit. |
| Match score < 30 | Show "low match" warning + suggest broader skill review before tailoring. Still allow proceed. |
| Puppeteer timeout (>15s) | Kill, retry once with smaller payload, then 500 with "Try again in a moment". No credit consumed on export fail. |
| Template HTML render fail | Fallback to most-recent-working template; flag for admin alert. |
| OpenAI 429 | Exp backoff 3× (1s, 3s, 9s). |
| Concurrent credit debit | Postgres row lock on `users.credit_balance`. |
| Stripe webhook replay | Idempotency key on `credit_ledger.external_ref`. |

**Principles:**
- Debit AFTER pre-checks. Refund on hard fail in same transaction.
- Hallucination detection runs on every rewriter output before return.
- Versioning is append-only; users never lose work.
- Always tell user what failed and the next step.

### Observability

- Structured JSON logs: `event`, `resume_id`, `user_id`, `pass`, `latency_ms`, `cost_usd`.
- Sentry for unhandled exceptions.
- Hallucination-rejection metric (rate per 1k rewrites). Alert if >2%.
- Puppeteer render time p95.
- Cost per evaluation/tailoring tracked per user (for free-tier policing + pricing tuning).

## 10. Testing

### Parser

| Test | What | Tool |
|---|---|---|
| Unit | Per-section extractor (experience, skills, education) | pytest |
| Fixtures | 20 fixture resumes (10 PDF, 10 DOCX), varied formats (tables, columns, headers) → assert structured output | pytest |
| Edge cases | Encrypted PDF, scanned image PDF, RTL text → graceful 400 | pytest |

### Evaluator + ATS sim

| Test | What |
|---|---|
| Schema | Pydantic models reject malformed outputs |
| Golden | 10 fixture resume + role pairs → snapshot weak-bullet flag IDs and severities |
| ATS heuristics | 5 known-bad PDFs (with tables, hidden text, columns) → parseability score below threshold |
| Raw-text accuracy | Compare simulator output to Workday/Greenhouse free parsers on same fixtures |

### Rewriter

| Test | What |
|---|---|
| Schema | Output schema validates |
| Hallucination detection | 100 rewrites on fixture bullets; assert 0 unprompted numbers leak through |
| Placeholder policy | Bullet with no metrics → assert at least 1 placeholder generated |
| Voice quality | Manual review of 50 rewrites by user (you) before launch — accept rate target >70% |

### JD extractor + tailor

| Test | What |
|---|---|
| Extractor schema | Pydantic schema, 20 JD fixtures (US-SWE, US-DS, IN-PM, etc.) |
| Tailor diff schema | resume × JD → valid diff plan |
| Golden | 10 fixture (resume, JD) pairs → snapshot match scores + accepted-change counts |

### PDF renderer

| Test | What |
|---|---|
| Render smoke | Each of 6 templates renders a fixture resume without error |
| Visual regression | Screenshot diff each template (Playwright) per PR |
| Performance | Render <8s p95 per template |
| Font embedding | Inter + IBM Plex embedded in output PDF (subset) |

### Frontend

| Test | What | Tool |
|---|---|---|
| Component | Bullet highlights, rewrite modal, diff view, template picker | Vitest + RTL |
| E2E happy path | Upload → evaluate → rewrite bullet → export | Playwright |
| E2E tailor flow | Upload + paste JD → accept changes → export | Playwright |
| Accessibility | Keyboard nav, screen-reader labels for severity colors | axe-core |

### CI gates

- All unit + schema + hallucination + credit tests block merge.
- Golden snapshot tests + visual-regression PDF tests block merge.
- Playwright E2E blocking for both flows.
- Hallucination metric monitored in prod; circuit breaker on >5% rate (disable rewriter, alert).

### Test data
- Fixtures: `backend/tests/fixtures/resumes/` (20 mixed), `jds/` (20 across countries+roles), `expected_diffs/` (snapshots).

### Out of MVP

- Multi-language resumes.
- OCR of scanned PDFs.
- LinkedIn-PDF import (different layout than DOCX/Word resumes).
- Word-document export (PDF only at launch).

## 11. Migration / Cleanup

- Move `referrals`, `email_*`, `activity_heatmap` services to `backend/app/services/_deprecated/`. Routes return 410 Gone with sunset header for one release, then deleted.
- Frontend: remove `/dashboard/referrals` and `/dashboard/activity` routes; redirect to `/dashboard/resume`.
- Existing `consolidated_resume_evaluator.py` is refactored into `services/resume/evaluator.py`. Old endpoint kept for one release with deprecation header.
- Job-tracking features stay live but demoted to secondary nav (`/dashboard/jobs`).
- DB tables for deprecated features remain (non-destructive). Manual drop after 30 days of zero usage confirmed via query.

## 12. Open Questions

- Final credit-pack pricing for INR and USD (needs market signal post-MVP).
- Whether to ship Word export in a fast-follow (recruiters sometimes ask for .docx).
- Onboarding flow: do new users go through a guided "polish your existing resume" tour, or land in upload flow directly?
- Stripe vs Razorpay primary for IN market (Razorpay better local UX; Stripe simpler ops). Probably Stripe first, Razorpay v2.
- Whether resume versions should auto-snapshot on every accept, or only on export.

## 13. Next Steps

This is the umbrella spec. Implementation is a single product, not multi-pillar — both flows share parser, evaluator, rewriter, PDF renderer. One implementation plan from writing-plans covers everything in §6–7.

Future spec stubs (deferred, NOT in this plan):
- Voice interview practice (full pillar 2 of original concept).
- Browser extension job tracker (pillar 3).
