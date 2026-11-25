'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { APIError, makeAPIRequest } from '@/app/lib/api/config';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/auth-context';
import { supportLevels, type EvidenceOwner } from '@/features/evidence/evidence-model';
import type { components } from '@/generated/api/types';

type Target = components['schemas']['CareerTarget'];
type Report = components['schemas']['TargetDefensibility'];
type Requirement = Report['requirements'][number];

const targetsPath = '/api/v1/career/targets';
const pageSize = 50;
const stateLabels = {
  supported: 'Supported',
  partial: 'Partially supported',
  communication_gap: 'Cited claim did not match a parsed résumé bullet',
  evidence_gap: 'Needs evidence of application',
  experience_gap: 'No eligible evidence of experience',
  knowledge_gap: 'Learning only',
  unresolved: 'Unresolved',
} satisfies Record<Requirement['state'], string>;
const unknownLabels = {
  evidence: 'Eligible evidence unavailable',
  ownership: 'Personal ownership unknown',
  measurement: 'Measurement unknown',
  qualification: 'Additional qualification unverified',
} satisfies Record<Requirement['unknowns'][number], string>;
const ownershipLabels = {
  individual: 'Individual', shared: 'Shared', team: 'Team', unknown: 'Unknown',
} satisfies Record<NonNullable<Requirement['claim']>['ownership'], string>;
const guidance = {
  insufficient_requirements: 'No must-have requirements are available to guide your decision.',
  review_required_gaps: 'Review the open must-have requirements before deciding whether to apply or close this target.',
  prepare_with_evidence: 'Use the available evidence to prepare an application. Review any résumé wording gaps before sending it.',
} satisfies Record<Report['guidance'], string>;

export function ClaimDefensibility({ evaluationId }: { evaluationId: string }) {
  const { user, isCurrentUser } = useAuth();
  const [open, setOpen] = useState(false);

  if (!user || !isCurrentUser(user.id)) return null;
  return (
    <details className="rounded-lg border bg-card p-4"
      onToggle={event => setOpen(event.currentTarget.open)}>
      <summary className="cursor-pointer rounded-sm font-medium focus-visible:outline-2 focus-visible:outline-ring">
        Review claim defensibility
      </summary>
      {open && <TargetReview key={`${user.id}:${evaluationId}`} owner={user.id}
        isCurrentUser={isCurrentUser} evaluationId={evaluationId} />}
    </details>
  );
}

