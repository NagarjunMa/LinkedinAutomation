// frontend/src/hooks/use-tailor-apply.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { jdApi } from '@/app/lib/api';
import type { ApplyTailorRequest, ApplyTailorResponse } from '@/app/lib/api';

export function useTailorApply(jdEvaluationId: string) {
  const qc = useQueryClient();
  return useMutation<ApplyTailorResponse, Error, ApplyTailorRequest>({
    mutationFn: (body) => jdApi.applyTailor(jdEvaluationId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['versions'] });
      qc.invalidateQueries({ queryKey: ['credits-balance'] });
      qc.invalidateQueries({ queryKey: ['jd-progress'] });
    },
  });
}
