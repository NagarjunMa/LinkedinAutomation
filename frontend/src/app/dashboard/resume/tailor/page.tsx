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
