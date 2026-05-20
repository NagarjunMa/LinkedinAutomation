# Prism Pro Frontend — Phase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Next.js frontend for Prism Pro's resume polish + JD-driven tailoring flows on top of the Phase-1 backend. Ship three new dashboard routes (`/dashboard/resume`, `/dashboard/resume/[id]/edit`, `/dashboard/resume/tailor`) plus a credits balance surface, wired to the existing FastAPI endpoints.

**Architecture:** Extend the existing Next.js 14 App Router monolith at `frontend/`. All new client code uses TanStack Query v5 (already installed) for server state, the existing Supabase-Bearer-JWT auth flow (`getAuthHeaders` in `app/lib/api/config.ts`), shadcn primitives from `components/ui/`, and `react-pdf` only for the source-file preview. The renderer for the structured resume is a custom React tree over `ResumeDocumentJSON` — NOT a PDF viewer — so bullets are first-class DOM nodes that can be highlighted and clicked. Server state and credits balance are query-cached; mutations invalidate the relevant queries on success.

**Tech Stack:** Next.js 14.2 (App Router), React 18, TypeScript, TanStack Query 5, react-hook-form + zod resolvers, shadcn/ui (Radix primitives + Tailwind), framer-motion, lucide-react icons, Playwright for e2e. No new top-level dependencies are required — every library called for is already in `frontend/package.json`.

**Out of scope (separate plans):**
- PDF export rendering and the 6 country/role templates (Phase 2 plan — backend `/api/exports` not yet shipped)
- Stripe credit purchase UI (Phase 4)
- Legacy `/dashboard/applications` and `/dashboard/jobs` redesign — they continue to use the legacy backend `resumes.py` endpoints unchanged
- Backend changes of any kind (Phase 1 already covers the API surface this plan consumes)
- Vitest + React Testing Library component tests (spec §10) — Playwright e2e covers the user-visible flows for MVP; unit-level component tests are a Phase 3.5 follow-up
- axe-core accessibility automation (spec §10) — keep severity-color dots paired with tooltips and `aria-label`s in this phase; full axe pass is Phase 3.5
- Version history list UI — backend does not yet expose `GET /resumes/{id}/versions`; surface this once that endpoint lands

**Spec reference:** `docs/superpowers/specs/2026-05-19-prism-pro-pivot-design.md` (sections 5, 7.9, 8.1, 8.2, 9).

**Backend API surface this plan consumes** (all under `${NEXT_PUBLIC_API_URL}/api/v1`):
- `POST /resumes/upload` — multipart `file`; returns `{resume_document_id, contact, summary, experience, education, skills, projects, certifications, raw_text}`
- `POST /resumes/{id}/evaluate` — body `{target_role}`; debits 1 credit; returns `{evaluation_id, overall_score, bullet_flags[], format_issues[], summary_critique, ats_parseability, ats_raw_text}`
- `POST /resumes/{id}/rewrite/{bullet_id}` — body `{target_role, country, jd_context?}`; 0 credits; returns `RewriteResult {rewritten, placeholders[], applied_changes[]}`; raises 422 on hallucination
- `POST /resumes/{id}/versions` — body `{parent_version_id?, change_set[]}` where each change is `{type: 'bullet_update' | 'skills_reorder' | 'summary_update', bullet_id?, new_text?, new_skills_order?, new_summary?}`; returns `{version_id}`
- `POST /jd/analyze` — body `{resume_document_id, jd_text}` (`jd_text` min length 50); debits 2 credits; returns `{jd_evaluation_id, extracted_requirements: JDExtraction, diff_plan: DiffPlan}`
- `GET /credits/balance` — returns `{balance: number}`

Error codes used in the UI:
- `400` — parse failure or invalid input; **no credit charged**
- `402` — insufficient credits (raised by `credit_transaction`)
- `404` — resume/version not found
- `422` — hallucination guard rejected output

---

## File Structure

**New files:**

```
frontend/src/app/lib/api/
├── types-v2.ts             (TS mirrors of Pydantic schemas)
├── resume-v2.ts            (upload, evaluate, rewrite, createVersion)
├── jd.ts                   (analyze)
└── credits.ts              (getBalance)

frontend/src/hooks/
├── use-resume.ts           (TanStack Query hooks for resume endpoints)
├── use-jd-analyze.ts
└── use-credits.ts

frontend/src/components/resume/
├── resume-upload-dropzone.tsx
├── resume-renderer.tsx     (renders ResumeDocumentJSON to DOM, bullets clickable)
├── bullet-highlight.tsx    (one bullet — severity dot + click handler)
├── rewrite-modal.tsx       (per-bullet rewrite UI with placeholder fill-in)
├── ats-tab.tsx             (parseability score + raw text monospace preview)
├── format-issues-list.tsx
└── version-history-panel.tsx

frontend/src/components/jd/
├── jd-input-form.tsx       (resume picker + JD textarea + submit)
├── jd-analysis-panel.tsx   (must_have/good_to_have + match score gauge)
├── diff-view.tsx           (per-change accept/reject + apply button)
└── change-card.tsx         (one diff row)

frontend/src/components/credits/
└── credits-balance-badge.tsx

frontend/src/app/dashboard/resume/
├── page.tsx                (library + upload)
└── [id]/edit/page.tsx      (edit view orchestrator)

frontend/src/app/dashboard/resume/tailor/
└── page.tsx

frontend/src/app/dashboard/credits/
└── page.tsx

frontend/tests/e2e/
├── resume-polish.spec.ts
└── jd-tailor.spec.ts
```

**Modified files:**

```
frontend/src/components/sophisticated-sidebar.tsx   (add Resume + Tailor + Credits nav items)
frontend/src/app/providers.tsx                       (wrap app in QueryClientProvider — only if not already)
frontend/src/app/lib/api/index.ts                    (re-export new modules)
```

Notes:
- Existing API helpers live under `frontend/src/app/lib/api/` (note the `app/` prefix — this is the legacy location; new modules go in the same dir to stay consistent).
- TanStack Query is already a dependency but the project root may or may not have a `QueryClientProvider` mounted. Task 3 verifies and mounts it if missing.
- We do not introduce a new `frontend/src/lib/api/` path; everything goes under `frontend/src/app/lib/api/`.
- All new components use shadcn primitives (`@/components/ui/...`); no new UI library.

---

## Task 1: TypeScript types mirroring backend schemas

**Files:**
- Create: `frontend/src/app/lib/api/types-v2.ts`

- [ ] **Step 1: Write the types file**

