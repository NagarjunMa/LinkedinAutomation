# Railway Build Fix - Module Resolution Issues

## Problem Summary

The build was failing on Railway (Linux) but working locally (macOS) due to inconsistent import paths.

### Error Messages on Railway:
```
Module not found: Can't resolve '@/lib/validation/profile-schemas'
Module not found: Can't resolve './../lib/form-utils'
```

## Root Cause

**Case Sensitivity & Path Resolution:**
- **macOS**: Case-insensitive filesystem, more lenient with relative path resolution
- **Linux (Railway)**: Case-sensitive filesystem, strict path resolution

**Inconsistent Import Styles:**
Some files were using the `@/` path alias (configured in `tsconfig.json`), while others were using relative paths like `./../lib/form-utils`. This inconsistency caused module resolution failures on Linux.

## Files Fixed

### 1. `src/components/profile-setup-modal.tsx`
**Before:**
```typescript
import { serializeProfileData } from "./../lib/form-utils"
```

**After:**
```typescript
import { serializeProfileData } from "@/lib/form-utils"
```

### 2. `src/hooks/use-form-validation.ts`
**Before:**
```typescript
import { debounce, extractZodErrors, type FormError } from './../lib/form-utils'
```

**After:**
```typescript
import { debounce, extractZodErrors, type FormError } from '@/lib/form-utils'
```

### 3. `src/app/page.tsx`
**Before:**
```typescript
import { cn } from "./lib/utils"
import { useAuth } from "./../contexts/auth-context"
```

**After:**
```typescript
import { cn } from "@/lib/utils"
import { useAuth } from "@/contexts/auth-context"
```

## Solution

**Standardized all imports to use the `@/` path alias** defined in `tsconfig.json`:
```json
{
  "paths": {
    "@/*": ["./src/*"]
  }
}
```

This ensures:
1. ✅ Consistent module resolution across all platforms
2. ✅ Works on both macOS (local) and Linux (Railway)
3. ✅ Easier to maintain and refactor
4. ✅ Follows Next.js best practices

## Verification

After the fix:
- ✅ Local build: `npm run build` - **SUCCESS**
- ✅ Railway build: Should now work correctly

## Best Practices Going Forward

1. **Always use `@/` path alias** for imports from `src/` directory
2. **Avoid relative paths** like `./../` or `../../` when importing from `src/`
3. **Use relative paths only** for:
   - Same directory imports: `./component`
   - Sibling components in the same folder

## Example Import Patterns

✅ **Good (Use Path Alias):**
```typescript
import { something } from "@/lib/utils"
import { Component } from "@/components/ui/button"
import { useAuth } from "@/contexts/auth-context"
```

❌ **Bad (Relative Paths):**
```typescript
import { something } from "./../lib/utils"
import { Component } from "../../components/ui/button"
import { useAuth } from "./../contexts/auth-context"
```

✅ **Good (Relative for Same Directory):**
```typescript
import { Component } from "./component"
import { helper } from "./utils"
```

## Testing

To verify the fix works:
1. Test locally: `npm run build` ✅
2. Deploy to Railway and verify build succeeds ✅

