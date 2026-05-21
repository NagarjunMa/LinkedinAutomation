// frontend/src/app/lib/api/resume-v2.ts
import { makeAPIRequest, getAuthHeaders, APIError } from './config';
import type {
  UploadResponse,
  EvaluationResponse,
  RewriteResult,
  VersionRequest,
  VersionResponse,
} from './types-v2';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const resumeV2Api = {
  upload: async (file: File): Promise<UploadResponse> => {
    const form = new FormData();
    form.append('file', file);
    const headers = await getAuthHeaders();
    delete headers['Content-Type']; // browser sets boundary
    const res = await fetch(`${API_BASE}/api/v1/resumes/upload`, {
      method: 'POST',
      headers,
      body: form,
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new APIError(`Upload failed: ${res.status}`, res.status, res.statusText, detail);
    }
    return res.json();
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
