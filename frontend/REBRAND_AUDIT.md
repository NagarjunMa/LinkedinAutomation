# Prism Pro Frontend Rebrand Audit

**Batch 1 output.** Documents every file that needs copy/content changes in Batches 2–4.
Files are grouped by domain. DO NOT delete anything listed here until Batch 4.

---

## How to read this document

- **Stale:** what is wrong with the current copy and why it conflicts with the new positioning.
- **Direction:** what the replacement should say/do (full copy written in Batch 2 or 3).
- **Batch:** which batch executes the change.

New positioning: **"Recruiter-Grade Resume Prep"** for 3–15 yr experienced engineers (South Asian + EU diaspora, USA + India markets). Voice: hand-tuned by senior recruiters, AI-powered, human-validated. No startup-bro language, no AI-hype. Avoid: "students", "LinkedIn automation", "job aggregation", "find jobs".

---

## 1. Landing Page (`src/app/page.tsx`)

**File:** `frontend/src/app/page.tsx`
**Batch:** 2

### Stale copy

| Location | Current | Problem |
|---|---|---|
| Badge / pill label | "Built for Senior Engineering Roles" | Acceptable but too narrow — excludes DS and PM target roles. |
| Hero H1 | "Your job search is a numbers game. You're playing without a scoreboard." | Job-tracker framing; not resume-polish positioning. |
| Hero subtext | "Engineering isn't about effort; it's about systems. Stop drowning in chaotic spreadsheets…" | Spreadsheets + job-tracker pain point, wrong product narrative. |
| CTA button | "Initialize System" | Startup-bro tech jargon, off-brand. |
| Section label | "The Mirror of Pain" | Borrowed startup-marketing language, feels theatrical. |
| Section copy | "Spreadsheets are where applications go to die." / "loses 40% of interview opportunities due to poor follow-up" | Job-tracking pain, not resume pain. Unverified stat. |
| Bento card | "URL Persistence Engine — Automatically snapshot job requirements…" | Describes the deprecated job-tracker feature, not resume polish. |
| Bento card | "Network Parser — Convert LinkedIn profiles into tailored referral requests…" | Describes deprecated referral engine, should be replaced. |
| Bento card | "Recursive Context Profiling — remembers your 4+ years of distributed systems…" | Hardcoded personal data; feature framing is confusing. |
| Section label | "Commitment Required" | Gatekeeping language; not inclusive of diaspora user. |
| Section copy | "Prism Pro is an exclusive system for engineers who treat their career…" | "Exclusive" + "engineers only" — wrong for DS/PM targets. |
| Footer copy | "High-precision career management for the top 1% of engineers." | Wrong positioning, wrong audience framing. |

**Direction:** Rewrite entire hero + bento section around resume polish / JD tailoring workflow. Keep earth-tone bento grid structure. Replace "exclusive" language with premium-but-accessible professional framing.

---

## 2. Landing page sub-components

### `src/components/landing/BentoGrid.tsx`
**Batch:** 2

- Cards 3 ("Network Parser") and 4 ("Recursive Context Profiling") describe deprecated referral + generic profile features. Rewrite to: ATS simulator preview, JD-diff accept/reject flow, country-aware PDF export, and credit/usage meter.

### `src/components/landing/Navigation.tsx`
**Batch:** 2

- Needs audit for any references to deprecated routes (`/dashboard/referrals`, `/dashboard/activity`) or stale nav items. Verify nav CTA still points to `/login`.

---

## 3. SEO + Meta (`src/app/layout.tsx`)

**File:** `frontend/src/app/layout.tsx`
**Batch:** 2

### Stale content

| Field | Current | Problem |
|---|---|---|
| `title.default` | "Prism Pro - AI-Powered LinkedIn Job Automation for Students" | Wrong product + wrong audience. |
| `description` | "Streamline your job search… Perfect for students and recent graduates." | Student targeting, job-tracker framing. |
| `keywords` | "LinkedIn automation", "student job search", "LinkedIn job extraction", etc. | All wrong for new product. Should be: resume tailoring, ATS optimization, JD matching, etc. |
| `metadataBase` | `https://jobflowpro.com` | **STALE DOMAIN** — must be `https://prismpro.live`. |
| `openGraph.url` | `https://jobflowpro.com` | **STALE DOMAIN.** |
| `openGraph.title` | "Prism Pro - AI-Powered LinkedIn Job Automation" | LinkedIn automation framing, wrong product. |
| `openGraph.description` | "…Perfect for students and recent graduates." | Student targeting. |
| `twitter.title` | Same LinkedIn automation framing | Wrong. |
| JSON-LD `description` | "AI-powered LinkedIn job search automation for students and recent graduates" | Both wrong. |
| JSON-LD `offers.description` | "Free for students" | Wrong tier/audience framing. |

