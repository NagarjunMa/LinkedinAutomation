/**
 * Task 22: ResumeUploadDropzone component tests
 *
 * Covers selection, validation, drag/drop, pending state, and upload recovery.
 *
 * useUploadResume is mocked so no network calls occur.
 * useToast is mocked to avoid Radix portal issues in jsdom.
 * QueryClientProvider is required because the component uses mutations under the hood.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

const { mutateAsync, toast, mutation } = vi.hoisted(() => ({
  mutateAsync: vi.fn(),
  toast: vi.fn(),
  mutation: { isPending: false },
}));

// The component boundary is mocked; hook/API tests exercise the actual request.
vi.mock('@/hooks/use-resume', () => ({
  useUploadResume: () => ({
    mutateAsync,
    isPending: mutation.isPending,
  }),
}));

// Mock useToast to avoid Radix portal issues in jsdom
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast }),
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
    mutateAsync.mockReset().mockResolvedValue({ resume_document_id: 'doc-001' });
    mutation.isPending = false;
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
    await waitFor(() => expect(handler).toHaveBeenCalledWith({ resume_document_id: 'doc-001' }));
    expect(mutateAsync).toHaveBeenCalledExactlyOnceWith(file);
    expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: 'Uploaded' }));
  });

  it.each([
    ['resume.txt', 10, 'Only PDF and DOCX files are supported'],
    ['resume.pdf', 10 * 1024 * 1024 + 1, 'File too large (max 10 MB)'],
  ])('rejects invalid file %s without starting an upload', (name, size, message) => {
    renderDropzone();
    const file = new File(['content'], name);
    Object.defineProperty(file, 'size', { value: size });
    fireEvent.drop(screen.getByTestId('resume-dropzone'), { dataTransfer: { files: [file] } });
    expect(toast).toHaveBeenCalledWith({ title: 'Invalid file', description: message, variant: 'destructive' });
    expect(screen.queryByRole('button', { name: /^Upload$/ })).not.toBeInTheDocument();
    expect(mutateAsync).not.toHaveBeenCalled();
  });

  it('accepts a case-insensitive DOCX at the size limit and allows removal', () => {
    renderDropzone();
    const file = new File(['content'], 'resume.DOCX');
    Object.defineProperty(file, 'size', { value: 10 * 1024 * 1024 });
    const zone = screen.getByTestId('resume-dropzone');
    fireEvent.dragOver(zone);
    expect(zone).toHaveClass('border-app-accent');
    fireEvent.dragLeave(zone);
    expect(zone).not.toHaveClass('border-app-accent');
    fireEvent.dragOver(zone);
    fireEvent.drop(zone, { dataTransfer: { files: [file] } });
    expect(zone).not.toHaveClass('border-app-accent');
    expect(screen.getByText('resume.DOCX')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Remove file' }));
    expect(screen.queryByText('resume.DOCX')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Choose file' })).toBeEnabled();
    expect(toast).not.toHaveBeenCalled();
    expect(mutateAsync).not.toHaveBeenCalled();
  });

  it('opens the file picker and safely handles cancelled selection and empty drops', () => {
    const { container } = renderDropzone();
    const input = container.querySelector('input')!;
    const click = vi.spyOn(input, 'click').mockImplementation(() => {});
    fireEvent.click(screen.getByRole('button', { name: 'Choose file' }));
    expect(click).toHaveBeenCalledOnce();
    fireEvent.change(input, { target: { files: [] } });
    fireEvent.drop(screen.getByTestId('resume-dropzone'), { dataTransfer: { files: [] } });
    expect(screen.queryByRole('button', { name: /^Upload$/ })).not.toBeInTheDocument();
    expect(toast).not.toHaveBeenCalled();
    expect(mutateAsync).not.toHaveBeenCalled();
    click.mockRestore();
  });

  it('disables submission while an upload is pending', () => {
    mutation.isPending = true;
    renderDropzone();
    fireEvent.drop(screen.getByTestId('resume-dropzone'), {
      dataTransfer: { files: [new File(['content'], 'resume.pdf')] },
    });
    const button = screen.getByRole('button', { name: 'Uploading…' });
    expect(button).toBeDisabled();
    fireEvent.click(button);
    expect(mutateAsync).not.toHaveBeenCalled();
  });

  it.each([new Error('Service unavailable'), null])('keeps the file available for retry after failure %s', async (error) => {
    mutateAsync.mockRejectedValueOnce(error);
    const onUploaded = vi.fn();
    renderDropzone({ onUploaded });
    const file = new File(['content'], 'resume.pdf');
    fireEvent.drop(screen.getByTestId('resume-dropzone'), { dataTransfer: { files: [file] } });
    fireEvent.click(screen.getByRole('button', { name: 'Upload' }));
    await waitFor(() => expect(toast).toHaveBeenCalledWith({
      title: 'Upload failed', description: error?.message ?? 'Try again', variant: 'destructive',
    }));
    expect(onUploaded).not.toHaveBeenCalled();
    expect(screen.getByText('resume.pdf')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Upload' }));
    await waitFor(() => expect(onUploaded).toHaveBeenCalledWith({ resume_document_id: 'doc-001' }));
    expect(mutateAsync).toHaveBeenNthCalledWith(2, file);
  });
});
