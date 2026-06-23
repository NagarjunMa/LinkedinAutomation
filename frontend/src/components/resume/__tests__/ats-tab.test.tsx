/**
 * Task 22: AtsTab component tests
 *
 * 2 tests:
 * 1. shows parseability score from evaluation.ats_parseability
 * 2. renders format issues (type + location) when present
 *
 * AtsTab accepts a single `evaluation` prop of type EvaluationResponse.
 * FormatIssue shape: { type, location, fix_hint } — mirrors backend schema.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AtsTab } from '@/components/resume/ats-tab';
import type { EvaluationResponse } from '@/app/lib/api';

function makeEvaluation(
  overrides: Partial<EvaluationResponse> = {}
): EvaluationResponse {
  return {
    evaluation_id: 'eval-001',
    overall_score: 80,
    readiness_label: 'minor_edits',
    score_breakdown: {
      content_quality: 80,
      role_fit: 80,
      evidence_strength: 80,
      recruiter_readability: 80,
    },
    score_explanation: [],
    top_actions_before_applying: [],
    parser_confidence: 'high',
    bullet_flags: [],
    format_issues: [],
    summary_critique: null,
    ats_parseability: 85,
    ats_raw_text: 'NAME\nEMAIL\nEXPERIENCE...',
    ...overrides,
  };
}

describe('AtsTab', () => {
  it('shows parseability score', () => {
    const evaluation = makeEvaluation({ ats_parseability: 85 });
    render(<AtsTab evaluation={evaluation} />);
    // Score is rendered as a bare number (e.g. "85")
    expect(screen.getByText(/85/)).toBeInTheDocument();
  });

  it('renders format issues when present', () => {
    const evaluation = makeEvaluation({
      ats_parseability: 60,
      ats_raw_text: 'x',
      format_issues: [
        {
          type: 'multi-column layout',
          location: 'skills section',
          fix_hint: 'Use a single-column layout for ATS compatibility.',
        },
      ],
    });
    render(<AtsTab evaluation={evaluation} />);
    expect(screen.getByText(/multi-column/i)).toBeInTheDocument();
  });
});
