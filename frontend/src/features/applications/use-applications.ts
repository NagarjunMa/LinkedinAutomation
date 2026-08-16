'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchJobDetails, fetchRecentApplications } from '@/app/lib/api/jobs';
import { mapJobDetails, mapRecentApplication } from './model';

export const applicationQueryKeys = {
  all: ['applications'] as const,
  recent: (limit: number) => [...applicationQueryKeys.all, 'recent', limit] as const,
  detail: (jobId: string | null) => [...applicationQueryKeys.all, 'detail', jobId] as const,
};

export function useApplications(limit = 50) {
  return useQuery({
    queryKey: applicationQueryKeys.recent(limit),
    queryFn: () => fetchRecentApplications(limit),
    select: (applications) => applications.map(mapRecentApplication),
  });
}

export function useApplicationDetails(jobId: string | null) {
  return useQuery({
    queryKey: applicationQueryKeys.detail(jobId),
    queryFn: () => fetchJobDetails(jobId as string),
    select: mapJobDetails,
    enabled: Boolean(jobId),
  });
}
