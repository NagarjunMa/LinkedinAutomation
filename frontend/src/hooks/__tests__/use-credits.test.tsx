import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { server, http, HttpResponse } from '@/test-utils/msw-server';
import { useCreditsBalance } from '@/hooks/use-credits';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('useCreditsBalance', () => {
  it('fetches balance from /credits/balance and returns it', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/credits/balance', () => {
        return HttpResponse.json({ balance: 20 });
      })
    );

    const { result } = renderHook(() => useCreditsBalance(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.balance).toBe(20);
  });
});
