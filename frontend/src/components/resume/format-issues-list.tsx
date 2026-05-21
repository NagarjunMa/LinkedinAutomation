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
