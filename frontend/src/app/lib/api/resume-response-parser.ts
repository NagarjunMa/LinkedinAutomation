import { z } from 'zod';
import type { components } from '@/generated/api/types';
import { APIError } from './config';
import type {
  UploadResponse, EvaluationResponse, RewriteResult, VersionResponse,
  ResumeListResponse, ResumeDetailResponse, ResumeDeleteResponse,
} from './resume-contracts';

const text = z.string();
const id = text.min(1);
const strings = z.array(text);
const optionalText = text.nullable().default(null);
const integer = z.number().int();
const score = integer.min(0).max(100);
const bullet = z.object({ id, text, raw_text: text });
const scoreBreakdown = z.object({
  content_quality: score, role_fit: score, evidence_strength: score, recruiter_readability: score,
});
const evaluationFields = {
  overall_score: score,
  readiness_label: z.enum(['ready', 'minor_edits', 'needs_work']),
  score_breakdown: scoreBreakdown,
  score_explanation: z.array(z.object({
    category: z.enum(['content_quality', 'role_fit', 'evidence_strength', 'recruiter_readability']),
    score, reason: text, evidence: strings.default([]), before_applying_action: text,
  })),
  top_actions_before_applying: strings,
  parser_confidence: z.enum(['high', 'medium', 'low']),
  bullet_flags: z.array(z.object({
    bullet_id: id, severity: z.enum(['critical', 'warning', 'info']), reason: text,
    category: z.enum(['quantification', 'verb', 'structure', 'clarity', 'redundancy', 'ats']),
  })),
  format_issues: z.array(z.object({ type: text, location: text, fix_hint: text })),
};

// Checked against generated output types. Runtime validation is intentionally
// separate from transport declarations; TypeScript alone cannot inspect JSON.
const upload = z.object({
  resume_document_id: id,
  contact: z.object({ name: text, email: optionalText, phone: optionalText, links: strings.default([]) }),
  raw_text: text, summary: optionalText,
  experience: z.array(z.object({
    company: text, role: text, dates: optionalText, location: optionalText, bullets: z.array(bullet).default([]),
  })).default([]),
  education: z.array(z.object({
    school: text, degree: optionalText, location: optionalText, dates: optionalText, gpa: optionalText,
  })).default([]),
  skills: z.object({ hard: strings.default([]), soft: strings.default([]) }).default({}),
  projects: z.array(z.object({ name: text, bullets: z.array(bullet).default([]) })).default([]),
  certifications: strings.default([]),
}) satisfies z.ZodType<UploadResponse, z.ZodTypeDef, unknown>;

const evaluation = z.object({
  ...evaluationFields, evaluation_id: id, summary_critique: text.nullable(),
  ats_parseability: integer, ats_raw_text: text,
}) satisfies z.ZodType<EvaluationResponse, z.ZodTypeDef, unknown>;

const savedEvaluation = z.object({
  ...evaluationFields, id, resume_id: id, resume_document_id: id,
  ats_score: integer, ats_compliance_score: integer, content_quality_score: integer,
  experience_points_score: integer, job_relevance_score: integer, quality_checks_score: integer,
  strengths: strings, improvements: strings, ats_compatibility: z.enum(['good', 'fair']),
  detailed_feedback: text.nullable(),
  keyword_analysis: z.object({ relevant: strings, missing: strings, score: integer }),
  created_at: text.nullable(),
}) satisfies z.ZodType<components['schemas']['ResumeSavedEvaluation'], z.ZodTypeDef, unknown>;

const row = z.object({
  id, resume_document_id: id, filename: text, original_filename: text,
  file_size: integer, file_type: text, uploaded_at: text.nullable(),
  evaluation_status: z.enum(['pending', 'completed']), is_primary: z.boolean(),
  evaluation_result: savedEvaluation.nullable(),
});
const list = z.object({ resumes: z.array(row), total_count: integer, totalCount: integer }) satisfies
  z.ZodType<ResumeListResponse, z.ZodTypeDef, unknown>;
const detail = z.object({ resume: row, evaluation: savedEvaluation.nullable() }) satisfies
  z.ZodType<ResumeDetailResponse, z.ZodTypeDef, unknown>;
const rewrite = z.object({
  rewritten: text, placeholders: z.array(z.object({ token: text, what: text })), applied_changes: strings,
}) satisfies z.ZodType<RewriteResult, z.ZodTypeDef, unknown>;
const version = z.object({ version_id: id }) satisfies z.ZodType<VersionResponse, z.ZodTypeDef, unknown>;

function parse<T>(schema: z.ZodType<T, z.ZodTypeDef, unknown>, status: number) {
  return async (response: Response): Promise<T> => {
    try {
      if (response.status !== status) throw new Error();
      return schema.parse(await response.json());
    } catch {
      // JSON/Zod errors may include resume text. Never attach the cause or data,
      // log the payload, or retry a mutation that may already have succeeded.
      throw new APIError('Invalid resume response');
    }
  };
}

export const resumeResponseParser = {
  upload: parse<UploadResponse>(upload, 201),
  evaluate: parse<EvaluationResponse>(evaluation, 200),
  list: parse<ResumeListResponse>(list, 200),
  get: parse<ResumeDetailResponse>(detail, 200),
  rewrite: parse<RewriteResult>(rewrite, 200),
  version: parse<VersionResponse>(version, 201),
  delete: async (response: Response): Promise<ResumeDeleteResponse> => {
    if (response.status !== 204 || await response.text() !== '') throw new APIError('Invalid resume response');
    return undefined;
  },
};
