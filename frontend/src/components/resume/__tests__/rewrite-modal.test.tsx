/**
 * Task 21: RewriteModal component tests
 *
 * 2 tests:
 * 1. renders rewrite text when mutation resolves
 * 2. calls onAccept with bulletId + filled text when Accept button clicked
 *
 * useRewriteBullet is mocked to return a pre-resolved mutation.
 * useToast is mocked to avoid Radix portal issues in jsdom.
 * QueryClientProvider is required because the component calls useMutation under the hood.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// Mock useRewriteBullet so no network calls occur.
// mutate calls onSuccess synchronously with mock data.
vi.mock('@/hooks/use-resume', () => ({
  useRewriteBullet: () => ({
    mutate: vi.fn((_args: unknown, { onSuccess }: { onSuccess: (data: unknown) => void }) => {
      onSuccess({
        rewritten: 'Reduced latency by [X%] across [N] services',
        placeholders: [
          { token: '[X%]', what: 'latency reduction percentage' },
          { token: '[N]', what: 'service count' },
        ],
        applied_changes: ['Added quantification placeholder', 'Improved action verb'],
      });
    }),
    isPending: false,
  }),
}));

// Mock useToast to avoid Radix portal issues in jsdom
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

import { RewriteModal } from '@/components/resume/rewrite-modal';
import type { Bullet } from '@/app/lib/api';

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
});
