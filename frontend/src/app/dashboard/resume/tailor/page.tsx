// frontend/src/app/dashboard/resume/tailor/page.tsx
"use client";
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { JdInputForm } from '@/components/jd/jd-input-form';
import { JdAnalysisPanel } from '@/components/jd/jd-analysis-panel';
import { DiffView } from '@/components/jd/diff-view';
import { PreviewPanel } from '@/components/tailor/preview-panel';
import { useTailorWorkflow } from '@/hooks/use-tailor-workflow';

export default function TailorPage() {
  const { analysis, acceptedChanges, applyResult, analyzing, applying, errorTitle, submit, selectChanges, applyChanges } = useTailorWorkflow();

  return (
    <div className="max-w-[1400px] mx-auto p-6 space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Tailor</h1>
        <p className="text-sm opacity-70">Paste a JD; we&apos;ll suggest targeted edits.</p>
      </header>

      <Card>
        <CardHeader><CardTitle>Inputs</CardTitle></CardHeader>
        <CardContent>
          <JdInputForm onSubmit={submit} pending={analyzing} />
        </CardContent>
      </Card>

      {analyzing && <p role="status">Analyzing the current submission…</p>}
      {errorTitle && (
        <div role="alert" className="text-sm text-foreground">
          <strong>{errorTitle}</strong>
          <p>Your inputs are preserved. Review them and retry when ready.</p>
        </div>
      )}

      {analysis && (
        <>
          <JdAnalysisPanel
            extraction={analysis.result.extracted_requirements}
            plan={analysis.result.diff_plan}
          />

          <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_minmax(520px,640px)] gap-8 items-start">
            {/* Left column: diff view + Apply button */}
            <div className="space-y-4">
              <DiffView
                key={analysis.generation}
                resumeId={analysis.resumeId}
                jdEvaluationId={analysis.result.jd_evaluation_id}
                plan={analysis.result.diff_plan}
                onApplied={() => {
                  // legacy path — not used when onAcceptedChangesChange is set
                }}
                onAcceptedChangesChange={selectChanges}
              />

              <Button
                onClick={applyChanges}
                disabled={analyzing || applying || acceptedChanges.length === 0}
                className="w-full sm:w-auto"
                data-testid="tailor-apply"
              >
                {applying
                  ? 'Applying…'
                  : `Apply ${acceptedChanges.length} change${acceptedChanges.length !== 1 ? 's' : ''}`}
              </Button>
            </div>

            {/* Right column: preview panel */}
            {applyResult ? (
              <PreviewPanel
                versionId={applyResult.version_id}
                previewHtml={applyResult.preview_html}
                suggestedTemplate={applyResult.suggested_template}
                filenameHint={applyResult.filename_hint}
                warning={applyResult.warning}
              />
            ) : (
              <aside className="sticky top-24 h-[calc(100vh-8rem)] border border-border rounded-md bg-card flex items-center justify-center text-sm text-muted-foreground p-6 text-center">
                Apply changes to see a live preview and download PDF
              </aside>
            )}
          </div>
        </>
      )}
    </div>
  );
}
