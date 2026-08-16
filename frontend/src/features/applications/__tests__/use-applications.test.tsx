import type { ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { fetchJobDetails, fetchRecentApplications } = vi.hoisted(() => ({
  fetchJobDetails: vi.fn(),
  fetchRecentApplications: vi.fn(),
}));

vi.mock('@/app/lib/api/jobs', () => ({ fetchJobDetails, fetchRecentApplications }));

import { useApplicationDetails, useApplications } from '../use-applications';

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe('applications queries', () => {
  beforeEach(() => vi.clearAllMocks());

  it('loads and maps the authenticated recent applications query', async () => {
    fetchRecentApplications.mockResolvedValue([{
      id: 'job-1',
      title: 'Backend Engineer',
      company: 'Acme',
      appliedAt: '2026-08-15T00:00:00Z',
      extracted_date: '2026-08-15T00:00:00Z',
      status: 'Applied',
    }]);

    const { result } = renderHook(() => useApplications(25), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(fetchRecentApplications).toHaveBeenCalledWith(25);
    expect(result.current.data?.[0]).toMatchObject({ id: 'job-1', status: 'applied' });
  });

  it('does not request job details until a job is selected', () => {
    renderHook(() => useApplicationDetails(null), { wrapper });
    expect(fetchJobDetails).not.toHaveBeenCalled();
  });

  it('loads selected job details through the canonical jobs API', async () => {
    fetchJobDetails.mockResolvedValue({
      id: 10,
      title: 'AI Engineer',
      company: 'Acme',
      skills: ['Python'],
    });

    const { result } = renderHook(() => useApplicationDetails('10'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(fetchJobDetails).toHaveBeenCalledWith('10');
    expect(result.current.data).toMatchObject({ id: '10', title: 'AI Engineer' });
  });
});
