import { focusManager, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { type Evidence } from '@/features/career-coach/api';
import { EvidenceNotebook } from './evidence-notebook';

const { auth, api } = vi.hoisted(() => ({
  auth: { id: 'account-a' },
  api: { evidence: vi.fn(), evidenceDetail: vi.fn(), evidenceHistory: vi.fn(), decide: vi.fn() },
}));
vi.mock('@/contexts/auth-context', () => ({
  useAuth: () => ({ user: { id: auth.id }, isCurrentUser: (id: string) => auth.id === id }),
}));
vi.mock('@/features/career-coach/api', () => ({
  careerApi: () => api, pageSize: 2,
}));

const first: Evidence = {
  schema_version: 1, evidence_id: 'evidence-1', owner_id: 'account-a', revision: 1, lifecycle: 'confirmed',
  claim: 'Account A claim', category: 'outcome', ownership: 'shared', support: 'candidate_statement',
  is_private: false, sources: [
    { source_id: 'a-note', source_version: 1, relationship: 'supports', locator: 'note', excerpt: 'Account A source', extraction: 'candidate' },
  ],
};
const second: Evidence = {
  ...first, owner_id: 'account-b', evidence_id: 'evidence-2', claim: 'Account B claim',
};
function mount() {
  const client = new QueryClient({ defaultOptions: { queries: { refetchOnWindowFocus: false } } });
  const element = () => <QueryClientProvider client={client}><EvidenceNotebook /></QueryClientProvider>;
  return { ...render(element()), element, client };
}

beforeEach(() => { vi.resetAllMocks(); auth.id = 'account-a'; });

describe('Evidence Notebook', () => {
  it('discards an old account response while switching and rejects mismatched detail and history', async () => {
    let finishA!: (value: Evidence) => void;
    api.evidence.mockImplementation(() => Promise.resolve(auth.id === 'account-a' ? [first] : [second]));
    api.evidenceDetail.mockImplementationOnce(() => new Promise(resolve => { finishA = resolve; }))
      .mockResolvedValueOnce(first).mockResolvedValueOnce(second);
    api.evidenceHistory.mockResolvedValue({ revisions: [first], decisions: [] });
    const view = mount();

    fireEvent.click(await screen.findByRole('button', { name: /Account A claim/ }));
    await waitFor(() => expect(api.evidenceDetail).toHaveBeenCalledOnce());
    auth.id = 'account-b';
    view.rerender(view.element());
    const newItem = await screen.findByRole('button', { name: /Account B claim/ });
    await act(async () => finishA(first));
    expect(screen.queryByText(first.claim)).toBeNull();

    fireEvent.click(newItem);
    expect(await screen.findByRole('alert')).toHaveTextContent('Evidence details are unavailable');
    expect(screen.queryByText('Account A source')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Refresh evidence' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Show history' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Revision history is unavailable');
    expect(screen.queryByText(first.claim)).toBeNull();
  });

  it('loads another page even when the active search has no matches', async () => {
    api.evidence.mockImplementation((offset: number) => Promise.resolve(offset === 0 ? [
      first, { ...first, evidence_id: 'other', claim: 'Another claim' },
    ] : [{ ...first, evidence_id: 'result', claim: 'Scheduled export' }]));
    mount();
    await screen.findByRole('button', { name: /Account A claim/ });
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'export' } });
    expect(screen.getByRole('status')).toHaveTextContent('0 shown of 2 loaded');
    fireEvent.click(screen.getByRole('button', { name: 'Load more evidence' }));
    expect(await screen.findByRole('button', { name: /Scheduled export/ })).toBeVisible();
    expect(api.evidence.mock.calls).toEqual([[0], [2]]);
  });

  it.each([
    { lifecycle: 'rejected', is_private: false },
    { lifecycle: 'confirmed', is_private: true },
    { lifecycle: 'private', is_private: true },
    { lifecycle: 'unavailable', is_private: false },
  ] as const)('does not offer generation eligibility or confirmation for $lifecycle with private=$is_private', async state => {
    const hidden = { ...first, ...state };
    api.evidence.mockResolvedValue([hidden]);
    api.evidenceDetail.mockResolvedValue(hidden);
    mount();
    fireEvent.click(await screen.findByRole('button', { name: /Account A claim/ }));
    expect(await screen.findByText('Excluded from generation')).toBeVisible();
    expect(screen.queryByText('Eligible for generation')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Confirm evidence' })).toBeNull();
  });
});

