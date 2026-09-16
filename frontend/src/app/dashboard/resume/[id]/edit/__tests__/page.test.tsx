import { beforeEach, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import type { EvaluationResponse } from '@/app/lib/api';

const mocks = vi.hoisted(() => ({ evaluate: vi.fn(), save: vi.fn(), push: vi.fn(), toast: vi.fn() }));
vi.mock('next/navigation', () => ({ useParams: () => ({ id: 'doc-1' }), useRouter: () => ({ push: mocks.push }) }));
vi.mock('@/hooks/use-resume', () => ({
  useEvaluateResume: () => ({ mutateAsync: mocks.evaluate, isPending: false }),
  useCreateVersion: () => ({ mutateAsync: mocks.save, isPending: false }),
}));
vi.mock('@/components/ui/use-toast', () => ({ useToast: () => ({ toast: mocks.toast }) }));
vi.mock('@/components/resume/resume-renderer', () => ({ ResumeRenderer: () => <p>Source resume</p> }));
vi.mock('@/components/resume/rewrite-modal', () => ({ RewriteModal: () => null }));
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
  sessionStorage.clear();
  sessionStorage.setItem('resumeDoc:doc-1', JSON.stringify({ contact: { name: 'Synthetic' }, experience: [], projects: [] }));
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
