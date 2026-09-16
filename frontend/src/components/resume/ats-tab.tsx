// frontend/src/components/resume/ats-tab.tsx
"use client";
import { Progress } from '@/components/ui/progress';
import { FormatIssuesList } from './format-issues-list';
import type { EvaluationResponse } from '@/app/lib/api';

export function AtsTab({ evaluation }: { evaluation: EvaluationResponse }) {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs uppercase opacity-70 mb-1">Document parseability</p>
        <div className="flex items-center gap-3">
          <Progress aria-label="PrismPro document parseability" value={evaluation.ats_parseability} className="flex-1" />
          <span className="text-sm font-semibold w-10 text-right">
            {evaluation.ats_parseability}
          </span>
        </div>
        <p className="text-sm mt-2">
          PrismPro&apos;s document diagnostic checks text extraction and formatting. It does not measure candidate quality or hiring probability, and cannot predict how another system will read this file.
        </p>
      </div>

      <div>
        <p className="text-xs uppercase opacity-70 mb-2">Format issues</p>
        <FormatIssuesList issues={evaluation.format_issues} />
      </div>

      <div>
        <p className="text-xs uppercase opacity-70 mb-2">Extracted text (PrismPro parser)</p>
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
