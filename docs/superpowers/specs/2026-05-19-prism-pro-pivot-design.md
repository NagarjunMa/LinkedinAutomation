# Prism Pro — Platform Pivot Design

**Date:** 2026-05-19
**Status:** Approved (umbrella vision spec)
**Author:** brainstorming session
**Scope:** Reposition Prism Pro from US-centric job aggregator to interview-prep + resume-prep platform for South Asian + EU diaspora job seekers. MVP covers two pillars (multi-agent resume evaluation, AI voice behavioral interview). Browser extension tracker deferred to a future spec.

---

## 1. Problem Statement

Existing job-hunting tools focus on the US market and on job aggregation. South Asian and European users (students, early-career, mid-career, career switchers, returnees, visa aspirants) lack tooling that:

1. Gives ATS-grade resume feedback from a panel that thinks like senior recruiters.
2. Provides realistic behavioral interview practice with voice, tailored personas, and JD-driven question sets.
3. Closes the loop: resume passes ATS → user drills the same JD via mock interview → ships a stronger application.

Prism Pro pivots to fill this gap. Job aggregation stops being the headline; preparation does.

## 2. Goals

- Ship a focused MVP: 5-agent resume evaluation + voice behavioral interview practice.
- Keep existing job tracking as a secondary feature (users still need to manage applications) but demote it in product narrative.
- Strip features that distract from the new positioning (referrals, email automation, activity heatmap).
- Preserve the existing brand (`prismpro.live`), Google-verified OAuth, and underlying auth + DB infrastructure.
- Use agentic / AI patterns wherever they materially raise output quality.

## 3. Non-Goals

- Job aggregation as a primary feature.
- US-only feature parity. Localization beyond English copy is out of MVP.
- Browser extension job tracker (Pillar 3) — deferred to a separate spec.
- Live human-in-the-loop coaching (always AI-driven for now).
- Multi-language voice. English only at launch.

## 4. Target User

South Asian + EU diaspora across all career stages: undergrad students through mid-career switchers and returnees. The MVP must be useful for any of these personas, but the experience surface (persona library, JD parsing, voice difficulty) accommodates seniority differences without forking the product.

## 5. Decisions Locked

| Topic | Choice | Reason |
|---|---|---|
| MVP scope | Resume eval + voice interview (C2) | Full prep loop; differentiates from aggregators |
| Existing code | Strip non-core (kill referrals, email, heatmap). Keep job tracking + resume eval as foundation. | Focus + faster ship |
| Voice stack | Gemini Live API | Lowest cost/min, low latency, sufficient persona steering |
| Resume agents | 5-agent panel + synthesizer | Maps to recruiter, hiring manager, ATS, industry, coach roles |
| Voice scope | Persona + JD-driven (B+C) | Max personalization for differentiated value |
| Brand | Prism Pro (keep) | Domain + OAuth verified; reframe marketing instead |
| Monetization | Freemium + credits hybrid | Student-friendly, scales with Gemini Live cost |
| Feedback mode | Post-session + replay coach | Preserves interview realism; coach loop drives improvement |
| Build order | Resume first → Voice second | Lowest-risk path; existing code reuse |
| Orchestration | `asyncio.gather` for resume panel; LangGraph only for voice state machine | Simplicity where it works; structure where state matters |
| Architecture | Approach 1 — extend existing FastAPI + Next.js monolith | Min infra change, fastest MVP |

## 6. Architecture

```
┌─────────────────────────────────────────────────┐
│  Next.js 14 (Vercel/Railway)                    │
│  Routes: /dashboard/resume-prep                 │
│          /dashboard/interview-prep              │
│          /dashboard/jobs (kept, demoted)        │
│  Voice client: WebRTC → backend WS proxy        │
└──────────────┬──────────────────────────────────┘
               │ HTTPS REST + WSS
┌──────────────▼──────────────────────────────────┐
│  FastAPI (Railway)                              │
│  ├─ api/resumes.py (existing, extended)         │
│  ├─ api/interview.py (NEW)                      │
│  ├─ api/credits.py (NEW)                        │
│  ├─ services/agents/ (NEW)                      │
│  │   ├─ ats_agent.py                            │
│  │   ├─ recruiter_agent.py                      │
│  │   ├─ hiring_manager_agent.py                 │
│  │   ├─ industry_specialist_agent.py            │
│  │   ├─ career_coach_agent.py                   │
│  │   ├─ synthesizer.py                          │
│  │   └─ orchestrator.py (asyncio.gather)        │
│  ├─ services/voice/ (NEW)                       │
│  │   ├─ gemini_live_bridge.py (WSS proxy)       │
│  │   ├─ interview_state.py (LangGraph)          │
│  │   ├─ question_generator.py (JD-driven)       │
│  │   └─ post_session_scorer.py                  │
│  └─ services/_deprecated/ (move legacy here)    │
│      referrals, email, activity                 │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│  Supabase (Postgres + Auth)                     │
│  Existing: users, jobs, resumes                 │
│  NEW: agent_evaluations, interview_sessions,    │
│       interview_turns, credit_ledger, personas  │
└─────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│  External                                        │
│  OpenAI GPT-4o (resume agents)                  │
│  Gemini Live API (voice interview)              │
│  Stripe (credits purchase)                      │
└─────────────────────────────────────────────────┘
```

