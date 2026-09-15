// frontend/src/app/lib/api/exports.ts
import { makeAPIRequest } from './config';
import type { ExportPdfRequest, ExportPdfResponse } from './workflow-contracts';
import { workflowResponseParser } from './workflow-response-parser';

export const exportsApi = {
  exportPdf: (body: ExportPdfRequest): Promise<ExportPdfResponse> =>
    makeAPIRequest<ExportPdfResponse>('/api/v1/exports', {
      method: 'POST',
      body: JSON.stringify(body),
    }, workflowResponseParser.export),

  downloadPdf: async (exportId: string): Promise<Blob> => {
    return makeAPIRequest<Blob>(
      `/api/v1/exports/${encodeURIComponent(exportId)}/download`,
      { method: 'GET' },
      workflowResponseParser.download,
    );
  },
};
