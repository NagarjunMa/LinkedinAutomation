// API Type definitions
export type JsonRecord = Record<string, unknown>;

export interface JobApiResponse extends JsonRecord {
    id: string;
    title: string;
    company: string;
    location?: string;
    job_type?: string;
    description?: string;
    application_url?: string;
    posted_date?: string;
    salary_range?: string;
    experience_level?: string;
    skills?: string[];
    applied?: boolean;
    applied_date?: string;
    extracted_date?: string;
    application_status?: string;
    application_notes?: string;
    application_context?: string;
    compatibility_score?: number;
    ai_insights?: string;
}

export interface DailyStatsResponse {
    date: string;
    jobs_extracted?: number;
    jobs_applied?: number;
    jobs_from_url?: number;
    jobs_from_extension?: number;
}

export interface RecentApplicationResponse extends JsonRecord {
    id: string;
    title?: string;
    company?: string;
    applied_date?: string;
    extracted_date?: string;
    status?: string;
    company_logo?: string;
}

export interface ResumeListItemResponse extends JsonRecord {
    id: string;
    original_filename?: string;
    filename?: string;
    file_size?: number;
    size?: number;
    file_type?: string;
    type?: string;
    uploaded_at?: string;
    uploadedAt?: string;
    evaluation_status?: string;
    evaluationStatus?: string;
}

export type JobApplicationStatusUpdate = JsonRecord;

// Enhanced profile types
export interface WorkExperience {
    job_title: string;
    company: string;
    location: string;
    start_date: string;
    end_date?: string;
}

export interface Education {
    university: string;
    degree: string;
    field_of_study: string;
    location: string;
    start_date: string;
    end_date?: string;
}

export interface UserProfile {
    user_id: string;
    full_name: string;
    email: string;
    phone?: string;
    location?: string;
    work_authorization?: string;

    // Professional Summary
    years_of_experience?: number;
    career_level?: string;
    professional_summary?: string;

    // Skills & Technologies (JSON arrays)
    programming_languages?: string[];
    frameworks_libraries?: string[];
    tools_platforms?: string[];
    soft_skills?: string[];

    // Experience
    job_titles?: string[];
    companies?: string[];
    industries?: string[];
    experience_descriptions?: string[];

    // Education
    degrees?: string[];
    institutions?: string[];
    graduation_years?: string[];
    relevant_coursework?: string[];

    // Job Preferences
    desired_roles?: string[];
    preferred_locations?: string[];
    salary_range_min?: number;
    salary_range_max?: number;
    job_types?: string[];
    company_size_preference?: string[];

    // AI-Generated Insights
    ai_profile_summary?: string;
    ai_strengths?: string[];
    ai_improvement_areas?: string[];
    ai_career_advice?: string;

    // Legacy/computed fields for backwards compatibility
    target_job_titles?: string[];
    minimum_salary?: number;
    experience_level?: string;
    graduation_date?: string;
    university?: string;
    background_summary?: string;
    email_signature?: string;
    primary_resume_id?: string;
    referral_template?: string;
    work_experiences?: WorkExperience[];
    education_history?: Education[];

    // Metadata
    created_at: string;
    updated_at: string;
    last_resume_upload?: string;
    total_applications: number;
    total_resumes: number;
    total_resume_versions?: number;
    total_resume_evaluations?: number;
    profile_completion: number;
}

export interface UserSettings {
    user_id: string;
    email_notifications?: {
        application_updates: boolean;
        interview_reminders: boolean;
        weekly_digest: boolean;
        referral_responses: boolean;
    };
    notification_frequency?: string;
    email_forwarding_enabled?: string;
    forwarding_address?: string;
    last_email_check?: string;
    data_retention_days?: number;
    analytics_enabled?: string;
    created_at: string;
    updated_at: string;
}

export interface ProfileChangeHistory {
    id: string;
    user_id: string;
    field_changed: string;
    old_value?: string;
    new_value?: string;
    changed_at: string;
}

// Resume evaluation types
export interface ResumeFile {
    id: string;
    filename: string;
    original_filename: string;
    file_size: number;
    file_type: string;
    uploaded_at: string;
    evaluation_status: 'pending' | 'evaluating' | 'completed' | 'failed';
    evaluation_result?: ResumeEvaluation;
    is_primary?: boolean;
}

export interface AtsCompatibilityDetails {
    status: string;
    analysis: string;
    missing_keywords: string[];
}

export interface WordingSuggestion {
    original: string;
    suggested: string;
    rationale: string;
}

export interface ResumeEvaluation {
    id: string;
    resume_id: string;

    // New Precision Analysis Fields
    ai_score: number;
    ats_score: number;
    optical_strengths: string[];
    strategic_improvements: string[];
    ats_compatibility_details?: AtsCompatibilityDetails;

    // Legacy/Compatibility
    overall_score: number;
    max_score?: number;
    readiness_label?: 'ready' | 'minor_edits' | 'needs_work';
    score_breakdown?: {
        content_quality: number;
        role_fit: number;
        evidence_strength: number;
        recruiter_readability: number;
    };
    score_explanation?: Array<{
        category: 'content_quality' | 'role_fit' | 'evidence_strength' | 'recruiter_readability';
        score: number;
        reason: string;
        evidence: string[];
        before_applying_action: string;
    }>;
    top_actions_before_applying?: string[];
    parser_confidence?: 'high' | 'medium' | 'low';
    bullet_flags?: Array<{
        bullet_id: string;
        severity: 'critical' | 'warning' | 'info';
        reason: string;
        category: string;
    }>;
    format_issues?: Array<{
        type: string;
        location: string;
        fix_hint: string;
    }>;
    ats_compliance_score: number;
    content_quality_score: number;
    experience_points_score: number;
    job_relevance_score: number;
    quality_checks_score: number;

    executive_summary?: string;
    strengths: string[];
    improvements: string[];
    ats_compatibility: 'excellent' | 'good' | 'fair' | 'poor'; // Kept as string union for UI consistency
    ats_checklist?: string[];
    detailed_feedback: string;
    keyword_analysis: {
        relevant: string[];
        missing: string[];
        score: number;
    };

    // New consolidated evaluation fields
    critical_issues?: {
        immediate_fixes: string[];
        strategic_improvements: string[];
        nice_to_have: string[];
    };
    market_positioning?: {
        current_level: string;
        salary_range: string;
        target_roles: string[];
        company_fit: {
            maang_companies: number;
            startups: number;
            enterprise: number;
        };
    };
    wording_suggestions?: WordingSuggestion[];

    agent_results?: Record<string, unknown>;

    // Evaluation metadata
    evaluation_metadata?: {
        processing_time_seconds?: number;
        successful_agents?: number;
        total_agents?: number;
        confidence_percentage?: number;
        evaluation_type: 'consolidated' | 'legacy';
    };
}

export interface RecentApplication {
    id: string;
    title: string;
    company: string;
    appliedAt: string;
    extracted_date: string;
    status: string;
    companyLogo?: string;
    location?: string;
    salary?: string;
    applicationSource?: string;
    sourceUrl?: string;
    compatibilityScore?: number;
}