## 7. Components

### 7.1 Multi-agent resume panel

Five specialist agents plus a synthesizer. Each agent is a discrete service class with its own system prompt (15+ yr recruiter framing), input contract, and Pydantic output schema.

| Agent | Role | Input | Output |
|---|---|---|---|
| `ATSAgent` | Parsing compliance, keyword density vs JD, format blockers (tables/columns/images) | resume_text, jd_text | `{ats_score: 0-100, keyword_gaps: [], format_issues: [], parseability: bool}` |
| `RecruiterAgent` | 7-second scan, above-the-fold impact, scannability, headline | resume_text | `{first_impression_score, scan_findings: [], headline_strength}` |
| `HiringManagerAgent` | XYZ formula audit, impact verbs, quantification, story arc per bullet | resume_text, jd_text | `{xyz_per_bullet: [], weak_bullets: [], impact_score}` |
| `IndustrySpecialistAgent` | Domain match (SWE/DS/PM/etc.), tech-stack relevance, seniority signaling | resume_text, jd_text, target_role | `{domain_fit: 0-100, missing_signals: [], red_flags: []}` |
| `CareerCoachAgent` | Improvement plan, prioritized fixes, learning resources for gaps | aggregate of above | `{action_plan: [], priority_fixes: [], skill_gap_resources: []}` |
| `Synthesizer` | Merge → final report, overall score, top-3 actions | all five outputs | `ResumeEvalReport` |

Orchestration runs agents 1–4 in parallel via `asyncio.gather`. CareerCoach runs after that aggregate is ready; Synthesizer runs last. Target end-to-end latency ~18s p95. Model: GPT-4o-2024-08-06 with Structured Outputs (Pydantic).

### 7.2 Voice interview pipeline

| Component | Responsibility |
|---|---|
| `PersonaCatalog` | Pre-built personas: Amazon LP, Google, Meta, Stripe, FAANG-PM, IN startup CTO. Each is system prompt + Gemini Live voice config. |
| `QuestionGenerator` | Pre-session: parse JD → extract competencies → generate 6–8 tailored questions (GPT-4o, structured). Mix STAR classics + JD-specific. |
| `GeminiLiveBridge` | FastAPI WSS endpoint. Proxies user audio to Gemini Live; streams Gemini audio back. Injects persona + Q list as system prompt context. |
| `InterviewStateMachine` | LangGraph FSM. States: `intro → ask_q → listen → followup? → next_q → wrap → ended`. Tracks Q index, time, interrupts. |
| `TranscriptStore` | Append-only turn log: speaker, audio_url (Supabase Storage), text, timestamp. |
| `PostSessionScorer` | Per-Q rubric (STAR completeness, clarity, impact, behavioral signal). Generates "ideal answer" using user's transcript context. |
| `ReplayCoachAgent` | User picks a Q → drills with coach (text or voice). Forces STAR rewrite. |

### 7.3 Credits + auth

- `credit_ledger` table: `user_id, delta, reason, balance_after, ts, external_ref` (Stripe idempotency).
- Free tier monthly grant: 4 resume evals + 30 voice minutes (cron job on 1st UTC).
- Stripe webhook → credit top-up.
- Middleware: `require_credits(amount)` decorator on relevant endpoints.

### 7.4 Frontend routes

| Route | Purpose |
|---|---|
| `/dashboard/resume-prep` | Upload + JD paste → 5-step progress → tabbed report |
| `/dashboard/interview-prep/new` | Persona picker + JD paste → start session |
| `/dashboard/interview-prep/[id]` | Live audio UI (mute, end, timer, Q counter) |
| `/dashboard/interview-prep/[id]/review` | Transcript + per-Q scores + ideal answers + replay |
| `/dashboard/credits` | Balance, history, Stripe buy |
| `/dashboard/jobs` | Existing job tracking (kept, demoted in nav) |

## 8. Data Flow

### 8.1 Resume eval (REST, sync, ~18s)

1. `POST /api/resumes/{id}/evaluate { jd_text, target_role }`.
2. Middleware `require_credits(1)` debits the ledger (with refund on failure).
3. Orchestrator:
   - `asyncio.gather(ATS, Recruiter, HiringManager, Industry)` — parallel.
   - `await CareerCoach(aggregate)` — sequential.
   - `await Synthesizer(all five)` — sequential.
