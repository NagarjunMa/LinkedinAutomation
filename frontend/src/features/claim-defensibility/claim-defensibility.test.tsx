import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import type { components } from '@/generated/api/types';
import { ClaimDefensibility } from './claim-defensibility';

const auth = vi.hoisted(() => ({ owner: 'owner-a' }));
vi.mock('@/contexts/auth-context', () => ({
  useAuth: () => ({ user: { id: auth.owner }, isCurrentUser: (id: string) => id === auth.owner }),
}));
const request = vi.hoisted(() => vi.fn());
vi.mock('@/app/lib/api/config', () => ({ makeAPIRequest: request, APIError: class extends Error {} }));

function target(owner: string, id: string) {
  return { schema_version: 1, owner_id: owner, target_id: id, status: 'active', role_family: id, seniority: 'Senior' };
}
const report: components['schemas']['TargetDefensibility'] = {
  schema_version: 1, owner_id: 'owner-a', target_id: 'Platform', jd_evaluation_id: 'jd',
  guidance: 'review_required_gaps', resume_comparable: false, jd_text_sha256: 'b'.repeat(64), requirements: [{
    requirement: { requirement_id: 'must_have-1', revision: 'a'.repeat(64), source_start: 1, source_end: 7 },
    priority: 'must_have', kind: 'technical', state: 'partial',
    claim: { evidence: { evidence_id: 'synthetic-proof', revision: 2 }, text: 'Built a synthetic scheduler',
      scope: 'Team', ownership: 'team', support: 'candidate_statement',
      measurement: { estimated: true, method: 'Fixture timing', scope: 'One service' }, qualifiers: [] },
    unknowns: ['qualification'], questions: ['What did you personally complete?'],
  }],
};

it('loads only when opened and removes prior claims on target or account changes', async () => {
  request.mockImplementation((url: string, options: { expectedUserId: string }) => {
    if (url.endsWith('?limit=50&offset=0')) return Promise.resolve(
      options.expectedUserId === 'owner-a' ? [target('owner-a', 'Platform'), target('owner-a', 'Data')] : [],
    );
    if (url.includes('/Data/')) return Promise.resolve(report); // Reject a mismatched report.
    return Promise.resolve(report);
  });
  const client = new QueryClient();
  const tree = <QueryClientProvider client={client}><ClaimDefensibility evaluationId="jd" /></QueryClientProvider>;
  const { rerender } = render(tree);
  expect(request).not.toHaveBeenCalled();
  const details = screen.getByText('Review claim defensibility').closest('details');
  if (!details) throw new Error('Missing review control');
  details.open = true;
  fireEvent(details, new Event('toggle', { bubbles: true }));

  const select = await screen.findByRole('combobox', { name: 'Career target' });
  fireEvent.change(select, { target: { value: 'Platform' } });
  expect(await screen.findByText('Built a synthetic scheduler')).toBeVisible();
  expect(screen.getByText('Estimated · Fixture timing · One service')).toBeVisible();
  expect(screen.getByText('Additional qualification unverified')).toBeVisible();
  const evidence = screen.getByRole('link', { name: /Evidence revision 2/ });
  expect(evidence).toHaveAttribute('href', '/dashboard/evidence?evidence=synthetic-proof&revision=2');
  expect(evidence).toHaveAttribute('target', '_blank');
  expect(evidence).toHaveAttribute('rel', 'noopener noreferrer');
  expect(screen.getByRole('button', { name: 'Show requirement text' })).toBeVisible();
  expect(screen.getByText('Résumé comparison unavailable for this analysis.')).toBeVisible();

  fireEvent.change(select, { target: { value: 'Data' } });
  expect(screen.queryByText('Built a synthetic scheduler')).not.toBeInTheDocument();
  expect(await screen.findByRole('alert')).toHaveTextContent('The claim review could not be loaded.');

  auth.owner = 'owner-b';
  rerender(<QueryClientProvider client={client}><ClaimDefensibility evaluationId="jd" /></QueryClientProvider>);
  expect(await screen.findByRole('link', { name: /LinkedIn Review/ })).toBeVisible();
  expect(screen.queryByText('Built a synthetic scheduler')).not.toBeInTheDocument();
  expect(request).toHaveBeenCalledWith('/api/v1/career/targets?limit=50&offset=0',
    expect.objectContaining({ expectedUserId: 'owner-b', cache: 'no-store' }));
});


afterEach(() => vi.unstubAllGlobals());

async function openPreviewFixture() {
  auth.owner = 'owner-a';
  request.mockImplementation((url: string) => {
    if (url.includes('?')) return Promise.resolve([target('owner-a', 'Platform'), target('owner-a', 'Data')]);
    return Promise.resolve({ ...report, target_id: url.includes('/Data/') ? 'Data' : 'Platform' });
  });
  render(<QueryClientProvider client={new QueryClient()}>
    <textarea id="jd" defaultValue="🚀Python." />
    <ClaimDefensibility evaluationId="jd" />
  </QueryClientProvider>);
  const details = screen.getByText('Review claim defensibility').closest('details');
  if (!details) throw new Error('Missing review control');
  details.open = true;
  fireEvent(details, new Event('toggle', { bubbles: true }));
  const select = await screen.findByRole('combobox', { name: 'Career target' });
  fireEvent.change(select, { target: { value: 'Platform' } });
  const show = await screen.findByRole('button', { name: 'Show requirement text' });
  return { select, show };
}

const matchedDigest = () => new Uint8Array(32).fill(0xbb).buffer;

it('clears a displayed source preview immediately when the input changes', async () => {
  const { show } = await openPreviewFixture();
  vi.stubGlobal('crypto', { subtle: { digest: async () => matchedDigest() } });
  fireEvent.click(show);
  expect(await screen.findByText('Python', { exact: true })).toBeVisible();
  fireEvent.input(screen.getByRole('textbox'), { target: { value: 'Changed source text' } });
  expect(screen.queryByText('Python', { exact: true })).not.toBeInTheDocument();
});

it('ignores an in-flight source preview when the target changes', async () => {
  const { select, show } = await openPreviewFixture();
  let complete!: (bytes: ArrayBuffer) => void;
  const digest = new Promise<ArrayBuffer>(resolve => { complete = resolve; });
  vi.stubGlobal('crypto', { subtle: { digest: () => digest } });
  fireEvent.click(show);
  fireEvent.change(select, { target: { value: 'Data' } });
  await screen.findByRole('button', { name: 'Show requirement text' });
  await act(async () => complete(matchedDigest()));
  expect(screen.queryByText('Python', { exact: true })).not.toBeInTheDocument();
});
