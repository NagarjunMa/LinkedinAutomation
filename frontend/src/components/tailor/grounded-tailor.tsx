'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { APIError, makeAPIRequest } from '@/app/lib/api/config';
import { Button } from '@/components/ui/button';
import { PreviewPanel } from '@/components/tailor/preview-panel';
import { useAuth } from '@/contexts/auth-context';
import type { components } from '@/generated/api/types';

type Schemas = components['schemas'];
type Context = Omit<Schemas['GroundedTailorPreviewRequest'], 'suggest_wording' | 'evaluation_id'>;
type Selection = Schemas['GroundedTailorApplyRequest']['selections'];

export function GroundedTailorEntry() {
  const params = useSearchParams();
  const { user, isCurrentUser } = useAuth();
  const documentId = params?.get('resumeDocument');
  const targetId = params?.get('careerTarget');
  const versionId = params?.get('resumeVersion');
  const reviewId = params?.get('groundedReview');
  if (!user || !isCurrentUser(user.id) || !documentId || !targetId || !reviewId) return null;
  return <GroundedTailor key={JSON.stringify([user.id, documentId, targetId, versionId, reviewId])}
    owner={user.id} isCurrentUser={isCurrentUser}
    context={{ document_id: documentId, target_id: targetId, resume_version_id: versionId ?? null, review_id: reviewId }} />;
}

function GroundedTailor({ owner, isCurrentUser, context }: {
  owner: string;
  isCurrentUser: (owner: string) => boolean;
  context: Context;
}) {
  const [draft, setDraft] = useState<Schemas['GroundedTailorResponse']>();
  const [selections, setSelections] = useState<Selection>({});
  const [saved, setSaved] = useState<Schemas['ApplyTailorResponse']>();
  const [suggest, setSuggest] = useState(false);
  const [pending, setPending] = useState<'preview' | 'apply'>();
  const [error, setError] = useState('');
  const request = useRef<AbortController | null>(null);
  useEffect(() => () => request.current?.abort(), []);

  async function run(action: 'preview' | 'apply') {
    if (request.current || !isCurrentUser(owner) || (action === 'apply' && !draft)) return;
    const controller = new AbortController();
    request.current = controller;
    setPending(action);
    setError('');
    setSaved(undefined);
    const options = { method: 'POST', cache: 'no-store' as const, signal: controller.signal, expectedUserId: owner };
    const current = () => !controller.signal.aborted && isCurrentUser(owner);
    try {
      if (action === 'preview') {
        setDraft(undefined);
        setSelections({});
        const value = await makeAPIRequest<Schemas['GroundedTailorResponse']>('/api/v1/jd/grounded/preview', {
          ...options, body: JSON.stringify({ ...context, suggest_wording: suggest }),
        });
        if (current() && value.resume_version_id === context.resume_version_id) setDraft(value);
      } else if (draft) {
        const value = await makeAPIRequest<Schemas['ApplyTailorResponse']>('/api/v1/jd/grounded/apply', {
          ...options, body: JSON.stringify({
            ...context, evaluation_id: draft.evaluation_id, selections, wording_receipt: draft.wording?.receipt,
          }),
        });
        if (current()) setSaved(value);
      }
    } catch (problem) {
      if (current()) setError(problem instanceof APIError ? problem.message : 'Tailor could not complete this request.');
    } finally {
      if (request.current === controller) request.current = null;
      if (current()) setPending(undefined);
    }
  }

  return <section aria-label="Tailor from confirmed evidence" className="space-y-4 rounded-lg border p-4">
    <div className="space-y-2">
      <h2 className="font-semibold">Tailor from confirmed evidence</h2>
      <p className="text-sm text-muted-foreground">Use the saved résumé review and job analysis to choose which contributions to add.</p>
      <div className="flex flex-wrap items-center gap-3">
        <Button disabled={!!pending} onClick={() => void run('preview')}>
          {draft ? 'Refresh grounded draft' : 'Build grounded draft'}
        </Button>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={suggest} disabled={!!pending}
            onChange={event => setSuggest(event.target.checked)} />
          Suggest wording when available
        </label>
        {pending && <Button variant="outline" onClick={() => {
          request.current?.abort();
          request.current = null;
          setPending(undefined);
        }}>Cancel</Button>}
      </div>
      {pending && <p role="status">{pending === 'preview' ? 'Checking confirmed evidence…' : 'Saving selected contributions…'}</p>}
      {error && <p role="alert" className="break-words text-sm">{error}</p>}
    </div>
    {draft && draft.choices.length === 0 && <p role="status">No confirmed contribution is ready for this job analysis.</p>}
    {draft?.wording?.validation.used_fallback && <p role="status">Safe wording is ready to use.</p>}
    {draft && draft.choices.length > 0 && <div className="grid items-start gap-5 xl:grid-cols-2">
      <div className="min-w-0 space-y-4">
        <ul className="space-y-3">
          {draft.choices.map(choice => {
            const suggestion = draft.wording?.plan_id === choice.plan_id && draft.wording.validation.accepted
              ? draft.wording.selected_option : undefined;
            return <li key={choice.plan_id} className="space-y-2 rounded-md border p-3 text-sm">
              <p className="break-words">{choice.options.safe}</p>
              <label className="block">
                Choose wording
                <select className="mt-1 block min-h-10 w-full rounded-md border bg-background px-2"
                  value={selections[choice.plan_id] ?? ''} disabled={!!pending}
                  onChange={event => {
                    const value = event.target.value;
                    const next = { ...selections };
                    if (value === 'safe' || value === 'action_first') next[choice.plan_id] = value;
                    else delete next[choice.plan_id];
                    setSelections(next);
                    setSaved(undefined);
                  }}>
                  <option value="">Skip this contribution</option>
                  {Object.entries(choice.options).map(([option, text]) => <option key={option} value={option}>
                    {suggestion === option ? 'Suggested: ' : ''}{text}
                  </option>)}
                </select>
              </label>
              <div className="flex flex-wrap gap-x-3 gap-y-1">
                {choice.requirements.map(ref => <span key={ref.revision}>JD {ref.requirement_id}</span>)}
                {choice.evidence.map(ref => <Link key={ref.evidence_id} className="underline" prefetch={false}
                  href={`/dashboard/evidence?evidence=${encodeURIComponent(ref.evidence_id)}&revision=${ref.revision}`}>
                  Evidence revision {ref.revision}
                </Link>)}
              </div>
            </li>;
          })}
        </ul>
        <Button disabled={!!pending || Object.keys(selections).length === 0} onClick={() => void run('apply')}>
          Apply grounded choices
        </Button>
      </div>
      {saved && <PreviewPanel key={saved.version_id} versionId={saved.version_id} previewHtml={saved.preview_html}
        suggestedTemplate={saved.suggested_template} filenameHint={saved.filename_hint} warning={saved.warning ?? undefined}
        downloadOwner={{ userId: owner, isCurrentUser }} />}
    </div>}
  </section>;
}
