/**
 * Task 14: PreviewPanel component tests
 *
 * 4 tests:
 * 1. iframe renders provided HTML (srcDoc)
 * 2. fallback message shown when previewHtml is empty
 * 3. filename input is editable
 * 4. Download button is enabled when not pending
 *
 * useExportPdf is mocked so no network calls occur.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// Mock useExportPdf so tests never hit the network
vi.mock('@/hooks/use-export-pdf', () => ({
  useExportPdf: () => ({
    mutateAsync: vi.fn().mockResolvedValue({
      export_id: 'test-export-id',
      signed_url: 'https://example.com/file.pdf',
      filename: 'test.pdf',
    }),
    isPending: false,
  }),
}));

// Mock useToast to avoid Radix portal issues in jsdom
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

import { PreviewPanel } from '../preview-panel';

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
});