function TargetReview({ owner, isCurrentUser, evaluationId }: EvidenceOwner & { evaluationId: string }) {
  const [targetId, setTargetId] = useState('');
  const [locationUnavailable, setLocationUnavailable] = useState(false);
  const [sourcePreview, setSourcePreview] = useState<{ requirementId: string; revision: string; text: string }>();
  const previewRequest = useRef(0);
  const clearPreview = useCallback(() => {
    previewRequest.current += 1;
    setSourcePreview(undefined);
    setLocationUnavailable(false);
  }, []);
  useEffect(() => {
    const input = document.getElementById('jd');
    input?.addEventListener('input', clearPreview);
    return () => {
      previewRequest.current += 1;
      input?.removeEventListener('input', clearPreview);
    };
  }, [clearPreview]);
  const targets = useInfiniteQuery({
    queryKey: ['defensibility-targets', owner, evaluationId],
    queryFn: async ({ pageParam, signal }) => {
      const results = await makeAPIRequest<Target[]>(`${targetsPath}?limit=${pageSize}&offset=${pageParam}`,
        { expectedUserId: owner, signal, cache: 'no-store' });
      if (!isCurrentUser(owner) || results.some(row => row.owner_id !== owner || row.status !== 'active')) {
        throw new Error('Active targets are unavailable');
      }
      return results;
    },
    initialPageParam: 0,
    getNextPageParam: (page, _, offset) => page.length === pageSize && offset < 1_000_000 ? offset + pageSize : undefined,
    retry: false,
    gcTime: 0,
  });
  const available = [...new Map(targets.data?.pages.flat().map(item => [item.target_id, item])).values()];
  const selected = available.some(target => target.target_id === targetId);
  const report = useQuery({
    queryKey: ['target-defensibility', owner, evaluationId, targetId],
    enabled: selected,
    queryFn: async ({ signal }) => {
      const path = `${targetsPath}/${encodeURIComponent(targetId)}/defensibility/${encodeURIComponent(evaluationId)}`;
      const value = await makeAPIRequest<Report>(path, { expectedUserId: owner, signal, cache: 'no-store' });
      if (!isCurrentUser(owner) || value.owner_id !== owner || value.target_id !== targetId
        || value.jd_evaluation_id !== evaluationId) throw new Error('Review is unavailable');
      return value;
    },
    retry: false,
    staleTime: 0,
    gcTime: 0,
    refetchOnMount: 'always',
    refetchOnWindowFocus: 'always',
    networkMode: 'always',
  });

  async function previewRequirement(reference: Requirement['requirement']) {
    const { source_start: start, source_end: end, requirement_id: requirementId, revision } = reference;
    clearPreview();
    const request = previewRequest.current;
    const isCurrent = () => request === previewRequest.current && isCurrentUser(owner);
    const input = document.getElementById('jd');
    const expectedHash = report.data?.jd_text_sha256;
    if (!(input instanceof HTMLTextAreaElement) || !expectedHash || start === null || end === null || end <= start) {
      setLocationUnavailable(true);
      return;
    }

    const text = input.value;
    try {
      const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
      if (!isCurrent() || !input.isConnected) return;
      const hash = Array.from(new Uint8Array(bytes), byte => byte.toString(16).padStart(2, '0')).join('');
      if (hash === expectedHash && input.value === text) {
        // Match the API's Unicode code-point offsets, including surrogate pairs.
        const points = Array.from(text);
        if (end <= points.length) {
          const limit = Math.min(end, start + 240);
          setSourcePreview({ requirementId, revision, text: points.slice(start, limit).join('') + (limit < end ? '…' : '') });
          return;
        }
      }
    } catch {
      // A browser without Web Crypto can still show the rest of the claim review.
    }
    if (isCurrent()) setLocationUnavailable(true);
  }

  return (
    <div className="mt-4 min-w-0 space-y-4">
      {targets.isPending && <p role="status">Loading active targets…</p>}
      {targets.isError && <div className="space-y-2">
        <p role="alert">Active targets could not be loaded.</p>
        <Button variant="outline" disabled={targets.isFetching}
          onClick={() => void (targets.isFetchNextPageError ? targets.fetchNextPage() : targets.refetch())}>Retry targets</Button>
      </div>}
      {targets.isSuccess && available.length === 0 && <p>
        Add a career target in <Link href="/dashboard/linkedin-review" className="underline" prefetch={false}
          target="_blank" rel="noopener noreferrer">LinkedIn Review<span className="sr-only"> (opens in a new tab)</span></Link> to compare it here.
      </p>}
      {available.length > 0 && <label className="block text-sm font-medium">
        Career target
        <select className="mt-1 block min-h-10 w-full max-w-md rounded-md border border-input bg-background px-2"
          value={selected ? targetId : ''} onChange={event => {
            clearPreview();
            setTargetId(event.target.value);
          }}>
          <option value="">Choose a target</option>
          {available.map(target => <option key={target.target_id} value={target.target_id}>
            {target.role_family} · {target.seniority}
          </option>)}
        </select>
      </label>}
      {targets.hasNextPage && <Button variant="outline" disabled={targets.isFetching}
        onClick={() => void targets.fetchNextPage()}>Load more targets</Button>}
      {selected && report.isFetching && <p role="status">Checking current evidence…</p>}
      {selected && report.isError && !report.isFetching && <p role="alert">
        {report.error instanceof APIError && report.error.status === 409
          ? 'This target is linked to a different job description. Select a matching target.'
          : 'The claim review could not be loaded.'}
      </p>}
      {selected && <Button size="sm" variant="outline" aria-disabled={report.isFetching} onClick={() => {
        if (report.isFetching) return;
        clearPreview();
        void report.refetch();
      }}>{report.isError ? 'Retry evidence review' : 'Refresh evidence'}</Button>}
      {selected && report.isSuccess && !report.isFetching && <>
        <div className="space-y-1">
          <h2 className="text-lg font-semibold">Evidence for this target</h2>
          <p className="text-sm">{guidance[report.data.guidance]}</p>
          {!report.data.resume_comparable && <p className="text-sm">Résumé comparison unavailable for this analysis.</p>}
        </div>
        {report.data.requirements.length === 0 && <p>No requirements were extracted for this analysis.</p>}
        {locationUnavailable && <p role="status">Use the original analyzed job description to preview this requirement.</p>}
        <ul className="grid min-w-0 gap-3 xl:grid-cols-2">
          {report.data.requirements.map(item => <RequirementCard key={item.requirement.requirement_id}
            item={item} preview={sourcePreview?.requirementId === item.requirement.requirement_id
              && sourcePreview.revision === item.requirement.revision ? sourcePreview.text : undefined}
            showSource={() => void previewRequirement(item.requirement)} />)}
        </ul>
      </>}
    </div>
  );
}