4. Persist `ResumeEvaluation` row with per-agent JSONB blobs.
5. Return `ResumeEvalReport` (overall + 5 sections + action plan).
6. Frontend renders tabbed report; top-3 actions pinned.

A 5-step progress UI uses polling on `/evaluate/{job_id}/status`.

### 8.2 Voice interview session

Pre-session (REST):

1. `POST /api/interview/sessions { persona_id, jd_text }`.
2. QuestionGenerator → GPT-4o → 6–8 Qs (structured) → persist.
3. Return `{ session_id, persona, q_count, est_minutes }`.

Session start (WSS):

4. Frontend → `WSS /api/interview/{session_id}/stream`. Browser captures mic via WebRTC, sends PCM frames.
5. Bridge opens upstream WSS to Gemini Live.
6. Inject system prompt: persona + Q list + behavioral rules.
7. State enters `intro_state` → Gemini emits greeting.

Loop:

8. User audio → bridge → Gemini → audio response → frontend.
9. State machine tracks Q index. Source of truth: text channel from Gemini parsed for "next_q" markers; fallback heuristic is turn count.
10. Transcript writer: every turn appends an `interview_turns` row. Audio chunks land in Supabase Storage; text comes from Gemini's transcription stream.

End:

11. User clicks "End" OR `state == ended` → close upstream WSS.
12. Background task `PostSessionScorer` pulls transcript, scores each Q, and generates an "ideal answer" per Q from the user's transcript context.
13. Frontend polls `/sessions/{id}/score` (WS push optional later).
14. `/review` page renders transcript + scores + replay buttons.

### 8.3 Replay coach

1. `POST /api/interview/{session_id}/replay { question_id, mode: "text"|"voice" }`.
2. Text mode: chat WS with Coach agent loaded with original Q + user answer + ideal answer → STAR rewrite drill.
3. Voice mode: re-open Gemini Live with Coach persona (lower difficulty, encouraging).
4. Save `coached_answer` to `interview_turns.coached_version`.

### 8.4 Credit lifecycle

1. Monthly cron (1st UTC) → grant free tier (4 evals + 30 voice min).
2. Resume eval → debit 1 credit.
3. Voice session → meter per minute (heartbeat from bridge every 60s; debit 1 voice-credit).
4. Stripe checkout → webhook → credit top-up.
5. Low-balance threshold → frontend warning + upsell modal.

## 9. Error Handling

### Resume eval

| Failure | Detection | Response |
|---|---|---|
| Single agent timeout (>30s) | `asyncio.wait_for` per agent | Mark agent `degraded`, synthesize from N-1. |
| OpenAI 429/503 | HTTP code | Exp backoff 3× (1s, 3s, 9s); then degrade. |
| Schema validation fail | Pydantic ValidationError | Retry once with stricter prompt; then degrade. |
| All 5 agents fail | gather all-fail | Refund credit; return 503 + actionable error. |
| Synthesizer fail | Pydantic fail | Return raw agent outputs in template; mark "synthesis pending". |
| JD/resume parse fail | Empty/garbled input | 400 before debit; no credit consumed. |
| Resume too long (>15k tokens) | Pre-check | Truncate + warn, OR reject if extreme. |

### Voice interview

| Failure | Detection | Response |
|---|---|---|
| Gemini Live upstream WSS fail | onclose/onerror | Bridge notifies client; 30s reconnect window; session marked `interrupted`. |
| User WSS drop | client disconnect | Save state; auto-resume within 30s; after that, end + partial scoring. |
| Mic permission denied | WebRTC error | Modal "Mic required, retry"; no session start, no credit debit. |
| Credits exhausted mid-session | Heartbeat debit fails | Bridge emits `low_credit`; UI shows 60s warning; at 0, graceful end + scoring. |
| Gemini rate limit | 429 upstream | End session; refund unused minutes; log incident; tell user to retry later. |
| Bridge crash | process death | Background reconciler: sessions with `status=active AND last_heartbeat > 5min` → marked failed + refund. |
| Transcript write fail | DB error | Buffer in Redis; async retry; don't break audio stream. |
| Post-session scorer fail | task error | Mark `unscored`; expose "Retry scoring" button; no refund (session happened). |

### Auth + credits

| Failure | Response |
|---|---|
| JWT expired mid-session | Bridge accepts long-lived session token issued at WSS handshake; doesn't recheck JWT per frame. |
| Stripe webhook replay | Idempotency key on `credit_ledger.external_ref`. |
| Concurrent credit debit (double-spend) | Postgres row lock on `users.credit_balance` during debit. |
| Refund after session end | Allowed within 24h; manual review flag if amount exceeds threshold. |

### Observability