**Direction:** Rewrite all to: "Recruiter-grade resume tailoring and JD matching for experienced engineers and product professionals. Used by SWEs, Data Scientists, and PMs targeting roles in the US and India." Update domain to `prismpro.live` everywhere.

---

## 4. Manifest (`src/app/manifest.ts`)

**File:** `frontend/src/app/manifest.ts`
**Batch:** 2

- `name`: "Prism Pro - AI-Powered LinkedIn Job Automation" → should be "Prism Pro — Recruiter-Grade Resume Prep"
- `description`: "AI-powered LinkedIn job search automation for students and recent graduates" → wrong on both counts.
- `theme_color`: `#2563eb` (bright blue) → must be updated to terracotta `hsl(18 52% 48%)` → `#b85a3a` (approximate hex).
- `background_color`: `#ffffff` → should be sand `#f7f5f2`.

---

## 5. Robots (`src/app/robots.ts`)

**File:** `frontend/src/app/robots.ts`
**Batch:** 2

- `sitemap` URL is `https://jobflowpro.com/sitemap.xml` → **stale domain**, must be `https://prismpro.live/sitemap.xml`.

---

## 6. Sitemap (`src/app/sitemap.ts`)

**File:** `frontend/src/app/sitemap.ts`
**Batch:** 2

