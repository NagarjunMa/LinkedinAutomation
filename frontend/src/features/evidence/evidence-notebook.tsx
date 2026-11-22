'use client';

import { useMemo, useRef, useState } from 'react';
import { useInfiniteQuery, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/contexts/auth-context';
import { careerApi, pageSize, type Evidence } from '@/features/career-coach/api';
import { EvidenceDetails } from './evidence-details';
import { checkEvidenceOwner, evidenceStatus, statuses, supportLevels, type EvidenceOwner } from './evidence-model';

type EvidenceCitation = { initialEvidence?: string; citedRevision?: number };

export function EvidenceNotebook({ initialEvidence, citedRevision }: EvidenceCitation) {
  const { user, isCurrentUser } = useAuth();
  return user && isCurrentUser(user.id)
    ? <Notebook key={user.id} owner={user.id} isCurrentUser={isCurrentUser} initialEvidence={initialEvidence} citedRevision={citedRevision} /> : null;
}

function Notebook(session: EvidenceOwner & EvidenceCitation) {
  const { owner } = session;
  const client = useQueryClient();
  const listKey = ['evidence-notebook', owner];
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [support, setSupport] = useState('');
  const [selected, setSelected] = useState(session.initialEvidence);
  const [saving, setSaving] = useState(false);
  const trigger = useRef<HTMLButtonElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);

  const list = useInfiniteQuery({
    queryKey: listKey,
    queryFn: async ({ pageParam, signal }) => {
      const items = await careerApi(owner, signal).evidence(pageParam);
      checkEvidenceOwner(session, items);
      return items;
    },
    initialPageParam: 0,
    getNextPageParam: (items, _, offset) => items.length === pageSize ? offset + pageSize : undefined,
    retry: false, gcTime: 0,
  });
  const items = useMemo(() => {
    const byId = new Map<string, Evidence>();
    for (const page of list.data?.pages ?? []) {
      for (const item of page) {
        const previous = byId.get(item.evidence_id);
        if (!previous || previous.revision < item.revision) byId.set(item.evidence_id, item);
      }
    }
    return [...byId.values()];
  }, [list.data]);
  const term = search.trim().toLowerCase();
  const matches = items.filter(item => (!status || item.lifecycle === status || (status === 'private' && item.is_private)) &&
    (!support || item.support === support) && item.claim.toLowerCase().includes(term));

  return (
    <div className="mx-auto min-w-0 max-w-6xl space-y-6 px-4 py-6 sm:px-6">
      <header className="space-y-2">
        <h1 ref={heading} tabIndex={-1} className="text-2xl font-semibold tracking-tight">Evidence Notebook</h1>
        <p className="text-sm text-muted-foreground">Review claims from your <Link href="/dashboard/career" className="text-foreground underline">Career Coach</Link> sessions and choose what PrismPro can use.</p>
      </header>
      <div className="grid min-w-0 items-start gap-5 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <section aria-label="Evidence list" className="min-w-0 space-y-4">
          <div className="space-y-3">
            <label className="block text-sm font-medium">Search loaded evidence
              <Input className="mt-1" type="search" value={search} onChange={event => setSearch(event.target.value)} />
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="min-w-0 text-sm font-medium">Status
                <select className="mt-1 block h-9 w-full rounded-md border border-input bg-background px-2" value={status} onChange={event => setStatus(event.target.value)}>
                  <option value="">All statuses</option>
                  {Object.entries(statuses).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
                </select>
              </label>
              <label className="min-w-0 text-sm font-medium">Support
                <select className="mt-1 block h-9 w-full rounded-md border border-input bg-background px-2" value={support} onChange={event => setSupport(event.target.value)}>
                  <option value="">All support levels</option>
                  {Object.entries(supportLevels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
                </select>
              </label>
            </div>
          </div>
          {list.isPending && <p role="status" className="text-sm text-muted-foreground">Loading evidence…</p>}
          {list.isError && <div className="space-y-2">
            <p role="alert" className="text-sm">Evidence could not be loaded.</p>
            <Button variant="outline" disabled={list.isFetching} onClick={() => void (list.isFetchNextPageError ? list.fetchNextPage() : list.refetch())}>Retry list</Button>
          </div>}
          {list.isSuccess && <div className="flex flex-wrap items-center justify-between gap-2">
            <p role="status" className="text-sm text-muted-foreground">
              {items.length ? `${matches.length} shown of ${items.length} loaded` : 'Your evidence proposals will appear here.'}
            </p>
            <Button size="sm" variant="ghost" disabled={list.isFetching || saving}
              onClick={() => void client.resetQueries({ queryKey: listKey, exact: true })}>Refresh list</Button>
          </div>}
          <ul className="space-y-2">
            {matches.map(item => (
              <li key={item.evidence_id}>
                <button type="button" disabled={saving} aria-pressed={selected === item.evidence_id}
                  onClick={event => { trigger.current = event.currentTarget; setSelected(item.evidence_id); }}
                  className="block w-full rounded-lg border border-border bg-card p-3 text-left focus-visible:outline-2 focus-visible:outline-ring aria-pressed:border-primary aria-pressed:bg-accent [overflow-wrap:anywhere]">
                  <span className="line-clamp-3 text-sm font-medium">{item.claim}</span>
                  <span className="mt-1 block text-xs text-muted-foreground">{evidenceStatus(item)} · {supportLevels[item.support]}</span>
                </button>
              </li>
            ))}
          </ul>
          {list.hasNextPage && !list.isFetchNextPageError &&
            <Button variant="outline" disabled={list.isFetching} onClick={() => void list.fetchNextPage()}>
              {list.isFetchingNextPage ? 'Loading…' : 'Load more evidence'}
            </Button>}
        </section>
        {selected && <EvidenceDetails key={selected} session={session} id={selected}
          citedRevision={selected === session.initialEvidence ? session.citedRevision : undefined}
          listedRevision={items.find(item => item.evidence_id === selected)?.revision}
          saving={saving} setSaving={setSaving} close={() => {
          setSelected(undefined);
          (trigger.current?.isConnected ? trigger.current : heading.current)?.focus();
        }} />}
      </div>
    </div>
  );
}
