// frontend/src/app/lib/api/resume-v2.ts
import { makeAPIRequest } from './config';
import type {
  UploadResponse,
  EvaluationResponse,
  RewriteResult,
  VersionRequest,
  VersionResponse,
} from './types-v2';

export const resumeV2Api = {
  upload: async (file: File): Promise<UploadResponse> => {
    const form = new FormData();
    form.append('file', file);
    return makeAPIRequest<UploadResponse>('/api/v1/resumes/upload', {
      method: 'POST',
      body: form,
    });
  },

  evaluate: (resumeId: string, targetRole: string): Promise<EvaluationResponse> =>
    makeAPIRequest(`/api/v1/resumes/${resumeId}/evaluate`, {
      method: 'POST',
      body: JSON.stringify({ target_role: targetRole }),
    }),

  rewriteBullet: (
    resumeId: string,
    bulletId: string,
    body: { target_role: string; country: string; jd_context?: string }
  ): Promise<RewriteResult> =>
    makeAPIRequest(`/api/v1/resumes/${resumeId}/rewrite/${bulletId}`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  createVersion: (resumeId: string, body: VersionRequest): Promise<VersionResponse> =>
    makeAPIRequest(`/api/v1/resumes/${resumeId}/versions`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};
