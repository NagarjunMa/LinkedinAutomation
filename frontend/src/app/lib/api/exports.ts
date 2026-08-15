// frontend/src/app/lib/api/exports.ts
import { makeAPIRequest } from './config';
import type { ExportPdfRequest, ExportPdfResponse } from './types-v2';

export const exportsApi = {
  exportPdf: (body: ExportPdfRequest): Promise<ExportPdfResponse> =>
    makeAPIRequest<ExportPdfResponse>('/api/v1/exports', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  downloadPdf: async (exportId: string): Promise<Blob> => {
    return makeAPIRequest<Blob>(
      `/api/v1/exports/${exportId}/download`,
      { method: 'GET' },
      (response) => response.blob(),
    );
  },
};
