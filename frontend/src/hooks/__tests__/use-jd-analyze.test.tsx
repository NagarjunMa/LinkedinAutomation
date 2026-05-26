import { describe, it, expect } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { server, http, HttpResponse } from '@/test-utils/msw-server';
import { useJdAnalyze } from '@/hooks/use-jd-analyze';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('useJdAnalyze', () => {
  it('posts to /jd/analyze and returns diff plan', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/jd/analyze', () => {
        return HttpResponse.json({
          jd_evaluation_id: 'jd-1',
          extracted_requirements: {
            must_have: [],
            good_to_have: [],
            soft_skills: [],
            seniority: 'mid',
            primary_role_category: 'SWE',
            country_hint: 'US',
            red_flags: [],
          },
          diff_plan: {
            match_score: 80,
            must_have_coverage_found: [],
            must_have_coverage_missing: [],
            good_to_have_coverage_found: [],
            good_to_have_coverage_missing: [],
            bullets: [],
            skills_reorder: null,
            summary_rewrite: null,
            suggested_additions: [],
          },
        });
      })
    );

    const { result } = renderHook(() => useJdAnalyze(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        resumeDocumentId: 'r-1',
        jdText: 'We are looking for a senior software engineer...',
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.jd_evaluation_id).toBe('jd-1');
    expect(result.current.data?.diff_plan.match_score).toBe(80);
  });
});
