import { describe, it, expect } from 'vitest';
import { server, http, HttpResponse } from '@/test-utils/msw-server';
import { creditsApi } from '@/app/lib/api/credits';

describe('creditsApi.getBalance', () => {
  it('fetches /credits/balance and returns balance number', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/credits/balance', () => {
        return HttpResponse.json({ balance: 42 });
      })
    );
    const result = await creditsApi.getBalance();
    expect(result.balance).toBe(42);
  });

  it('returns 0 balance when user has no credits', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/credits/balance', () => {
        return HttpResponse.json({ balance: 0 });
      })
    );
    const result = await creditsApi.getBalance();
    expect(result.balance).toBe(0);
  });

  it('throws on 401 when unauthenticated', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/credits/balance', () => {
        return HttpResponse.json({ detail: 'unauthorized' }, { status: 401 });
      })
    );
    await expect(creditsApi.getBalance()).rejects.toThrow();
  });
});