```typescript
// frontend/src/app/lib/api/types-v2.ts
// Mirrors backend/app/schemas/resume.py and backend/app/schemas/jd.py.
// Keep field names in snake_case to match wire format — do not camelCase.

export type Severity = 'critical' | 'warning' | 'info';
export type BulletCategory =
  | 'quantification'
  | 'verb'
  | 'structure'
  | 'clarity'
  | 'redundancy'
  | 'ats';

export interface Contact {
  name: string;
  email: string | null;
  phone: string | null;
  links: string[];
}

export interface Bullet {
  id: string;
  text: string;
  raw_text: string;
}

export interface ExperienceEntry {
  company: string;
  role: string;
  dates: string | null;
  location: string | null;
  bullets: Bullet[];
}

export interface EducationEntry {
  school: string;
  degree: string | null;
  dates: string | null;
  gpa: string | null;
}

export interface Skills {
  hard: string[];
  soft: string[];
}

export interface ProjectEntry {
  name: string;
  bullets: Bullet[];
}

export interface ResumeDocumentJSON {
  contact: Contact;
  summary: string | null;
  experience: ExperienceEntry[];
  education: EducationEntry[];
  skills: Skills;
  projects: ProjectEntry[];
  certifications: string[];
  raw_text: string;
}

export interface UploadResponse extends ResumeDocumentJSON {
  resume_document_id: string;
}

export interface BulletFlag {
  bullet_id: string;
  severity: Severity;
  reason: string;
  category: BulletCategory;
}

export interface FormatIssue {
  type: string;
  location: string;
  fix_hint: string;
}

export interface EvaluationResponse {
  evaluation_id: string;
  overall_score: number;
  bullet_flags: BulletFlag[];
  format_issues: FormatIssue[];
  summary_critique: string | null;
  ats_parseability: number;
  ats_raw_text: string;
}

export interface Placeholder {
  token: string;
  what: string;
}

export interface RewriteResult {
  rewritten: string;
  placeholders: Placeholder[];
  applied_changes: string[];
}

export type ChangeItem =
  | { type: 'bullet_update'; bullet_id: string; new_text: string }
  | { type: 'skills_reorder'; new_skills_order: string[] }
  | { type: 'summary_update'; new_summary: string };

export interface VersionRequest {
  parent_version_id?: string;
  change_set: ChangeItem[];
}

export interface VersionResponse {
  version_id: string;
}

// JD --------------------------------------------------------------------

export type RequirementType = 'technical' | 'experience' | 'credential';
export type Seniority = 'junior' | 'mid' | 'senior' | 'staff';
export type RoleCategory = 'SWE' | 'DS' | 'PM' | 'other';
export type CountryHint = 'US' | 'IN' | 'other';

export interface Requirement {
  skill: string;
  evidence_from_jd: string;
  type: RequirementType;
}

export interface JDExtraction {
  must_have: Requirement[];
  good_to_have: Requirement[];
  soft_skills: string[];
  seniority: Seniority;
  primary_role_category: RoleCategory;
  country_hint: CountryHint;
  red_flags: string[];
}

export interface BulletDiff {
  bullet_id: string;
  old: string;
  new: string;
  reason: string;
  placeholders: Placeholder[];
}

export interface SkillsReorder {
  new_order: string[];
  rationale: string;
}

export interface SummaryRewrite {
  old: string | null;
  new: string;
  reason: string;
}

export interface SuggestedAddition {
  section: string;
  item: string;
  reason: string;
}

export interface DiffPlan {
  match_score: number;
  must_have_coverage_found: string[];
  must_have_coverage_missing: string[];
  good_to_have_coverage_found: string[];
  good_to_have_coverage_missing: string[];
  bullets: BulletDiff[];
  skills_reorder: SkillsReorder | null;
  summary_rewrite: SummaryRewrite | null;
  suggested_additions: SuggestedAddition[];
}

export interface JDAnalyzeResponse {
  jd_evaluation_id: string;
  extracted_requirements: JDExtraction;
  diff_plan: DiffPlan;
}

export interface CreditsBalance {
  balance: number;
}
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit src/app/lib/api/types-v2.ts`
Expected: exits 0 (no errors).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/lib/api/types-v2.ts
git commit -m "feat(frontend): Phase 3 Task 1 — TS types mirroring Phase 1 schemas"
```

---

## Task 2: API client modules

**Files:**
- Create: `frontend/src/app/lib/api/resume-v2.ts`
- Create: `frontend/src/app/lib/api/jd.ts`
- Create: `frontend/src/app/lib/api/credits.ts`
- Modify: `frontend/src/app/lib/api/index.ts`

- [ ] **Step 1: Read the existing API config helper**

Run: `cat frontend/src/app/lib/api/config.ts`
You should see `makeAPIRequest<T>(url, options)`, `getAuthHeaders()`, and `APIError`. Reuse them; do not duplicate.

- [ ] **Step 2: Write `resume-v2.ts`**

```typescript
// frontend/src/app/lib/api/resume-v2.ts
import { makeAPIRequest, getAuthHeaders, APIError } from './config';
import type {
  UploadResponse,
  EvaluationResponse,
  RewriteResult,
  VersionRequest,
  VersionResponse,
} from './types-v2';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const resumeV2Api = {
  upload: async (file: File): Promise<UploadResponse> => {
    const form = new FormData();
    form.append('file', file);
    const headers = await getAuthHeaders();
    delete headers['Content-Type']; // browser sets boundary
    const res = await fetch(`${API_BASE}/api/v1/resumes/upload`, {
      method: 'POST',
      headers,
      body: form,
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new APIError(`Upload failed: ${res.status}`, res.status, res.statusText, detail);
    }
    return res.json();
  },

  evaluate: (resumeId: string, targetRole: string): Promise<EvaluationResponse> =>
    makeAPIRequest(`/api/v1/resumes/${resumeId}/evaluate`, {
      method: 'POST',
      body: JSON.stringify({ target_role: targetRole }),
    }),

  rewriteBullet: (
    resumeId: string,
    bulletId: string,
    body: { target_role: string; country: string; jd_context?: string }
  ): Promise<RewriteResult> =>
    makeAPIRequest(`/api/v1/resumes/${resumeId}/rewrite/${bulletId}`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  createVersion: (resumeId: string, body: VersionRequest): Promise<VersionResponse> =>
    makeAPIRequest(`/api/v1/resumes/${resumeId}/versions`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};
```

- [ ] **Step 3: Write `jd.ts`**

```typescript
// frontend/src/app/lib/api/jd.ts
import { makeAPIRequest } from './config';
import type { JDAnalyzeResponse } from './types-v2';

export const jdApi = {
  analyze: (body: { resume_document_id: string; jd_text: string }): Promise<JDAnalyzeResponse> =>
    makeAPIRequest(`/api/v1/jd/analyze`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};
```

- [ ] **Step 4: Write `credits.ts`**

```typescript
// frontend/src/app/lib/api/credits.ts
import { makeAPIRequest } from './config';
import type { CreditsBalance } from './types-v2';

export const creditsApi = {
  getBalance: (): Promise<CreditsBalance> =>
    makeAPIRequest(`/api/v1/credits/balance`, { method: 'GET' }),
};
```

- [ ] **Step 5: Re-export from `index.ts`**

Open `frontend/src/app/lib/api/index.ts` and append:

```typescript
export * from './types-v2';
export { resumeV2Api } from './resume-v2';
export { jdApi } from './jd';
export { creditsApi } from './credits';
```

- [ ] **Step 6: Verify**

Run: `cd frontend && npx tsc --noEmit`
Expected: exits 0.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/app/lib/api/
git commit -m "feat(frontend): Phase 3 Task 2 — API client for resume-v2, jd, credits"
```

---

## Task 3: TanStack Query provider verification

**Files:**
- Inspect (and possibly modify): `frontend/src/app/providers.tsx` (or whatever wraps the root)

- [ ] **Step 1: Locate the root provider**

Run: `grep -rn "QueryClientProvider\|QueryClient" frontend/src --include="*.tsx" --include="*.ts" | head -20`

Two cases:
- **Case A** — `QueryClientProvider` already mounted somewhere in the tree (likely `app/providers.tsx` or `app/layout.tsx`). Skip to Step 4.
- **Case B** — no `QueryClientProvider` found. Continue to Step 2.

- [ ] **Step 2 (Case B only): Find the existing root providers component**

Run: `find frontend/src -maxdepth 4 -name "providers.tsx" -o -name "provider.tsx" | head -5`
You should find an existing client-side providers file (e.g. `frontend/src/components/providers.tsx`). If multiple, pick the one already imported by `frontend/src/app/layout.tsx`.

- [ ] **Step 3 (Case B only): Add a `QueryClientProvider` wrapper**

Edit the providers file. Add at the top:

```typescript
"use client";
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
```

Inside the component, before the existing tree:

```typescript
const [queryClient] = useState(() => new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
    mutations: { retry: 0 },
  },
}));
```

Wrap the existing children:

```tsx
<QueryClientProvider client={queryClient}>
  {/* existing providers */}
</QueryClientProvider>
```

- [ ] **Step 4: Smoke test the provider**

Run: `cd frontend && npm run dev`
Visit `http://localhost:3000/dashboard` in a browser.
Expected: page loads with no `useQueryClient must be used within a QueryClientProvider` error in the browser console.

Kill the dev server (Ctrl-C).

- [ ] **Step 5: Commit (only if Case B applied)**

```bash
git add frontend/src/components/providers.tsx   # or whichever file was edited
git commit -m "feat(frontend): Phase 3 Task 3 — mount QueryClientProvider"
```

If Case A applied, no commit; record the existing mount location in your scratch notes for the next tasks.

---

## Task 4: TanStack Query hooks for resume + JD + credits

**Files:**
- Create: `frontend/src/hooks/use-resume.ts`
- Create: `frontend/src/hooks/use-jd-analyze.ts`
- Create: `frontend/src/hooks/use-credits.ts`

- [ ] **Step 1: Write `use-resume.ts`**

```typescript
// frontend/src/hooks/use-resume.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { resumeV2Api } from '@/app/lib/api';
import type {
  UploadResponse,
  EvaluationResponse,
  RewriteResult,
  VersionRequest,
  VersionResponse,
} from '@/app/lib/api';

export function useUploadResume() {
  const qc = useQueryClient();
  return useMutation<UploadResponse, Error, File>({
    mutationFn: (file) => resumeV2Api.upload(file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resumes'] }),
  });
}

export function useEvaluateResume() {
  const qc = useQueryClient();
  return useMutation<EvaluationResponse, Error, { resumeId: string; targetRole: string }>({
    mutationFn: ({ resumeId, targetRole }) => resumeV2Api.evaluate(resumeId, targetRole),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ['evaluation', vars.resumeId] });
      qc.invalidateQueries({ queryKey: ['credits-balance'] });
    },
  });
}

export function useRewriteBullet() {
  return useMutation<
    RewriteResult,
    Error,
    { resumeId: string; bulletId: string; targetRole: string; country: string; jdContext?: string }
  >({
    mutationFn: ({ resumeId, bulletId, targetRole, country, jdContext }) =>
      resumeV2Api.rewriteBullet(resumeId, bulletId, {
        target_role: targetRole,
        country,
        jd_context: jdContext,
      }),
  });
}

export function useCreateVersion() {
  const qc = useQueryClient();
  return useMutation<VersionResponse, Error, { resumeId: string; body: VersionRequest }>({
    mutationFn: ({ resumeId, body }) => resumeV2Api.createVersion(resumeId, body),
    onSuccess: (_data, vars) =>
      qc.invalidateQueries({ queryKey: ['resume-versions', vars.resumeId] }),
  });
}
```

- [ ] **Step 2: Write `use-jd-analyze.ts`**

```typescript
// frontend/src/hooks/use-jd-analyze.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { jdApi } from '@/app/lib/api';
import type { JDAnalyzeResponse } from '@/app/lib/api';

export function useJdAnalyze() {
  const qc = useQueryClient();
  return useMutation<
    JDAnalyzeResponse,
    Error,
    { resumeDocumentId: string; jdText: string }
  >({
    mutationFn: ({ resumeDocumentId, jdText }) =>
      jdApi.analyze({ resume_document_id: resumeDocumentId, jd_text: jdText }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['credits-balance'] }),
  });
}
```

- [ ] **Step 3: Write `use-credits.ts`**

```typescript
// frontend/src/hooks/use-credits.ts
import { useQuery } from '@tanstack/react-query';
import { creditsApi } from '@/app/lib/api';

export function useCreditsBalance() {
  return useQuery({
    queryKey: ['credits-balance'],
    queryFn: () => creditsApi.getBalance(),
    staleTime: 10_000,
  });
}
```

- [ ] **Step 4: Verify**

Run: `cd frontend && npx tsc --noEmit`
Expected: exits 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/hooks/
git commit -m "feat(frontend): Phase 3 Task 4 — react-query hooks for resume + jd + credits"
```

---

## Task 5: Resume upload dropzone component

**Files:**
- Create: `frontend/src/components/resume/resume-upload-dropzone.tsx`

- [ ] **Step 1: Write the component**

```tsx
// frontend/src/components/resume/resume-upload-dropzone.tsx
"use client";
import { useCallback, useRef, useState } from 'react';
import { Upload, FileText, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useUploadResume } from '@/hooks/use-resume';
import { useToast } from '@/components/ui/use-toast';

const MAX_BYTES = 10 * 1024 * 1024; // 10 MB
const ALLOWED = ['.pdf', '.docx'];

export interface ResumeUploadDropzoneProps {
  onUploaded: (resumeDocumentId: string) => void;
}

export function ResumeUploadDropzone({ onUploaded }: ResumeUploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const upload = useUploadResume();
  const { toast } = useToast();

  const validate = (f: File): string | null => {
    const ext = '.' + f.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED.includes(ext)) return 'Only PDF and DOCX files are supported';
    if (f.size > MAX_BYTES) return 'File too large (max 10 MB)';
    return null;
  };

  const onPick = useCallback((f: File) => {
    const err = validate(f);
    if (err) {
      toast({ title: 'Invalid file', description: err, variant: 'destructive' });
      return;
    }
    setFile(f);
  }, [toast]);

  const onSubmit = async () => {
    if (!file) return;
    try {
      const res = await upload.mutateAsync(file);
      onUploaded(res.resume_document_id);
    } catch (e: any) {
      toast({
        title: 'Upload failed',
        description: e?.message ?? 'Try again',
        variant: 'destructive',
      });
    }
  };

  return (
    <div
      data-testid="resume-dropzone"
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        const f = e.dataTransfer.files[0];
        if (f) onPick(f);
      }}
      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
        dragging ? 'border-app-accent bg-app-accent/5' : 'border-app-text/20'
      }`}
    >
      {!file ? (
        <>
          <Upload className="mx-auto mb-3 w-8 h-8 opacity-50" />
          <p className="text-sm mb-3">Drag PDF or DOCX here, or</p>
          <Button variant="outline" onClick={() => inputRef.current?.click()}>
            Choose file
          </Button>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && onPick(e.target.files[0])}
          />
        </>
      ) : (
        <div className="flex items-center justify-center gap-3">
          <FileText className="w-5 h-5" />
          <span className="text-sm">{file.name}</span>
          <button onClick={() => setFile(null)} aria-label="Remove file">
            <X className="w-4 h-4 opacity-60" />
          </button>
          <Button onClick={onSubmit} disabled={upload.isPending}>
            {upload.isPending ? 'Uploading…' : 'Upload'}
          </Button>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify**

Run: `cd frontend && npx tsc --noEmit`
Expected: exits 0.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/resume/resume-upload-dropzone.tsx
git commit -m "feat(frontend): Phase 3 Task 5 — resume upload dropzone"
```

---

## Task 6: `/dashboard/resume` library page

**Files:**
- Create: `frontend/src/app/dashboard/resume/page.tsx`

Note: there is no backend endpoint to list resume documents (Phase 1 didn't add one). We rely on the user uploading and being redirected to `/edit`; on this page we only show the dropzone + a short "Recent uploads" stored in `localStorage` keyed by user. If a future Phase 1.5 adds `GET /resumes`, this page can be upgraded to a real list.

- [ ] **Step 1: Write the page**

```tsx
// frontend/src/app/dashboard/resume/page.tsx
"use client";
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ResumeUploadDropzone } from '@/components/resume/resume-upload-dropzone';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface RecentItem {
  id: string;
  name: string;
  uploaded_at: string;
}

const LS_KEY = 'prism.recentResumes';

function loadRecent(): RecentItem[] {
  if (typeof window === 'undefined') return [];
  try {
    return JSON.parse(localStorage.getItem(LS_KEY) || '[]');
  } catch {
    return [];
  }
}

function pushRecent(item: RecentItem) {
  const next = [item, ...loadRecent().filter((r) => r.id !== item.id)].slice(0, 10);
  localStorage.setItem(LS_KEY, JSON.stringify(next));
}

export default function ResumeLibraryPage() {
  const router = useRouter();
  const [recent, setRecent] = useState<RecentItem[]>([]);

  useEffect(() => { setRecent(loadRecent()); }, []);

  const onUploaded = (resumeDocumentId: string) => {
    const item: RecentItem = {
      id: resumeDocumentId,
      name: 'Resume',
      uploaded_at: new Date().toISOString(),
    };
    pushRecent(item);
    router.push(`/dashboard/resume/${resumeDocumentId}/edit`);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <header>
        <h1 className="text-2xl font-bold">Resume</h1>
        <p className="text-sm opacity-70">Upload a PDF or DOCX to get recruiter-grade feedback.</p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Upload</CardTitle>
        </CardHeader>
        <CardContent>
          <ResumeUploadDropzone onUploaded={onUploaded} />
        </CardContent>
      </Card>

      {recent.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {recent.map((r) => (
                <li key={r.id}>
                  <Link
                    href={`/dashboard/resume/${r.id}/edit`}
                    className="text-sm hover:underline"
                  >
                    {r.name} — {new Date(r.uploaded_at).toLocaleString()}
                  </Link>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Smoke test**

Run: `cd frontend && npm run dev`
Visit `http://localhost:3000/dashboard/resume`.
Expected: page renders with dropzone visible. Auth redirect to `/login` is acceptable if not signed in; sign in and re-check.

Kill the dev server.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/dashboard/resume/page.tsx
git commit -m "feat(frontend): Phase 3 Task 6 — /dashboard/resume library + upload"
```

---

## Task 7: Resume renderer (structured DOM, severity-aware)

**Files:**
- Create: `frontend/src/components/resume/bullet-highlight.tsx`
- Create: `frontend/src/components/resume/resume-renderer.tsx`

- [ ] **Step 1: Write `bullet-highlight.tsx`**

```tsx
// frontend/src/components/resume/bullet-highlight.tsx
"use client";
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import type { Bullet, BulletFlag, Severity } from '@/app/lib/api';

const DOT: Record<Severity, string> = {
  critical: 'bg-red-500',
  warning: 'bg-amber-500',
  info: 'bg-blue-500',
};

export interface BulletHighlightProps {
  bullet: Bullet;
  flag?: BulletFlag;
  onClick: (bulletId: string) => void;
}

export function BulletHighlight({ bullet, flag, onClick }: BulletHighlightProps) {
  const dot = flag ? DOT[flag.severity] : 'bg-transparent';
  return (
    <li
      data-testid={`bullet-${bullet.id}`}
      data-severity={flag?.severity ?? 'none'}
      className="flex gap-2 items-start py-1 cursor-pointer hover:bg-app-text/5 rounded px-1"
      onClick={() => onClick(bullet.id)}
    >
      <Tooltip>
        <TooltipTrigger asChild>
          <span className={`mt-2 w-2 h-2 rounded-full shrink-0 ${dot}`} aria-hidden />
        </TooltipTrigger>
        {flag && (
          <TooltipContent>
            <p className="text-xs max-w-xs">
              <strong className="capitalize">{flag.severity}</strong> — {flag.reason}
            </p>
          </TooltipContent>
        )}
      </Tooltip>
      <span className="text-sm">{bullet.text}</span>
    </li>
  );
}
```

- [ ] **Step 2: Write `resume-renderer.tsx`**

```tsx
// frontend/src/components/resume/resume-renderer.tsx
"use client";
import { useMemo } from 'react';
import { BulletHighlight } from './bullet-highlight';
import type { ResumeDocumentJSON, BulletFlag } from '@/app/lib/api';

export interface ResumeRendererProps {
  doc: ResumeDocumentJSON;
  flags?: BulletFlag[];
  onBulletClick: (bulletId: string) => void;
}

export function ResumeRenderer({ doc, flags = [], onBulletClick }: ResumeRendererProps) {
  const flagByBullet = useMemo(() => {
    const m = new Map<string, BulletFlag>();
    for (const f of flags) m.set(f.bullet_id, f);
    return m;
  }, [flags]);

  return (
    <article className="bg-white text-black rounded-lg p-8 shadow-sm font-serif">
      <header className="text-center border-b pb-4 mb-4">
        <h1 className="text-xl font-bold">{doc.contact.name}</h1>
        <p className="text-xs opacity-70">
          {[doc.contact.email, doc.contact.phone, ...doc.contact.links]
            .filter(Boolean)
            .join(' · ')}
        </p>
      </header>

      {doc.summary && (
        <section className="mb-4">
          <h2 className="text-sm font-bold uppercase tracking-wide mb-1">Summary</h2>
          <p className="text-sm">{doc.summary}</p>
        </section>
      )}

      {doc.experience.length > 0 && (
        <section className="mb-4">
          <h2 className="text-sm font-bold uppercase tracking-wide mb-2">Experience</h2>
          {doc.experience.map((exp, i) => (
            <div key={i} className="mb-3">
              <div className="flex justify-between text-sm font-semibold">
                <span>{exp.role} — {exp.company}</span>
                <span className="opacity-70">{exp.dates}</span>
              </div>
              <ul className="ml-4 mt-1">
                {exp.bullets.map((b) => (
                  <BulletHighlight
                    key={b.id}
                    bullet={b}
                    flag={flagByBullet.get(b.id)}
                    onClick={onBulletClick}
                  />
                ))}
              </ul>
            </div>
          ))}
        </section>
      )}

      {doc.projects.length > 0 && (
        <section className="mb-4">
          <h2 className="text-sm font-bold uppercase tracking-wide mb-2">Projects</h2>
          {doc.projects.map((p, i) => (
            <div key={i} className="mb-2">
              <p className="text-sm font-semibold">{p.name}</p>
              <ul className="ml-4">
                {p.bullets.map((b) => (
                  <BulletHighlight
                    key={b.id}
                    bullet={b}
                    flag={flagByBullet.get(b.id)}
                    onClick={onBulletClick}
                  />
                ))}
              </ul>
            </div>
          ))}
        </section>
      )}

      {doc.education.length > 0 && (
        <section className="mb-4">
          <h2 className="text-sm font-bold uppercase tracking-wide mb-2">Education</h2>
          {doc.education.map((e, i) => (
            <div key={i} className="text-sm">
              <span className="font-semibold">{e.school}</span>
              {e.degree && <span> — {e.degree}</span>}
              {e.dates && <span className="opacity-70"> ({e.dates})</span>}
            </div>
          ))}
        </section>
      )}

      {(doc.skills.hard.length > 0 || doc.skills.soft.length > 0) && (
        <section>
          <h2 className="text-sm font-bold uppercase tracking-wide mb-1">Skills</h2>
          <p className="text-sm">{doc.skills.hard.join(' · ')}</p>
          {doc.skills.soft.length > 0 && (
            <p className="text-xs opacity-70 mt-1">{doc.skills.soft.join(' · ')}</p>
          )}
        </section>
      )}
    </article>
  );
}
```

- [ ] **Step 3: Verify**

Run: `cd frontend && npx tsc --noEmit`
Expected: exits 0.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/resume/bullet-highlight.tsx frontend/src/components/resume/resume-renderer.tsx
git commit -m "feat(frontend): Phase 3 Task 7 — resume renderer with severity highlights"
```

---

## Task 8: Rewrite modal (per-bullet)

**Files:**
- Create: `frontend/src/components/resume/rewrite-modal.tsx`

- [ ] **Step 1: Write the modal**

```tsx
// frontend/src/components/resume/rewrite-modal.tsx
"use client";
import { useEffect, useState } from 'react';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { useRewriteBullet } from '@/hooks/use-resume';
import { useToast } from '@/components/ui/use-toast';
import type { Bullet, RewriteResult } from '@/app/lib/api';

export interface RewriteModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resumeId: string;
  bullet: Bullet | null;
  targetRole: string;
  country: string;
  jdContext?: string;
  onAccept: (bulletId: string, newText: string) => void;
}

function fillPlaceholders(template: string, values: Record<string, string>): string {
  let out = template;
  for (const [token, val] of Object.entries(values)) {
    if (val) out = out.split(token).join(val);
  }
  return out;
}

export function RewriteModal(props: RewriteModalProps) {
  const { open, onOpenChange, resumeId, bullet, targetRole, country, jdContext, onAccept } = props;
  const [result, setResult] = useState<RewriteResult | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const rewrite = useRewriteBullet();
  const { toast } = useToast();

  useEffect(() => {
    if (!open || !bullet) { setResult(null); setValues({}); return; }
    rewrite.mutate(
      { resumeId, bulletId: bullet.id, targetRole, country, jdContext },
      {
        onSuccess: (data) => {
          setResult(data);
          setValues(Object.fromEntries(data.placeholders.map((p) => [p.token, ''])));
        },
        onError: (e: any) => {
          if (e?.status === 422) {
            toast({
              title: 'Rewrite rejected',
              description: 'AI tried to invent a number. Please try again.',
              variant: 'destructive',
            });
          } else {
            toast({ title: 'Rewrite failed', description: e?.message, variant: 'destructive' });
          }
          onOpenChange(false);
        },
      },
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, bullet?.id]);

  if (!bullet) return null;
  const filled = result ? fillPlaceholders(result.rewritten, values) : '';

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Rewrite bullet</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <Label className="text-xs uppercase opacity-70">Original</Label>
            <p className="text-sm bg-app-text/5 p-2 rounded">{bullet.text}</p>
          </div>

          {rewrite.isPending && <p className="text-sm opacity-60">Rewriting…</p>}

          {result && (
            <>
              <div>
                <Label className="text-xs uppercase opacity-70">Suggested</Label>
                <p className="text-sm bg-app-accent/10 p-2 rounded">{filled}</p>
              </div>

              {result.placeholders.length > 0 && (
                <div className="space-y-2">
                  <Label className="text-xs uppercase opacity-70">Fill in</Label>
                  {result.placeholders.map((p) => (
                    <div key={p.token} className="flex items-center gap-2">
                      <code className="text-xs bg-app-text/5 px-1 rounded">{p.token}</code>
                      <input
                        data-testid={`placeholder-${p.token}`}
                        className="flex-1 border rounded px-2 py-1 text-sm"
                        placeholder={p.what}
                        value={values[p.token] || ''}
                        onChange={(e) => setValues({ ...values, [p.token]: e.target.value })}
                      />
                    </div>
                  ))}
                </div>
              )}

              {result.applied_changes.length > 0 && (
                <ul className="text-xs opacity-70 list-disc ml-5">
                  {result.applied_changes.map((c, i) => <li key={i}>{c}</li>)}
                </ul>
              )}
            </>
          )}
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            disabled={!result}
            onClick={() => {
              if (!result) return;
              onAccept(bullet.id, filled);
              onOpenChange(false);
            }}
          >
            Accept
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

- [ ] **Step 2: Verify**

Run: `cd frontend && npx tsc --noEmit`
Expected: exits 0.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/resume/rewrite-modal.tsx
git commit -m "feat(frontend): Phase 3 Task 8 — bullet rewrite modal with placeholder fill"
```

---

## Task 9: ATS tab + format issues

**Files:**
- Create: `frontend/src/components/resume/ats-tab.tsx`
- Create: `frontend/src/components/resume/format-issues-list.tsx`

- [ ] **Step 1: Write `format-issues-list.tsx`**

```tsx
// frontend/src/components/resume/format-issues-list.tsx
"use client";
import { AlertTriangle } from 'lucide-react';
import type { FormatIssue } from '@/app/lib/api';

export function FormatIssuesList({ issues }: { issues: FormatIssue[] }) {
  if (issues.length === 0) {
    return <p className="text-sm opacity-60">No format issues detected.</p>;
  }
  return (
    <ul className="space-y-2">
      {issues.map((it, i) => (
        <li key={i} className="flex items-start gap-2 text-sm">
          <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
          <div>
            <p><strong>{it.type}</strong> — {it.location}</p>
            <p className="opacity-70 text-xs">{it.fix_hint}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}
```

- [ ] **Step 2: Write `ats-tab.tsx`**

```tsx
// frontend/src/components/resume/ats-tab.tsx
"use client";
import { Progress } from '@/components/ui/progress';
import { FormatIssuesList } from './format-issues-list';
import type { EvaluationResponse } from '@/app/lib/api';

export function AtsTab({ evaluation }: { evaluation: EvaluationResponse }) {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs uppercase opacity-70 mb-1">Parseability</p>
        <div className="flex items-center gap-3">
          <Progress value={evaluation.ats_parseability} className="flex-1" />
          <span className="text-sm font-semibold w-10 text-right">
            {evaluation.ats_parseability}
          </span>
        </div>
        <p className="text-xs opacity-60 mt-1">
          How cleanly an ATS like Workday or Greenhouse will parse this file.
        </p>
      </div>

      <div>
        <p className="text-xs uppercase opacity-70 mb-2">Format issues</p>
        <FormatIssuesList issues={evaluation.format_issues} />
      </div>

      <div>
        <p className="text-xs uppercase opacity-70 mb-2">Raw text (ATS view)</p>
        <pre
          data-testid="ats-raw-text"
          className="text-xs bg-app-text/5 p-3 rounded max-h-96 overflow-auto whitespace-pre-wrap font-mono"
        >
          {evaluation.ats_raw_text}
        </pre>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verify**

Run: `cd frontend && npx tsc --noEmit`
Expected: exits 0.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/resume/ats-tab.tsx frontend/src/components/resume/format-issues-list.tsx
git commit -m "feat(frontend): Phase 3 Task 9 — ATS parseability tab"
```

---

## Task 10: `/dashboard/resume/[id]/edit` page (orchestrator)

**Files:**
- Create: `frontend/src/app/dashboard/resume/[id]/edit/page.tsx`

This page evaluates the resume on first load, then renders the structured resume with severity highlights, an ATS tab, and on bullet click opens the rewrite modal. Accepted rewrites are queued locally; the user clicks "Save version" to send them all as a single `change_set` to `POST /versions`.

- [ ] **Step 1: Write the page**

```tsx
// frontend/src/app/dashboard/resume/[id]/edit/page.tsx
"use client";
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { ResumeRenderer } from '@/components/resume/resume-renderer';
import { RewriteModal } from '@/components/resume/rewrite-modal';
import { AtsTab } from '@/components/resume/ats-tab';
import { useEvaluateResume, useCreateVersion } from '@/hooks/use-resume';
import { useToast } from '@/components/ui/use-toast';
import type {
  ResumeDocumentJSON, EvaluationResponse, Bullet, ChangeItem,
} from '@/app/lib/api';

export default function ResumeEditPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { toast } = useToast();
  const [doc, setDoc] = useState<ResumeDocumentJSON | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null);
  const [targetRole, setTargetRole] = useState('Software Engineer');
  const [country, setCountry] = useState('US');
  const [activeBullet, setActiveBullet] = useState<Bullet | null>(null);
  const [pendingChanges, setPendingChanges] = useState<ChangeItem[]>([]);

  const evaluate = useEvaluateResume();
  const createVersion = useCreateVersion();

  // On mount, fetch the doc from the upload response cached in sessionStorage,
  // or refuse to render (the user must go through /dashboard/resume to upload).
  useEffect(() => {
    const raw = sessionStorage.getItem(`resumeDoc:${id}`);
    if (raw) setDoc(JSON.parse(raw));
  }, [id]);

  const runEvaluate = async () => {
    if (!targetRole || targetRole.length < 2) {
      toast({ title: 'Set a target role first', variant: 'destructive' });
      return;
    }
    try {
      const res = await evaluate.mutateAsync({ resumeId: id, targetRole });
      setEvaluation(res);
    } catch (e: any) {
      if (e?.status === 402) {
        toast({
          title: 'Out of credits',
          description: 'Top up to continue.',
          variant: 'destructive',
        });
      } else {
        toast({ title: 'Evaluation failed', description: e?.message, variant: 'destructive' });
      }
    }
  };

  const findBullet = (bulletId: string): Bullet | null => {
    if (!doc) return null;
    for (const exp of doc.experience) for (const b of exp.bullets) if (b.id === bulletId) return b;
    for (const p of doc.projects) for (const b of p.bullets) if (b.id === bulletId) return b;
    return null;
  };

  const onBulletClick = (bulletId: string) => {
    const b = findBullet(bulletId);
    if (b) setActiveBullet(b);
  };

  const onAcceptRewrite = (bulletId: string, newText: string) => {
    setPendingChanges((prev) => [
      ...prev.filter((c) => !(c.type === 'bullet_update' && c.bullet_id === bulletId)),
      { type: 'bullet_update', bullet_id: bulletId, new_text: newText },
    ]);
    // Optimistically update the rendered doc.
    setDoc((prev) => {
      if (!prev) return prev;
      const next = structuredClone(prev) as ResumeDocumentJSON;
      for (const exp of next.experience)
        for (const b of exp.bullets) if (b.id === bulletId) b.text = newText;
      for (const p of next.projects)
        for (const b of p.bullets) if (b.id === bulletId) b.text = newText;
      return next;
    });
  };

  const onSaveVersion = async () => {
    if (pendingChanges.length === 0) return;
    try {
      const res = await createVersion.mutateAsync({
        resumeId: id,
        body: { change_set: pendingChanges },
      });
      toast({ title: 'Version saved', description: `Version ${res.version_id.slice(0, 8)}` });
      setPendingChanges([]);
    } catch (e: any) {
      toast({ title: 'Save failed', description: e?.message, variant: 'destructive' });
    }
  };

  if (!doc) {
    return (
      <div className="max-w-3xl mx-auto p-6">
        <p className="text-sm opacity-70 mb-3">No resume loaded.</p>
        <Button onClick={() => router.push('/dashboard/resume')}>Upload one</Button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <Card>
        <CardContent className="pt-6 flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-40">
            <Label htmlFor="role">Target role</Label>
            <Input id="role" value={targetRole} onChange={(e) => setTargetRole(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="country">Country</Label>
            <select
              id="country"
              className="border rounded px-2 py-1 block"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
            >
              <option value="US">US</option>
              <option value="IN">IN</option>
            </select>
          </div>
          <Button onClick={runEvaluate} disabled={evaluate.isPending}>
            {evaluate.isPending ? 'Evaluating…' : evaluation ? 'Re-evaluate' : 'Evaluate (1 credit)'}
          </Button>
          <Button
            variant="outline"
            onClick={onSaveVersion}
            disabled={pendingChanges.length === 0 || createVersion.isPending}
          >
            Save version ({pendingChanges.length})
          </Button>
        </CardContent>
      </Card>

      <Tabs defaultValue="resume">
        <TabsList>
          <TabsTrigger value="resume">Resume</TabsTrigger>
          <TabsTrigger value="ats" disabled={!evaluation}>ATS</TabsTrigger>
        </TabsList>
        <TabsContent value="resume">
          {evaluation && (
            <div className="text-sm mb-3">
              <strong>Overall: {evaluation.overall_score}</strong>
              {evaluation.summary_critique && (
                <p className="opacity-70 mt-1">{evaluation.summary_critique}</p>
              )}
            </div>
          )}
          <ResumeRenderer
            doc={doc}
            flags={evaluation?.bullet_flags ?? []}
            onBulletClick={onBulletClick}
          />
        </TabsContent>
        <TabsContent value="ats">
          {evaluation && <AtsTab evaluation={evaluation} />}
        </TabsContent>
      </Tabs>

      <RewriteModal
        open={!!activeBullet}
        onOpenChange={(o) => { if (!o) setActiveBullet(null); }}
        resumeId={id}
        bullet={activeBullet}
        targetRole={targetRole}
        country={country}
        onAccept={onAcceptRewrite}
      />
    </div>
  );
}
```

- [ ] **Step 2: Persist the upload response in sessionStorage from Task 6**

Open `frontend/src/app/dashboard/resume/page.tsx` and update `onUploaded`:

```tsx
const onUploaded = (resumeDocumentId: string) => {
  // unchanged: pushRecent ...
  // we don't have the doc here; we need to receive it
  router.push(`/dashboard/resume/${resumeDocumentId}/edit`);
};
```

The dropzone's `onUploaded` only passed the id. Modify `ResumeUploadDropzone` to pass the full upload response, and update both sites:

Edit `frontend/src/components/resume/resume-upload-dropzone.tsx`:

```typescript
export interface ResumeUploadDropzoneProps {
  onUploaded: (res: UploadResponse) => void;
}
// ...
import type { UploadResponse } from '@/app/lib/api';
// ...
const res = await upload.mutateAsync(file);
onUploaded(res);
```

Edit `frontend/src/app/dashboard/resume/page.tsx`:

```tsx
import type { UploadResponse } from '@/app/lib/api';
// ...
const onUploaded = (res: UploadResponse) => {
  const item: RecentItem = {
    id: res.resume_document_id,
    name: res.contact.name || 'Resume',
    uploaded_at: new Date().toISOString(),
  };
  pushRecent(item);
  sessionStorage.setItem(`resumeDoc:${res.resume_document_id}`, JSON.stringify(res));
  router.push(`/dashboard/resume/${res.resume_document_id}/edit`);
};
```

- [ ] **Step 3: Verify**

Run: `cd frontend && npx tsc --noEmit`
Expected: exits 0.

- [ ] **Step 4: Smoke test**

Run: `cd frontend && npm run dev` and `cd backend && uvicorn app.main:app --reload` (in two terminals).
With a signed-in test user:
1. Visit `/dashboard/resume`, upload a PDF resume — should redirect to `/dashboard/resume/<id>/edit`.
2. Click "Evaluate (1 credit)" — should show bullet dots and ATS tab.
3. Click a bullet with a colored dot — modal should open and call the rewrite endpoint.
4. Accept a rewrite, click "Save version" — should toast "Version saved".

Kill both servers.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/dashboard/resume/ frontend/src/components/resume/resume-upload-dropzone.tsx
git commit -m "feat(frontend): Phase 3 Task 10 — resume edit page wires evaluate + rewrite + save version"
```

---

## Task 11: JD tailor page — shell, upload, JD textarea

**Files:**
- Create: `frontend/src/components/jd/jd-input-form.tsx`
- Create: `frontend/src/app/dashboard/resume/tailor/page.tsx`

- [ ] **Step 1: Write `jd-input-form.tsx`**

```tsx
// frontend/src/components/jd/jd-input-form.tsx
"use client";
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { ResumeUploadDropzone } from '@/components/resume/resume-upload-dropzone';
import type { UploadResponse } from '@/app/lib/api';

export interface JdInputFormProps {
  onSubmit: (args: { resumeDocumentId: string; jdText: string }) => void;
  pending: boolean;
}

export function JdInputForm({ onSubmit, pending }: JdInputFormProps) {
  const [uploaded, setUploaded] = useState<UploadResponse | null>(null);
  const [jdText, setJdText] = useState('');
  const tooShort = jdText.trim().length < 50;

  return (
    <div className="space-y-4">
      {!uploaded ? (
        <ResumeUploadDropzone onUploaded={setUploaded} />
      ) : (
        <div className="text-sm">
          Using resume for <strong>{uploaded.contact.name || 'uploaded resume'}</strong>{' '}
          <button
            onClick={() => setUploaded(null)}
            className="underline text-xs opacity-70 ml-2"
          >
            change
          </button>
        </div>
      )}

      <div>
        <Label htmlFor="jd">Job description</Label>
        <Textarea
          id="jd"
          rows={10}
          placeholder="Paste the full job description here (min 50 chars)…"
          value={jdText}
          onChange={(e) => setJdText(e.target.value)}
        />
        {tooShort && jdText.length > 0 && (
          <p className="text-xs text-amber-500 mt-1">At least 50 characters required.</p>
        )}
      </div>

      <Button
        disabled={!uploaded || tooShort || pending}
        onClick={() => uploaded && onSubmit({ resumeDocumentId: uploaded.resume_document_id, jdText })}
      >
        {pending ? 'Analyzing…' : 'Analyze (2 credits)'}
      </Button>
    </div>
  );
}
```

- [ ] **Step 2: Write the tailor page (shell only; diff view added in Task 13)**

```tsx
// frontend/src/app/dashboard/resume/tailor/page.tsx
"use client";
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { JdInputForm } from '@/components/jd/jd-input-form';
import { useJdAnalyze } from '@/hooks/use-jd-analyze';
import { useToast } from '@/components/ui/use-toast';
import type { JDAnalyzeResponse } from '@/app/lib/api';

export default function TailorPage() {
  const { toast } = useToast();
  const analyze = useJdAnalyze();
  const [result, setResult] = useState<JDAnalyzeResponse | null>(null);
  const [resumeId, setResumeId] = useState<string | null>(null);

  const onSubmit = async (args: { resumeDocumentId: string; jdText: string }) => {
    setResumeId(args.resumeDocumentId);
    try {
      const r = await analyze.mutateAsync(args);
      setResult(r);
    } catch (e: any) {
      if (e?.status === 402) {
        toast({
          title: 'Out of credits',
          description: 'Tailoring costs 2 credits.',
          variant: 'destructive',
        });
      } else if (e?.status === 422) {
        toast({
          title: 'Tailor rejected',
          description: 'AI tried to fabricate a number. Try a different JD.',
          variant: 'destructive',
        });
      } else {
        toast({ title: 'Analyze failed', description: e?.message, variant: 'destructive' });
      }
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Tailor</h1>
        <p className="text-sm opacity-70">Paste a JD; we'll suggest targeted edits.</p>
      </header>

      <Card>
        <CardHeader><CardTitle>Inputs</CardTitle></CardHeader>
        <CardContent>
          <JdInputForm onSubmit={onSubmit} pending={analyze.isPending} />
        </CardContent>
      </Card>

      {/* JD analysis panel + diff view rendered here in later tasks */}
      {result && resumeId && (
        <pre className="text-xs bg-app-text/5 p-3 rounded">
          {/* placeholder until Tasks 12-13 land */}
          Match score: {result.diff_plan.match_score}
        </pre>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Verify**

Run: `cd frontend && npx tsc --noEmit`
Expected: exits 0.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/dashboard/resume/tailor/ frontend/src/components/jd/jd-input-form.tsx
git commit -m "feat(frontend): Phase 3 Task 11 — JD tailor page shell + input form"
```

---

## Task 12: JD analysis panel (match score + must/good-to-have)

**Files:**
- Create: `frontend/src/components/jd/jd-analysis-panel.tsx`

- [ ] **Step 1: Write the panel**

```tsx
// frontend/src/components/jd/jd-analysis-panel.tsx
"use client";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import type { JDExtraction, DiffPlan } from '@/app/lib/api';

export interface JdAnalysisPanelProps {
  extraction: JDExtraction;
  plan: DiffPlan;
}

export function JdAnalysisPanel({ extraction, plan }: JdAnalysisPanelProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>JD analysis</CardTitle>
        <div className="text-right">
          <p className="text-xs uppercase opacity-70">Match score</p>
          <p
            data-testid="match-score"
            className={`text-2xl font-bold ${
              plan.match_score >= 70 ? 'text-emerald-500' :
              plan.match_score >= 40 ? 'text-amber-500' : 'text-red-500'
            }`}
          >
            {plan.match_score}
          </p>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-3 text-xs">
          <Badge variant="outline">{extraction.primary_role_category}</Badge>
          <Badge variant="outline">{extraction.seniority}</Badge>
          <Badge variant="outline">{extraction.country_hint}</Badge>
        </div>

        <div>
          <p className="text-xs uppercase opacity-70 mb-1">Must-have coverage</p>
          <Progress
            value={
              plan.must_have_coverage_found.length /
              Math.max(1, plan.must_have_coverage_found.length + plan.must_have_coverage_missing.length) * 100
            }
          />
          <p className="text-xs mt-1">
            Found: {plan.must_have_coverage_found.join(', ') || '—'}
          </p>
          {plan.must_have_coverage_missing.length > 0 && (
            <p className="text-xs text-red-500">
              Missing: {plan.must_have_coverage_missing.join(', ')}
            </p>
          )}
        </div>

        <div>
          <p className="text-xs uppercase opacity-70 mb-1">Good-to-have</p>
          <p className="text-xs">
            Found: {plan.good_to_have_coverage_found.join(', ') || '—'}
          </p>
          {plan.good_to_have_coverage_missing.length > 0 && (
            <p className="text-xs opacity-70">
              Missing: {plan.good_to_have_coverage_missing.join(', ')}
            </p>
          )}
        </div>

        {extraction.red_flags.length > 0 && (
          <div className="text-xs">
            <p className="uppercase opacity-70 mb-1">Red flags</p>
            <ul className="list-disc ml-5 text-amber-500">
              {extraction.red_flags.map((f, i) => <li key={i}>{f}</li>)}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: Verify**

Run: `cd frontend && npx tsc --noEmit`
Expected: exits 0.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/jd/jd-analysis-panel.tsx
git commit -m "feat(frontend): Phase 3 Task 12 — JD analysis panel"
```

---

## Task 13: Diff view (per-change accept) + apply to version

**Files:**
- Create: `frontend/src/components/jd/change-card.tsx`
- Create: `frontend/src/components/jd/diff-view.tsx`
- Modify: `frontend/src/app/dashboard/resume/tailor/page.tsx`

The diff view supports three change kinds: `bullet_update` (per-bullet rewrite from `diff_plan.bullets`), `skills_reorder` (from `diff_plan.skills_reorder`), `summary_update` (from `diff_plan.summary_rewrite`). Each is an independently checkable card. On apply, accepted changes are submitted as a `change_set` to `POST /resumes/{id}/versions`.

- [ ] **Step 1: Write `change-card.tsx`**

```tsx
// frontend/src/components/jd/change-card.tsx
"use client";
import { Checkbox } from '@/components/ui/checkbox';

export interface ChangeCardProps {
  title: string;
  reason: string;
  before: string | null;
  after: string;
  accepted: boolean;
  onToggle: (accepted: boolean) => void;
  testId?: string;
}

export function ChangeCard(props: ChangeCardProps) {
  return (
    <div
      data-testid={props.testId}
      className="border rounded p-3 flex gap-3 items-start"
    >
      <Checkbox
        checked={props.accepted}
        onCheckedChange={(v) => props.onToggle(Boolean(v))}
        aria-label="Accept change"
      />
      <div className="flex-1 space-y-1">
        <p className="text-xs uppercase opacity-70">{props.title}</p>
        {props.before && (
          <p className="text-sm bg-red-500/10 p-2 rounded line-through opacity-70">
            {props.before}
          </p>
        )}
        <p className="text-sm bg-emerald-500/10 p-2 rounded">{props.after}</p>
        <p className="text-xs opacity-60">{props.reason}</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Write `diff-view.tsx`**

```tsx
// frontend/src/components/jd/diff-view.tsx
"use client";
import { useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ChangeCard } from './change-card';
import { useCreateVersion } from '@/hooks/use-resume';
import { useToast } from '@/components/ui/use-toast';
import type { DiffPlan, ChangeItem } from '@/app/lib/api';

type Selection = {
  bullets: Record<string, boolean>;
  skillsReorder: boolean;
  summaryRewrite: boolean;
};

export interface DiffViewProps {
  resumeId: string;
  plan: DiffPlan;
  onApplied: (versionId: string) => void;
}

export function DiffView({ resumeId, plan, onApplied }: DiffViewProps) {
  const { toast } = useToast();
  const createVersion = useCreateVersion();
  const initial: Selection = useMemo(() => ({
    bullets: Object.fromEntries(plan.bullets.map((b) => [b.bullet_id, true])),
    skillsReorder: !!plan.skills_reorder,
    summaryRewrite: !!plan.summary_rewrite,
  }), [plan]);
  const [sel, setSel] = useState<Selection>(initial);

  const buildChangeSet = (): ChangeItem[] => {
    const out: ChangeItem[] = [];
    for (const b of plan.bullets) {
      if (sel.bullets[b.bullet_id]) {
        out.push({ type: 'bullet_update', bullet_id: b.bullet_id, new_text: b.new });
      }
    }
    if (sel.skillsReorder && plan.skills_reorder) {
      out.push({ type: 'skills_reorder', new_skills_order: plan.skills_reorder.new_order });
    }
    if (sel.summaryRewrite && plan.summary_rewrite) {
      out.push({ type: 'summary_update', new_summary: plan.summary_rewrite.new });
    }
    return out;
  };

  const acceptedCount =
    Object.values(sel.bullets).filter(Boolean).length +
    (sel.skillsReorder ? 1 : 0) +
    (sel.summaryRewrite ? 1 : 0);

  const onApply = async () => {
    const cs = buildChangeSet();
    if (cs.length === 0) {
      toast({ title: 'Select at least one change', variant: 'destructive' });
      return;
    }
    try {
      const res = await createVersion.mutateAsync({ resumeId, body: { change_set: cs } });
      toast({ title: 'Version saved', description: `Version ${res.version_id.slice(0, 8)}` });
      onApplied(res.version_id);
    } catch (e: any) {
      toast({ title: 'Save failed', description: e?.message, variant: 'destructive' });
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row justify-between items-center">
        <CardTitle>Proposed changes</CardTitle>
        <Button
          onClick={onApply}
          disabled={acceptedCount === 0 || createVersion.isPending}
          data-testid="apply-changes"
        >
          {createVersion.isPending ? 'Saving…' : `Apply ${acceptedCount}`}
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {plan.bullets.map((b) => (
          <ChangeCard
            key={b.bullet_id}
            testId={`change-bullet-${b.bullet_id}`}
            title="Bullet rewrite"
            reason={b.reason}
            before={b.old}
            after={b.new}
            accepted={!!sel.bullets[b.bullet_id]}
            onToggle={(v) =>
              setSel((s) => ({ ...s, bullets: { ...s.bullets, [b.bullet_id]: v } }))
            }
          />
        ))}
        {plan.skills_reorder && (
          <ChangeCard
            testId="change-skills"
            title="Skills reorder"
            reason={plan.skills_reorder.rationale}
            before={null}
            after={plan.skills_reorder.new_order.join(' · ')}
            accepted={sel.skillsReorder}
            onToggle={(v) => setSel((s) => ({ ...s, skillsReorder: v }))}
          />
        )}
        {plan.summary_rewrite && (
          <ChangeCard
            testId="change-summary"
            title="Summary rewrite"
            reason={plan.summary_rewrite.reason}
            before={plan.summary_rewrite.old}
            after={plan.summary_rewrite.new}
            accepted={sel.summaryRewrite}
            onToggle={(v) => setSel((s) => ({ ...s, summaryRewrite: v }))}
          />
        )}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 3: Wire diff view into tailor page**

Replace the placeholder `pre` block in `frontend/src/app/dashboard/resume/tailor/page.tsx` with:

```tsx
{result && resumeId && (
  <>
    <JdAnalysisPanel
      extraction={result.extracted_requirements}
      plan={result.diff_plan}
    />
    <DiffView
      resumeId={resumeId}
      plan={result.diff_plan}
      onApplied={(versionId) => {
        // user can navigate to the edit page if they want to see the result.
      }}
    />
  </>
)}
```

Add imports at the top:

```tsx
import { JdAnalysisPanel } from '@/components/jd/jd-analysis-panel';
import { DiffView } from '@/components/jd/diff-view';
```

- [ ] **Step 4: Verify**

Run: `cd frontend && npx tsc --noEmit`
Expected: exits 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/jd/ frontend/src/app/dashboard/resume/tailor/page.tsx
git commit -m "feat(frontend): Phase 3 Task 13 — JD diff view with per-change accept and apply"
```

---

## Task 14: Credits balance page + header badge

**Files:**
- Create: `frontend/src/components/credits/credits-balance-badge.tsx`
- Create: `frontend/src/app/dashboard/credits/page.tsx`
- Modify: `frontend/src/components/sophisticated-header.tsx` (mount the badge)

- [ ] **Step 1: Write the badge**

```tsx
// frontend/src/components/credits/credits-balance-badge.tsx
"use client";
import Link from 'next/link';
import { Coins } from 'lucide-react';
import { useCreditsBalance } from '@/hooks/use-credits';

export function CreditsBalanceBadge() {
  const { data, isLoading } = useCreditsBalance();
  const balance = data?.balance ?? 0;
  const low = !isLoading && balance < 3;
  return (
    <Link
      href="/dashboard/credits"
      data-testid="credits-badge"
      className={`flex items-center gap-1 text-xs px-2 py-1 rounded border ${
        low ? 'border-amber-500 text-amber-500' : 'border-app-text/20'
      }`}
    >
      <Coins className="w-3 h-3" />
      {isLoading ? '…' : balance}
    </Link>
  );
}
```

- [ ] **Step 2: Write the credits page**

```tsx
// frontend/src/app/dashboard/credits/page.tsx
"use client";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCreditsBalance } from '@/hooks/use-credits';

export default function CreditsPage() {
  const { data, isLoading, error } = useCreditsBalance();

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Credits</h1>
      </header>
      <Card>
        <CardHeader><CardTitle>Balance</CardTitle></CardHeader>
        <CardContent>
          {isLoading && <p className="text-sm opacity-60">Loading…</p>}
          {error && <p className="text-sm text-red-500">{(error as Error).message}</p>}
          {data && (
            <p className="text-4xl font-bold" data-testid="credits-balance">{data.balance}</p>
          )}
          <p className="text-xs opacity-60 mt-2">
            Evaluate: 1 credit · Tailor: 2 credits · Rewrite: 0 credits
          </p>
        </CardContent>
      </Card>
      <p className="text-xs opacity-60">
        Top-up via Stripe is coming in a later release.
      </p>
    </div>
  );
}
```

- [ ] **Step 3: Mount the badge in the header**

Open `frontend/src/components/sophisticated-header.tsx`. Find the right-hand control region (avatar / user menu) and add:

```tsx
import { CreditsBalanceBadge } from '@/components/credits/credits-balance-badge';
// ... in the JSX where the user controls live:
<CreditsBalanceBadge />
```

If the header file does not currently exist or is laid out differently, place the badge inside `frontend/src/components/sophisticated-layout.tsx` in the top-right slot — verify by grepping for the avatar dropdown.

- [ ] **Step 4: Verify**

Run: `cd frontend && npx tsc --noEmit`
Expected: exits 0.

- [ ] **Step 5: Smoke test**

Run dev server, visit `/dashboard/credits` — should show current balance. Header badge should match.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/credits/ frontend/src/app/dashboard/credits/ frontend/src/components/sophisticated-header.tsx
git commit -m "feat(frontend): Phase 3 Task 14 — credits balance page + header badge"
```

---

## Task 15: Sidebar nav update

**Files:**
- Modify: `frontend/src/components/sophisticated-sidebar.tsx`

The current nav has Dashboard / Job Search / Applications / Profile / Sign Out. Add Resume and Tailor as primary entries (above Job Search), and Credits below Profile.

- [ ] **Step 1: Add imports**

Open `frontend/src/components/sophisticated-sidebar.tsx`. In the lucide-react import line, add `FileText, Wand2, Coins`:

```typescript
import {
  Search, Briefcase, PanelLeft, LayoutGrid, Settings, LogOut,
  ChevronDown, FileText, Wand2, Coins,
} from 'lucide-react';
```

- [ ] **Step 2: Insert new NavItem entries**

Find the existing block (around line 125):

```tsx
<NavItem to="/dashboard" label="Dashboard" icon={<LayoutGrid className="w-5 h-5" />} isCollapsed={isCollapsed} />
<NavItem to="/dashboard/jobs" label="Job Search" icon={<Search className="w-5 h-5" />} isCollapsed={isCollapsed} />
<NavItem to="/dashboard/applications" label="Applications" icon={<Briefcase className="w-5 h-5" />} isCollapsed={isCollapsed} />
```

Replace with:

```tsx
<NavItem to="/dashboard" label="Dashboard" icon={<LayoutGrid className="w-5 h-5" />} isCollapsed={isCollapsed} />
<NavItem to="/dashboard/resume" label="Resume" icon={<FileText className="w-5 h-5" />} isCollapsed={isCollapsed} />
<NavItem to="/dashboard/resume/tailor" label="Tailor" icon={<Wand2 className="w-5 h-5" />} isCollapsed={isCollapsed} />
<NavItem to="/dashboard/jobs" label="Job Search" icon={<Search className="w-5 h-5" />} isCollapsed={isCollapsed} />
<NavItem to="/dashboard/applications" label="Applications" icon={<Briefcase className="w-5 h-5" />} isCollapsed={isCollapsed} />
```

Find the Profile entry (around line 136). Insert Credits above it:

```tsx
<NavItem to="/dashboard/credits" label="Credits" icon={<Coins className="w-5 h-5" />} isCollapsed={isCollapsed} />
<NavItem to="/dashboard/profile" label="Profile Settings" icon={<Settings className="w-5 h-5" />} isCollapsed={isCollapsed} />
```

- [ ] **Step 3: Verify**

Run: `cd frontend && npx tsc --noEmit`
Expected: exits 0.

- [ ] **Step 4: Smoke test**

Dev server up. Sidebar should now show: Dashboard, Resume, Tailor, Job Search, Applications, Credits, Profile, Sign Out. Each link should resolve.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/sophisticated-sidebar.tsx
git commit -m "feat(frontend): Phase 3 Task 15 — sidebar nav adds Resume, Tailor, Credits"
```

---

## Task 16: Playwright e2e — resume polish happy path

**Files:**
- Create: `frontend/tests/e2e/resume-polish.spec.ts`
- Create: `frontend/tests/fixtures/sample-resume.pdf` (a 1-page PDF — see note)

The test mocks the backend so it does not require a live FastAPI. We use Playwright's `page.route()` to intercept API calls.

- [ ] **Step 1: Add a tiny fixture PDF**

If you don't already have a 1-page PDF, generate one:

```bash
mkdir -p frontend/tests/fixtures
python3 - <<'PY'
from reportlab.pdfgen import canvas
c = canvas.Canvas("frontend/tests/fixtures/sample-resume.pdf")
c.drawString(72, 720, "Jane Doe")
c.drawString(72, 700, "jane@example.com")
c.drawString(72, 680, "Experience: Software Engineer at Acme")
c.drawString(72, 660, "- Built backend services")
c.save()
PY
```

If `reportlab` is unavailable, drop any small PDF you have at that path. Test does not parse it; the backend is mocked.

- [ ] **Step 2: Write the spec**

```typescript
// frontend/tests/e2e/resume-polish.spec.ts
import { test, expect } from '@playwright/test';
import path from 'path';

const UPLOAD_RESPONSE = {
  resume_document_id: 'doc-1',
  contact: { name: 'Jane Doe', email: 'jane@example.com', phone: null, links: [] },
  summary: 'Engineer.',
  experience: [
    {
      company: 'Acme',
      role: 'SWE',
      dates: '2022—now',
      location: null,
      bullets: [
        { id: 'b1', text: 'Built backend services', raw_text: 'Built backend services' },
      ],
    },
  ],
  education: [],
  skills: { hard: ['Python'], soft: [] },
  projects: [],
  certifications: [],
  raw_text: 'Jane Doe\nAcme — SWE\n- Built backend services',
};

const EVAL_RESPONSE = {
  evaluation_id: 'eval-1',
  overall_score: 62,
  bullet_flags: [
    {
      bullet_id: 'b1',
      severity: 'critical',
      reason: 'No quantification',
      category: 'quantification',
    },
  ],
  format_issues: [],
  summary_critique: 'Weak summary',
  ats_parseability: 88,
  ats_raw_text: 'Jane Doe\nSWE at Acme',
};

const REWRITE_RESPONSE = {
  rewritten: 'Built backend services serving [N users]',
  placeholders: [{ token: '[N users]', what: 'number of users' }],
  applied_changes: ['Added scope placeholder'],
};

const VERSION_RESPONSE = { version_id: 'ver-1' };

test('resume polish happy path', async ({ page }) => {
  await page.route('**/api/v1/resumes/upload', (route) =>
    route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(UPLOAD_RESPONSE) }));
  await page.route('**/api/v1/resumes/doc-1/evaluate', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(EVAL_RESPONSE) }));
  await page.route('**/api/v1/resumes/doc-1/rewrite/b1', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(REWRITE_RESPONSE) }));
  await page.route('**/api/v1/resumes/doc-1/versions', (route) =>
    route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(VERSION_RESPONSE) }));
  await page.route('**/api/v1/credits/balance', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ balance: 10 }) }));

  // The /dashboard layout currently requires auth via Supabase. The test is
  // illustrative; to run, either disable ProtectedRoute in test env or stub
  // the Supabase session. For CI, set NEXT_PUBLIC_TEST_BYPASS_AUTH=1 and have
  // ProtectedRoute read it. See Task 17 prerequisite below.
  await page.goto('/dashboard/resume');

  const file = path.resolve('tests/fixtures/sample-resume.pdf');
  await page.setInputFiles('input[type=file]', file);
  await page.getByRole('button', { name: 'Upload' }).click();

  await expect(page).toHaveURL(/\/dashboard\/resume\/doc-1\/edit$/);

  await page.getByRole('button', { name: /Evaluate \(1 credit\)/ }).click();
  await expect(page.getByTestId('bullet-b1')).toHaveAttribute('data-severity', 'critical');

  await page.getByTestId('bullet-b1').click();
  await expect(page.getByText('Built backend services serving [N users]')).toBeVisible();
  await page.getByTestId('placeholder-[N users]').fill('1000');
  await page.getByRole('button', { name: 'Accept' }).click();

  await page.getByRole('button', { name: /Save version \(1\)/ }).click();
  await expect(page.getByText(/Version ver-1/)).toBeVisible();
});
```

- [ ] **Step 3: Add auth bypass for tests**

The dashboard layout wraps everything in `ProtectedRoute`. For Playwright we need to bypass that. Edit `frontend/src/components/protected-route.tsx` and at the top of the component add:

```typescript
if (process.env.NEXT_PUBLIC_TEST_BYPASS_AUTH === '1') {
  return <>{children}</>;
}
```

Edit `frontend/playwright.config.ts`, update the `webServer` block to pass the env var:

```typescript
webServer: {
  command: 'NEXT_PUBLIC_TEST_BYPASS_AUTH=1 npm run dev',
  url: 'http://localhost:3000',
  reuseExistingServer: !process.env.CI,
},
```

- [ ] **Step 4: Run the test**

Run: `cd frontend && npx playwright test tests/e2e/resume-polish.spec.ts --project=chromium`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/tests/ frontend/src/components/protected-route.tsx frontend/playwright.config.ts
git commit -m "test(frontend): Phase 3 Task 16 — e2e resume polish happy path + auth bypass"
```

---

## Task 17: Playwright e2e — JD tailor flow

**Files:**
- Create: `frontend/tests/e2e/jd-tailor.spec.ts`

- [ ] **Step 1: Write the spec**

```typescript
// frontend/tests/e2e/jd-tailor.spec.ts
import { test, expect } from '@playwright/test';
import path from 'path';

const UPLOAD_RESPONSE = {
  resume_document_id: 'doc-2',
  contact: { name: 'Jane Doe', email: null, phone: null, links: [] },
  summary: null,
  experience: [
    {
      company: 'Acme', role: 'SWE', dates: null, location: null,
      bullets: [{ id: 'b1', text: 'Built services', raw_text: 'Built services' }],
    },
  ],
  education: [],
  skills: { hard: [], soft: [] },
  projects: [],
  certifications: [],
  raw_text: '',
};

const ANALYZE_RESPONSE = {
  jd_evaluation_id: 'jd-1',
  extracted_requirements: {
    must_have: [{ skill: 'Python', evidence_from_jd: 'required', type: 'technical' }],
    good_to_have: [],
    soft_skills: [],
    seniority: 'mid',
    primary_role_category: 'SWE',
    country_hint: 'US',
    red_flags: [],
  },
  diff_plan: {
    match_score: 75,
    must_have_coverage_found: ['Python'],
    must_have_coverage_missing: [],
    good_to_have_coverage_found: [],
    good_to_have_coverage_missing: [],
    bullets: [
      {
        bullet_id: 'b1',
        old: 'Built services',
        new: 'Built Python services serving [N users]',
        reason: 'JD emphasizes scale',
        placeholders: [{ token: '[N users]', what: 'scale' }],
      },
    ],
    skills_reorder: null,
    summary_rewrite: null,
    suggested_additions: [],
  },
};

const VERSION_RESPONSE = { version_id: 'ver-2' };

test('JD tailor flow', async ({ page }) => {
  await page.route('**/api/v1/resumes/upload', (r) =>
    r.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(UPLOAD_RESPONSE) }));
  await page.route('**/api/v1/jd/analyze', (r) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ANALYZE_RESPONSE) }));
  await page.route('**/api/v1/resumes/doc-2/versions', (r) =>
    r.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(VERSION_RESPONSE) }));
  await page.route('**/api/v1/credits/balance', (r) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ balance: 10 }) }));

  await page.goto('/dashboard/resume/tailor');

  const file = path.resolve('tests/fixtures/sample-resume.pdf');
  await page.setInputFiles('input[type=file]', file);
  await page.getByRole('button', { name: 'Upload' }).click();

  const jdText = 'We are hiring a Python engineer. ' + 'Must have Python and REST experience. '.repeat(3);
  await page.locator('#jd').fill(jdText);
  await page.getByRole('button', { name: /Analyze \(2 credits\)/ }).click();

  await expect(page.getByTestId('match-score')).toHaveText('75');
  await expect(page.getByTestId('change-bullet-b1')).toBeVisible();

  await page.getByTestId('apply-changes').click();
  await expect(page.getByText(/Version ver-2/)).toBeVisible();
});
```

- [ ] **Step 2: Run**

Run: `cd frontend && npx playwright test tests/e2e/jd-tailor.spec.ts --project=chromium`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add frontend/tests/e2e/jd-tailor.spec.ts
git commit -m "test(frontend): Phase 3 Task 17 — e2e JD tailor flow"
```

---

## Task 18: Error handling polish + low-credit warning

**Files:**
- Modify: `frontend/src/app/lib/api/config.ts`
- Modify: `frontend/src/app/dashboard/resume/[id]/edit/page.tsx` (already handles 402, verify wording)

`makeAPIRequest` currently returns the response body in `APIError.data` as raw text. Parse the JSON body when possible so toasts can show the FastAPI `detail` field.

- [ ] **Step 1: Update `config.ts`**

Replace the error block in `makeAPIRequest`:

```typescript
if (!response.ok) {
  let detail: any = await response.text();
  try {
    const parsed = JSON.parse(detail);
    detail = parsed.detail ?? parsed;
  } catch { /* not JSON — keep text */ }
  const msg = typeof detail === 'string' ? detail : JSON.stringify(detail);
  throw new APIError(msg, response.status, response.statusText, detail);
}
```

- [ ] **Step 2: Verify existing toasts now show backend detail**

Run dev. Hit `/dashboard/resume`, upload a `.txt` file (should be rejected by backend with "Only PDF and DOCX files are supported"). Toast should show that exact string.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/lib/api/config.ts
git commit -m "fix(frontend): Phase 3 Task 18 — surface FastAPI error detail in toasts"
```

---

## Task 19: README + plan close-out

**Files:**
- Modify: `frontend/README.md` (add Phase 3 section)

- [ ] **Step 1: Append to README**

Add to the end of `frontend/README.md`:

```markdown
## Phase 3 — Resume + JD tailor UI

Routes:
- `/dashboard/resume` — upload + recent uploads.
- `/dashboard/resume/[id]/edit` — evaluate, bullet rewrites, ATS tab, save version.
- `/dashboard/resume/tailor` — paste JD, see analysis + diff plan, apply selected changes.
- `/dashboard/credits` — current credit balance.

Run e2e tests:

```bash
cd frontend
NEXT_PUBLIC_TEST_BYPASS_AUTH=1 npx playwright test
```
```

- [ ] **Step 2: Commit**

```bash
git add frontend/README.md
git commit -m "docs(frontend): Phase 3 — README routes + test instructions"
```

---

## Definition of done

- [ ] All 19 tasks committed, each green on `npx tsc --noEmit`.
- [ ] Both Playwright e2e specs (`resume-polish`, `jd-tailor`) pass against the chromium project locally.
- [ ] Manual smoke against a live backend: upload → evaluate → rewrite one bullet → save version, then a separate tailor run → apply → version saved. Credits badge decrements after evaluate and tailor.
- [ ] Sidebar shows Resume, Tailor, Credits items and they all resolve.
- [ ] No TypeScript errors in the changed files.
- [ ] No regressions on `/dashboard/jobs` and `/dashboard/applications` (manual click-through).
