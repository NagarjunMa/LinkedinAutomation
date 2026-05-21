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
