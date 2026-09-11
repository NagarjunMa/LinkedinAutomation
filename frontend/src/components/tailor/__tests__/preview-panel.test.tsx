/**
 * Task 14: PreviewPanel component tests
 *
 * Covers preview rendering, download inputs, and recoverable export failures.
 *
 * useExportPdf is mocked so no network calls occur.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

const { mutateAsync, toast, mutation } = vi.hoisted(() => ({
  mutateAsync: vi.fn(), toast: vi.fn(), mutation: { isPending: false },
}));

vi.mock('@/hooks/use-export-pdf', () => ({
  useExportPdf: () => ({
    mutateAsync,
    isPending: mutation.isPending,
  }),
}));

// Mock useToast to avoid Radix portal issues in jsdom
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast }),
}));

import { PreviewPanel } from '../preview-panel';
import { APIError } from '@/app/lib/api/config';

function makeClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
}

function renderPanel(overrides: Partial<React.ComponentProps<typeof PreviewPanel>> = {}) {
  const props = {
    versionId: 'v-001',
    previewHtml: '<p>Hello</p>',
    suggestedTemplate: 'us-swe',
    filenameHint: 'john-doe-acme.pdf',
    ...overrides,
  };
  const client = makeClient();
  return render(
    <QueryClientProvider client={client}>
      <PreviewPanel {...props} />
    </QueryClientProvider>
  );
}

describe('PreviewPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mutateAsync.mockReset().mockResolvedValue({});
    mutation.isPending = false;
  });

  it('renders an iframe with srcDoc when previewHtml is provided', () => {
    renderPanel({ previewHtml: '<p>Resume content</p>' });
    const iframe = screen.getByTitle('Resume preview') as HTMLIFrameElement;
    expect(iframe).toBeInTheDocument();
    expect(iframe.getAttribute('srcdoc')).toContain('<p>Resume content</p>');
    expect(iframe.getAttribute('srcdoc')).toContain('data-prism-preview-page');
    expect(screen.getByText('Letter')).toBeInTheDocument();
  });

  it('shows A4 label for India templates', () => {
    renderPanel({ suggestedTemplate: 'in-swe' });
    expect(screen.getByText('A4')).toBeInTheDocument();
  });

  it('shows fallback message when previewHtml is empty', () => {
    renderPanel({ previewHtml: '' });
    expect(screen.queryByTitle('Resume preview')).not.toBeInTheDocument();
    expect(
      screen.getByText('Apply changes to see preview')
    ).toBeInTheDocument();
  });

  it('shows custom warning when previewHtml is empty and warning is provided', () => {
    renderPanel({ previewHtml: '', warning: 'Preview render failed: timeout' });
    expect(
      screen.getByText('Preview render failed: timeout')
    ).toBeInTheDocument();
  });

  it('filename input is editable', () => {
    renderPanel({ filenameHint: 'original-name.pdf' });
    const input = screen.getByPlaceholderText(
      'firstname-lastname-company.pdf'
    ) as HTMLInputElement;
    expect(input).toBeInTheDocument();
    expect(input.value).toBe('original-name.pdf');

    fireEvent.change(input, { target: { value: 'updated-name.pdf' } });
    expect(input.value).toBe('updated-name.pdf');
  });

  it('Download PDF button is enabled when not pending', () => {
    renderPanel();
    const button = screen.getByRole('button', { name: /Download PDF/i });
    expect(button).toBeInTheDocument();
    expect(button).not.toBeDisabled();
  });

  it('inserts page styles into an existing head without removing preview content', () => {
    renderPanel({ previewHtml: '<html><head><title>Resume</title></head><body>Experience</body></html>' });
    const iframe = screen.getByTitle('Resume preview');
    expect(iframe.getAttribute('srcdoc')).toContain('</style></head><body>Experience</body>');
    expect(iframe.getAttribute('srcdoc')).toContain('<title>Resume</title>');
    expect(iframe).toHaveAttribute('sandbox', 'allow-same-origin');
  });

  it('downloads the selected version/template with the edited filename', async () => {
    renderPanel({ suggestedTemplate: 'in-swe' });
    fireEvent.change(screen.getByPlaceholderText('firstname-lastname-company.pdf'), {
      target: { value: 'my-resume.pdf' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Download PDF' }));
    await waitFor(() => expect(toast).toHaveBeenCalledWith({ title: 'Downloaded', description: 'my-resume.pdf' }));
    expect(mutateAsync).toHaveBeenCalledExactlyOnceWith({
      resume_version_id: 'v-001', template_id: 'in-swe', filename: 'my-resume.pdf',
    });
  });

  it('prevents repeat downloads while generating', () => {
    mutation.isPending = true;
    renderPanel();
    const button = screen.getByRole('button', { name: 'Generating PDF…' });
    expect(button).toBeDisabled();
    fireEvent.click(button);
    expect(mutateAsync).not.toHaveBeenCalled();
  });

  it.each([
    [new APIError('Payment required', 402), 'Need more credits', 'Credits refresh monthly during the freemium launch.'],
    [new Error('Insufficient CREDITS'), 'Need more credits', 'Credits refresh monthly during the freemium launch.'],
    [new APIError('Preview unavailable', 503), 'Export failed', 'Preview unavailable'],
    [new Error('Network unavailable'), 'Export failed', 'Network unavailable'],
    [null, 'Export failed', 'Export failed'],
  ])('shows an actionable export failure and permits retry: %s', async (error, title, description) => {
    mutateAsync.mockRejectedValueOnce(error);
    renderPanel();
    fireEvent.click(screen.getByRole('button', { name: 'Download PDF' }));
    await waitFor(() => expect(toast).toHaveBeenCalledExactlyOnceWith({ title, description, variant: 'destructive' }));
    expect(screen.getByTitle('Resume preview')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Download PDF' }));
    await waitFor(() => expect(toast).toHaveBeenCalledWith({ title: 'Downloaded', description: 'john-doe-acme.pdf' }));
    expect(mutateAsync).toHaveBeenCalledTimes(2);
  });
});
