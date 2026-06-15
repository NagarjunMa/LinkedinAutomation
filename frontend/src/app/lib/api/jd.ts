// frontend/src/app/lib/api/jd.ts
import { makeAPIRequest } from './config';
import type { BulletDiff, JDAnalyzeResponse, ApplyTailorRequest, ApplyTailorResponse } from './types-v2';

export const jdApi = {
  analyze: (body: { resume_document_id: string; jd_text: string }): Promise<JDAnalyzeResponse> =>
    makeAPIRequest(`/api/v1/jd/analyze`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  applyTailor: (
    jdEvaluationId: string,
    body: ApplyTailorRequest,
  ): Promise<ApplyTailorResponse> =>
    makeAPIRequest<ApplyTailorResponse>(`/api/v1/jd/${jdEvaluationId}/apply`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  regenerateBulletOptions: (
    jdEvaluationId: string,
    bulletId: string,
  ): Promise<BulletDiff> =>
    makeAPIRequest<BulletDiff>(`/api/v1/jd/${jdEvaluationId}/bullets/${bulletId}/options`, {
      method: 'POST',
    }),
};
