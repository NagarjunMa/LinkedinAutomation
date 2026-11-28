// frontend/src/hooks/use-export-pdf.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { tailoredResumesApi } from '@/app/lib/api';
import type { ExportPdfRequest } from '@/app/lib/api';

type DownloadResult = {
  blob: Blob;
  filename: string;
};

export function useExportPdf(owner?: { userId: string; isCurrentUser: (userId: string) => boolean }) {
  const qc = useQueryClient();
  return useMutation<DownloadResult, Error, ExportPdfRequest>({
    mutationFn: async (body) => {
      const request = { template_id: body.template_id, filename: body.filename };
      const blob = owner
        ? await tailoredResumesApi.downloadPdf(body.resume_version_id, request, owner.userId)
        : await tailoredResumesApi.downloadPdf(body.resume_version_id, request);
      return {
        blob,
        filename: body.filename || 'resume.pdf',
      };
    },
    onSuccess: async (data) => {
      qc.invalidateQueries({ queryKey: ['credits-balance'] });
      qc.invalidateQueries({ queryKey: ['jd-progress'] });
      qc.invalidateQueries({ queryKey: ['tailored-resumes'] });
      if (owner && !owner.isCurrentUser(owner.userId)) return;
      const objectUrl = URL.createObjectURL(data.blob);
      // Trigger browser download
      const a = document.createElement('a');
      a.href = objectUrl;
      a.download = data.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(objectUrl);
    },
  });
}
