import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { APIError } from '@/app/lib/api/config';
import { GroundedTailorEntry } from '../grounded-tailor';

const mocks = vi.hoisted(() => ({
  params: new URLSearchParams(),
  current: true,
  request: vi.fn(),
}));
vi.mock('next/navigation', () => ({ useSearchParams: () => mocks.params }));
vi.mock('@/contexts/auth-context', () => ({
  useAuth: () => ({ user: { id: 'owner' }, isCurrentUser: () => mocks.current }),
}));
vi.mock('@/app/lib/api/config', async (load) => ({
  ...await load<typeof import('@/app/lib/api/config')>(),
  makeAPIRequest: mocks.request,
}));
vi.mock('../preview-panel', () => ({
  PreviewPanel: ({ versionId }: { versionId: string }) => <div>Saved {versionId}</div>,
}));

const draft = {
  resume_version_id: null,
  evaluation_id: 'evaluation-1',
  choices: [{
    plan_id: 'plan-1',
    requirements: [{ requirement_id: 'must-have-1', revision: 'jd-rev-1' }],
    evidence: [{ evidence_id: 'evidence-1', revision: 3 }],
    options: { safe: 'A safe contribution.', action_first: 'Alternate safe wording.' },
  }],
};
const wording = {
  plan_id: 'plan-1', selected_option: 'action_first', receipt: 'opaque-proof',
  validation: { accepted: true, used_fallback: false },
};

beforeEach(() => {
  mocks.params = new URLSearchParams('resumeDocument=doc-1&careerTarget=target-1&groundedReview=review-1');
  mocks.current = true;
  mocks.request.mockReset();
});

it('previews an original upload, applies an approved choice, and refreshes the draft', async () => {
  mocks.request.mockResolvedValueOnce({ ...draft, wording }).mockResolvedValueOnce({ version_id: 'version-1' })
    .mockResolvedValueOnce({ ...draft, choices: [] });
  render(<GroundedTailorEntry />);
  fireEvent.click(screen.getByLabelText('Suggest wording when available'));
  fireEvent.click(screen.getByRole('button', { name: 'Build grounded draft' }));
  expect(screen.getByRole('status')).toHaveTextContent('Checking confirmed evidence');
  const picker = await screen.findByLabelText('Choose wording');
  expect(screen.getByRole('link', { name: 'Evidence revision 3' })).toHaveAttribute(
    'href', '/dashboard/evidence?evidence=evidence-1&revision=3',
  );
  expect(screen.getByRole('option', { name: 'Suggested: Alternate safe wording.' })).toBeInTheDocument();
  expect(JSON.parse(mocks.request.mock.calls[0][1].body)).toMatchObject({
    resume_version_id: null, suggest_wording: true,
  });
  fireEvent.change(picker, { target: { value: 'action_first' } });
  fireEvent.click(screen.getByRole('button', { name: 'Apply grounded choices' }));
  expect(await screen.findByText('Saved version-1')).toBeInTheDocument();
  expect(JSON.parse(mocks.request.mock.calls[1][1].body)).toMatchObject({
    evaluation_id: 'evaluation-1', selections: { 'plan-1': 'action_first' }, wording_receipt: 'opaque-proof',
  });
  fireEvent.change(picker, { target: { value: '' } });
  expect(screen.queryByText('Saved version-1')).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Apply grounded choices' })).toBeDisabled();
  fireEvent.click(screen.getByRole('button', { name: 'Refresh grounded draft' }));
  expect(await screen.findByText(/No confirmed contribution/)).toBeInTheDocument();
});

it('shows the safe fallback and a recoverable conflict when apply becomes stale', async () => {
  mocks.request.mockResolvedValueOnce({
    ...draft, wording: { ...wording, validation: { accepted: false, used_fallback: true } },
  }).mockRejectedValueOnce(new APIError('Evidence changed.', 409));
  render(<GroundedTailorEntry />);
  fireEvent.click(screen.getByRole('button', { name: 'Build grounded draft' }));
  expect(await screen.findByText('Safe wording is ready to use.')).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Choose wording'), { target: { value: 'safe' } });
  fireEvent.click(screen.getByRole('button', { name: 'Apply grounded choices' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Evidence changed.');
  expect(screen.getByRole('button', { name: 'Refresh grounded draft' })).toBeEnabled();
});

it('aborts canceled requests and ignores data returned after an account switch', async () => {
  let finish: (value: unknown) => void = () => undefined;
  mocks.request.mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  const { rerender } = render(<GroundedTailorEntry />);
  const build = screen.getByRole('button', { name: 'Build grounded draft' });
  fireEvent.click(build);
  fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
  expect(mocks.request.mock.calls[0][1].signal.aborted).toBe(true);
  await act(async () => finish(draft));
  expect(screen.queryByLabelText('Choose wording')).not.toBeInTheDocument();
  fireEvent.click(build);
  mocks.current = false;
  await act(async () => finish(draft));
  rerender(<GroundedTailorEntry />);
  await waitFor(() => expect(screen.queryByLabelText('Tailor from confirmed evidence')).not.toBeInTheDocument());
});
