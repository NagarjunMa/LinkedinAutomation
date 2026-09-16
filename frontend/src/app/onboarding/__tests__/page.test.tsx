import { expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
const mocks = vi.hoisted(() => ({ user: { user_metadata: { full_name: 'Synthetic Person' } }, router: { push: vi.fn() } }));
vi.mock('@/contexts/auth-context', () => ({ useAuth: () => ({ user: mocks.user, refreshUser: vi.fn() }) }));
vi.mock('next/navigation', () => ({ useRouter: () => mocks.router }));
vi.mock('@/lib/supabase', () => ({ createClient: vi.fn() }));
import OnboardingPage from '../page';

it('keeps step navigation while explaining factual limits instead of keyword-density or ATS-score promises', () => {
  const { container } = render(<OnboardingPage />);
  fireEvent.click(screen.getByRole('button', { name: 'Next' }));
  expect(screen.getByText(/does not predict employer screening rules/)).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Target Role *'), { target: { value: 'Engineer' } });
  fireEvent.click(screen.getByRole('button', { name: 'Next' }));
  expect(screen.getByText(/does not establish skills or seniority/)).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Degree *'), { target: { value: 'Computer Science' } });
  fireEvent.change(screen.getByLabelText('Institution *'), { target: { value: 'Synthetic University' } });
  fireEvent.click(screen.getByRole('button', { name: 'Next' }));
  expect(screen.getByText(/Accept only suggestions supported by your actual experience/)).toBeInTheDocument();
  expect(container).not.toHaveTextContent(/ATS score|keyword density/);
  fireEvent.click(screen.getByRole('button', { name: 'Back' }));
  expect(screen.getByLabelText('Degree *')).toHaveValue('Computer Science');
});
