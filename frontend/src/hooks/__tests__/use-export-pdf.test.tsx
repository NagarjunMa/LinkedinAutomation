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
  });

  it('triggers download on success', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/exports', () => {
        return HttpResponse.json({
          export_id: 'exp-1',
          signed_url: 'https://example.com/file.pdf',
          filename: 'resume.pdf',
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
    expect(HTMLAnchorElement.prototype.click).toHaveBeenCalled();
  });

  it('surfaces 402 insufficient credits as error', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/exports', () => {
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
