import { makeAPIRequest } from './config';
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
    return makeAPIRequest<Blob>(
      `/api/v1/tailored-resumes/${versionId}/download`,
      {
        method: 'POST',
        body: JSON.stringify(body),
      },
      (response) => response.blob(),
    );
  },
};