it('does not retry an ambiguous decision or render a mismatched mutation response', async () => {
  const proposed = { ...first, lifecycle: 'proposed' } as const;
  api.evidence.mockResolvedValue([proposed]);
  api.evidenceDetail.mockResolvedValue(proposed);
  let finish!: (item: Evidence) => void;
  api.decide.mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  mount();
  fireEvent.click(await screen.findByRole('button', { name: /Account A claim/ }));
  const confirmButton = await screen.findByRole('button', { name: 'Confirm evidence' });
  act(() => { confirmButton.click(); confirmButton.click(); });
  expect(api.decide).toHaveBeenCalledExactlyOnceWith(proposed.evidence_id, { action: 'confirm', revision: 1 });
  await act(async () => finish({ ...second, evidence_id: first.evidence_id, revision: 2 }));
  expect(await screen.findByRole('alert')).toHaveTextContent('decision could not be verified');
  expect(screen.queryByText(second.claim)).toBeNull();
  expect(screen.queryByText('Eligible for generation')).toBeNull();
  expect(screen.queryByRole('button', { name: 'Confirm evidence' })).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Refresh evidence' }));
  expect(await screen.findByRole('button', { name: 'Confirm evidence' })).toBeEnabled();
  expect(api.decide).toHaveBeenCalledOnce();
});

it('refreshes eligibility after a privacy decision in another tab', async () => {
  api.evidence.mockResolvedValue([first]);
  api.evidenceDetail.mockResolvedValueOnce(first).mockResolvedValue({
    ...first, revision: 2, lifecycle: 'private', is_private: true,
  });
  mount();
  fireEvent.click(await screen.findByRole('button', { name: /Account A claim/ }));
  expect(await screen.findByText('Eligible for generation')).toBeVisible();
  try {
    act(() => focusManager.setFocused(false));
    act(() => focusManager.setFocused(true));
    expect(await screen.findByText('Excluded from generation')).toBeVisible();
    expect(screen.queryByText('Eligible for generation')).toBeNull();
  } finally {
    focusManager.setFocused(undefined);
  }
});

it('deduplicates shifted pages by evidence ID and can restart pagination', async () => {
  const duplicate = { ...first, evidence_id: 'duplicate', claim: 'Duplicate entry' };
  api.evidence.mockImplementation((offset: number) => Promise.resolve(offset === 0 ? [
    first, duplicate,
  ] : [duplicate, { ...first, evidence_id: 'new', claim: 'New entry' }]));
  mount();
  fireEvent.click(await screen.findByRole('button', { name: 'Load more evidence' }));
  await screen.findByRole('button', { name: /New entry/ });
  expect(screen.getAllByRole('button', { name: /Duplicate entry/ })).toHaveLength(1);
  expect(screen.getByRole('status')).toHaveTextContent('3 shown of 3 loaded');
  fireEvent.click(screen.getByRole('button', { name: 'Refresh list' }));
  await waitFor(() => expect(api.evidence.mock.calls).toEqual([[0], [2], [0]]));
});

it('allows recovery from a decision that never settles without replaying it', async () => {
  const proposed = { ...first, lifecycle: 'proposed' } as const;
  api.evidence.mockResolvedValue([proposed]);
  api.evidenceDetail.mockResolvedValue(proposed);
  api.decide.mockReturnValue(new Promise(() => undefined));
  mount();
  fireEvent.click(await screen.findByRole('button', { name: /Account A claim/ }));
  const confirm = await screen.findByRole('button', { name: 'Confirm evidence' });
  vi.useFakeTimers();
  try {
    fireEvent.click(confirm);
    expect(screen.getByRole('button', { name: 'Close details' })).toBeDisabled();
    await act(() => vi.advanceTimersByTimeAsync(30_000));
    expect(screen.getByRole('alert')).toHaveTextContent('decision could not be verified');
    expect(screen.getByRole('button', { name: 'Close details' })).toBeEnabled();
    expect(screen.queryByRole('button', { name: 'Confirm evidence' })).toBeNull();
    expect(api.decide).toHaveBeenCalledOnce();
  } finally {
    vi.useRealTimers();
  }
});

it('withholds eligibility when a refreshed list shows a newer private revision', async () => {
  const privateItem = { ...first, revision: 2, lifecycle: 'private', is_private: true } as const;
  api.evidence.mockResolvedValueOnce([first]).mockResolvedValueOnce([privateItem])
    .mockReturnValue(new Promise(() => undefined));
  api.evidenceDetail.mockResolvedValueOnce(first).mockResolvedValue(privateItem);
  mount();
  fireEvent.click(await screen.findByRole('button', { name: /Account A claim/ }));
  expect(await screen.findByText('Eligible for generation')).toBeVisible();
  fireEvent.click(screen.getByRole('button', { name: 'Refresh list' }));
  await screen.findByRole('button', { name: /Account A claim Private/ });
  expect(screen.queryByText('Eligible for generation')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Refresh list' }));
  await screen.findByText('Loading evidence…');
  expect(screen.queryByText('Eligible for generation')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Refresh evidence' }));
  expect(await screen.findByText('Excluded from generation')).toBeVisible();
});
