// frontend/src/app/lib/api/jd.ts
import { makeAPIRequest } from './config';
import type { BulletDiff, JDAnalyzeRequest, JDAnalyzeResponse, ApplyTailorRequest, ApplyTailorResponse } from './workflow-contracts';
import { workflowResponseParser } from './workflow-response-parser';

export const jdApi = {
  analyze: (body: JDAnalyzeRequest): Promise<JDAnalyzeResponse> =>
    makeAPIRequest(`/api/v1/jd/analyze`, {
      method: 'POST',
      body: JSON.stringify(body),
    }, workflowResponseParser.analyze),

  applyTailor: (
    jdEvaluationId: string,
    body: ApplyTailorRequest,
  ): Promise<ApplyTailorResponse> =>
    makeAPIRequest<ApplyTailorResponse>(`/api/v1/jd/${encodeURIComponent(jdEvaluationId)}/apply`, {
      method: 'POST',
      body: JSON.stringify(body),
    }, workflowResponseParser.apply),

  regenerateBulletOptions: (
    jdEvaluationId: string,
    bulletId: string,
  ): Promise<BulletDiff> =>
    makeAPIRequest<BulletDiff>(`/api/v1/jd/${encodeURIComponent(jdEvaluationId)}/bullets/${encodeURIComponent(bulletId)}/options`, {
      method: 'POST',
    }, workflowResponseParser.options),
};
