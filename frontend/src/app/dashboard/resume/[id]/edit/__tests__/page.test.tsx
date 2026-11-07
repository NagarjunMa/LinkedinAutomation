import { beforeEach, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { EvaluationResponse, VersionResponse } from '@/app/lib/api';
import { resumeDocKey } from '@/lib/resume-cache';

const mocks = vi.hoisted(() => ({ evaluate: vi.fn(), save: vi.fn(), push: vi.fn(), toast: vi.fn(), userId: 'owner-a' }));
vi.mock('next/navigation', () => ({ useParams: () => ({ id: 'doc-1' }), useRouter: () => ({ push: mocks.push }) }));
vi.mock('@/contexts/auth-context', () => ({ useAuth: () => ({ user: { id: mocks.userId } }) }));
vi.mock('@/hooks/use-resume', () => ({
  useEvaluateResume: () => ({ mutateAsync: mocks.evaluate, isPending: false }),
  useCreateVersion: () => ({ mutateAsync: mocks.save, isPending: false }),
}));
vi.mock('@/components/ui/use-toast', () => ({ useToast: () => ({ toast: mocks.toast }) }));
vi.mock('@/components/resume/resume-renderer', () => ({ ResumeRenderer: ({ doc, onBulletClick }: any) => <>
  <p>Source resume</p>{doc.experience.flatMap((e: any) => e.bullets).map((b: any) =>
    <button key={b.id} onClick={() => onBulletClick(b.id)}>{b.text}</button>)}
</> }));
vi.mock('@/components/resume/rewrite-modal', () => ({ RewriteModal: ({ open, bullet, onAccept, onOpenChange }: any) =>
  open ? <button onClick={() => { onAccept(bullet.id, `${bullet.text} revised`); onOpenChange(false); }}>Accept test rewrite</button> : null,
}));
import ResumeEditPage from '../page';

const evaluation: EvaluationResponse = {
  evaluation_id: 'eval-1', overall_score: 92, readiness_label: 'minor_edits',
  score_breakdown: { content_quality: 80, role_fit: 70, evidence_strength: 60, recruiter_readability: 90 },
  score_explanation: [{ category: 'evidence_strength', score: 60, reason: 'Clarify personal contribution.',
    evidence: [], before_applying_action: 'Describe the component you built.' }],
  top_actions_before_applying: ['Review ownership claims.'], parser_confidence: 'high',
  bullet_flags: [], format_issues: [], summary_critique: 'Review each suggestion against your work.',
  ats_parseability: 85, ats_raw_text: 'Private synthetic source',
};
beforeEach(() => {
  vi.clearAllMocks();
  mocks.userId = 'owner-a';
  sessionStorage.clear();
  sessionStorage.setItem(resumeDocKey('owner-a', 'doc-1'), JSON.stringify({ contact: { name: 'Synthetic' },
    experience: [{ bullets: [{ id: 'b1', text: 'First', raw_text: 'First' }, { id: 'b2', text: 'Second', raw_text: 'Second' }] }], projects: [] }));
});

async function acceptBullet(text: string) {
  fireEvent.click(screen.getByRole('button', { name: text }));
  fireEvent.click(await screen.findByRole('button', { name: 'Accept test rewrite' }));
}

it('hides the edited resume and ignores ownerless cache entries after an account switch', async () => {
  const view = render(<ResumeEditPage />);
  await acceptBullet('First');
  expect(screen.getByRole('button', { name: 'First revised' })).toBeInTheDocument();
  sessionStorage.setItem('resumeDoc:doc-1', JSON.stringify({
    experience: [{ bullets: [{ id: 'legacy', text: 'Legacy source' }] }], projects: [],
  }));

  mocks.userId = 'owner-b';
  view.rerender(<ResumeEditPage />);
  expect(screen.getByText('No resume loaded.')).toBeInTheDocument();
  expect(screen.queryByText('First revised')).not.toBeInTheDocument();
  expect(screen.queryByText('Legacy source')).not.toBeInTheDocument();
});

it('chains subsequent saves to the previous saved version and restores the editor after refresh', async () => {
  mocks.save.mockResolvedValueOnce({ version_id: 'v1' }).mockResolvedValueOnce({ version_id: 'v2' });
  const view = render(<ResumeEditPage />);
  await acceptBullet('First');
  fireEvent.click(screen.getByRole('button', { name: 'Save version (1)' }));
  await waitFor(() => expect(screen.getByRole('button', { name: 'Save version (0)' })).toBeInTheDocument());
  await acceptBullet('Second');
  fireEvent.click(screen.getByRole('button', { name: 'Save version (1)' }));
  await waitFor(() => expect(mocks.save).toHaveBeenCalledTimes(2));
  expect(mocks.save.mock.calls[1][0].body).toEqual({ parent_version_id: 'v1', change_set: [
    { type: 'bullet_update', bullet_id: 'b2', new_text: 'Second revised' },
  ] });
  await waitFor(() => expect(screen.getByRole('button', { name: 'Save version (0)' })).toBeInTheDocument());
  view.unmount();
  render(<ResumeEditPage />);
  expect(await screen.findByRole('button', { name: 'First revised' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Second revised' })).toBeInTheDocument();
});

it('saves pending changes before evaluating the current version', async () => {
  mocks.save.mockResolvedValue({ version_id: 'v1' });
  mocks.evaluate.mockResolvedValue(evaluation);
  render(<ResumeEditPage />);
  await acceptBullet('First');
  fireEvent.click(screen.getByRole('button', { name: 'Evaluate (1 credit)' }));
  await waitFor(() => expect(mocks.evaluate).toHaveBeenCalledWith({
    resumeId: 'doc-1', targetRole: 'Software Engineer', versionId: 'v1',
  }));
  expect(mocks.save).toHaveBeenCalledTimes(1);
});

it('does not start evaluation when a save completes after an account switch', async () => {
  let finishSave!: (version: VersionResponse) => void;
  mocks.save.mockReturnValue(new Promise<VersionResponse>(resolve => { finishSave = resolve; }));
  const view = render(<ResumeEditPage />);
  await acceptBullet('First');
  fireEvent.click(screen.getByRole('button', { name: 'Evaluate (1 credit)' }));
  expect(mocks.save).toHaveBeenCalledTimes(1);
  mocks.userId = 'owner-b';
  view.rerender(<ResumeEditPage />);

  await act(async () => finishSave({ version_id: 'v1' }));
  expect(mocks.evaluate).not.toHaveBeenCalled();
});

it('waits for an in-flight save before opening another rewrite', async () => {
  let finishSave!: (version: VersionResponse) => void;
  mocks.save.mockReturnValue(new Promise<VersionResponse>((resolve) => { finishSave = resolve; }));
  render(<ResumeEditPage />);
  await acceptBullet('First');
  fireEvent.click(screen.getByRole('button', { name: 'Save version (1)' }));
  fireEvent.click(screen.getByRole('button', { name: 'Second' }));
  expect(screen.queryByRole('button', { name: 'Accept test rewrite' })).not.toBeInTheDocument();
  expect(mocks.save).toHaveBeenCalledTimes(1);
  await act(async () => finishSave({ version_id: 'v1' }));
  await acceptBullet('Second');
  expect(screen.getByRole('button', { name: 'Save version (1)' })).toBeEnabled();
});

it('evaluates into separate findings without an overall score or source-text disclosure', async () => {
  mocks.evaluate.mockResolvedValue(evaluation);
  render(<ResumeEditPage />);
  fireEvent.click(screen.getByRole('button', { name: 'Evaluate (1 credit)' }));
  expect(await screen.findByText('Clarify personal contribution.')).toBeInTheDocument();
  expect(screen.getByText('Describe the component you built.')).toBeInTheDocument();
  expect(screen.getByText('Review ownership claims.')).toBeInTheDocument();
  expect(screen.queryByText(/Overall:|Potential Score|92/)).not.toBeInTheDocument();
  expect(screen.queryByText('Private synthetic source')).not.toBeInTheDocument();
  expect(mocks.evaluate).toHaveBeenCalledWith({ resumeId: 'doc-1', targetRole: 'Software Engineer' });
  expect(screen.getByRole('button', { name: 'Re-evaluate' })).toBeEnabled();
  expect(screen.getByRole('tab', { name: 'Document checks' })).toBeEnabled();
});

it('does not fabricate findings for an empty evaluation and keeps the upload recovery route', async () => {
  mocks.evaluate.mockResolvedValue({ ...evaluation, score_explanation: [], top_actions_before_applying: [], summary_critique: null });
  const view = render(<ResumeEditPage />);
  fireEvent.click(screen.getByRole('button', { name: 'Evaluate (1 credit)' }));
  expect(await screen.findByText('No content findings returned. This is not a hiring assessment.')).toBeInTheDocument();
  view.unmount();
  sessionStorage.clear();
  render(<ResumeEditPage />);
  fireEvent.click(screen.getByRole('button', { name: 'Upload one' }));
  expect(mocks.push).toHaveBeenCalledWith('/dashboard/resume');
});
