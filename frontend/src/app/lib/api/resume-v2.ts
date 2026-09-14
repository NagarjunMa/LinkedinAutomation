// frontend/src/app/lib/api/resume-v2.ts
import { makeAPIRequest } from './config';
import { resumeResponseParser } from './resume-response-parser';
import type {
  UploadResponse,
  EvaluationResponse,
  RewriteResult,
  VersionRequest,
  VersionResponse,
  EvaluationRequest,
  RewriteRequest,
  ResumeListResponse,
  ResumeDetailResponse,
  ResumeDeleteResponse,
} from './resume-contracts';

export const resumeV2Api = {
  upload: async (file: File): Promise<UploadResponse> => {
    const form = new FormData();
    form.append('file', file);
    return makeAPIRequest<UploadResponse>('/api/v1/resumes/upload', {
      method: 'POST',
      body: form,
    }, resumeResponseParser.upload);
  },

  evaluate: (resumeId: string, targetRole: string): Promise<EvaluationResponse> =>
    makeAPIRequest(`/api/v1/resumes/${resumeId}/evaluate`, {
      method: 'POST',
      body: JSON.stringify({ target_role: targetRole } satisfies EvaluationRequest),
    }, resumeResponseParser.evaluate),

  rewriteBullet: (
    resumeId: string,
    bulletId: string,
    body: RewriteRequest
  ): Promise<RewriteResult> =>
    makeAPIRequest(`/api/v1/resumes/${resumeId}/rewrite/${bulletId}`, {
      method: 'POST',
      body: JSON.stringify(body),
    }, resumeResponseParser.rewrite),

  createVersion: (resumeId: string, body: VersionRequest): Promise<VersionResponse> =>
    makeAPIRequest(`/api/v1/resumes/${resumeId}/versions`, {
      method: 'POST',
      body: JSON.stringify(body),
    }, resumeResponseParser.version),

  list: (): Promise<ResumeListResponse> =>
    makeAPIRequest('/api/v1/resumes/list', {}, resumeResponseParser.list),

  get: (resumeId: string): Promise<ResumeDetailResponse> =>
    makeAPIRequest(`/api/v1/resumes/${resumeId}`, {}, resumeResponseParser.get),

  delete: (resumeId: string): Promise<ResumeDeleteResponse> =>
    makeAPIRequest(`/api/v1/resumes/${resumeId}`, { method: 'DELETE' }, resumeResponseParser.delete),
};
