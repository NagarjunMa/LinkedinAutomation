'use client';

import { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import type { Decision, Evidence } from './api';

export function EvidenceReview({ items, busy, loading, unavailable, decide, refresh }: {
  items: Evidence[];
  busy: boolean;
  loading?: boolean;
  unavailable?: boolean;
  decide: (item: Evidence, action: Decision['action'], claim?: string) => void;
  refresh?: () => void;
}) {
  const proposed = items.filter(item => item.lifecycle === 'proposed' && !item.is_private).length;
  const heading = useRef<HTMLHeadingElement>(null);
  const decisionTarget = useRef<Evidence | null>(null);
  useEffect(() => {
    const target = decisionTarget.current;
    if (!busy && target && items.some(item => item.evidence_id === target.evidence_id && item.revision > target.revision)) {
      decisionTarget.current = null;
      if (document.activeElement === document.body) heading.current?.focus({ preventScroll: true });
    }
  }, [busy, items]);

  return (
    <section aria-labelledby="coach-evidence" className="min-w-0 space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 ref={heading} id="coach-evidence" tabIndex={-1} className="text-base font-semibold">Evidence review</h2>
          {!loading && <p className="mt-1 text-sm text-muted-foreground">
            {unavailable ? 'Saved proposals are unavailable.' : items.length
              ? `${proposed} awaiting review on this page` : 'Your saved proposals will appear here.'}
          </p>}
        </div>
        {refresh && <Button variant="ghost" size="sm" disabled={busy} onClick={refresh}>Refresh evidence</Button>}
      </div>
      {items.length > 0 && <ul className="divide-y divide-border rounded-xl border border-border bg-card">
        {items.map(item => <EvidenceCard key={`${item.evidence_id}:${item.revision}`} item={item} busy={busy}
          decide={(...args) => { decisionTarget.current = args[0]; decide(...args); }} />)}
      </ul>}
    </section>
  );
}

function EvidenceCard({ item, busy, decide }: {
  item: Evidence;
  busy: boolean;
  decide: (item: Evidence, action: Decision['action'], claim?: string) => void;
}) {
  const [edit, setEdit] = useState<string>();
  const editable = item.lifecycle === 'proposed' && !item.is_private;
  return (
    <li className="space-y-3 p-4 [overflow-wrap:anywhere]">
      <p className="text-sm font-semibold capitalize text-muted-foreground">{item.lifecycle}</p>
      <p className="whitespace-pre-wrap text-sm leading-relaxed">{item.claim}</p>
      <details className="text-sm text-muted-foreground" open>
        <summary className="cursor-pointer font-medium">Sources</summary>
        <ul className="mt-2 space-y-2">
          {item.sources.map((source, index) => (
            <li key={index}>
              <p className="font-medium text-foreground">{source.locator} · Source version {source.source_version}</p>
              <p className="whitespace-pre-wrap">{source.excerpt ?? 'Excerpt unavailable'}</p>
            </li>
          ))}
        </ul>
      </details>
      {editable && (edit === undefined ? (
        <div className="flex flex-wrap gap-2">
          <Button size="sm" disabled={busy} onClick={() => decide(item, 'confirm')}>Confirm</Button>
          <Button size="sm" variant="outline" disabled={busy} onClick={() => setEdit(item.claim)}>Edit</Button>
          <Button size="sm" variant="outline" disabled={busy} onClick={() => decide(item, 'reject')}>Reject</Button>
          <Button size="sm" variant="outline" disabled={busy} onClick={() => decide(item, 'mark_private')}>Mark private</Button>
          <Button size="sm" variant="outline" disabled={busy} onClick={() => decide(item, 'mark_unavailable')}>Mark unavailable</Button>
        </div>
      ) : (
        <form className="space-y-2" onSubmit={event => {
          event.preventDefault();
          if (!busy && edit.trim() && edit.trim() !== item.claim) decide(item, 'edit', edit.trim());
        }}>
          <label className="text-sm font-medium">
            Edit claim
            <Textarea className="mt-1" value={edit} maxLength={4000} disabled={busy} onChange={event => setEdit(event.target.value)} />
          </label>
          <div className="flex flex-wrap gap-2">
            <Button size="sm" type="submit" disabled={busy || !edit.trim() || edit.trim() === item.claim}>Save edit</Button>
            <Button size="sm" type="button" variant="outline" disabled={busy} onClick={() => setEdit(undefined)}>Cancel</Button>
          </div>
        </form>
      ))}
    </li>
  );
}
