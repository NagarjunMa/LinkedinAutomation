import { describe, it, expect } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { server, http, HttpResponse } from '@/test-utils/msw-server';
import { useUploadResume, useEvaluateResume } from '@/hooks/use-resume';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('useUploadResume', () => {
  it('posts FormData and returns parsed resume on success', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/resumes/upload', () => {
        return HttpResponse.json({
          resume_id: 'r-1',
          resume_document_id: 'r-1',
          parsed: { contact: { name: 'Alice' } },
          filename: 'resume.pdf',
        });
      })
    );

    const { result } = renderHook(() => useUploadResume(), { wrapper });

    const file = new File(['resume content'], 'resume.pdf', { type: 'application/pdf' });

    await act(async () => {
      await result.current.mutateAsync(file);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.resume_document_id).toBe('r-1');
  });

  it('surfaces upload errors as mutation error', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/resumes/upload', () => {
        return HttpResponse.json({ detail: 'Unsupported file type' }, { status: 422 });
      })
    );

    const { result } = renderHook(() => useUploadResume(), { wrapper });

    const file = new File(['bad'], 'bad.txt', { type: 'text/plain' });

    await act(async () => {
      try {
        await result.current.mutateAsync(file);
      } catch {
        /* expected */
      }
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useEvaluateResume', () => {
  it('posts to /resumes/{id}/evaluate and returns evaluation result', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/resumes/r-1/evaluate', () => {
        return HttpResponse.json({
          evaluation_id: 'e-1',
          overall_score: 75,
          readiness_label: 'minor_edits',
          score_breakdown: {
            content_quality: 76,
            role_fit: 72,
            evidence_strength: 70,
            recruiter_readability: 82,
          },
          score_explanation: [],
          top_actions_before_applying: [],
          parser_confidence: 'high',
          bullet_flags: [],
          format_issues: [],
          summary_critique: null,
          ats_parseability: 88,
          ats_raw_text: 'raw',
        });
      })
    );

    const { result } = renderHook(() => useEvaluateResume(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ resumeId: 'r-1', targetRole: 'Software Engineer' });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.evaluation_id).toBe('e-1');
    expect(result.current.data?.overall_score).toBe(75);
  });

  it('surfaces 402 insufficient credits as error', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/resumes/r-2/evaluate', () => {
        return HttpResponse.json({ detail: 'Insufficient credits' }, { status: 402 });
      })
    );

    const { result } = renderHook(() => useEvaluateResume(), { wrapper });

    await act(async () => {
      try {
        await result.current.mutateAsync({ resumeId: 'r-2', targetRole: 'PM' });
      } catch {
        /* expected */
      }
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
