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
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
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
    },
    {
      bullet_id: 'b2',
      old: 'Worked on UI',
      new: 'Built React dashboards',
      reason: 'JD wants React',
      placeholders: [],
    },
  ],
  summary_rewrite: { old: 'Old summary', new: 'New summary', reason: 'tone' },
  skills_reorder: null,
  must_have_coverage_found: ['Python'],
  must_have_coverage_missing: ['Go'],
  good_to_have_coverage_found: [],
  good_to_have_coverage_missing: [],
  suggested_additions: [],
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
    // ChangeCard renders the `after` prop in an emerald-highlighted paragraph
    expect(screen.getByText('Shipped Python services')).toBeInTheDocument();
    expect(screen.getByText('Built React dashboards')).toBeInTheDocument();
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
