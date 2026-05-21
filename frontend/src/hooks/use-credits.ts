// frontend/src/hooks/use-credits.ts
import { useQuery } from '@tanstack/react-query';
import { creditsApi } from '@/app/lib/api';

export function useCreditsBalance() {
  return useQuery({
    queryKey: ['credits-balance'],
    queryFn: () => creditsApi.getBalance(),
    staleTime: 10_000,
  });
}
