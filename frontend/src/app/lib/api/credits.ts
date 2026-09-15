// frontend/src/app/lib/api/credits.ts
import { makeAPIRequest } from './config';
import type { CreditsBalance } from './workflow-contracts';
import { workflowResponseParser } from './workflow-response-parser';

export const creditsApi = {
  getBalance: (): Promise<CreditsBalance> =>
    makeAPIRequest(`/api/v1/credits/balance`, { method: 'GET' }, workflowResponseParser.balance),
};
