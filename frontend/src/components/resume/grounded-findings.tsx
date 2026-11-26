'use client';

import { useState } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { makeAPIRequest } from '@/app/lib/api/config';
import { Button } from '@/components/ui/button';
import type { components } from '@/generated/api/types';

type Review = components['schemas']['GroundedResumeReview'];
type Target = components['schemas']['CareerTarget'];
const documentCategories = new Set(['formatting', 'parseability', 'document_limit']);
const pageSize = 50;

export function GroundedFindings({ review, document = false }: { review: Review; document?: boolean }) {
  const findings = review.findings.filter(row => documentCategories.has(row.category) === document);

  return <div className="space-y-3">
    {!document && review.mode === 'document_only' && (
      <p><strong>Limited confidence.</strong> This review uses the résumé as its only source.</p>
    )}
    {!document && review.needs_refresh && <p>Some cited evidence is no longer eligible. Re-evaluate for updated findings.</p>}
    {findings.length === 0 ? <p>{document ? 'No document issues were flagged.' : 'No candidate evidence findings are available.'}</p> : (
      <ul className="space-y-3">
        {findings.map(row => <li key={row.finding_id}>
          <h3 className="font-semibold capitalize">
            {row.category.replaceAll('_', ' ')}{row.focus_label && ` · ${row.focus_label}`}
          </h3>
          <p>{row.explanation}</p>
          <p>{row.next_action}</p>
          {row.source_locator && <p className="text-muted-foreground">Source {row.source_locator}</p>}
          {row.evidence_revisions?.map(ref => (
            <Link key={`${ref.evidence_id}:${ref.revision}`} target="_blank" rel="noopener noreferrer" className="underline"
              href={`/dashboard/evidence?evidence=${encodeURIComponent(ref.evidence_id)}&revision=${ref.revision}`}>
              View evidence revision {ref.revision}
            </Link>
          ))}
        </li>)}
      </ul>
    )}
  </div>;
}

interface PickerProps {
  userId: string;
  selected: string;
  onSelect: (target: Target | undefined) => void;
  disabled: boolean;
}

export function ResumeReviewTargetPicker(props: PickerProps) {
  const [open, setOpen] = useState(false);
  return <details onToggle={event => setOpen(event.currentTarget.open)}>
    <summary className="cursor-pointer text-sm">{props.selected ? 'Change saved career target' : 'Use a saved career target'}</summary>
    {open && <Targets {...props} />}
  </details>;
}

function Targets({ userId, selected, onSelect, disabled }: PickerProps) {
  const targets = useInfiniteQuery({
    queryKey: ['resume-review-targets', userId],
    queryFn: async ({ pageParam, signal }) => {
      const result = await makeAPIRequest<Target[]>(`/api/v1/career/targets?limit=${pageSize}&offset=${pageParam}`,
        { expectedUserId: userId, signal, cache: 'no-store' });
      if (result.some(target => target.owner_id !== userId || target.status !== 'active')) throw new Error('Targets unavailable');
      return result;
    },
    initialPageParam: 0,
    getNextPageParam: (page, _, offset) => page.length === pageSize && offset < 1_000_000 ? offset + pageSize : undefined,
    retry: false,
    gcTime: 0,
  });
  const options = [...new Map(targets.data?.pages.flat().map(target => [target.target_id, target])).values()];
  return <div className="space-y-2 pt-2">
    <label className="block text-sm">
      Career target
      <select className="block w-full rounded border bg-background px-2 py-1" value={selected}
        disabled={disabled} onChange={event => onSelect(options.find(option => option.target_id === event.target.value))}>
        <option value="">Document-only review</option>
        {selected && !options.some(option => option.target_id === selected) && <option value={selected}>Selected target</option>}
        {options.map(option => <option key={option.target_id} value={option.target_id}>
          {option.role_family} ({option.seniority})
        </option>)}
      </select>
    </label>
    {targets.isPending && <p role="status">Loading career targets…</p>}
    {targets.isError && <p role="alert">Career targets are unavailable. <Button size="sm" variant="outline"
      onClick={() => void targets.refetch()}>Retry</Button></p>}
    {targets.hasNextPage && <Button size="sm" variant="outline" disabled={targets.isFetchingNextPage}
      onClick={() => void targets.fetchNextPage()}>More targets</Button>}
  </div>;
}
