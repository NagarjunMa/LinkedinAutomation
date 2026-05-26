/**
 * Task 22: ResumeUploadDropzone component tests
 *
 * 2 tests:
 * 1. renders upload affordance (PDF/DOCX copy + Choose file button)
 * 2. calls onUploaded after selecting a file and submitting (via mocked useUploadResume)
 *
 * useUploadResume is mocked so no network calls occur.
 * useToast is mocked to avoid Radix portal issues in jsdom.
 * QueryClientProvider is required because the component uses mutations under the hood.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// Mock useUploadResume so mutateAsync resolves immediately with a fake UploadResponse.
vi.mock('@/hooks/use-resume', () => ({
  useUploadResume: () => ({
    mutateAsync: vi.fn().mockResolvedValue({
      resume_document_id: 'doc-001',
      contact: { name: 'Test User', email: null, phone: null, links: [] },
      summary: null,
      experience: [],
      education: [],
      skills: { hard: [], soft: [] },
      projects: [],
      certifications: [],
      raw_text: '',
    }),
    isPending: false,
  }),
}));

// Mock useToast to avoid Radix portal issues in jsdom
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

import { ResumeUploadDropzone } from '@/components/resume/resume-upload-dropzone';

function makeClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
}

function renderDropzone(
  overrides: Partial<React.ComponentProps<typeof ResumeUploadDropzone>> = {}
) {
  const props: React.ComponentProps<typeof ResumeUploadDropzone> = {
    onUploaded: vi.fn(),
    ...overrides,
  };
  const client = makeClient();
  return render(
    <QueryClientProvider client={client}>
      <ResumeUploadDropzone {...props} />
    </QueryClientProvider>
  );
}

describe('ResumeUploadDropzone', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders upload affordance with PDF / DOCX copy', () => {
    renderDropzone();
    // The drag instruction text explicitly mentions "PDF or DOCX"
    expect(screen.getByText(/PDF or DOCX/i)).toBeInTheDocument();
    // "Choose file" button should be visible
    expect(screen.getByRole('button', { name: /choose file/i })).toBeInTheDocument();
  });

  it('calls onUploaded after selecting a valid file and clicking Upload', async () => {
    const handler = vi.fn();
    renderDropzone({ onUploaded: handler });

    // Pick a file via the hidden file input
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toBeTruthy();

    const file = new File(['resume content'], 'resume.pdf', { type: 'application/pdf' });
    fireEvent.change(input, { target: { files: [file] } });

    // After picking a file the Upload button should appear
    const uploadBtn = await screen.findByRole('button', { name: /^upload$/i });
    fireEvent.click(uploadBtn);

    // mutateAsync resolves, then onUploaded should have been called
    await vi.waitFor(() => expect(handler).toHaveBeenCalled());
  });
});
