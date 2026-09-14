import { useCallback, useEffect, useRef, useState } from 'react';
import { useJdAnalyze } from './use-jd-analyze';
import { useTailorApply } from './use-tailor-apply';
import { useToast } from '@/components/ui/use-toast';
import type { ApplyTailorResponse, ChangeItem, JDAnalyzeResponse } from '@/app/lib/api';

type Analysis = { generation: number; resumeId: string; result: JDAnalyzeResponse };
type Submission = { resumeDocumentId: string; jdText: string };

// Own the page's result lifecycle, not transport retries or server-side rollback.
export function useTailorWorkflow() {
  const { toast } = useToast();
  const analyze = useJdAnalyze();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [acceptedChanges, setAcceptedChanges] = useState<ChangeItem[]>([]);
  const [applyResult, setApplyResult] = useState<ApplyTailorResponse | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [applying, setApplying] = useState(false);
  const [errorTitle, setErrorTitle] = useState<string | null>(null);
  const apply = useTailorApply(analysis?.result.jd_evaluation_id ?? '');
  const generation = useRef(0);
  // Refs close the duplicate-event window before React commits pending state.
  const analysisInFlight = useRef(false);
  const applyInFlight = useRef(false);

  useEffect(() => () => { generation.current += 1; }, []);

  const submit = async (args: Submission) => {
    if (analysisInFlight.current) return;
    const current = ++generation.current;
    analysisInFlight.current = true;
    applyInFlight.current = false;
    setAnalyzing(true);
    setApplying(false);
    setAnalysis(null);
    setAcceptedChanges([]);
    setApplyResult(null);
    setErrorTitle(null);
    try {
      const result = await analyze.mutateAsync(args);
      if (generation.current !== current) return;
      setAnalysis({ generation: current, resumeId: args.resumeDocumentId, result });
    } catch (error: unknown) {
      if (generation.current !== current) return;
      const err = error as { status?: number; message?: string } | null;
      const failure = err?.status === 402
        ? { title: 'Out of credits', description: 'Tailoring costs 2 credits.' }
        : err?.status === 422
          ? { title: 'Tailor rejected', description: 'AI tried to fabricate a number. Try a different JD.' }
          : { title: 'Analyze failed', description: err?.message };
      setErrorTitle(failure.title);
      toast({ ...failure, variant: 'destructive' });
    } finally {
      if (generation.current === current) {
        analysisInFlight.current = false;
        setAnalyzing(false);
      }
    }
  };

  const selectChanges = useCallback((changes: ChangeItem[]) => {
    if (analysis && analysis.generation === generation.current) setAcceptedChanges(changes);
  }, [analysis]);

  const applyChanges = async () => {
    if (!analysis || analysis.generation !== generation.current || analysisInFlight.current
      || applyInFlight.current || acceptedChanges.length === 0) return;
    const current = analysis.generation;
    applyInFlight.current = true;
    setApplying(true);
    setErrorTitle(null);
    try {
      const result = await apply.mutateAsync({ accepted_changes: acceptedChanges });
      // A new analysis invalidates the preview even if the old Apply succeeds.
      if (generation.current !== current) return;
      setApplyResult(result);
      toast({ title: 'Applied', description: `${acceptedChanges.length} change${acceptedChanges.length !== 1 ? 's' : ''} saved` });
    } catch (error: unknown) {
      if (generation.current !== current) return;
      const err = error as { message?: string } | null;
      setErrorTitle('Apply failed');
      toast({ title: 'Apply failed', description: err?.message, variant: 'destructive' });
    } finally {
      if (generation.current === current) {
        applyInFlight.current = false;
        setApplying(false);
      }
    }
  };

  return { analysis, acceptedChanges, applyResult, analyzing, applying, errorTitle, submit, selectChanges, applyChanges };
}
