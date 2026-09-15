import type { components, paths } from '@/generated/api/types';
import type { ChangeItem } from './resume-contracts';

type Schemas = components['schemas'];
type Analyze = paths['/api/v1/jd/analyze']['post'];
type Apply = paths['/api/v1/jd/{jd_evaluation_id}/apply']['post'];
type Options = paths['/api/v1/jd/{jd_evaluation_id}/bullets/{bullet_id}/options']['post'];
type Export = paths['/api/v1/exports']['post'];
type Download = paths['/api/v1/exports/{export_id}/download']['get'];
type Defaulted<T, Keys extends keyof T> = Omit<T, Keys> & Required<Pick<T, Keys>>;

export type JDAnalyzeRequest = Analyze['requestBody']['content']['application/json'];
type AnalysisTransport = Analyze['responses'][200]['content']['application/json'];
type ApplyTransport = Apply['requestBody']['content']['application/json'];
type ApplyResult = Apply['responses'][200]['content']['application/json'];
type ExportTransport = Export['requestBody']['content']['application/json'];
export type CreditsBalance = paths['/api/v1/credits/balance']['get']['responses'][200]['content']['application/json'];
export type ExportPdfResponse = Export['responses'][201]['content']['application/json'];
export type PdfDownloadMediaType = keyof Download['responses'][200]['content'];

// Keep the version-based UI command complete; the wire also supports legacy
// document exports. Do not widen this caller to an empty/nullable export request.
export type ExportPdfRequest = { resume_version_id: NonNullable<ExportTransport['resume_version_id']> }
  & { [Key in 'template_id' | 'filename']?: NonNullable<ExportTransport[Key]> };
export type ApplyTailorRequest = Omit<ApplyTransport, 'accepted_changes'> & { accepted_changes: ChangeItem[] };
// PreviewPanel treats no warning as undefined rather than null.
export type ApplyTailorResponse = Omit<ApplyResult, 'warning'> & { warning?: NonNullable<ApplyResult['warning']> };

// UI-required collections/nulls are filled only by the response adapter. Facts
// and optional truth metadata remain untouched; no defaults imply verification.
export type JDExtraction = Defaulted<Schemas['JDExtraction'], 'soft_skills' | 'red_flags'>;
export type Requirement = Schemas['Requirement'];
export type RequirementType = Requirement['type'];
export type Seniority = JDExtraction['seniority'];
export type RoleCategory = JDExtraction['primary_role_category'];
export type CountryHint = JDExtraction['country_hint'];
export type BulletTruthCheck = Required<Schemas['BulletTruthCheck']>;
export type BulletOption = Omit<Defaulted<Schemas['BulletOption'], 'placeholders'>, 'truth_check'>
  & { truth_check?: BulletTruthCheck };
export type BulletDiff = Omit<Defaulted<Options['responses'][200]['content']['application/json'], 'placeholders'>, 'options' | 'truth_check'>
  & { options?: BulletOption[]; truth_check?: BulletTruthCheck };
export type BulletFitSignal = Defaulted<Schemas['BulletFitSignal'], 'matched_requirements' | 'noise_flags'>;
export type BulletFitRecommendation = BulletFitSignal['recommendation'];
export type BulletFitEvidenceLevel = BulletFitSignal['evidence_level'];
export type ContentBudget = Schemas['ContentBudget'];
export type SkillsReorder = Schemas['SkillsReorder'];
export type SummaryRewrite = Defaulted<Schemas['SummaryRewrite'], 'old'>;
export type SuggestedAddition = Schemas['SuggestedAddition'];
export type DiffPlan = Omit<Defaulted<Schemas['DiffPlan'], 'skills_reorder' | 'suggested_additions'>, 'bullets' | 'summary_rewrite' | 'bullet_fit'>
  & { bullets: BulletDiff[]; summary_rewrite: SummaryRewrite | null; bullet_fit?: BulletFitSignal[] };
export type JDAnalyzeResponse = Omit<AnalysisTransport, 'extracted_requirements' | 'diff_plan'>
  & { extracted_requirements: JDExtraction; diff_plan: DiffPlan };
