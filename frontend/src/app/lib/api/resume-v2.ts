// frontend/src/app/lib/api/resume-v2.ts
import { APIError, makeAPIRequest } from './config';
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
  upload: async (file: File, userId: string): Promise<UploadResponse> => {
    const form = new FormData();
    form.append('file', file);
    return makeAPIRequest<UploadResponse>('/api/v1/resumes/upload', {
      method: 'POST',
      body: form,
      expectedUserId: userId,
    }, resumeResponseParser.upload);
  },

  evaluate: async (
    resumeId: string, targetRole: string | undefined, versionId?: string, review?: { userId: string; targetId?: string },
  ): Promise<EvaluationResponse> => {
    const target = review?.targetId ? { target_id: review.targetId } : targetRole ? { target_role: targetRole } : null;
    if (!target) throw new APIError('Select a target or enter a target role.');
    return makeAPIRequest(`/api/v1/resumes/${resumeId}/evaluate`, {
      method: 'POST',
      expectedUserId: review?.userId,
      body: JSON.stringify({
        ...target, version_id: versionId,
        ...(review ? { grounded_review: true } : {}),
      } satisfies EvaluationRequest),
    }, resumeResponseParser.evaluate);
  },

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

  get: (resumeId: string, expectedUserId?: string, evaluationId?: string): Promise<ResumeDetailResponse> => {
    const query = evaluationId ? `?grounded_evaluation_id=${encodeURIComponent(evaluationId)}` : '';
    return makeAPIRequest(`/api/v1/resumes/${resumeId}${query}`, { expectedUserId, cache: 'no-store' }, resumeResponseParser.get);
  },

  delete: (resumeId: string): Promise<ResumeDeleteResponse> =>
    makeAPIRequest(`/api/v1/resumes/${resumeId}`, { method: 'DELETE' }, resumeResponseParser.delete),
};
