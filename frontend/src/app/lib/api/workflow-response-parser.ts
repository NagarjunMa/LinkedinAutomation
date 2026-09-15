import { z } from 'zod';
import { APIError } from './config';
import type { ApplyTailorResponse, BulletDiff, CreditsBalance, ExportPdfResponse, JDAnalyzeResponse, PdfDownloadMediaType } from './workflow-contracts';

const text = z.string();
const id = text.min(1);
const integer = z.number().int();
const score = integer.min(0).max(100);
const strings = z.array(text);
const nullableText = text.nullable();
const risk = z.enum(['low', 'medium', 'high']);
const placeholders = z.array(z.object({ token: text, what: text })).default([]);
const truth = z.object({
  numeric_claims: z.enum(['verified', 'placeholder_used']), new_skill_status: z.enum(['none', 'resume_supported']),
  unsupported_claims: strings.default([]), placeholders_used: strings.default([]), source_evidence: strings.default([]),
  verified_numbers: strings.default([]), verified_skills: strings.default([]),
});
const bullet = z.object({
  bullet_id: id, old: text, new: text, reason: text, placeholders, truth_check: truth.optional(),
  options: z.array(z.object({ option_id: id, text, reason: text, placeholders, truth_check: truth.optional() })).optional(),
}) satisfies z.ZodType<BulletDiff, z.ZodTypeDef, unknown>;
const requirement = z.object({ skill: text, evidence_from_jd: text, type: z.enum(['technical', 'experience', 'credential']) });
const analysis = z.object({
  jd_evaluation_id: id,
  extracted_requirements: z.object({
    must_have: z.array(requirement), good_to_have: z.array(requirement), soft_skills: strings.default([]),
    seniority: z.enum(['junior', 'mid', 'senior', 'staff']), primary_role_category: z.enum(['SWE', 'DS', 'PM', 'other']),
    country_hint: z.enum(['US', 'IN', 'other']), red_flags: strings.default([]),
    company_name: nullableText.optional(), job_title: nullableText.optional(),
  }),
  diff_plan: z.object({
    match_score: score, must_have_coverage_found: strings, must_have_coverage_missing: strings,
    good_to_have_coverage_found: strings, good_to_have_coverage_missing: strings, bullets: z.array(bullet),
    skills_reorder: z.object({ new_order: strings, rationale: text }).nullable().default(null),
    summary_rewrite: z.object({ old: nullableText.default(null), new: text, reason: text }).nullable().default(null),
    suggested_additions: z.array(z.object({ section: text, item: text, reason: text })).default([]),
    bullet_fit: z.array(z.object({
      bullet_id: id, relevance_score: score, evidence_level: z.enum(['high', 'medium', 'low']),
      recommendation: z.enum(['keep', 'rewrite', 'consider_trim']), matched_requirements: strings.default([]),
      noise_flags: strings.default([]), rationale: text, why_stronger: text.optional(),
      matched_jd_phrases: strings.optional(), source_resume_evidence: strings.optional(), page_cost: risk.optional(), truth_risk: risk.optional(),
    })).optional(),
    content_budget: z.object({
      source_page_estimate: z.number().finite().min(1), target_max_pages: integer.min(1).max(2),
      recommended_bullet_budget: integer.min(1), current_bullet_count: integer.min(0), page_fit_risk: risk, guidance: text,
    }).nullable().optional(),
  }),
}) satisfies z.ZodType<JDAnalyzeResponse, z.ZodTypeDef, unknown>;
const applied = z.object({
  version_id: id, preview_html: text, company_name: nullableText, target_role_title: nullableText.optional(),
  suggested_template: text, filename_hint: text, warning: nullableText.optional().transform(value => value ?? undefined),
}) satisfies z.ZodType<ApplyTailorResponse, z.ZodTypeDef, unknown>;
const exported = z.object({
  export_id: id, download_url: text, expires_at: text, country: z.enum(['US', 'IN']),
  role_template: z.enum(['swe', 'ds', 'pm']), filename: nullableText.optional(),
}) satisfies z.ZodType<ExportPdfResponse, z.ZodTypeDef, unknown>;
const balance = z.object({ balance: integer }) satisfies z.ZodType<CreditsBalance, z.ZodTypeDef, unknown>;

function parse<T>(schema: z.ZodType<T, z.ZodTypeDef, unknown>, status: number, message: string) {
  return async (response: Response): Promise<T> => {
    try {
      if (response.status !== status) throw new Error();
      return schema.parse(await response.json());
    } catch {
      // Never expose JSON/Zod inputs or causes, log JD data, or retry a mutation.
      throw new APIError(message);
    }
  };
}

export const workflowResponseParser = {
  analyze: parse<JDAnalyzeResponse>(analysis, 200, 'Invalid JD response'),
  apply: parse<ApplyTailorResponse>(applied, 200, 'Invalid JD response'),
  options: parse<BulletDiff>(bullet, 200, 'Invalid JD response'),
  export: parse<ExportPdfResponse>(exported, 201, 'Invalid export response'),
  balance: parse<CreditsBalance>(balance, 200, 'Invalid credit response'),
  download: async (response: Response): Promise<Blob> => {
    try {
      // OpenAPI's string/binary is a wire description, not the browser Blob type.
      const mediaType = 'application/pdf' satisfies PdfDownloadMediaType;
      if (response.status !== 200 || response.headers.get('content-type')?.split(';')[0].trim().toLowerCase() !== mediaType) throw new Error();
      const blob = await response.blob();
      if (!blob.size) throw new Error();
      return blob;
    } catch {
      throw new APIError('Invalid export response');
    }
  },
};
