// Generated transport contracts and explicit UI adapters.
export * from './resume-contracts';
export * from './workflow-contracts';
import type { ChangeItem, ResumeDocumentJSON } from './resume-contracts';

// Tailored library and analytics remain outside this migration.
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
