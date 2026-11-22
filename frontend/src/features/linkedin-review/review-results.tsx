import { useLayoutEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { APIError } from '@/app/lib/api/config';
import { Button } from '@/components/ui/button';
import { linkedInApi, sourceKey, type EvidenceRevision, type Recommendation, type Review, type ReviewOwner, type Source } from './api';

const sections = { headline: 'Headline', about: 'About', experience: 'Experience', skills: 'Skills' };

function EvidenceLinks({ revisions }: { revisions: EvidenceRevision[] }) {
  return revisions.map(({ evidence_id, revision }) => (
    <li key={`${evidence_id}:${revision}`}>
      <Link className="underline underline-offset-2" href={`/dashboard/evidence?evidence=${encodeURIComponent(evidence_id)}&revision=${revision}`}>
        Evidence revision {revision}
      </Link>
    </li>
  ));
}

function Findings({ findings }: { findings: Review['findings'] }) {
  return (
    <section aria-labelledby="linkedin-findings" className="min-w-0 space-y-3">
      <h2 id="linkedin-findings" className="text-lg font-semibold">Review findings</h2>
      {!findings.length && <p className="text-sm text-muted-foreground">No findings for this PDF version and target.</p>}
      <ul className="space-y-2">
        {findings.map((finding, index) => (
          <li key={index} className="space-y-2 rounded-lg border bg-card p-4 [overflow-wrap:anywhere]">
            <h3 className="text-sm font-medium capitalize">{finding.kind.replaceAll('_', ' ')}</h3>
            <p className="text-sm">{finding.explanation}</p>
            <ul className="space-y-1 text-xs text-muted-foreground">
              {finding.document_locator && <li>LinkedIn PDF · {finding.document_locator}</li>}
              {finding.target_requirement_id && <li>Target requirement · {finding.target_requirement_id}</li>}
              {finding.resume_source && <li>Résumé version {finding.resume_source.source_version} · {finding.resume_locator}</li>}
              <EvidenceLinks revisions={finding.evidence_revisions ?? []} />
            </ul>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function ReviewResults({ session, source, target }: { session: ReviewOwner; source: Source; target: string }) {
  const [hasRun, setHasRun] = useState(false);
  const [blocked, setBlocked] = useState(false);
  const [copying, setCopying] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const pendingCopy = useRef<AbortController | null>(null);
  const query = useQuery({
    queryKey: ['linkedin-review', session.owner, sourceKey(source), target],
    queryFn: ({ signal }) => linkedInApi(session, signal).review(source, target),
    enabled: false,
    retry: false,
    gcTime: 0,
  });
  useLayoutEffect(() => () => {
    const pending = pendingCopy.current;
    pendingCopy.current = null;
    pending?.abort();
  }, []);

  async function runReview() {
    if (pendingCopy.current) return;
    setHasRun(true);
    setError('');
    setNotice('');
    const result = await query.refetch();
    if (result.isSuccess) setBlocked(false);
  }

  async function copy(recommendation: Recommendation) {
    if (pendingCopy.current || !session.isCurrentUser(session.owner)) return;
    const controller = new AbortController();
    pendingCopy.current = controller;
    const deadline = setTimeout(() => controller.abort(), 30_000);
    const current = () => pendingCopy.current === controller && session.isCurrentUser(session.owner);
    setCopying(true);
    setNotice('');
    setError('');
    try {
      if (!navigator.clipboard?.write || typeof ClipboardItem === 'undefined') {
        setError('Clipboard access is unavailable in this browser.');
        return;
      }
      const text = linkedInApi(session, controller.signal).copy(source, target, recommendation);
      const data = text.then(value => new Blob([value], { type: 'text/plain' }));
      void data.catch(() => undefined);
      // Reserve the browser gesture now. A failed recheck rejects the clipboard item without supplying text.
      const write = navigator.clipboard.write([new ClipboardItem({ 'text/plain': data })]);
      const [recheck, clipboard] = await Promise.allSettled([text, write]);
      if (!current()) return;
      if (recheck.status === 'rejected') {
        setBlocked(true);
        const status = recheck.reason instanceof APIError ? recheck.reason.status : undefined;
        setError(status === 409 || status === 404
          ? 'Evidence changed or is unavailable. Refresh the review before copying.'
          : 'Copy eligibility could not be verified. Refresh the review before copying.');
      } else if (clipboard.status === 'rejected') {
        setError('Clipboard access failed. Check your browser permissions and try again.');
      } else {
        setNotice('Copied to clipboard.');
      }
    } catch {
      if (current()) {
        setError('Clipboard access failed. Check your browser permissions and try again.');
      }
    } finally {
      clearTimeout(deadline);
      if (current()) setCopying(false);
      if (pendingCopy.current === controller) pendingCopy.current = null;
    }
  }

  const result = hasRun && !blocked && query.isSuccess && !query.isFetching ? query.data : undefined;
  return (
    <div className="min-w-0 space-y-5">
      <Button disabled={query.isFetching || copying} onClick={() => void runReview()}>
        {hasRun ? 'Refresh review' : 'Run review'}
      </Button>
      <div role="status" className="text-sm text-muted-foreground empty:sr-only">
        {query.isFetching ? 'Reviewing PDF…' : copying ? 'Checking copy eligibility…' : notice}
      </div>
      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
      {query.isError && !query.isFetching && <p role="alert" className="text-sm text-destructive">The review could not be loaded. Refresh to try again.</p>}
      {result && <>
        <Findings findings={result.review.findings} />
        <section aria-labelledby="linkedin-recommendations" className="min-w-0 space-y-3">
          <h2 id="linkedin-recommendations" className="text-lg font-semibold">Copy-ready recommendations</h2>
          <p className="text-sm text-muted-foreground">Based on confirmed, non-private evidence. PrismPro checks each citation again when you copy.</p>
          {!result.recommendations.length && <p className="text-sm">No copy-ready recommendations for this target.</p>}
          {Object.entries(sections).map(([section, title]) => {
            const options = result.recommendations.filter(item => item.section === section);
            return options.length > 0 && (
              <section key={section} className="space-y-2" aria-label={title}>
                <h3 className="text-sm font-semibold">{title}</h3>
                <ul className="space-y-2">
                  {options.map((item, index) => (
                    <li key={index} className="space-y-3 rounded-lg border bg-card p-4 [overflow-wrap:anywhere]">
                      <p className="whitespace-pre-wrap text-sm">{item.text}</p>
                      <ul className="space-y-1 text-xs text-muted-foreground"><EvidenceLinks revisions={item.evidence_revisions} /></ul>
                      <Button variant="outline" size="sm" disabled={copying} onClick={() => void copy(item)}>
                        Copy {title.toLowerCase()}{options.length > 1 ? ` option ${index + 1}` : ''}
                      </Button>
                    </li>
                  ))}
                </ul>
              </section>
            );
          })}
        </section>
      </>}
    </div>
  );
}
