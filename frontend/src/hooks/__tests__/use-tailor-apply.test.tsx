import { describe, it, expect } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { server, http, HttpResponse } from '@/test-utils/msw-server';
import { useTailorApply } from '@/hooks/use-tailor-apply';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('useTailorApply', () => {
  it('posts to /jd/{id}/apply and returns response', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/jd/jd-123/apply', () => {
        return HttpResponse.json({
          version_id: 'ver-1',
          preview_html: '<html><body>x</body></html>',
          company_name: null,
          suggested_template: 'us-swe',
          filename_hint: 'resume-jd-123.pdf',
        });
      })
    );

    const { result } = renderHook(() => useTailorApply('jd-123'), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        accepted_changes: [
          { type: 'bullet_update', bullet_id: 'b1', new_text: 'Updated bullet' },
        ],
        template_id: 'us-swe',
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.version_id).toBe('ver-1');
    expect(result.current.data?.suggested_template).toBe('us-swe');
  });

  it('surfaces 4xx as error', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/jd/jd-bad/apply', () => {
        return HttpResponse.json({ detail: 'Bad request' }, { status: 400 });
      })
    );

    const { result } = renderHook(() => useTailorApply('jd-bad'), { wrapper });

    await act(async () => {
      try {
        await result.current.mutateAsync({
          accepted_changes: [],
          template_id: 'us-swe',
        });
      } catch {
        /* expected */
      }
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
