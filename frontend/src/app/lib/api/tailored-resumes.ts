import { API_BASE_URL, APIError, getAuthHeaders, makeAPIRequest } from './config';
import type { TailoredResumeDetail, TailoredResumeListItem } from './types-v2';

export const tailoredResumesApi = {
  list: (): Promise<TailoredResumeListItem[]> =>
    makeAPIRequest<TailoredResumeListItem[]>('/api/v1/tailored-resumes'),

  get: (versionId: string): Promise<TailoredResumeDetail> =>
    makeAPIRequest<TailoredResumeDetail>(`/api/v1/tailored-resumes/${versionId}`),

  downloadPdf: async (
    versionId: string,
    body: { template_id?: string; filename?: string } = {},
  ): Promise<Blob> => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/api/v1/tailored-resumes/${versionId}/download`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      let detail: unknown = await response.text();
      try {
        const parsed = JSON.parse(String(detail));
        detail = parsed.detail ?? parsed;
      } catch {
        /* keep text detail */
      }
      throw new APIError(
        typeof detail === 'string' ? detail : JSON.stringify(detail),
        response.status,
        response.statusText,
        detail
      );
    }

    return response.blob();
  },
};
