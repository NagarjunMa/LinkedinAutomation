# Strict Lint Remediation Tracker

This checklist groups the current `npm run lint` failures so we can fix them in sensible batches without missing any rule category. Update the table as issues are resolved.

| Category | Symptoms | Affected Areas (sample) | Notes / Fix Strategy |
| --- | --- | --- | --- |
| Unused imports, symbols, and state | `@typescript-eslint/no-unused-vars` (Strict preset) | `src/app/dashboard/page.tsx`, `src/components/sophisticated-cards.tsx`, `src/components/*.tsx` | Remove dead code or prefix intentionally unused variables with `_`. Many UI files import full icon sets that are never rendered. |
| Unsafely typed data | `@typescript-eslint/no-explicit-any` across API layers and hooks | `src/lib/api.ts`, `src/lib/enhanced-api.ts`, `src/lib/form-utils.ts`, `src/hooks/use-form-validation.ts`, `src/contexts/activity-context.tsx` | Define domain interfaces for API responses (Jobs, Referrals, Resume, Analytics) and update helper functions to use them. Favor `unknown` + type guards where shape is dynamic. |
| React hook dependency issues | `react-hooks/exhaustive-deps`, `react-hooks/rules-of-hooks` | `src/components/profile-completion-banner.tsx`, `src/components/applied-jobs-list.tsx`, `src/components/job-extraction-calendar.tsx` | Wrap async helpers in `useCallback`, list dependencies, and ensure hooks are called only inside components/custom hooks. |
| Unescaped apostrophes/quotes in JSX | `react/no-unescaped-entities` | `src/app/dashboard/page.tsx`, `src/app/onboarding/page.tsx`, `src/components/enhanced-resume-analysis.tsx`, `src/components/resume-improvement-modal.tsx` | Replace `'` with `&rsquo;` or escape via `{"'"}`. For large narrative text consider moving content into `t()` strings. |
| Prefer-const / interface hygiene | `prefer-const`, `@typescript-eslint/no-empty-object-type` | `src/components/real-time-resume-loader.tsx`, `src/components/team-switcher.tsx`, `src/components/ui/color-mode.tsx` | Use `const` when reassignments never happen and collapse empty interfaces into their parents. |
| Runtime/platform constraints | Need `export const runtime = 'nodejs'` and server-only logic in Edge-safe files | `src/app/api/auth/callback/route.ts`, `src/middleware.ts` | Ensure all server APIs that rely on Node-only clients declare the runtime or move logic into Node helpers. Already adjusted middleware to cookie-based gating; review remaining API routes after types tighten. |

## Open Tasks

- [ ] Update shared API/lib types first (`src/lib/**`, contexts, hooks) so downstream components inherit strict typing.
- [ ] Remove unused lucide icons/components where no UI references exist.
- [ ] Fix hook dependency warnings page-by-page after type cleanup.
- [ ] Escape literal quotes/apostrophes in marketing copy components.
- [ ] Re-run `npm run lint` after each batch and update this tracker.

