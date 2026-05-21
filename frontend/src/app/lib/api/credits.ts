// frontend/src/app/lib/api/credits.ts
import { makeAPIRequest } from './config';
import type { CreditsBalance } from './types-v2';

export const creditsApi = {
  getBalance: (): Promise<CreditsBalance> =>
    makeAPIRequest(`/api/v1/credits/balance`, { method: 'GET' }),
};
