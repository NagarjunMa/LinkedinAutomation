// frontend/src/hooks/use-jd-analyze.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { jdApi } from '@/app/lib/api';
import type { JDAnalyzeResponse } from '@/app/lib/api';

export function useJdAnalyze() {
  const qc = useQueryClient();
  return useMutation<
    JDAnalyzeResponse,
    Error,
    { resumeDocumentId: string; jdText: string }
  >({
    mutationFn: ({ resumeDocumentId, jdText }) =>
      jdApi.analyze({ resume_document_id: resumeDocumentId, jd_text: jdText }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['credits-balance'] }),
  });
}
