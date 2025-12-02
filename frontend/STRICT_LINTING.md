# Strict Linting Reference

The frontend now runs the official Next.js **Strict** preset (core-web-vitals +
TypeScript) for every `npm run lint`/`npm run build`.

## Running the Linter

```bash
cd /Users/nagarjunmallesh/Desktop/projects/linkedin-automation/frontend
npm run lint
```

- The command fails on the first error. Use `NEXT_PRIVATE_SKIP_ESLINT_SETUP=1`
  only when running inside CI environments that re-use cached configs.
- To fix auto-fixable issues quickly, run `npx eslint . --fix` from the same
  directory (optional).

## Active Rule Categories

The strict preset surfaces a predictable set of rule families. Track them while
remediating:

| Category | Description | Status |
| --- | --- | --- |
| Unused code | Imports, variables, helper components defined but not consumed. Remove, wire-up, or export them. | 🔄 In progress |
| `any` usage | Replace with typed DTOs or `unknown`, or add type guards. | 🔄 In progress |
| React hooks deps | Ensure `useEffect`/`useCallback` lists the functions/values they read. Memoize helpers if needed. | 🔄 In progress |
| Text escaping | Replace smart quotes with HTML entities inside JSX literals. | 🔄 In progress |
| Runtime typing | Extend shared interfaces (e.g., `JobStats`, `RecentApplication`) so components read only declared properties. | ✅ Stabilized |

Update this checklist as remediation milestones are completed.

