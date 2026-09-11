/**
 * Task 21: RewriteModal component tests
 *
 * Covers evidence placeholders, explicit acceptance, cancellation, and rejection.
 *
 * useRewriteBullet is mocked to return a pre-resolved mutation.
 * useToast is mocked to avoid Radix portal issues in jsdom.
 * QueryClientProvider is required because the component calls useMutation under the hood.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

const { mutate, toast, mutation } = vi.hoisted(() => ({
  mutate: vi.fn(), toast: vi.fn(), mutation: { isPending: false },
}));

vi.mock('@/hooks/use-resume', () => ({
  useRewriteBullet: () => ({
    mutate,
    isPending: mutation.isPending,
  }),
}));

// Mock useToast to avoid Radix portal issues in jsdom
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast }),
}));

import { RewriteModal } from '@/components/resume/rewrite-modal';
import type { Bullet, RewriteResult } from '@/app/lib/api';

const suggestion: RewriteResult = {
  rewritten: 'Reduced latency by [X%] across [N] services',
  placeholders: [
    { token: '[X%]', what: 'latency reduction percentage' },
    { token: '[N]', what: 'service count' },
  ],
  applied_changes: ['Added quantification placeholder', 'Improved action verb'],
};

const mockBullet: Bullet = { id: 'b1', text: 'Did stuff', raw_text: 'Did stuff' };

function makeClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
}

function renderModal(overrides: Partial<React.ComponentProps<typeof RewriteModal>> = {}) {
  const props: React.ComponentProps<typeof RewriteModal> = {
    open: true,
    onOpenChange: vi.fn(),
    resumeId: 'resume-001',
    bullet: mockBullet,
    targetRole: 'Software Engineer',
    country: 'US',
    onAccept: vi.fn(),
    ...overrides,
  };
  const client = makeClient();
  return render(
    <QueryClientProvider client={client}>
      <RewriteModal {...props} />
    </QueryClientProvider>
  );
}

describe('RewriteModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mutation.isPending = false;
    mutate.mockReset().mockImplementation((_args, { onSuccess }) => onSuccess(suggestion));
  });

  it('renders rewrite text returned by the mutation', async () => {
    renderModal();
    // The rewritten text (with unfilled placeholders) should be visible
    await waitFor(() => {
      expect(
        screen.getByText(/Reduced latency by \[X%\] across \[N\] services/)
      ).toBeInTheDocument();
    });
  });

  it('calls onAccept with bulletId when Accept button is clicked', async () => {
    const handler = vi.fn();
    renderModal({ onAccept: handler });

    // Wait for rewrite result to appear
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /accept/i })).not.toBeDisabled();
    });

    fireEvent.click(screen.getByRole('button', { name: /accept/i }));
    expect(handler).toHaveBeenCalledWith(
      'b1',
      expect.stringContaining('Reduced latency')
    );
  });

  it('sends the selected evidence context and accepts only the user-filled text', () => {
    const onAccept = vi.fn();
    const onOpenChange = vi.fn();
    renderModal({ onAccept, onOpenChange, jdContext: 'API performance' });
    expect(mutate).toHaveBeenCalledWith({
      resumeId: 'resume-001', bulletId: 'b1', targetRole: 'Software Engineer',
      country: 'US', jdContext: 'API performance',
    }, expect.objectContaining({ onSuccess: expect.any(Function), onError: expect.any(Function) }));
    expect(onAccept).not.toHaveBeenCalled();
    fireEvent.change(screen.getByTestId('placeholder-[X%]'), { target: { value: '25%' } });
    fireEvent.change(screen.getByTestId('placeholder-[N]'), { target: { value: '3' } });
    expect(screen.getByText('Reduced latency by 25% across 3 services')).toBeInTheDocument();
    expect(screen.getByText('Improved action verb')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Accept' }));
    expect(onAccept).toHaveBeenCalledExactlyOnceWith('b1', 'Reduced latency by 25% across 3 services');
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it('keeps Accept disabled while generating and permits cancellation without accepting', () => {
    mutation.isPending = true;
    mutate.mockImplementation(() => {});
    const onAccept = vi.fn();
    const onOpenChange = vi.fn();
    renderModal({ onAccept, onOpenChange });
    expect(screen.getByText('Rewriting…')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Accept' })).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: 'Accept' }));
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onAccept).not.toHaveBeenCalled();
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it.each([
    [{ status: 422 }, 'Rewrite rejected', 'AI tried to invent a number. Please try again.'],
    [new Error('Service unavailable'), 'Rewrite failed', 'Service unavailable'],
  ])('reports rejected requests without accepting a suggestion: %s', (error, title, description) => {
    mutate.mockImplementation((_args, { onError }) => onError(error));
    const onAccept = vi.fn();
    const onOpenChange = vi.fn();
    renderModal({ onAccept, onOpenChange });
    expect(toast).toHaveBeenCalledWith({ title, description, variant: 'destructive' });
    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(onAccept).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Accept' })).toBeDisabled();
  });

  it.each([{ open: false }, { bullet: null }])('does not request a rewrite without an open selected bullet: %s', (props) => {
    renderModal(props);
    expect(mutate).not.toHaveBeenCalled();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders a suggestion with no placeholders or change notes', () => {
    mutate.mockImplementation((_args, { onSuccess }) => onSuccess({
      rewritten: 'Built the reporting API', placeholders: [], applied_changes: [],
    }));
    renderModal();
    expect(screen.getByText('Built the reporting API')).toBeInTheDocument();
    expect(screen.queryByText('Fill in')).not.toBeInTheDocument();
    expect(screen.queryByRole('list')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Accept' })).toBeEnabled();
  });
});
