// frontend/src/hooks/use-resume.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { resumeV2Api } from '@/app/lib/api';
import type {
  UploadResponse,
  EvaluationResponse,
  RewriteResult,
  VersionRequest,
  VersionResponse,
} from '@/app/lib/api';

export function useUploadResume() {
  const qc = useQueryClient();
  return useMutation<UploadResponse, Error, File>({
    mutationFn: (file) => resumeV2Api.upload(file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resumes'] }),
  });
}

export function useEvaluateResume() {
  const qc = useQueryClient();
  return useMutation<EvaluationResponse, Error, { resumeId: string; targetRole: string }>({
    mutationFn: ({ resumeId, targetRole }) => resumeV2Api.evaluate(resumeId, targetRole),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ['evaluation', vars.resumeId] });
      qc.invalidateQueries({ queryKey: ['credits-balance'] });
    },
  });
}

export function useRewriteBullet() {
  return useMutation<
    RewriteResult,
    Error,
    { resumeId: string; bulletId: string; targetRole: string; country: string; jdContext?: string }
  >({
    mutationFn: ({ resumeId, bulletId, targetRole, country, jdContext }) =>
      resumeV2Api.rewriteBullet(resumeId, bulletId, {
        target_role: targetRole,
        country,
        jd_context: jdContext,
      }),
  });
}

export function useCreateVersion() {
  const qc = useQueryClient();
  return useMutation<VersionResponse, Error, { resumeId: string; body: VersionRequest }>({
    mutationFn: ({ resumeId, body }) => resumeV2Api.createVersion(resumeId, body),
    onSuccess: (_data, vars) =>
      qc.invalidateQueries({ queryKey: ['resume-versions', vars.resumeId] }),
  });
}
