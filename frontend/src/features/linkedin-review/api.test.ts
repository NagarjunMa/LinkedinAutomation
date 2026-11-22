import { beforeEach, expect, it, vi } from 'vitest';
import { makeAPIRequest } from '@/app/lib/api/config';
import { linkedInApi, type Recommendation, type Review, type Target } from './api';

vi.mock('@/app/lib/api/config', () => ({ makeAPIRequest: vi.fn() }));
const request = vi.mocked(makeAPIRequest);
const source = { source_id: 'source-a', source_version: 1 };
const reference = { evidence_id: 'evidence-a', revision: 2 };
const recommendation: Recommendation = { section: 'headline', text: 'Preview', evidence_revisions: [reference] };
const target: Target = {
  target_id: 'target-a', owner_id: 'account-a', role_family: 'Engineer', seniority: 'Senior',
  status: 'active', schema_version: 1,
};

beforeEach(() => vi.resetAllMocks());

it('pins the request to the owning session and rejects a late response after an account change', async () => {
  let current = 'account-a';
  let respond!: (value: Target[]) => void;
  const controller = new AbortController();
  request.mockReturnValue(new Promise(resolve => { respond = resolve; }));
  const pending = linkedInApi({ owner: current, isCurrentUser: id => id === current }, controller.signal).targets(0);
  expect(request).toHaveBeenCalledWith('/api/v1/career/targets?limit=50&offset=0', {
    expectedUserId: 'account-a', cache: 'no-store', signal: controller.signal,
  });
  current = 'account-b';
  respond([target]);
  await expect(pending).rejects.toThrow('Sign-in changed');
});

it('rejects target lists containing another owner', async () => {
  request.mockResolvedValue([target, { ...target, owner_id: 'account-b', target_id: 'target-b' }]);
  await expect(linkedInApi({ owner: 'account-a', isCurrentUser: () => true }).targets(0)).rejects.toThrow('Target is unavailable');
});

it('rejects findings for a different PDF version', async () => {
  request.mockResolvedValueOnce({
    schema_version: 1, document: { ...source, source_version: 2 }, target_id: target.target_id,
    parser_version: 'linked-in-pdf-v1', findings: [],
  } satisfies Review).mockResolvedValueOnce([]);
  await expect(linkedInApi({ owner: 'account-a', isCurrentUser: () => true })
    .review(source, target.target_id)).rejects.toThrow('Review selection has changed');
});

it('copies only the authorized text and rejects the wrong citation revision', async () => {
  const api = linkedInApi({ owner: 'account-a', isCurrentUser: () => true });
  request.mockResolvedValueOnce({ ...recommendation, text: 'Server-authorized wording' });
  await expect(api.copy(source, target.target_id, recommendation)).resolves.toBe('Server-authorized wording');
  expect(JSON.parse(String(request.mock.calls[0][1]?.body))).toEqual({
    target_id: target.target_id, selection: { section: 'headline', evidence_revisions: [reference] },
  });
  request.mockResolvedValueOnce({ ...recommendation, evidence_revisions: [{ ...reference, revision: 3 }] });
  await expect(api.copy(source, target.target_id, recommendation)).rejects.toThrow('Copy text is unavailable');
});

it('rejects a copy response that completes after the view is canceled', async () => {
  let respond!: (value: Recommendation) => void;
  const controller = new AbortController();
  request.mockReturnValue(new Promise(resolve => { respond = resolve; }));
  const pending = linkedInApi({ owner: 'account-a', isCurrentUser: () => true }, controller.signal)
    .copy(source, target.target_id, recommendation);
  controller.abort();
  respond(recommendation);
  await expect(pending).rejects.toMatchObject({ name: 'AbortError' });
});
