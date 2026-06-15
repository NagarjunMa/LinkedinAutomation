// frontend/src/app/lib/api/exports.ts
import { API_BASE_URL, APIError, getAuthHeaders, makeAPIRequest } from './config';
import type { ExportPdfRequest, ExportPdfResponse } from './types-v2';

export const exportsApi = {
  exportPdf: (body: ExportPdfRequest): Promise<ExportPdfResponse> =>
    makeAPIRequest<ExportPdfResponse>('/api/v1/exports', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  downloadPdf: async (exportId: string): Promise<Blob> => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/api/v1/exports/${exportId}/download`, {
      headers,
    });

    if (!response.ok) {
      let detail = await response.text();
      try {
        const parsed = JSON.parse(detail);
        detail = parsed.detail ?? detail;
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
