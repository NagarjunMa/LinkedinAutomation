import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { server, http, HttpResponse } from '@/test-utils/msw-server';
import { useExportPdf } from '@/hooks/use-export-pdf';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('useExportPdf', () => {
  beforeEach(() => {
    // Reset the anchor click spy before each test
    HTMLAnchorElement.prototype.click = vi.fn();
    URL.createObjectURL = vi.fn(() => 'blob:test-export');
    URL.revokeObjectURL = vi.fn();
  });

  it('triggers blob download on success', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/tailored-resumes/ver-1/download', async ({ request }) => {
        const body = await request.json() as Record<string, unknown>;
        expect(body.template_id).toBe('us-swe');
        expect(body.filename).toBe('resume');
        return new HttpResponse('%PDF-test', {
          headers: { 'Content-Type': 'application/pdf' },
        });
      })
    );

    const { result } = renderHook(() => useExportPdf(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        resume_version_id: 'ver-1',
        template_id: 'us-swe',
        filename: 'resume',
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(URL.createObjectURL).toHaveBeenCalled();
    expect(HTMLAnchorElement.prototype.click).toHaveBeenCalled();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:test-export');
  });

  it('surfaces 402 insufficient credits as error', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/tailored-resumes/v/download', () => {
        return HttpResponse.json({ detail: 'Insufficient credits' }, { status: 402 });
      })
    );

    const { result } = renderHook(() => useExportPdf(), { wrapper });

    await act(async () => {
      try {
        await result.current.mutateAsync({
          resume_version_id: 'v',
          template_id: 'us-swe',
        });
      } catch {
        /* expected */
      }
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
