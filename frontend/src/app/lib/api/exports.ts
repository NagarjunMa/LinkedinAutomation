// frontend/src/app/lib/api/exports.ts
import { makeAPIRequest } from './config';
import type { ExportPdfRequest, ExportPdfResponse } from './types-v2';

export const exportsApi = {
  exportPdf: (body: ExportPdfRequest): Promise<ExportPdfResponse> =>
    makeAPIRequest<ExportPdfResponse>('/api/v1/exports', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};
