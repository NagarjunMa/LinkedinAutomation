import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { StrictMode, useState } from 'react';
import type { JdInputFormProps } from '@/components/jd/jd-input-form';
import type { DiffViewProps } from '@/components/jd/diff-view';
import type { ApplyTailorResponse, JDAnalyzeResponse } from '@/app/lib/api';

const mocks = vi.hoisted(() => ({
  analyze: vi.fn(), apply: vi.fn(), toast: vi.fn(),
  submit: null as JdInputFormProps['onSubmit'] | null,
  select: null as DiffViewProps['onAcceptedChangesChange'] | null,
}));
vi.mock('@/hooks/use-jd-analyze', () => ({
  useJdAnalyze: () => ({ mutateAsync: mocks.analyze, isPending: false }),
}));
vi.mock('@/hooks/use-tailor-apply', () => ({
  useTailorApply: (id: string) => ({
    mutateAsync: (body: unknown) => mocks.apply(id, body), isPending: false,
  }),
}));
vi.mock('@/components/ui/use-toast', () => ({ useToast: () => ({ toast: mocks.toast }) }));
vi.mock('@/components/jd/jd-input-form', () => ({
  JdInputForm: ({ onSubmit, pending }: JdInputFormProps) => {
    const [resume, setResume] = useState('doc-1');
    const [jdText, setJdText] = useState('Synthetic job description');
    mocks.submit = onSubmit;
    return <>
      <input aria-label="Resume" value={resume} onChange={e => setResume(e.target.value)} />
      <input aria-label="JD" value={jdText} onChange={e => setJdText(e.target.value)} />
      <button disabled={pending} onClick={() => onSubmit({ resumeDocumentId: resume, jdText })}>Analyze</button>
    </>;
  },
}));
vi.mock('@/components/jd/jd-analysis-panel', () => ({ JdAnalysisPanel: () => null }));
vi.mock('@/components/jd/diff-view', () => ({
  DiffView: ({ resumeId, jdEvaluationId, onAcceptedChangesChange }: DiffViewProps) => {
    mocks.select = onAcceptedChangesChange;
    return <div data-testid="suggestions">
      {resumeId}/{jdEvaluationId}
      <button onClick={() => onAcceptedChangesChange?.([
        { type: 'bullet_update', bullet_id: 'b1', new_text: 'Selected pointer' },
      ])}>Select pointer</button>
    </div>;
  },
}));
vi.mock('@/components/tailor/preview-panel', () => ({
  PreviewPanel: ({ versionId }: { versionId: string }) => <div data-testid="preview">{versionId}</div>,
}));

import TailorPage from '../page';

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
function analysis(id: string): JDAnalyzeResponse {
  return {
    jd_evaluation_id: id,
    extracted_requirements: { must_have: [], good_to_have: [], soft_skills: [], red_flags: [],
      seniority: 'mid', primary_role_category: 'SWE', country_hint: 'US' },
    diff_plan: { match_score: 50, must_have_coverage_found: [], must_have_coverage_missing: [],
      good_to_have_coverage_found: [], good_to_have_coverage_missing: [], bullets: [],
      skills_reorder: null, summary_rewrite: null, suggested_additions: [] },
  };
}
function applied(id: string): ApplyTailorResponse {
  return { version_id: id, preview_html: '<p>Synthetic</p>', company_name: null,
    suggested_template: 'us-swe', filename_hint: 'resume.pdf' };
}
async function analyzeSuccessfully(id = 'jd-1') {
  mocks.analyze.mockResolvedValueOnce(analysis(id));
  fireEvent.click(screen.getByRole('button', { name: 'Analyze' }));
  await waitFor(() => expect(screen.getByTestId('suggestions')).toHaveTextContent(id));
}
function selectAndApply() {
  fireEvent.click(screen.getByRole('button', { name: 'Select pointer' }));
  fireEvent.click(screen.getByTestId('tailor-apply'));
}
beforeEach(() => { vi.resetAllMocks(); mocks.submit = null; mocks.select = null; });

it('clears old suggestions and preview while pending, keeps input after failure, and recovers manually', async () => {
  render(<StrictMode><TailorPage /></StrictMode>);
  expect(screen.queryByTestId('tailor-apply')).not.toBeInTheDocument();
  await analyzeSuccessfully();
  mocks.apply.mockResolvedValueOnce(applied('v1'));
  selectAndApply();
  await waitFor(() => expect(screen.getByTestId('preview')).toHaveTextContent('v1'));

  const failed = deferred<JDAnalyzeResponse>();
  mocks.analyze.mockReturnValueOnce(failed.promise);
  fireEvent.change(screen.getByLabelText('Resume'), { target: { value: 'doc-2' } });
  fireEvent.change(screen.getByLabelText('JD'), { target: { value: 'New synthetic job' } });
  fireEvent.click(screen.getByRole('button', { name: 'Analyze' }));
  expect(screen.queryByTestId('suggestions')).not.toBeInTheDocument();
  expect(screen.queryByTestId('preview')).not.toBeInTheDocument();
  expect(screen.queryByTestId('tailor-apply')).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Analyze' })).toBeDisabled();
  await act(async () => failed.reject(new Error('Analysis unavailable')));
  expect(screen.queryByTestId('suggestions')).not.toBeInTheDocument();
  expect(screen.getByLabelText('JD')).toHaveValue('New synthetic job');
  expect(mocks.analyze).toHaveBeenCalledTimes(2);
  expect(mocks.toast).toHaveBeenLastCalledWith(expect.objectContaining({ title: 'Analyze failed' }));
  expect(screen.getByRole('alert')).toHaveTextContent('Analyze failed');

  await analyzeSuccessfully('jd-2');
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(screen.getByTestId('suggestions')).toHaveTextContent('doc-2/jd-2');
  expect(screen.getByTestId('tailor-apply')).toBeDisabled();
  mocks.apply.mockResolvedValueOnce(applied('v2'));
  selectAndApply();
  await waitFor(() => expect(screen.getByTestId('preview')).toHaveTextContent('v2'));
  expect(mocks.apply).toHaveBeenLastCalledWith('jd-2', {
    accepted_changes: [{ type: 'bullet_update', bullet_id: 'b1', new_text: 'Selected pointer' }],
  });
});

