// frontend/src/app/lib/api/jd.ts
import { makeAPIRequest } from './config';
import type { JDAnalyzeResponse } from './types-v2';

export const jdApi = {
  analyze: (body: { resume_document_id: string; jd_text: string }): Promise<JDAnalyzeResponse> =>
    makeAPIRequest(`/api/v1/jd/analyze`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};
