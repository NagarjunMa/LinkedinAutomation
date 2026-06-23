// frontend/src/app/lib/api/types-v2.ts
// Mirrors backend/app/schemas/resume.py and backend/app/schemas/jd.py.
// Keep field names in snake_case to match wire format — do not camelCase.

export type Severity = 'critical' | 'warning' | 'info';
export type BulletCategory =
  | 'quantification'
  | 'verb'
  | 'structure'
  | 'clarity'
  | 'redundancy'
  | 'ats';

export interface Contact {
  name: string;
  email: string | null;
  phone: string | null;
  links: string[];
}

export interface Bullet {
  id: string;
  text: string;
  raw_text: string;
}

export interface ExperienceEntry {
  company: string;
  role: string;
  dates: string | null;
  location: string | null;
  bullets: Bullet[];
}

export interface EducationEntry {
  school: string;
  degree: string | null;
  dates: string | null;
  gpa: string | null;
}

export interface Skills {
  hard: string[];
  soft: string[];
}

export interface ProjectEntry {
  name: string;
  bullets: Bullet[];
}

export interface ResumeDocumentJSON {
  contact: Contact;
  summary: string | null;
  experience: ExperienceEntry[];
  education: EducationEntry[];
  skills: Skills;
  projects: ProjectEntry[];
  certifications: string[];
  raw_text: string;
}

export interface UploadResponse extends ResumeDocumentJSON {
  resume_document_id: string;
}

export interface BulletFlag {
  bullet_id: string;
  severity: Severity;
  reason: string;
  category: BulletCategory;
}

export interface FormatIssue {
  type: string;
  location: string;
  fix_hint: string;
}

export interface EvaluationResponse {
  evaluation_id: string;
  overall_score: number;
  readiness_label: 'ready' | 'minor_edits' | 'needs_work';
  score_breakdown: {
    content_quality: number;
    role_fit: number;
    evidence_strength: number;
    recruiter_readability: number;
  };
  score_explanation: Array<{
    category: 'content_quality' | 'role_fit' | 'evidence_strength' | 'recruiter_readability';
    score: number;
    reason: string;
    evidence: string[];
    before_applying_action: string;
  }>;
  top_actions_before_applying: string[];
  parser_confidence: 'high' | 'medium' | 'low';
  bullet_flags: BulletFlag[];
  format_issues: FormatIssue[];
  summary_critique: string | null;
  ats_parseability: number;
  ats_raw_text: string;
}

export interface Placeholder {
  token: string;
  what: string;
}

export interface RewriteResult {
  rewritten: string;
  placeholders: Placeholder[];
  applied_changes: string[];
}

export type ChangeItem =
  | { type: 'bullet_update'; bullet_id: string; new_text: string }
  | { type: 'skills_reorder'; new_skills_order: string[] }
  | { type: 'summary_update'; new_summary: string };

export interface VersionRequest {
  parent_version_id?: string;
  change_set: ChangeItem[];
}

export interface VersionResponse {
  version_id: string;
}

// JD --------------------------------------------------------------------

export type RequirementType = 'technical' | 'experience' | 'credential';
export type Seniority = 'junior' | 'mid' | 'senior' | 'staff';
export type RoleCategory = 'SWE' | 'DS' | 'PM' | 'other';
export type CountryHint = 'US' | 'IN' | 'other';

export interface Requirement {
  skill: string;
  evidence_from_jd: string;
  type: RequirementType;
}

export interface JDExtraction {
  must_have: Requirement[];
  good_to_have: Requirement[];
  soft_skills: string[];
  seniority: Seniority;
  primary_role_category: RoleCategory;
  country_hint: CountryHint;
  red_flags: string[];
  company_name?: string | null;
  job_title?: string | null;
}

export interface BulletOption {
  option_id: string;
  text: string;
  reason: string;
  placeholders: Placeholder[];
}

export interface BulletDiff {
  bullet_id: string;
  old: string;
  new: string;
  reason: string;
  placeholders: Placeholder[];
  options?: BulletOption[];
}

export type BulletFitRecommendation = 'keep' | 'rewrite' | 'consider_trim';
export type BulletFitEvidenceLevel = 'high' | 'medium' | 'low';

export interface BulletFitSignal {
  bullet_id: string;
  relevance_score: number;
  evidence_level: BulletFitEvidenceLevel;
  recommendation: BulletFitRecommendation;
  matched_requirements: string[];
  noise_flags: string[];
  rationale: string;
  why_stronger?: string;
  matched_jd_phrases?: string[];
  source_resume_evidence?: string[];
  page_cost?: 'low' | 'medium' | 'high';
  truth_risk?: 'low' | 'medium' | 'high';
}

export interface ContentBudget {
  source_page_estimate: number;
  target_max_pages: number;
  recommended_bullet_budget: number;
  current_bullet_count: number;
  page_fit_risk: 'low' | 'medium' | 'high';
  guidance: string;
}

export interface SkillsReorder {
  new_order: string[];
  rationale: string;
}

export interface SummaryRewrite {
  old: string | null;
  new: string;
  reason: string;
}

export interface SuggestedAddition {
  section: string;
  item: string;
  reason: string;
}

export interface DiffPlan {
  match_score: number;
  must_have_coverage_found: string[];
  must_have_coverage_missing: string[];
  good_to_have_coverage_found: string[];
  good_to_have_coverage_missing: string[];
  bullets: BulletDiff[];
  skills_reorder: SkillsReorder | null;
  summary_rewrite: SummaryRewrite | null;
  suggested_additions: SuggestedAddition[];
  bullet_fit?: BulletFitSignal[];
  content_budget?: ContentBudget | null;
}

export interface JDAnalyzeResponse {
  jd_evaluation_id: string;
  extracted_requirements: JDExtraction;
  diff_plan: DiffPlan;
}

export interface CreditsBalance {
  balance: number;
}

// Tailor-apply types (2026-05-25) -------------------------------------------

export interface ApplyTailorRequest {
  accepted_changes: ChangeItem[];
  template_id?: string;
}

export interface ApplyTailorResponse {
  version_id: string;
  preview_html: string;
  company_name: string | null;
  target_role_title?: string | null;
  suggested_template: string;
  filename_hint: string;
  warning?: string;
}

export interface TailoredResumeListItem {
  version_id: string;
  resume_document_id: string;
  source_filename: string;
  company_name: string | null;
  target_role_title: string | null;
  role_category: string | null;
  seniority: string | null;
  country_hint: string | null;
  match_score: number | null;
  template_id: string | null;
  accepted_change_count: number;
  created_at: string | null;
  accepted_at: string | null;
}

export interface TailoredResumeDetail extends TailoredResumeListItem {
  resume_json: ResumeDocumentJSON;
  source_jd_text: string | null;
  extracted_requirements: Record<string, unknown>;
  diff_plan: Record<string, unknown>;
  accepted_changes: ChangeItem[];
}

export interface AnalyticsJdProgress {
  jds: Array<{
    jd_evaluation_id: string;
    jd_company: string | null;
    tailored_at: string | null;
    applies_count: number;
    exports_count: number;
    last_match_score: number | null;
  }>;
  totals: {
    jds_tailored: number;
    versions_created: number;
    pdfs_exported: number;
  };
}

// Exports types (2026-05-25) -------------------------------------------------

export interface ExportPdfRequest {
  resume_version_id: string;
  template_id?: string;
  filename?: string;
}

export interface ExportPdfResponse {
  export_id: string;
  download_url: string;
  expires_at?: string;
  country?: string;
  role_template?: string;
  filename: string;
}
