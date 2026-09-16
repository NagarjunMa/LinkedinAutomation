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
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm">
          These are model-assisted comparisons with the uploaded resume, not verified skills or hiring probability. Review each finding against your experience.
        </p>
        <p className="text-sm">
          Only add a skill or job-description term when your actual experience supports it. A missing term may reflect a communication gap or an experience gap; do not invent a claim to fill it.
        </p>
        <div className="flex gap-3 text-xs">
          <Badge variant="outline">{extraction.primary_role_category}</Badge>
          <Badge variant="outline">{extraction.seniority}</Badge>
          <Badge variant="outline">{extraction.country_hint}</Badge>
        </div>

        <div>
          <p className="text-xs uppercase opacity-70 mb-1">Must-have coverage</p>
          <Progress
            aria-label="Requirements found in the uploaded resume"
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
              Not found in this resume: {plan.must_have_coverage_missing.join(', ')}
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
              Not found in this resume: {plan.good_to_have_coverage_missing.join(', ')}
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
