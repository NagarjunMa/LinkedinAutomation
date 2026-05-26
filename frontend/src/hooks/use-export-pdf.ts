// frontend/src/hooks/use-export-pdf.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { exportsApi } from '@/app/lib/api';
import type { ExportPdfRequest, ExportPdfResponse } from '@/app/lib/api';

export function useExportPdf() {
  const qc = useQueryClient();
  return useMutation<ExportPdfResponse, Error, ExportPdfRequest>({
    mutationFn: (body) => exportsApi.exportPdf(body),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['credits-balance'] });
      qc.invalidateQueries({ queryKey: ['jd-progress'] });
      // Trigger browser download
      const a = document.createElement('a');
      a.href = data.signed_url;
      a.download = data.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    },
  });
}
