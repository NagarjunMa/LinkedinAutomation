'use client';

import { useEffect, useRef, useState } from 'react';
import { useInfiniteQuery, useQuery, useQueryClient, type InfiniteData } from '@tanstack/react-query';
import { APIError } from '@/app/lib/api/config';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogTitle, AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { careerApi, pageSize, type Decision, type Evidence } from '@/features/career-coach/api';
import { EvidenceEdit, ownershipLabels } from './evidence-edit';
import { checkEvidenceOwner, evidenceStatus, supportLevels, type EvidenceOwner } from './evidence-model';

const cautions = {
  reject: ['Reject evidence', 'Rejected'],
  mark_private: ['Mark private', 'Marked private'],
  mark_unavailable: ['Mark unavailable', 'Marked unavailable'],
  resolve_contradiction: ['Resolve contradiction', 'Contradiction resolved'],
} as const;

type Caution = keyof typeof cautions;

export function EvidenceDetails({ session, id, close, listedRevision, citedRevision, saving, setSaving }: {
  session: EvidenceOwner; id: string; close: () => void; listedRevision?: number; citedRevision?: number; saving: boolean; setSaving: (saving: boolean) => void;
}) {
  const { owner, isCurrentUser } = session;
  const client = useQueryClient();
  const listKey = ['evidence-notebook', owner];
  const detailKey = [...listKey, 'detail', id];
  const historyKey = [...listKey, 'history', id];
  const heading = useRef<HTMLHeadingElement>(null);
  const operation = useRef<AbortController | null>(null);
  const [issue, setIssue] = useState('');
  const [editRevision, setEditRevision] = useState<number>();
  const [showHistory, setShowHistory] = useState(citedRevision !== undefined);
  const [notice, setNotice] = useState('');
  const [highestListedRevision, setHighestListedRevision] = useState(listedRevision ?? 0);
  if (listedRevision !== undefined && listedRevision > highestListedRevision) {
    setHighestListedRevision(listedRevision);
  }
  const detail = useQuery({
    queryKey: detailKey,
    queryFn: async ({ signal }) => {
      const item = await careerApi(owner, signal).evidenceDetail(id);
      checkEvidenceOwner(session, [item], id);
      return item;
    },
    retry: false, gcTime: 0, refetchOnMount: 'always',
    refetchOnWindowFocus: saving ? false : 'always', refetchOnReconnect: saving ? false : 'always',
  });
  const checking = detail.fetchStatus !== 'idle';
  const knownStale = detail.isSuccess && highestListedRevision > detail.data.revision;
  const history = useInfiniteQuery({
    queryKey: historyKey,
    queryFn: async ({ pageParam, signal }) => {
      const page = await careerApi(owner, signal).evidenceHistory(id, pageParam);
      checkEvidenceOwner(session, page.revisions, id);
      if (page.decisions.some(decision => decision.actor_id !== owner || decision.evidence.evidence_id !== id)) {
        throw new Error('History is unavailable');
      }
      return page;
    },
    initialPageParam: 0,
    getNextPageParam: (page, _, offset) => page.revisions.length === pageSize ? offset + pageSize : undefined,
    enabled: showHistory && detail.isSuccess && !issue && !knownStale,
    retry: false, gcTime: 0,
  });

  useEffect(() => {
    heading.current?.focus();
    return () => {
      const pending = operation.current;
      operation.current = null;
      pending?.abort();
    };
  }, []);

  function syncList(item: Evidence) {
    client.setQueryData<InfiniteData<Evidence[]>>(listKey, data => data && ({
      ...data,
      pages: data.pages.map(page => page.map(row => row.evidence_id === id && row.revision <= item.revision ? item : row)),
    }));
  }

  async function save(decision: Decision) {
    if (operation.current || checking || issue || knownStale || !isCurrentUser(owner)) return;
    const controller = new AbortController();
    operation.current = controller;
    setSaving(true);
    setNotice('');
    const canceled = new Promise<never>((_, reject) => {
      controller.signal.addEventListener('abort', () => reject(controller.signal.reason), { once: true });
    });
    const deadline = setTimeout(() => controller.abort(), 30_000);
    try {
      const updated = await Promise.race([careerApi(owner, controller.signal).decide(id, decision), canceled]);
      if (controller.signal.aborted || !isCurrentUser(owner)) return;
      checkEvidenceOwner(session, [updated], id);
      if (updated.revision !== decision.revision + 1) throw new Error('Unexpected evidence revision');
      await client.cancelQueries({ queryKey: listKey, exact: true });
      if (controller.signal.aborted || !isCurrentUser(owner)) return;
      const latest = client.setQueryData<Evidence>(detailKey, cached =>
        cached && cached.revision > updated.revision ? cached : updated,
      );
      if (latest) syncList(latest);
      setEditRevision(undefined);
      setNotice('Decision saved.');
      void client.invalidateQueries({ queryKey: historyKey, exact: true });
      if (document.activeElement === document.body) heading.current?.focus();
    } catch (error) {
      if (operation.current !== controller || !isCurrentUser(owner)) return;
      const conflict = error instanceof APIError && error.status === 409;
      setIssue(conflict ? 'This evidence changed in another tab. Refresh and review the latest revision.' :
        'The decision could not be verified. Refresh the evidence before trying again.');
      void client.invalidateQueries({ queryKey: listKey, exact: true });
    } finally {
      clearTimeout(deadline);
      if (operation.current === controller) {
        operation.current = null;
        if (isCurrentUser(owner)) setSaving(false);
      }
    }
  }

  async function refresh() {
    const result = await detail.refetch();
    if (!result.isSuccess || !isCurrentUser(owner)) return;
    syncList(result.data);
    setIssue('');
    void client.invalidateQueries({ queryKey: historyKey, exact: true });
  }

  const item = detail.isSuccess && !knownStale ? detail.data : undefined;
  const disabled = saving || checking;
  const canConfirm = item?.lifecycle === 'proposed' && !item.is_private;
  const canEdit = item && item.lifecycle !== 'rejected' && item.lifecycle !== 'unavailable';
  const canResolve = item?.lifecycle === 'contradicted' && !item.is_private &&
    item.sources.some(source => source.relationship === 'supports');
  const actions: Caution[] = [];
  if (item && item.lifecycle !== 'rejected') actions.push('reject');
  if (item && !item.is_private) actions.push('mark_private');
  if (item && item.lifecycle !== 'unavailable') actions.push('mark_unavailable');
  if (canResolve) actions.push('resolve_contradiction');
  const historyPages = history.data?.pages ?? [];
  const decisions = new Map(historyPages.flatMap(page => page.decisions).map(decision => [decision.resulting_revision, decision]));
  const revisions = historyPages.flatMap(page => page.revisions);

  return (
    <section aria-labelledby="evidence-details" className="min-w-0 space-y-4 rounded-xl border border-border bg-card p-4 [overflow-wrap:anywhere] sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="evidence-details" ref={heading} tabIndex={-1} className="text-lg font-semibold">Evidence details</h2>
        <div className="flex flex-wrap justify-end gap-1">
          {detail.isSuccess && !issue && !knownStale &&
            <Button variant="ghost" size="sm" disabled={disabled} onClick={() => void refresh()}>Refresh evidence</Button>}
          <Button variant="ghost" size="sm" disabled={saving} onClick={close}>Close details</Button>
        </div>
      </div>
      {detail.isPending && <p role="status" className="text-sm">Loading details…</p>}
      {(detail.isError || issue || knownStale) && <div className="space-y-2">
        <p role="alert" className="text-sm">{issue || (knownStale ? 'A newer revision is available. Refresh to review it.' : 'Evidence details are unavailable.')}</p>
        <Button variant="outline" disabled={checking} onClick={() => void refresh()}>Refresh evidence</Button>
      </div>}
      <p role="status" className="text-sm text-muted-foreground empty:hidden">{saving ? 'Saving decision…' : notice}</p>
      {item && !issue && <>
        <p className="whitespace-pre-wrap text-base font-medium">{item.claim}</p>
        <p className="text-sm text-muted-foreground">{evidenceStatus(item)} · {supportLevels[item.support]} · Revision {item.revision}</p>
        <p className="text-sm font-medium">
          {checking || saving ? 'Checking generation eligibility…' :
            item.lifecycle === 'confirmed' && item.is_private === false ? 'Eligible for generation' : 'Excluded from generation'}
        </p>
        <dl className="space-y-2 text-sm">
          <div><dt className="font-medium">Ownership</dt><dd>{ownershipLabels[item.ownership]}</dd></div>
          {item.scope && <div><dt className="font-medium">Contribution scope</dt><dd>{item.scope}</dd></div>}
          {!!item.qualifiers?.length && <div><dt className="font-medium">Qualifiers</dt><dd>{item.qualifiers.join(', ')}</dd></div>}
          {item.measurement && <div><dt className="font-medium">Measurement</dt>
            <dd>{item.measurement.method}<br />{item.measurement.scope} · {item.measurement.estimated ? 'Estimated' : 'Recorded as exact'}</dd></div>}
          {item.verification_ref && <div><dt className="font-medium">Verification reference</dt><dd>{item.verification_ref}</dd></div>}
        </dl>
        <p className="text-sm text-muted-foreground">Confidential work can still be valid evidence without a public link. Private claims stay out of generated material.</p>
        <h3 className="font-medium">Source lineage</h3>
        {item.lifecycle === 'contradicted' && <p className="text-sm">Sources disagree. Review the supporting and conflicting records before deciding. {canResolve ? 'Resolving returns this claim to review.' : 'A resolution requires a supporting source and non-private evidence.'}</p>}
        <SourceLineage sources={item.sources} />
        {editRevision === item.revision ? <EvidenceEdit key={item.revision} item={item} disabled={disabled}
          save={decision => void save(decision)} cancel={() => { setEditRevision(undefined); heading.current?.focus(); }} /> :
          <div className="flex flex-wrap gap-2">
            {canConfirm && <Button disabled={disabled} onClick={() => void save({ action: 'confirm', revision: item.revision })}>Confirm evidence</Button>}
            {canEdit && <Button variant="outline" disabled={disabled} onClick={() => setEditRevision(item.revision)}>Edit evidence</Button>}
            {actions.map(action => <AlertDialog key={`${action}:${item.revision}`}>
              <AlertDialogTrigger asChild><Button variant="outline" disabled={disabled}>{cautions[action][0]}</Button></AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogTitle>{cautions[action][0]}?</AlertDialogTitle>
                <AlertDialogDescription>
                  {action === 'resolve_contradiction'
                    ? 'This keeps the supporting sources on the current claim and returns it to review. The conflicting sources remain in revision history.'
                    : 'This excludes the claim from generation and can make prior generated material unavailable. The claim stays in your notebook history.'}
                </AlertDialogDescription>
                <AlertDialogFooter className="gap-2">
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction disabled={disabled} onClick={() => void save({ action, revision: item.revision })}>{cautions[action][0]}</AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>)}
          </div>}
        <Button variant="ghost" aria-expanded={showHistory} onClick={() => setShowHistory(!showHistory)}>{showHistory ? 'Hide history' : 'Show history'}</Button>
        {showHistory && <section aria-label="Revision history" className="space-y-2 text-sm">
          {history.isPending && <p role="status">Loading history…</p>}
          {history.isError && <>
            <p role="alert">Revision history is unavailable.</p>
            <Button variant="outline" disabled={history.isFetching} onClick={() => void (history.isFetchNextPageError ? history.fetchNextPage() : history.refetch())}>Retry history</Button>
          </>}
          {citedRevision !== undefined && (
            <p className="font-medium">
              LinkedIn Review cites revision {citedRevision}.
              {history.isSuccess && !revisions.some(revision => revision.revision === citedRevision)
                ? (history.hasNextPage ? ' Load more revisions to find it.' : ' This revision is unavailable.') : ''}
            </p>
          )}
          <ol className="space-y-2">
            {revisions.map(revision => {
              const decision = decisions.get(revision.revision);
              const action = decision?.action;
              const label = action === 'confirm' ? 'Confirmed' : action === 'edit' ? 'Edited' : action ? cautions[action][1] : evidenceStatus(revision);
              return <li key={revision.revision} aria-current={revision.revision === citedRevision ? true : undefined}
                className="rounded-md border border-border p-3 aria-[current=true]:border-primary">
                <p className="font-medium">Revision {revision.revision} · {label}</p>
                <p className="whitespace-pre-wrap">{revision.claim}</p>
                <p className="text-muted-foreground">{evidenceStatus(revision)}</p>
                {decision && <time className="text-muted-foreground" dateTime={decision.decided_at}>{new Date(decision.decided_at).toLocaleString()}</time>}
                {decision?.reason && <p className="whitespace-pre-wrap">{decision.reason}</p>}
                <details className="mt-2 space-y-2">
                  <summary className="cursor-pointer">Sources for revision {revision.revision}</summary>
                  <SourceLineage sources={revision.sources} />
                </details>
              </li>;
            })}
          </ol>
          {history.hasNextPage && !history.isFetchNextPageError && <Button variant="outline" disabled={history.isFetching} onClick={() => void history.fetchNextPage()}>Load more revisions</Button>}
        </section>}
      </>}
    </section>
  );
}

function SourceLineage({ sources }: { sources: Evidence['sources'] }) {
  return (
    <ul className="space-y-2 text-sm">
      {sources.map(source => <li key={`${source.source_id}:${source.source_version}:${source.locator}`} className="rounded-md border border-border p-3">
        <p className="font-medium">{source.relationship === 'supports' ? 'Supports claim' : 'Conflicts with claim'}</p>
        <p className="text-muted-foreground">{source.locator} · Version {source.source_version} · {source.extraction}</p>
        <p className="text-muted-foreground">Source {source.source_id}</p>
        <p className="whitespace-pre-wrap">{source.excerpt ?? 'Excerpt unavailable. This link retains an excerpt fingerprint.'}</p>
      </li>)}
    </ul>
  );
}