it('rejects duplicate analysis events before React has rerendered', async () => {
  render(<TailorPage />);
  const pending = deferred<JDAnalyzeResponse>();
  mocks.analyze.mockReturnValue(pending.promise);
  act(() => {
    mocks.submit?.({ resumeDocumentId: 'doc-1', jdText: 'First' });
    mocks.submit?.({ resumeDocumentId: 'doc-2', jdText: 'Duplicate' });
  });
  expect(mocks.analyze).toHaveBeenCalledTimes(1);
  await act(async () => pending.resolve(analysis('jd-1')));
  expect(screen.getByTestId('suggestions')).toHaveTextContent('doc-1/jd-1');
});

it.each(['success', 'failure'])('ignores obsolete Apply %s without clearing the new pending Apply', async outcome => {
  render(<TailorPage />);
  await analyzeSuccessfully();
  const old = deferred<ApplyTailorResponse>();
  mocks.apply.mockReturnValueOnce(old.promise);
  selectAndApply();
  const staleSelect = mocks.select;
  await analyzeSuccessfully('jd-2');
  act(() => staleSelect?.([{ type: 'summary_update', new_summary: 'Obsolete selection' }]));
  expect(screen.getByTestId('tailor-apply')).toBeDisabled();
  const current = deferred<ApplyTailorResponse>();
  mocks.apply.mockReturnValueOnce(current.promise);
  selectAndApply();
  mocks.toast.mockClear();
  await act(async () => {
    if (outcome === 'success') old.resolve(applied('old-version'));
    else old.reject(new Error('Obsolete failure'));
  });
  expect(screen.queryByTestId('preview')).not.toBeInTheDocument();
  expect(mocks.toast).not.toHaveBeenCalled();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(screen.getByTestId('tailor-apply')).toBeDisabled();
  fireEvent.click(screen.getByTestId('tailor-apply'));
  expect(mocks.apply).toHaveBeenCalledTimes(2);
  await act(async () => current.resolve(applied('new-version')));
  expect(screen.getByTestId('preview')).toHaveTextContent('new-version');
});

it('does not replay Apply on double click and permits manual retry after failure', async () => {
  render(<TailorPage />);
  await analyzeSuccessfully();
  fireEvent.click(screen.getByRole('button', { name: 'Select pointer' }));
  const pending = deferred<ApplyTailorResponse>();
  mocks.apply.mockReturnValueOnce(pending.promise);
  act(() => {
    screen.getByTestId('tailor-apply').click();
    screen.getByTestId('tailor-apply').click();
  });
  expect(mocks.apply).toHaveBeenCalledTimes(1);
  await act(async () => pending.reject(new Error('Apply unavailable')));
  expect(mocks.toast).toHaveBeenLastCalledWith(expect.objectContaining({ title: 'Apply failed' }));
  expect(screen.getByRole('alert')).toHaveTextContent('Apply failed');
  expect(screen.getByTestId('tailor-apply')).not.toBeDisabled();
  mocks.apply.mockResolvedValueOnce(applied('retried'));
  fireEvent.click(screen.getByTestId('tailor-apply'));
  await waitFor(() => expect(screen.getByTestId('preview')).toHaveTextContent('retried'));
});

it.each([
  ['analysis', 'success'], ['analysis', 'failure'], ['apply', 'success'], ['apply', 'failure'],
])('ignores late %s %s after leaving the page', async (operation, outcome) => {
  const view = render(<TailorPage />);
  const pending = deferred<JDAnalyzeResponse | ApplyTailorResponse>();
  if (operation === 'analysis') {
    mocks.analyze.mockReturnValueOnce(pending.promise);
    fireEvent.click(screen.getByRole('button', { name: 'Analyze' }));
  } else {
    await analyzeSuccessfully();
    mocks.apply.mockReturnValueOnce(pending.promise);
    selectAndApply();
  }
  view.unmount();
  render(<TailorPage />);
  mocks.toast.mockClear();
  await act(async () => {
    if (outcome === 'failure') pending.reject(new Error('Late failure'));
    else pending.resolve(operation === 'analysis' ? analysis('old') : applied('old'));
  });
  expect(mocks.toast).not.toHaveBeenCalled();
  expect(screen.queryByTestId('suggestions')).not.toBeInTheDocument();
  expect(screen.queryByTestId('preview')).not.toBeInTheDocument();
});

it.each([
  [{ status: 402, message: 'Insufficient credits' }, 'Out of credits'],
  [{ status: 422, message: 'Rejected' }, 'Tailor rejected'],
  [null, 'Analyze failed'],
])('preserves existing analysis error handling and manual recovery: %s', async (error, title) => {
  render(<TailorPage />);
  mocks.analyze.mockRejectedValueOnce(error);
  fireEvent.click(screen.getByRole('button', { name: 'Analyze' }));
  await waitFor(() => expect(mocks.toast).toHaveBeenCalledWith(expect.objectContaining({ title })));
  expect(screen.getByRole('button', { name: 'Analyze' })).not.toBeDisabled();
  expect(screen.queryByTestId('tailor-apply')).not.toBeInTheDocument();
  expect(mocks.analyze).toHaveBeenCalledTimes(1);
  await analyzeSuccessfully();
});