- Structured JSON logs extending existing schema: `event`, `session_id`, `user_id`, `agent`, `latency_ms`, `cost_usd`.
- Sentry for unhandled exceptions.
- Per-agent latency + cost dashboard (Supabase view + Recharts panel, admin-only).
- Voice SLO: <500ms time-to-first-token from user speech end. Alert on p95 breach.

### Principles

- Debit AFTER pre-checks; refund on hard fail in same transaction.
- Partial output beats no output.
- Never lose transcripts (Redis buffer).
- Always tell user what failed and the next step.

## 10. Testing

### Resume panel

| Type | What | Tool |
|---|---|---|
| Unit | Each agent prompt → mock OpenAI → schema validates | pytest + respx |
| Schema | Pydantic models reject malformed agent outputs | pytest property tests |
| Golden | 10 fixture resume + JD pairs (SWE/DS/PM/leadership/junior/senior/IN/EU) → snapshot scored outputs | pytest-snapshot |
| Orchestrator | gather() partial-fail path: mock 1 agent raise → degraded report, no refund | pytest async |
| Latency | Real OpenAI, full panel → <25s p95 | nightly |
| Cost | Sum token usage → <$0.15/eval p95 | log + assert |

### Voice pipeline

| Type | What | Tool |
|---|---|---|
| Unit | QuestionGenerator on JD fixtures → 6–8 STAR-shaped Qs, JD-grounded | pytest |
| State machine | LangGraph driven by synthetic events; assert state correctness | pytest |
| Bridge integration | Mock Gemini Live WSS server → bridge handles connect/disconnect/audio frames | pytest + websockets mock |
| E2E (manual) | Real Gemini Live; Playwright loads `/interview-prep/new` → start → grant mic → speak canned answers → review page shows scored Qs | Playwright + audio injection |
| Latency SLO | Probe: 1s audio → first audio byte from Gemini → <500ms p95 | scripted, hourly in staging |
| Scoring | PostSessionScorer on 5 fixture transcripts (strong/weak/partial-STAR/off-topic/ESL) → scores in expected bands | pytest |

### Credits + auth

| Test | What |
|---|---|
| Concurrent debit | 10 parallel evals → no negative balance, exactly 10 debits |
| Stripe webhook idempotency | Replay 3× → 1 ledger entry |
| JWT expiry mid-session | Session token continues even after underlying JWT expiry |
| Refund correctness | Force agent panel fail → credit refunded in same tx |

### Frontend

| Test | What | Tool |
|---|---|---|
| Component | Report tabs, persona picker, credit balance | Vitest + RTL |
| E2E resume | Upload → eval → report | Playwright |
| E2E voice (mock backend) | Frontend renders state correctly | Playwright + WSS mock |
| Accessibility | Keyboard nav, screen-reader labels, mic-permission fallback | axe-core |

### CI gates

- Unit + schema + state-machine + credit tests block merge.
- Golden snapshot tests run nightly (model drift detection; not merge-blocking).
- Latency SLO probes hourly in staging; alert Slack on breach.
- Playwright E2E blocking for resume flow; voice E2E tagged + nightly (flaky).

### Test data

- Fixtures: `backend/tests/fixtures/resumes/`, `jds/`, `transcripts/` (10 + 10 + 5).
- Seed personas: 6 (Amazon LP, Google, Meta, Stripe, FAANG-PM, IN startup CTO) in a migration.
- Mock Gemini Live: local FastAPI WSS that echoes canned audio.

### Out of MVP

- Load testing (defer to post-PMF).
- Multi-language voice.
- Voice biometric / accent eval (privacy + scope creep).

## 11. Migration / Cleanup

- Move `referrals`, `email`, `activity_heatmap` service modules to `backend/app/services/_deprecated/`. Routes return 410 Gone with sunset header for one release, then deleted.
- Frontend: remove `/dashboard/referrals` and `/dashboard/activity` routes; redirect to dashboard.
- DB tables for deprecated features remain (no destructive migration) until usage is confirmed zero for 30 days.
- Job-tracking features stay live but moved out of primary nav. `/dashboard/jobs` reachable via secondary menu.

## 12. Open Questions (resolve in follow-up specs / discovery)

- Final pricing for credits packs and free-tier resets — needs market research for INR / EUR.
- Whether Stripe vs Razorpay primary for IN market.
- Persona catalog v1 list — final 6 are reasonable starters; expand based on user demand signals.
- Voice consent + transcript retention policy — privacy review needed before launch (likely 30-day default retention with explicit user delete).

## 13. Next Steps

This umbrella spec is the foundation. Each pillar gets its own implementation plan via the writing-plans skill:

1. **Pillar 1 plan:** Multi-agent resume eval implementation (this is built first).
2. **Pillar 2 plan:** Voice interview implementation (after Pillar 1 ships).
3. **Pillar 3 spec (future):** Browser extension job tracker — own design doc + plan.