function RequirementCard({ item, preview, showSource }: { item: Requirement; preview?: string; showSource: () => void }) {
  const claim = item.claim;
  const metric = claim?.measurement;
  const { requirement_id, source_start, source_end } = item.requirement;
  const ordinal = requirement_id.split('-').at(-1);
  return (
    <li className="min-w-0 space-y-2 rounded-md border p-3 text-sm [overflow-wrap:anywhere]">
      <h3 className="font-medium">{item.priority === 'must_have' ? 'Must-have' : 'Preferred'} {item.kind} requirement {ordinal}</h3>
      {source_start !== null && source_end !== null
        ? <Button size="sm" variant="outline" onClick={showSource}>Show requirement text</Button>
        : <p className="text-muted-foreground">The requirement text could not be verified.</p>}
      <div aria-live="polite">
        {preview !== undefined && <blockquote aria-label="Analyzed requirement"
          className="whitespace-pre-wrap border-s-2 ps-3">{preview}</blockquote>}
      </div>
      <p className="font-medium">{stateLabels[item.state]}</p>
      {claim && <>
        <p className="whitespace-pre-wrap">{claim.text}</p>
        <dl className="space-y-1 text-muted-foreground">
          <div><dt className="inline font-medium">Support </dt><dd className="inline">{supportLevels[claim.support]}</dd></div>
          <div><dt className="inline font-medium">Ownership </dt><dd className="inline">{ownershipLabels[claim.ownership]}</dd></div>
          {claim.scope && <div><dt className="inline font-medium">Scope </dt><dd className="inline">{claim.scope}</dd></div>}
          {metric && <div><dt className="inline font-medium">Measurement </dt>
            <dd className="inline">{metric.estimated ? 'Estimated' : 'Recorded as exact'} · {metric.method} · {metric.scope}</dd></div>}
          {claim.qualifiers.length > 0 && <div><dt className="inline font-medium">Conditions </dt>
            <dd className="inline">{claim.qualifiers.join(' · ')}</dd></div>}
        </dl>
        <Link className="underline underline-offset-2" prefetch={false} target="_blank" rel="noopener noreferrer"
          href={`/dashboard/evidence?evidence=${encodeURIComponent(claim.evidence.evidence_id)}&revision=${claim.evidence.revision}`}>
          Evidence revision {claim.evidence.revision}<span className="sr-only"> (opens in a new tab)</span>
        </Link>
      </>}
      {item.unknowns.length > 0 && <ul className="space-y-1 text-muted-foreground">
        {item.unknowns.map(value => <li key={value}>{unknownLabels[value]}</li>)}
      </ul>}
      <details>
        <summary className="cursor-pointer font-medium">Questions to prepare for</summary>
        <ol className="list-decimal space-y-1 ps-5">
          {item.questions.map(question => <li key={question}>{question}</li>)}
        </ol>
      </details>
    </li>
  );
}
