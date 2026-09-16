import { expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
vi.mock('@/components/landing/Navigation', () => ({ Navigation: () => null }));
vi.mock('@/contexts/theme-context', () => ({ useTheme: () => ({ isDark: false }) }));
import Documentation from '../page';

it('explains document limits and evidence-backed terminology without vendor or score promises', () => {
  const { container } = render(<Documentation />);
  for (const button of screen.getAllByRole('button', { expanded: false })) fireEvent.click(button);
  expect(screen.getByText(/not a replica of any ATS/)).toBeInTheDocument();
  expect(screen.getByText(/Only add job-description terms.*actual experience/)).toBeInTheDocument();
  expect(container).not.toHaveTextContent(/ATS readiness score|keyword density|trained against|Workday|Greenhouse|7-second/);
  expect(screen.getByRole('link', { name: 'Document checks' })).toHaveAttribute('href', '#ats-simulator');
  expect(screen.getByRole('button', { name: /Document checks/, expanded: true })).toBeInTheDocument();
});
