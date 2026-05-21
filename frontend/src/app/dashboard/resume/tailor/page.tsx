// frontend/src/app/dashboard/resume/tailor/page.tsx
"use client";
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { JdInputForm } from '@/components/jd/jd-input-form';
import { JdAnalysisPanel } from '@/components/jd/jd-analysis-panel';
import { DiffView } from '@/components/jd/diff-view';
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

      {result && resumeId && (
        <>
          <JdAnalysisPanel
            extraction={result.extracted_requirements}
            plan={result.diff_plan}
          />
          <DiffView
            key={result.jd_evaluation_id}
            resumeId={resumeId}
            plan={result.diff_plan}
            onApplied={(versionId) => {
              // user can navigate to the edit page if they want to see the result.
            }}
          />
        </>
      )}
    </div>
  );
}