- Route `/jobs` → this is not a valid app route; should be `/dashboard/jobs` (or removed; it's a secondary nav item).
- Route `/analytics` → this route does not exist in the current app; remove.
- Route `/email-agent` → deprecated; remove entirely.
- Add new primary routes: `/dashboard/resume`, `/dashboard/resume/tailor`, `/dashboard/credits`.

---

## 7. Dashboard Nav + Page Titles

### `src/components/sophisticated-sidebar.tsx`
**File:** `frontend/src/components/sophisticated-sidebar.tsx`
**Batch:** 3

- Nav label "Job Search" (pointing to `/dashboard/jobs`) should be demoted in hierarchy per spec — in secondary section, not primary. Rename label to "Job Boards" to clarify it's an external-links page, not the product's primary workflow.
- Nav label "Applications" (pointing to `/dashboard/applications`) should similarly be a secondary item (per spec: `/dashboard/jobs` kept but demoted). Consider renaming to "Application Tracker" to be explicit.
- Sidebar footer account copy: "Professional Account" is a placeholder; replace with user's tier badge (Free / Pro) once credit system is live, or at least a neutral label.
- PRISM / *pro* wordmark: italic serif "pro" currently uses `font-serif` which now resolves to Fraunces — visually verify this looks correct and intentional. No code change needed if it renders well.

### `src/app/dashboard/page.tsx` (Dashboard H1 / Overview)
**File:** `frontend/src/app/dashboard/page.tsx`
**Batch:** 3

- Page title and any on-screen H1/intro text should reference the resume-centric product, not job-tracking. Quick-actions panel (in `src/components/dashboard/quick-actions.tsx`) should surface "Polish Resume" and "Tailor to JD" as primary actions.

### `src/components/dashboard/header.tsx`
**File:** `frontend/src/components/dashboard/header.tsx`
**Batch:** 3

- Verify no stale "JobFlow", "LinkedIn automation" or "student" copy in header context text or welcome messages.

### `src/app/dashboard/jobs/page.tsx`
**File:** `frontend/src/app/dashboard/jobs/page.tsx`
**Batch:** 3

- Page title is "Job Search" — update to "Job Boards" to reflect that this is a curated external-links directory (Otta, CareerVault etc.), not a first-class product feature. Add a brief secondary-feature note: "This feature is maintained for convenience; resume tailoring is the primary workflow."

### `src/app/dashboard/applications/page.tsx`
**File:** `frontend/src/app/dashboard/applications/page.tsx`
**Batch:** 3

- Page is the Kanban application tracker. Verify page H1 and any intro text does not say "track applications" in a way that implies this is the primary product value. Light copy update OK ("Track your active applications alongside your resume polish pipeline").

---

## 8. Onboarding (`src/app/onboarding/page.tsx`)

**File:** `frontend/src/app/onboarding/page.tsx`
**Batch:** 3

- Step 1 asks for `company` + `jobTitle` — fine, maps to new profiling.
- Checkbox `acceptGmailAccess` (label not shown in read excerpt) — Gmail integration is a deprecated/demoted feature per spec; this checkbox and the associated consent should be removed or moved to an opt-in advanced settings page.
- Checkbox `acceptJobTracking` — framing needs updating; "job tracking" is demoted to secondary feature.
- Overall: onboarding should orient user toward "polish your first resume" as the opening action. Add a step: "Upload your resume to get started."

---

## 9. Docs Pages (`src/app/docs/page.tsx`)

**File:** `frontend/src/app/docs/page.tsx`
**Batch:** 3

### Stale content

| Section | Current content | Problem |
|---|---|---|
| "Getting Started" step 1 | "Install the Extension: Download our Chrome Extension to enable one-click job saving from LinkedIn." | Extension is deferred per spec. Remove or mark as "coming soon". |
| "Job Tracking" section | "Dashboard View: See all your applications in a Kanban board or List view." + "Smart Extraction: Use the extension on any LinkedIn job post…" | Job-tracker is secondary; LinkedIn extension is deferred. |
| "AI Resume Builder" | Content is accurate but uses generic "compatibility score (0-100%)" framing | Opportunity to use more specific language: "bullet-level severity flags", "ATS simulator", "JD diff view". |
| "Referrals" section (if present — see grep hit in BentoGrid) | Referral feature described as active | Deprecated per spec; remove or replace with "JD Tailoring" doc. |

**Direction:** Replace doc sections: Getting Started → Upload + evaluate resume flow. Remove extension/LinkedIn steps. Add sections: "JD Tailoring", "ATS Simulator", "Export + Templates", "Credits".

---

## 10. Settings + Profile

### `src/app/dashboard/settings/page.tsx`
**File:** `frontend/src/app/dashboard/settings/page.tsx`
**Batch:** 3

- Page description: "Configure your application preferences and privacy settings" — generic, no issue.
- Tabs: `privacy` and `history` — verify history tab doesn't surface stale job-automation history. Minor copy check only.

### `src/app/dashboard/settings/components/privacy-tab.tsx`
**File:** `frontend/src/app/dashboard/settings/components/privacy-tab.tsx`
**Batch:** 3

- Likely references Gmail / email-automation permissions. Audit for any "LinkedIn automation", "email scanning", or "job application tracking via Gmail" consent copy that needs updating or removal (Gmail scope is deprecated in this product iteration per spec).

### `src/app/dashboard/profile/constants.tsx`
**File:** `frontend/src/app/dashboard/profile/constants.tsx`
**Batch:** 3

- Contains user profile field labels/options. Contains reference to "referral" in type definitions (confirmed via grep). Audit for field labels or dropdown options that reference deprecated features.

### `src/app/dashboard/profile/page.tsx`
**File:** `frontend/src/app/dashboard/profile/page.tsx`
**Batch:** 3

- Grep shows "referral" reference. Profile page likely surfaces stale fields or help text. Audit and update any copy that references "LinkedIn automation" or "job tracking" as primary use cases.

---

## 11. Login Page (`src/app/login/page.tsx`)

**File:** `frontend/src/app/login/page.tsx`
**Batch:** 2

- Line 364: "Join thousands of students who've streamlined their job search" → student targeting + job-tracker framing. Replace with: "Join engineers and PMs who prep smarter, not longer."

---

## 12. Privacy Policy (`src/app/privacy-policy/page.tsx`)

**File:** `frontend/src/app/privacy-policy/page.tsx`
**Batch:** 3

- States: "Prism Pro is an AI-powered LinkedIn automation and job search management platform. Students and job seekers use Prism Pro to extract job listings, track applications, and tailor resumes."
  - "LinkedIn automation" and "extract job listings" reference deprecated product features.
  - "Students" is wrong audience.
  - Replace with: "Prism Pro is a recruiter-grade resume tailoring platform. Professionals use Prism Pro to evaluate and tailor their resumes to job descriptions, prepare for ATS systems, and export polished, country-aware PDF resumes."
- Gmail scope section (line ~80) accurately describes existing Gmail integration. Since Gmail is being demoted, add a note: "Gmail integration is an optional feature that can be configured in Settings > Privacy."

---

## 13. Terms of Service (`src/app/terms/page.tsx`)

**File:** `frontend/src/app/terms/page.tsx`
**Batch:** 3

- Line 33: "automated job application management and resume optimization platform. We provide tools to help users organize their job search, evaluate resumes, and track applications."
  - "Automated job application management" and "track applications" are secondary features.
  - Replace platform description with: "AI-powered resume polishing and JD-tailoring platform."

---

## 14. Survivor files to DELETE in Batch 4

The following files are Phase 0 leftovers from the referral/activity features. Before deletion in Batch 4, verify no active import exists. Current import audit is shown.

### Confirmed safe to delete (zero imports from non-deprecated code)

| File | Why | Import status |
|---|---|---|
| `src/lib/referral-api.ts` | Deprecated referral engine API client | Imported only by `referral-request-form.tsx` (also deprecated) |
| `src/lib/referral-templates-api.ts` | Deprecated referral template engine | No active imports found |
| `src/lib/activity-api.ts` | Deprecated activity heatmap API | Imported only by `sophisticated-cards.tsx` which uses `useActivity` — see below |
| `src/components/referral-request-form.tsx` | Deprecated referral request form UI | Zero imports (no page renders it) |

### Dependent chain — must be cleaned up before deletion

These files import the deprecated modules and must be patched (imports removed) before the above files can be deleted:

| File | What to patch |
|---|---|
| `src/contexts/activity-context.tsx` | Entire context is for activity heatmap. Remove `ActivityProvider` from `src/app/dashboard/layout.tsx`. |
| `src/components/sophisticated-cards.tsx` | Imports `useActivity` + `getDailyActivity`. Remove these imports; replace activity heatmap card with a credits-usage or resume-version card. |
| `src/components/job-url-extractor.tsx` | Imports `useActivity` to log URL extraction events. Remove the import and `useActivity` call (activity logging is going away). |
| `src/app/dashboard/layout.tsx` | Wraps children in `<ActivityProvider>`. Remove this wrapper after `activity-context` is cleaned up. |

### Files to archive, NOT delete (keep but move to `_deprecated/`)

| File | Reason to keep temporarily |
|---|---|
| `src/lib/enhanced-api.ts` | Contains `/api/v1/email-agent/*` calls. Keep for one release cycle; remove after backend returns 410. |
| `src/components/gmail-connection.tsx` | Gmail feature demoted, not removed. Keep behind a settings opt-in toggle. |

---

## 15. Email / transactional copy

No transactional email templates were found in the frontend source tree. Email templates likely live in the FastAPI backend (`backend/`). No frontend action needed for Batch 2-4. Flag for backend audit separately.

---

## 16. Hardcoded personal data (fix in Batch 2/3)

| File | Line | Issue |
|---|---|---|
| `src/components/enhanced-resume-analysis.tsx` | ~323 | Hardcoded personal email/phone/LinkedIn: `"Boston, MA \| (857) 799-0214 \| nagarjunmallesh@gmail.com \| linkedin.com/in/nagarjun-mallesh"` — this is example/demo copy in a prompt; replace with a generic placeholder like `"City, State \| (555) 000-0000 \| you@email.com \| linkedin.com/in/your-profile"`. |

---

## 17. Batch 1 visual notes (for Batch 2 follow-up)

After switching to earth-tone tokens, the following contrast / legibility concerns should be checked during Batch 2 visual review:

1. **Terracotta primary on sand background** (`hsl(18 52% 48%)` on `hsl(40 20% 97%)`): contrast ratio ~4.5:1 — passes AA for normal text, borderline for small text. Consider darkening primary slightly to `hsl(18 52% 42%)` for body links if WCAG AA strict compliance needed.
2. **Sage secondary** (`hsl(140 14% 58%)`) used as badge/pill text on `--muted` sand background: low saturation may read as gray; visually verify badges are distinguishable from plain text.
3. **Dark mode terracotta** (`hsl(18 60% 58%)`) on dark charcoal (`hsl(28 12% 10%)`): should have strong enough contrast; verify in browser dark mode toggle.
4. **Landing page hardcoded color references** in `page.tsx` and `BentoGrid.tsx` use inline `isDark ? 'bg-[#0a0a0a]' : 'bg-[#f0eff2]'` — these bypass the CSS var system. Batch 2 should replace these with `bg-background`, `bg-muted`, `border-border` Tailwind tokens.
5. **Sidebar active state** uses `bg-blue-600` in `src/components/sidebar.tsx` (the non-sophisticated sidebar) — update to `bg-primary` in Batch 3.

---

## Quick stale-term grep summary

The following stale terms were found in source files. All have been audited above.

```
JobFlow / jobflowpro      → layout.tsx (lines 76, 83), robots.ts (line 10)
LinkedIn automation       → layout.tsx (line 39, 67, 122), docs/page.tsx, privacy-policy/page.tsx
students / graduates      → layout.tsx (multiple), manifest.ts, login/page.tsx
track applications        → layout.tsx, privacy-policy, terms, gmail-connection
email automation          → sitemap.ts (/email-agent route), enhanced-api.ts, onboarding
referral                  → referral-request-form.tsx, referral-api.ts, referral-templates-api.ts, activity-context.tsx (indirect), profile/constants.tsx
find jobs / job aggregat  → Not found in .tsx/.ts (only in external link titles in jobs/page.tsx — acceptable)
```

---

*Generated: Batch 1, 2026-05-19. Execute changes in order: Batch 2 (landing + SEO), Batch 3 (dashboard + docs + settings), Batch 4 (deletions + final cleanup).*
