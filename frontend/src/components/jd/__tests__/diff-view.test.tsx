/**
 * Task 20: DiffView component tests
 *
 * 3 tests:
 * 1. renders bullet diffs (old + new text visible via ChangeCard)
 * 2. calls onAcceptedChangesChange when a bullet checkbox is toggled
 * 3. renders match score via JdAnalysisPanel (companion component — DiffView
 *    itself does not display match_score; the score lives in JdAnalysisPanel
 *    which receives the same DiffPlan prop)
 *
 * Note on actual prop/callback names:
 *   - Prop is `plan` (DiffPlan), not `diffPlan`
 *   - Required props: resumeId (string), plan (DiffPlan), onApplied (fn)
 *   - Optional callback: onAcceptedChangesChange (ChangeItem[]) => void
 *   - Accept controls are checkboxes (aria-label="Accept change"), not buttons
 *   - When onAcceptedChangesChange is provided the internal Apply button is hidden
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { server, http, HttpResponse } from '@/test-utils/msw-server';
import type { DiffPlan } from '@/app/lib/api';

// Mock hooks to avoid network calls and Radix portal issues
vi.mock('@/hooks/use-resume', () => ({
  useCreateVersion: () => ({
    mutateAsync: vi.fn().mockResolvedValue({ version_id: 'ver-001' }),
    isPending: false,
  }),
}));

vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

import { DiffView } from '../diff-view';
import { JdAnalysisPanel } from '../jd-analysis-panel';

// -----------------------------------------------------------------------
// Shared test data
// -----------------------------------------------------------------------

const mockPlan: DiffPlan = {
  match_score: 75,
  bullets: [
    {
      bullet_id: 'b1',
      old: 'Did stuff',
      new: 'Shipped Python services',
      reason: 'JD wants Python',
      placeholders: [],
      options: [
        { option_id: 'conservative', text: 'Shipped Python services', reason: 'Safe', placeholders: [] },
        { option_id: 'impact', text: 'Shipped Python services with measurable impact', reason: 'Impact', placeholders: [] },
        { option_id: 'keyword', text: 'Built Python backend services', reason: 'Keyword', placeholders: [] },
      ],
    },
    {
      bullet_id: 'b2',
      old: 'Worked on UI',
      new: 'Built React dashboards',
      reason: 'JD wants React',
      placeholders: [],
      options: [
        { option_id: 'conservative', text: 'Built React dashboards', reason: 'Safe', placeholders: [] },
        { option_id: 'impact', text: 'Built React dashboards for operational visibility', reason: 'Impact', placeholders: [] },
        { option_id: 'keyword', text: 'Developed React frontend dashboards', reason: 'Keyword', placeholders: [] },
      ],
    },
  ],
  summary_rewrite: { old: 'Old summary', new: 'New summary', reason: 'tone' },
  skills_reorder: null,
  must_have_coverage_found: ['Python'],
  must_have_coverage_missing: ['Go'],
  good_to_have_coverage_found: [],
  good_to_have_coverage_missing: [],
  suggested_additions: [],
  content_budget: {
    source_page_estimate: 1.1,
    target_max_pages: 1,
    recommended_bullet_budget: 12,
    current_bullet_count: 14,
    page_fit_risk: 'medium',
    guidance: 'Keep only the strongest JD-matched bullets.',
  },
  bullet_fit: [
    {
      bullet_id: 'b1',
      relevance_score: 82,
      evidence_level: 'high',
      recommendation: 'keep',
      matched_requirements: ['Python'],
      noise_flags: [],
      rationale: 'Strong overlap with this JD.',
    },
    {
      bullet_id: 'b2',
      relevance_score: 38,
      evidence_level: 'low',
      recommendation: 'consider_trim',
      matched_requirements: [],
      noise_flags: ['no_jd_requirement_match'],
      rationale: 'Limited JD overlap.',
    },
  ],
};

const mockExtraction = {
  primary_role_category: 'SWE',
  seniority: 'Senior',
  country_hint: 'USA',
  must_have_skills: ['Python'],
  good_to_have_skills: ['Go'],
  red_flags: [],
  jd_summary: 'Backend engineer role.',
};

function makeClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
}

function renderDiffView(overrides: Partial<React.ComponentProps<typeof DiffView>> = {}) {
  const props = {
    resumeId: 'resume-abc',
    plan: mockPlan,
    onApplied: vi.fn(),
    onAcceptedChangesChange: vi.fn(),
    ...overrides,
  };
  const client = makeClient();
  return render(
    <QueryClientProvider client={client}>
      <DiffView {...props} />
    </QueryClientProvider>
  );
}

// -----------------------------------------------------------------------
// Tests
// -----------------------------------------------------------------------

describe('DiffView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all bullet diffs', () => {
    renderDiffView();
    expect(screen.getByDisplayValue('Shipped Python services')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Built React dashboards')).toBeInTheDocument();
    expect(screen.getByText(/Resume fit target: 1 page/i)).toBeInTheDocument();
    expect(screen.getByText(/keep · 82/i)).toBeInTheDocument();
    expect(screen.getByText(/consider trim · 38/i)).toBeInTheDocument();
    expect(screen.getByTestId('one-page-guardrail')).toHaveTextContent(/low-fit pointer is still selected/i);
  });

  it('calls onAcceptedChangesChange when a bullet checkbox is toggled', () => {
    const handler = vi.fn();
    renderDiffView({ onAcceptedChangesChange: handler });

    // Both bullets start checked (default). Uncheck the first bullet.
    const checkboxes = screen.getAllByRole('checkbox', { name: /accept change/i });
    fireEvent.click(checkboxes[0]);

    // handler is called on mount (useEffect) and again after toggle
    expect(handler).toHaveBeenCalled();
    // After unchecking bullet b1, the changeset should only include b2
    const lastCall = handler.mock.calls[handler.mock.calls.length - 1][0] as Array<{ bullet_id?: string }>;
    expect(lastCall.some((c: { bullet_id?: string }) => c.bullet_id === 'b1')).toBe(false);
    expect(lastCall.some((c: { bullet_id?: string }) => c.bullet_id === 'b2')).toBe(true);
  });

  it('uses edited pointer text in accepted changes', () => {
    const handler = vi.fn();
    renderDiffView({ onAcceptedChangesChange: handler });

    const pointerText = screen.getByDisplayValue('Shipped Python services');
    fireEvent.change(pointerText, { target: { value: 'Edited Python pointer' } });

    const lastCall = handler.mock.calls[handler.mock.calls.length - 1][0] as Array<{ bullet_id?: string; new_text?: string }>;
    expect(lastCall.find((c) => c.bullet_id === 'b1')?.new_text).toBe('Edited Python pointer');
  });

  it('supports clear all and option selection', () => {
    const handler = vi.fn();
    renderDiffView({ onAcceptedChangesChange: handler });

    fireEvent.change(screen.getAllByLabelText('Pointer option')[0], {
      target: { value: 'impact' },
    });
    let lastCall = handler.mock.calls[handler.mock.calls.length - 1][0] as Array<{ bullet_id?: string; new_text?: string }>;
    expect(lastCall.find((c) => c.bullet_id === 'b1')?.new_text).toBe('Shipped Python services with measurable impact');

    fireEvent.click(screen.getByRole('button', { name: /clear all/i }));
    lastCall = handler.mock.calls[handler.mock.calls.length - 1][0] as Array<{ bullet_id?: string }>;
    expect(lastCall.some((c) => c.bullet_id === 'b1')).toBe(false);
    expect(lastCall.some((c) => c.bullet_id === 'b2')).toBe(false);
  });

  it('selects recommended pointers and trims low-fit changes', () => {
    const handler = vi.fn();
    renderDiffView({ onAcceptedChangesChange: handler });

    fireEvent.click(screen.getByRole('button', { name: /recommended/i }));

    const lastCall = handler.mock.calls[handler.mock.calls.length - 1][0] as Array<{ bullet_id?: string; type: string }>;
    expect(lastCall.some((c) => c.bullet_id === 'b1')).toBe(true);
    expect(lastCall.some((c) => c.bullet_id === 'b2')).toBe(false);
    expect(lastCall.some((c) => c.type === 'summary_update')).toBe(true);
    expect(screen.getByTestId('one-page-guardrail')).toHaveTextContent(/starts above the one-page bullet budget/i);
  });

  it('selects only high-fit bullet rewrites for one-page tightening', () => {
    const handler = vi.fn();
    renderDiffView({ onAcceptedChangesChange: handler });

    fireEvent.click(screen.getByRole('button', { name: /high fit only/i }));

    const lastCall = handler.mock.calls[handler.mock.calls.length - 1][0] as Array<{ bullet_id?: string; type: string }>;
    expect(lastCall).toHaveLength(1);
    expect(lastCall[0]).toMatchObject({ type: 'bullet_update', bullet_id: 'b1' });
  });

  it('resets all pointer selections and edited text', () => {
    const handler = vi.fn();
    renderDiffView({ onAcceptedChangesChange: handler });

    fireEvent.change(screen.getAllByLabelText('Pointer option')[0], {
      target: { value: 'impact' },
    });
    fireEvent.change(screen.getByDisplayValue('Shipped Python services with measurable impact'), {
      target: { value: 'Edited impact pointer' },
    });
    fireEvent.click(screen.getByRole('button', { name: /clear all/i }));
    fireEvent.click(screen.getByRole('button', { name: /reset all/i }));

    expect(screen.getByDisplayValue('Shipped Python services')).toBeInTheDocument();
    const lastCall = handler.mock.calls[handler.mock.calls.length - 1][0] as Array<{ bullet_id?: string; new_text?: string }>;
    expect(lastCall.find((c) => c.bullet_id === 'b1')?.new_text).toBe('Shipped Python services');
    expect(lastCall.some((c) => c.bullet_id === 'b2')).toBe(true);
  });

  it('regenerates options for a single pointer', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/jd/jd-1/bullets/b1/options', () => {
        return HttpResponse.json({
          bullet_id: 'b1',
          old: 'Did stuff',
          new: 'Regenerated Python pointer',
          reason: 'Regenerated',
          placeholders: [],
          options: [
            { option_id: 'conservative', text: 'Regenerated Python pointer', reason: 'Safe', placeholders: [] },
            { option_id: 'impact', text: 'Regenerated impact pointer', reason: 'Impact', placeholders: [] },
            { option_id: 'keyword', text: 'Regenerated keyword pointer', reason: 'Keyword', placeholders: [] },
          ],
        });
      })
    );
    renderDiffView({ jdEvaluationId: 'jd-1' });

    fireEvent.click(screen.getAllByRole('button', { name: /regenerate pointer/i })[0]);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Regenerated Python pointer')).toBeInTheDocument();
    });
  });

  it('keeps the existing pointer text when regeneration fails', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/jd/jd-1/bullets/b1/options', () => {
        return HttpResponse.json({ detail: 'LLM unavailable' }, { status: 503 });
      })
    );
    renderDiffView({ jdEvaluationId: 'jd-1' });

    fireEvent.click(screen.getAllByRole('button', { name: /regenerate pointer/i })[0]);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Shipped Python services')).toBeInTheDocument();
    });
  });

  it('applies selected changes when the internal apply button is visible', async () => {
    const onApplied = vi.fn();
    renderDiffView({ onAcceptedChangesChange: undefined, onApplied });

    fireEvent.click(screen.getByTestId('apply-changes'));

    await waitFor(() => {
      expect(onApplied).toHaveBeenCalledWith('ver-001');
    });
  });

  it('renders match score via JdAnalysisPanel', () => {
    // DiffView does not display match_score directly; the score is shown by
    // the companion JdAnalysisPanel component that receives the same DiffPlan.
    render(
      <JdAnalysisPanel
        extraction={mockExtraction as any}
        plan={mockPlan}
      />
    );
    // match_score of 75 is rendered inside [data-testid="match-score"]
    expect(screen.getByTestId('match-score')).toHaveTextContent('75');
  });
});
