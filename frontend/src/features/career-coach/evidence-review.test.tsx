import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Evidence } from './api';
import { EvidenceReview } from './evidence-review';

const proposal: Evidence = {
  schema_version: 1, evidence_id: 'proposal', owner_id: 'owner', revision: 3,
  lifecycle: 'proposed', category: 'action', ownership: 'individual', support: 'candidate_statement',
  claim: 'Built the scheduler.', sources: [{
    source_id: 'note', source_version: 7, relationship: 'supports', locator: 'Project note',
    excerpt: 'Built the scheduler.', extraction: 'candidate',
  }],
};

describe('Evidence review', () => {
  it.each([
    ['Confirm', 'confirm'], ['Reject', 'reject'],
    ['Mark private', 'mark_private'], ['Mark unavailable', 'mark_unavailable'],
  ])('sends %s against the displayed revision without changing the local decision', (label, action) => {
    const decide = vi.fn();
    render(<EvidenceReview items={[proposal]} busy={false} decide={decide} />);
    fireEvent.click(screen.getByRole('button', { name: label }));
    expect(decide).toHaveBeenCalledExactlyOnceWith(proposal, action);
    expect(screen.getByText('proposed')).toBeVisible();
  });

  it('saves edited text as a separate decision and removes actions from a private item', () => {
    const decide = vi.fn();
    const { rerender } = render(<EvidenceReview items={[proposal]} busy={false} decide={decide} />);
    fireEvent.click(screen.getByRole('button', { name: 'Edit' }));
    expect(screen.getByRole('button', { name: 'Save edit' })).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Edit claim'), { target: { value: '  Implemented the scheduler.  ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save edit' }));
    expect(decide).toHaveBeenCalledExactlyOnceWith(proposal, 'edit', 'Implemented the scheduler.');
    rerender(<EvidenceReview items={[{ ...proposal, revision: 4, lifecycle: 'private', is_private: true }]} busy={false} decide={decide} />);
    expect(screen.queryByRole('button', { name: 'Confirm' })).not.toBeInTheDocument();
  });
});
