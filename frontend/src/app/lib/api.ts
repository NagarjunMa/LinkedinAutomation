

import { JobStats, TimeRange } from '../types/stats';
import type { JobFilters } from '../types/job';

// Enhanced profile types
export interface WorkExperience {
    job_title: string;
    company: string;
    location: string;
    start_date: string;
    end_date?: string; // Optional for current job
}

export interface Education {
    university: string;
    degree: string;
    field_of_study: string;
    location: string;
    start_date: string;
    end_date?: string;
}

// Profile types - Updated to match backend database schema
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
    target_job_titles?: string[]; // alias for desired_roles
    minimum_salary?: number; // alias for salary_range_min
    experience_level?: string; // alias for career_level
    graduation_date?: string;
    university?: string;
    background_summary?: string; // alias for professional_summary
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

export interface ResumeEvaluation {
    overall_score: number;
    ats_compliance_score: number;
    content_quality_score: number;
    experience_points_score: number;
    job_relevance_score: number;
    quality_checks_score: number;
    strengths: string[];
    improvements: string[];
    ats_compatibility: 'excellent' | 'good' | 'fair' | 'poor';
    detailed_feedback: string;
    keyword_analysis: {
        relevant: string[];
        missing: string[];
        score: number;
    };
    // New agentic evaluation fields
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
    // Agent-specific results
    agent_results?: {
        ats?: ATSAnalysisResult;
        experience?: ExperienceAnalysisResult;
        skills?: SkillsAnalysisResult;
        format?: FormatAnalysisResult;
        red_flags?: RedFlagAnalysisResult;
        company_fit?: CompanyFitAnalysisResult;
    };
    // Evaluation metadata
    evaluation_metadata?: {
        processing_time_seconds?: number;
        successful_agents?: number;
        total_agents?: number;
        confidence_percentage?: number;
        evaluation_type: 'agentic' | 'legacy';
    };
}

// Agent-specific result types
export interface ATSAnalysisResult {
    ats_score: number;
    parsing_issues: string[];
    keyword_optimization: {
        missing_keywords: string[];
        overused_keywords: string[];
        placement_suggestions: string[];
    };
    format_recommendations: string[];
    section_analysis: {
        contact_info: string;
        summary: string;
        experience: string;
        skills: string;
        education: string;
    };
    critical_fixes: string[];
    optimization_priority: 'high' | 'medium' | 'low';
}

export interface ExperienceAnalysisResult {
    experience_score: number;
    impact_analysis: {
        quantified_achievements: Array<{
            achievement: string;
            impact: string;
            score: number;
        }>;
        missing_metrics: string[];
        impact_strength: 'high' | 'medium' | 'low';
    };
    progression_analysis: {
        career_trajectory: 'upward' | 'lateral' | 'mixed';
        responsibility_growth: 'clear' | 'unclear' | 'missing';
        leadership_development: 'strong' | 'moderate' | 'weak';
        progression_concerns: string[];
    };
    technical_leadership: {
        architecture_experience: 'extensive' | 'moderate' | 'limited';
        team_leadership: 'strong' | 'moderate' | 'weak';
        innovation_examples: string[];
        leadership_gaps: string[];
    };
    credibility_indicators: {
        company_reputation: 'high' | 'medium' | 'low';
        project_scale: 'enterprise' | 'mid' | 'small';
        industry_recognition: 'strong' | 'moderate' | 'none';
        cross_functional_work: 'extensive' | 'moderate' | 'limited';
    };
    strengths: string[];
    improvement_areas: string[];
    rewrite_suggestions: Array<{
        current: string;
        improved: string;
    }>;
    experience_gaps: string[];
}

export interface SkillsAnalysisResult {
    skills_score: number;
    skill_analysis: {
        hot_skills_present: string[];
        hot_skills_missing: string[];
        emerging_skills: string[];
        outdated_skills: string[];
        skill_depth_indicators: {
            expert: string[];
            proficient: string[];
            familiar: string[];
        };
    };
    market_alignment: {
        demand_score: number;
        future_relevance: number;
        competitive_advantage: 'high' | 'medium' | 'low';
        skill_gaps: string[];
    };
    organization_quality: {
        categorization: 'excellent' | 'good' | 'fair' | 'poor';
        proficiency_indicators: 'clear' | 'unclear' | 'missing';
        scanning_ease: 'high' | 'medium' | 'low';
        improvement_suggestions: string[];
    };
    role_specific_analysis: {
        core_skills_coverage: number;
        missing_core_skills: string[];
        nice_to_have_skills: string[];
        overqualified_areas: string[];
    };
    recommendations: {
        add_skills: Array<{
            skill: string;
            reason: string;
            priority: 'high' | 'medium' | 'low';
        }>;
        remove_skills: Array<{
            skill: string;
            reason: string;
        }>;
        reorganize_suggestions: string[];
        proficiency_improvements: string[];
    };
    strengths: string[];
    critical_gaps: string[];
}

export interface FormatAnalysisResult {
    format_score: number;
    visual_hierarchy: {
        score: number;
        header_consistency: 'excellent' | 'good' | 'fair' | 'poor';
        font_usage: 'excellent' | 'good' | 'fair' | 'poor';
        spacing_quality: 'excellent' | 'good' | 'fair' | 'poor';
        visual_flow: 'excellent' | 'good' | 'fair' | 'poor';
        improvements: string[];
    };
    section_organization: {
        score: number;
        section_order: 'optimal' | 'good' | 'needs_improvement' | 'poor';
        section_lengths: 'balanced' | 'some_issues' | 'unbalanced';
        section_headers: 'clear' | 'unclear' | 'missing';
        section_boundaries: 'clear' | 'unclear' | 'confusing';
        recommendations: string[];
    };
    bullet_point_analysis: {
        score: number;
        consistency: 'excellent' | 'good' | 'fair' | 'poor';
        indentation: 'proper' | 'inconsistent' | 'poor';
        length_balance: 'optimal' | 'too_long' | 'too_short';
        action_verbs: 'strong' | 'moderate' | 'weak';
        improvements: string[];
    };
    contact_information: {
        score: number;
        completeness: 'complete' | 'mostly_complete' | 'incomplete';
        presentation: 'professional' | 'adequate' | 'unprofessional';
        placement: 'optimal' | 'good' | 'poor';
        readability: 'excellent' | 'good' | 'fair' | 'poor';
        issues: string[];
    };
    length_density: {
        score: number;
        overall_length: 'optimal' | 'too_long' | 'too_short';
        information_density: 'balanced' | 'too_dense' | 'too_sparse';
        white_space: 'appropriate' | 'too_much' | 'too_little';
        readability: 'excellent' | 'good' | 'fair' | 'poor';
        adjustments: string[];
    };
    professional_presentation: {
        score: number;
        overall_appeal: 'excellent' | 'good' | 'fair' | 'poor';
        consistency: 'excellent' | 'good' | 'fair' | 'poor';
        error_free: boolean;
        professional_look: 'excellent' | 'good' | 'fair' | 'poor';
        overall_impression: 'strong' | 'moderate' | 'weak';
    };
    critical_format_issues: Array<{
        issue: string;
        severity: 'critical' | 'high' | 'medium' | 'low';
        impact: string;
        fix: string;
    }>;
    format_recommendations: Array<{
        category: string;
        priority: 'high' | 'medium' | 'low';
        recommendation: string;
        impact: 'High' | 'Medium' | 'Low';
    }>;
    template_suggestions: {
        current_style: 'modern' | 'traditional' | 'creative' | 'basic';
        recommended_style: 'modern' | 'traditional' | 'creative' | 'basic';
        reasoning: string;
        template_examples: string[];
    };
}

export interface RedFlagAnalysisResult {
    red_flag_score: number;
    critical_red_flags: Array<{
        issue: string;
        severity: 'critical' | 'high' | 'medium';
        impact: string;
        evidence: string;
        fix_suggestion: string;
    }>;
    minor_concerns: Array<{
        issue: string;
        severity: 'low' | 'minor';
        impact: string;
        evidence: string;
        fix_suggestion: string;
    }>;
    pattern_analysis: {
        job_hopping: {
            detected: boolean;
            pattern: string;
            severity: 'high' | 'medium' | 'low';
            explanation_suggestions: string[];
        };
        employment_gaps: {
            detected: boolean;
            gaps: string[];
            severity: 'high' | 'medium' | 'low';
            explanation_suggestions: string[];
        };
        scale_inconsistencies: {
            detected: boolean;
            inconsistencies: string[];
            severity: 'high' | 'medium' | 'low';
            verification_suggestions: string[];
        };
    };
    quality_issues: {
        grammar_errors: string[];
        formatting_issues: string[];
        generic_language: string[];
        professionalism_concerns: string[];
    };
    credibility_concerns: {
        unverifiable_claims: string[];
        inconsistent_info: string[];
        missing_information: string[];
        suspicious_elements: string[];
    };
    technical_red_flags: {
        skill_mismatches: string[];
        impossible_achievements: string[];
        timeline_inconsistencies: string[];
        depth_inconsistencies: string[];
    };
    overall_assessment: {
        interview_risk: 'high' | 'medium' | 'low';
        competitiveness_impact: 'severe' | 'moderate' | 'minor';
        priority_fixes: string[];
        general_recommendations: string[];
    };
}

export interface CompanyFitAnalysisResult {
    company_fit_scores: {
        maang: {
            score: number;
            strengths: string[];
            gaps: string[];
            positioning_advice: string;
        };
        startups: {
            score: number;
            strengths: string[];
            gaps: string[];
            positioning_advice: string;
        };
        enterprise: {
            score: number;
            strengths: string[];
            gaps: string[];
            positioning_advice: string;
        };
    };
    overall_fit_analysis: {
        best_fit: 'maang' | 'startups' | 'enterprise' | 'mixed';
        fit_explanation: string;
        versatility_score: number;
        adaptability_indicators: string[];
    };
    positioning_strategies: {
        maang_positioning: {
            key_messages: string[];
            resume_highlights: string[];
            interview_prep: string[];
        };
        startup_positioning: {
            key_messages: string[];
            resume_highlights: string[];
            interview_prep: string[];
        };
        enterprise_positioning: {
            key_messages: string[];
            resume_highlights: string[];
            interview_prep: string[];
        };
    };
    culture_alignment: {
        work_style: 'collaborative' | 'independent' | 'mixed';
        innovation_focus: 'high' | 'medium' | 'low';
        risk_tolerance: 'high' | 'medium' | 'low';
        growth_mindset: 'strong' | 'moderate' | 'weak';
    };
    recommendations: {
        resume_tailoring: Array<{
            company_type: string;
            changes: string[];
        }>;
        skill_development: Array<{
            skill: string;
            priority: 'high' | 'medium' | 'low';
            reason: string;
        }>;
        experience_gaps: Array<{
            experience: string;
            company_types: string[];
            priority: 'high' | 'medium' | 'low';
        }>;
    };
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper function to get authentication headers
function getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    };

    // Add authentication if available
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    // In development mode, don't send any auth headers to allow backend fallback to test user

    return headers;
}

// Email Agent API endpoints
export const emailAgentApi = {
    // Get configuration status
    getConfigStatus: async () => {
        const response = await fetch(`${API_BASE_URL}/api/v1/email-agent/config/status`);
        if (!response.ok) throw new Error('Failed to get config status');
        return response.json();
    },

    // Connect Gmail
    connectGmail: async (userId: string, userEmail?: string) => {
        console.log('Connecting Gmail...', userId, userEmail)
        const response = await fetch(`${API_BASE_URL}/api/v1/email-agent/connect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, user_email: userEmail })
        });
        console.log('Response:', response)
        if (!response.ok) throw new Error('Failed to connect Gmail');
        return response.json();
    },

    // Get Gmail status
    getGmailStatus: async (userId: string) => {
        const response = await fetch(`${API_BASE_URL}/api/v1/email-agent/status/${userId}`);
        if (!response.ok) throw new Error('Failed to get Gmail status');
        return response.json();
    },

    // Process emails
    processEmails: async (userId: string, userEmail?: string) => {
        const body: any = {}
        if (userEmail) {
            body.user_email = userEmail
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/email-agent/process/${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!response.ok) throw new Error('Failed to process emails');
        return response.json();
    },

    // Disconnect Gmail
    disconnectGmail: async (userId: string) => {
        const response = await fetch(`${API_BASE_URL}/api/v1/email-agent/disconnect/${userId}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to disconnect Gmail');
        return response.json();
    },

    // Get email summary
    getEmailSummary: async (userId: string) => {
        const response = await fetch(`${API_BASE_URL}/api/v1/email-agent/summary/${userId}`);
        if (!response.ok) throw new Error('Failed to get email summary');
        return response.json();
    },

    // Get email events
    getEmailEvents: async (userId: string, limit = 50, offset = 0, emailType?: string) => {
        const params = new URLSearchParams();
        if (limit) params.append('limit', limit.toString());
        if (offset) params.append('offset', offset.toString());
        if (emailType) params.append('email_type', emailType);

        const response = await fetch(`${API_BASE_URL}/api/v1/email-agent/events/${userId}?${params}`);
        if (!response.ok) throw new Error('Failed to get email events');
        return response.json();
    },

    // Mark event as reviewed
    markEventReviewed: async (eventId: number) => {
        const response = await fetch(`${API_BASE_URL}/api/v1/email-agent/events/${eventId}/review`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to mark event as reviewed');
        return response.json();
    }
};

export async function fetchJobs(filters?: JobFilters & {
    page?: number;
    limit?: number;
    applied?: boolean;
}) {
    // Build query parameters
    const queryParams = new URLSearchParams();
    if (filters) {
        if (filters.title) queryParams.append('title', filters.title);
        if (filters.location) queryParams.append('location', filters.location);
        if (filters.company) queryParams.append('company', filters.company);
        if (filters.dateRange) {
            queryParams.append('from_date', filters.dateRange.from.toISOString());
            queryParams.append('to_date', filters.dateRange.to.toISOString());
        }
        if (filters.sortBy) queryParams.append('sort_by', filters.sortBy);
        if (filters.page !== undefined) {
            const skip = (filters.page - 1) * (filters.limit || 25);
            queryParams.append('skip', skip.toString());
        }
        if (filters.limit) queryParams.append('limit', filters.limit.toString());
        if (filters.applied !== undefined) queryParams.append('applied', filters.applied.toString());
    }

    const url = `${API_BASE_URL}/api/v1/jobs/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error("Failed to fetch jobs");
    }
    const data = await response.json();

    return data.map((job: any) => ({
        id: job.id,
        title: job.title,
        company: job.company,
        location: job.location,
        type: job.job_type,
        description: job.description,
        url: job.application_url,
        postedAt: job.posted_date ? job.posted_date.split('T')[0] : new Date().toISOString().split('T')[0],
        salary: job.salary_range,
        experience: job.experience_level,
        skills: job.skills || [],
        applied: job.applied || false,
        appliedAt: job.applied_date,
        extracted_date: job.extracted_date,
        // New status system
        application_status: job.application_status || 'pending',
        application_notes: job.application_notes,
        application_context: job.application_context,
        compatibility_score: job.compatibility_score,
        ai_insights: job.ai_insights,
    }));
}

export async function fetchJobCounts(filters?: JobFilters) {
    // Build query parameters for counts
    const queryParams = new URLSearchParams();
    if (filters) {
        if (filters.title) queryParams.append('title', filters.title);
        if (filters.location) queryParams.append('location', filters.location);
        if (filters.company) queryParams.append('company', filters.company);
        if (filters.dateRange) {
            queryParams.append('from_date', filters.dateRange.from.toISOString());
            queryParams.append('to_date', filters.dateRange.to.toISOString());
        }
        if (filters.applicationStatus && filters.applicationStatus !== 'all') {
            queryParams.append('application_status', filters.applicationStatus);
        }
    }

    const url = `${API_BASE_URL}/api/v1/jobs/counts${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error("Failed to fetch job counts");
    }

    const data = await response.json();

    // Return counts based on new status system
    return {
        total: data.total_jobs || 0,
        applied: data.applied_count || 0,
        want_to_apply: data.want_to_apply_count || 0,
        maybe_later: data.maybe_later_count || 0,
        not_interested: data.not_interested_count || 0,
        pending: data.pending_count || 0
    };
}

export async function fetchJobStats(timeRange: TimeRange = 'last_30_days'): Promise<JobStats> {
    try {
        console.log('Fetching job stats for time range:', timeRange)
        const response = await fetch(`${API_BASE_URL}/api/v1/jobs/stats?time_range=${timeRange}`);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('API Error Response:', response.status, errorText);
            throw new Error(`Failed to fetch job stats: ${response.status} ${errorText}`);
        }

        const data = await response.json();
        console.log('Raw API response:', data);

        // Map backend response to frontend interface
        const mappedData = {
            totalJobs: data.total_jobs || 0,
            appliedJobs: data.total_applied || 0,
            pendingJobs: Math.max(0, (data.total_jobs || 0) - (data.total_applied || 0)),
            responseRate: data.success_rate || 0,
            applicationsByDate: (data.daily_stats || []).map((stat: any) => ({
                date: stat.date,
                jobs_extracted: stat.jobs_extracted || 0,
                jobs_applied: stat.jobs_applied || 0,
                jobs_from_url: stat.jobs_from_url || 0,
                jobs_from_extension: stat.jobs_from_extension || 0
            }))
        };

        console.log('Mapped data:', mappedData);
        return mappedData;
    } catch (error) {
        console.error('Error in fetchJobStats:', error);
        throw error;
    }
}

export async function updateJobStatus(jobId: string, applied: boolean) {
    const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}/status`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ applied }),
    });

    if (!response.ok) {
        throw new Error("Failed to update job status");
    }
    return await response.json();
}

// New function for comprehensive status updates
export async function updateJobApplicationStatus(jobId: string, statusUpdate: any) {
    const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}/application-status`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(statusUpdate),
    });

    if (!response.ok) {
        throw new Error("Failed to update job application status");
    }
    return await response.json();
}

export interface RecentApplication {
    id: string;
    title: string;
    company: string;
    appliedAt: string;
    extracted_date: string;
    status: string;
    companyLogo?: string;
}

export async function fetchRecentApplications(limit: number = 5) {
    const response = await fetch(`${API_BASE_URL}/api/v1/jobs/recent-applications?limit=${limit}`);
    if (!response.ok) {
        throw new Error('Failed to fetch recent applications');
    }
    const data = await response.json();

    // Map backend response to frontend interface
    return data.map((app: any) => ({
        id: app.id,
        title: app.title,
        company: app.company,
        appliedAt: app.applied_date,
        extracted_date: app.extracted_date,
        status: app.status || 'Applied',
        companyLogo: app.company_logo
    }));
}

// Resume API endpoints
export const resumeApi = {
    // Upload resume
    uploadResume: async (file: File, targetRole?: string, targetSeniority?: string): Promise<ResumeFile> => {
        const formData = new FormData();
        formData.append('file', file);
        if (targetRole) formData.append('target_role', targetRole);
        if (targetSeniority) formData.append('target_seniority', targetSeniority);

        const response = await fetch(`${API_BASE_URL}/api/v1/resumes/upload`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to upload resume');
        }

        const data = await response.json();
        return {
            id: data.id,
            filename: data.original_filename,
            original_filename: data.original_filename,
            file_size: data.file_size,
            file_type: data.file_type,
            uploaded_at: data.uploaded_at,
            evaluation_status: data.evaluation_status,
        };
    },

    // Evaluate resume
    evaluateResume: async (resumeId: string, targetRole?: string, targetSeniority?: string): Promise<{message: string, process_id: string, status: string}> => {
        const response = await fetch(`${API_BASE_URL}/api/v1/resumes/${resumeId}/evaluate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                resume_id: resumeId,
                target_role: targetRole || null,
                target_seniority: targetSeniority || null
            })
        });

        if (!response.ok) {
            const error = await response.json();
            // Handle specific lock error
            if (response.status === 409) {
                throw new Error(error.detail || 'Resume is currently being evaluated by another process');
            }
            throw new Error(error.detail || 'Failed to start resume evaluation');
        }

        const data = await response.json();
        return {
            message: data.message,
            process_id: data.process_id,
            status: data.status
        };
    },

    getEvaluationProgress: async (resumeId: string): Promise<{
        resume_id: string
        evaluation_status: string
        progress: {
            status: string
            started_at: string
            stages: Record<string, {
                status: 'pending' | 'running' | 'completed' | 'failed'
                started_at: string | null
                completed_at: string | null
            }>
            overall_progress: number
        }
    }> => {
        const response = await fetch(`${API_BASE_URL}/api/v1/resumes/${resumeId}/evaluation-progress`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        })

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        return response.json()
    },

    // List resumes
    listResumes: async (): Promise<{ resumes: ResumeFile[]; totalCount: number }> => {
        const response = await fetch(`${API_BASE_URL}/api/v1/resumes/list`);
        if (!response.ok) {
            throw new Error('Failed to fetch resumes');
        }

        const data = await response.json();
        console.log('API response:', data);

        // For each resume, fetch the detailed evaluation if status is completed
        const resumesWithEvaluations = await Promise.all(
            data.resumes.map(async (r: any) => {
                const baseResume: ResumeFile = {
                    id: r.id,
                    filename: r.original_filename || r.filename || 'Untitled Resume',
                    original_filename: r.original_filename || r.filename || 'Untitled Resume',
                    file_size: r.file_size || r.size || 0,
                    file_type: r.file_type || r.type || 'unknown',
                    uploaded_at: r.uploaded_at || r.uploadedAt || new Date().toISOString(),
                    evaluation_status: r.evaluation_status || r.evaluationStatus || 'pending',
                    evaluation_result: undefined,
                };

                // If evaluation is completed, fetch the detailed results
                if (baseResume.evaluation_status === 'completed') {
                    try {
                        const detailedResponse = await fetch(`${API_BASE_URL}/api/v1/resumes/${r.id}`);
                        if (detailedResponse.ok) {
                            const detailedData = await detailedResponse.json();
                            if (detailedData.evaluation) {
                                baseResume.evaluation_result = {
                                    overall_score: detailedData.evaluation.overall_score,
                                    ats_compliance_score: detailedData.evaluation.ats_compliance_score,
                                    content_quality_score: detailedData.evaluation.content_quality_score,
                                    experience_points_score: detailedData.evaluation.experience_points_score,
                                    job_relevance_score: detailedData.evaluation.job_relevance_score,
                                    quality_checks_score: detailedData.evaluation.quality_checks_score,
                                    strengths: detailedData.evaluation.strengths || [],
                                    improvements: detailedData.evaluation.improvements || [],
                                    ats_compatibility: detailedData.evaluation.ats_compatibility,
                                    detailed_feedback: detailedData.evaluation.detailed_feedback,
                                    keyword_analysis: detailedData.evaluation.keyword_analysis || { relevant: [], missing: [], score: 0 },
                                    // Include enhanced agentic evaluation data
                                    agent_results: detailedData.evaluation.agent_results,
                                    critical_issues: detailedData.evaluation.critical_issues,
                                    market_positioning: detailedData.evaluation.market_positioning,
                                    evaluation_metadata: detailedData.evaluation.evaluation_metadata,
                                };
                            }
                        }
                    } catch (error) {
                        console.error(`Failed to fetch evaluation for resume ${r.id}:`, error);
                    }
                }

                return baseResume;
            })
        );

        return {
            resumes: resumesWithEvaluations,
            totalCount: data.total_count || data.totalCount || 0,
        };
    },

    // Get resume with evaluation
    getResume: async (resumeId: string): Promise<ResumeFile & { evaluationResult?: ResumeEvaluation }> => {
        const response = await fetch(`${API_BASE_URL}/api/v1/resumes/${resumeId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch resume');
        }

        const data = await response.json();
        return {
            id: data.resume.id,
            filename: data.resume.original_filename,
            original_filename: data.resume.original_filename,
            file_size: data.resume.file_size,
            file_type: data.resume.file_type,
            uploaded_at: data.resume.uploaded_at,
            evaluation_status: data.resume.evaluation_status,
            evaluation_result: data.evaluation ? {
                overall_score: data.evaluation.overall_score,
                ats_compliance_score: data.evaluation.ats_compliance_score,
                content_quality_score: data.evaluation.content_quality_score,
                experience_points_score: data.evaluation.experience_points_score,
                job_relevance_score: data.evaluation.job_relevance_score,
                quality_checks_score: data.evaluation.quality_checks_score,
                strengths: data.evaluation.strengths || [],
                improvements: data.evaluation.improvements || [],
                ats_compatibility: data.evaluation.ats_compatibility,
                detailed_feedback: data.evaluation.detailed_feedback,
                keyword_analysis: data.evaluation.keyword_analysis || { relevant: [], missing: [], score: 0 },
                // Include enhanced agentic evaluation data
                agent_results: data.evaluation.agent_results,
                critical_issues: data.evaluation.critical_issues,
                market_positioning: data.evaluation.market_positioning,
                evaluation_metadata: data.evaluation.evaluation_metadata,
            } : undefined,
        };
    },

    // Delete resume
    deleteResume: async (resumeId: string): Promise<void> => {
        const response = await fetch(`${API_BASE_URL}/api/v1/resumes/${resumeId}`, {
            method: 'DELETE',
        });

        if (!response.ok) {
            throw new Error('Failed to delete resume');
        }
    },

    // Get storage info
    getStorageInfo: async (): Promise<{ totalCount: number; storageUsed: number; storageLimit: number }> => {
        const response = await fetch(`${API_BASE_URL}/api/v1/resumes/storage-info`);
        if (!response.ok) {
            throw new Error('Failed to fetch storage info');
        }

        const data = await response.json();
        return {
            totalCount: data.total_count,
            storageUsed: data.storage_used,
            storageLimit: data.storage_limit,
        };
    },
};

// Profile API
export const profileApi = {
    // Get user profile with statistics
    getProfile: async (userId: string = 'current'): Promise<UserProfile> => {
        const response = await fetch(`${API_BASE_URL}/api/v1/user-profiles/${userId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch profile');
        }
        return response.json();
    },

    // Create user profile
    createProfile: async (userId: string, profileData: Partial<UserProfile>): Promise<UserProfile> => {
        const response = await fetch(`${API_BASE_URL}/api/v1/user-profiles/${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profileData),
        });
        if (!response.ok) {
            throw new Error('Failed to create profile');
        }
        return response.json();
    },

    // Update user profile
    updateProfile: async (profileData: Partial<UserProfile>, userId: string = 'current'): Promise<UserProfile> => {
        const response = await fetch(`${API_BASE_URL}/api/v1/user-profiles/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profileData),
        });
        if (!response.ok) {
            throw new Error('Failed to update profile');
        }
        return response.json();
    },

    // Get user settings
    getSettings: async (userId: string): Promise<UserSettings> => {
        const response = await fetch(`${API_BASE_URL}/api/v1/user-profiles/${userId}/settings`);
        if (!response.ok) {
            throw new Error('Failed to fetch settings');
        }
        return response.json();
    },

    // Update user settings
    updateSettings: async (userId: string, settingsData: Partial<UserSettings>): Promise<UserSettings> => {
        const response = await fetch(`${API_BASE_URL}/api/v1/user-profiles/${userId}/settings`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settingsData),
        });
        if (!response.ok) {
            throw new Error('Failed to update settings');
        }
        return response.json();
    },

    // Update notification settings
    updateNotifications: async (userId: string, notifications: Partial<UserSettings['email_notifications']>): Promise<UserSettings> => {
        const response = await fetch(`${API_BASE_URL}/api/v1/user-profiles/${userId}/settings/notifications`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(notifications),
        });
        if (!response.ok) {
            throw new Error('Failed to update notifications');
        }
        return response.json();
    },

    // Update email tracking settings
    updateEmailTracking: async (userId: string, emailSettings: { email_forwarding_enabled?: string; forwarding_address?: string; notification_frequency?: string }): Promise<UserSettings> => {
        const response = await fetch(`${API_BASE_URL}/api/v1/user-profiles/${userId}/settings/email-tracking`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(emailSettings),
        });
        if (!response.ok) {
            throw new Error('Failed to update email settings');
        }
        return response.json();
    },

    // Update privacy settings
    updatePrivacy: async (userId: string, privacySettings: { data_retention_days?: number; analytics_enabled?: string }): Promise<UserSettings> => {
        const response = await fetch(`${API_BASE_URL}/api/v1/user-profiles/${userId}/settings/privacy`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(privacySettings),
        });
        if (!response.ok) {
            throw new Error('Failed to update privacy settings');
        }
        return response.json();
    },

    // Get profile change history
    getChangeHistory: async (userId: string, limit: number = 50): Promise<ProfileChangeHistory[]> => {
        const response = await fetch(`${API_BASE_URL}/api/v1/user-profiles/${userId}/change-history?limit=${limit}`);
        if (!response.ok) {
            throw new Error('Failed to fetch change history');
        }
        return response.json();
    },
};

// Referral types and API
export interface ReferralDetailedInfo {
    // Sent email info
    sent_id: number;
    sent_at: string;
    response_received: boolean;
    response_date?: string;

    // Contact information
    contact_name: string;
    contact_email: string;
    company: string;
    position?: string;
    contact_relationship?: string;

    // Email content
    email_subject?: string;
    email_body?: string;
    template_used?: string;

    // Job information (if applicable)
    job_title?: string;
    job_company?: string;
    job_id?: number;
}

export interface ReferralDetailedListResponse {
    referrals: ReferralDetailedInfo[];
    total_count: number;
    page: number;
    page_size: number;
}

export interface ReferralFilters {
    page?: number;
    page_size?: number;
    company_filter?: string;
    date_from?: string;
    date_to?: string;
}

// Referral API endpoints
export const referralApi = {
    // Get all sent referrals with detailed information
    getSentReferrals: async (filters?: ReferralFilters): Promise<ReferralDetailedListResponse> => {
        const queryParams = new URLSearchParams();

        if (filters?.page) queryParams.append('page', filters.page.toString());
        if (filters?.page_size) queryParams.append('page_size', filters.page_size.toString());
        if (filters?.company_filter) queryParams.append('company_filter', filters.company_filter);
        if (filters?.date_from) queryParams.append('date_from', filters.date_from);
        if (filters?.date_to) queryParams.append('date_to', filters.date_to);

        const url = `${API_BASE_URL}/api/v1/referral/sent${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error('Failed to fetch sent referrals');
        }

        return response.json();
    },

    // Get referral analytics
    getAnalytics: async () => {
        const response = await fetch(`${API_BASE_URL}/api/v1/referral/analytics`);
        if (!response.ok) {
            throw new Error('Failed to fetch referral analytics');
        }
        return response.json();
    },

    // Get referral stats for dashboard
    getStats: async () => {
        const response = await fetch(`${API_BASE_URL}/api/v1/referral/stats`);
        if (!response.ok) {
            throw new Error('Failed to fetch referral stats');
        }
        return response.json();
    },

    // Mark response as received
    markResponseReceived: async (sentId: number, responseDate?: string) => {
        const body: any = {};
        if (responseDate) body.response_date = responseDate;

        const response = await fetch(`${API_BASE_URL}/api/v1/referral/responses/${sentId}/mark-received`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            throw new Error('Failed to mark response as received');
        }

        return response.json();
    },

    // Generate referral email (preview only)
    generateEmail: async (jobId: string | number, contactInfo: any) => {
        try {
            console.log('API call to:', `${API_BASE_URL}/api/v1/referral/generate-email`)
            console.log('Request payload:', {
                job_id: parseInt(String(jobId)),
                contact_info: contactInfo,
            })

            const response = await fetch(`${API_BASE_URL}/api/v1/referral/generate-email`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    job_id: parseInt(String(jobId)),
                    contact_info: contactInfo,
                }),
            });

            console.log('API response status:', response.status)

            if (!response.ok) {
                const errorText = await response.text()
                console.error('API error response:', errorText)
                throw new Error(`Failed to generate referral email: ${response.status} ${errorText}`)
            }

            const result = await response.json()
            console.log('API response data:', result)
            return result
        } catch (error) {
            console.error('API call error:', error)
            throw error
        }
    },

    // Create referral request (save draft and contact)
    createRequest: async (jobId: string | number, contactInfo: any) => {
        const response = await fetch(`${API_BASE_URL}/api/v1/referral/create-request`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                job_id: parseInt(String(jobId)),
                contact_info: contactInfo,
            }),
        });

        if (!response.ok) {
            throw new Error('Failed to create referral request');
        }

        return response.json();
    },

    // Update draft email
    updateDraft: async (draftId: string, updates: any) => {
        const response = await fetch(`${API_BASE_URL}/api/v1/referral/drafts/${draftId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates),
        });

        if (!response.ok) {
            throw new Error('Failed to update draft');
        }

        return response.json();
    },

    // Send referral email (mark as sent)
    sendEmail: async (draftId: string) => {
        const response = await fetch(`${API_BASE_URL}/api/v1/referral/send/${draftId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });

        if (!response.ok) {
            throw new Error('Failed to send referral email');
        }

        return response.json();
    },
};

// Referral Templates API
export const referralTemplatesAPI = {
    // Generate a new referral template
    generate: async (data: {
        contact_info: {
            name: string;
            email?: string;
            company: string;
            position?: string;
            company_size?: string;
            linkedin_url?: string;
        };
        job_info: {
            job_id?: string;
            title: string;
            company: string;
            industry?: string;
            level?: string;
            description?: string;
            user_background?: string;
        };
        user_preferences?: {
            preferred_tone?: string;
            preferred_length?: string;
            include_resume?: boolean;
            include_portfolio?: boolean;
        };
    }) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/referral-templates/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeaders()
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                const errorData = await response.text();
                console.error('Referral template API error:', {
                    status: response.status,
                    statusText: response.statusText,
                    body: errorData
                });
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return response.json();
        } catch (error) {
            console.error('Referral template generation failed:', error);
            throw error;
        }
    },

    // Get user's templates
    getTemplates: async (limit: number = 20, offset: number = 0) => {
        const response = await fetch(`${API_BASE_URL}/api/v1/referral-templates/?limit=${limit}&offset=${offset}`, {
            method: 'GET',
            headers: getAuthHeaders(),
        });

        if (!response.ok) {
            throw new Error('Failed to fetch templates');
        }

        return response.json();
    },

    // Get template statistics
    getStats: async () => {
        const response = await fetch(`${API_BASE_URL}/api/v1/referral-templates/stats`, {
            method: 'GET',
            headers: getAuthHeaders(),
        });

        if (!response.ok) {
            throw new Error('Failed to fetch template stats');
        }

        return response.json();
    },

    // Get specific template
    getTemplate: async (templateId: string) => {
        const response = await fetch(`${API_BASE_URL}/api/v1/referral-templates/${templateId}`, {
            method: 'GET',
            headers: getAuthHeaders(),
        });

        if (!response.ok) {
            throw new Error('Failed to fetch template');
        }

        return response.json();
    },

    // Mark template as sent
    markSent: async (templateId: string) => {
        const response = await fetch(`${API_BASE_URL}/api/v1/referral-templates/${templateId}/mark-sent`, {
            method: 'POST',
            headers: getAuthHeaders(),
        });

        if (!response.ok) {
            throw new Error('Failed to mark template as sent');
        }

        return response.json();
    },

    // Record feedback
    recordFeedback: async (templateId: string, feedback: {
        got_response: boolean;
        response_type?: string;
        response_quality_score?: number;
        user_satisfaction_score?: number;
        feedback_notes?: string;
    }) => {
        const response = await fetch(`${API_BASE_URL}/api/v1/referral-templates/${templateId}/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify(feedback),
        });

        if (!response.ok) {
            throw new Error('Failed to record feedback');
        }

        return response.json();
    },

    // Delete template
    deleteTemplate: async (templateId: string) => {
        const response = await fetch(`${API_BASE_URL}/api/v1/referral-templates/${templateId}`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
        });

        if (!response.ok) {
            throw new Error('Failed to delete template');
        }

        return response.json();
    },

    // Get user preferences
    getPreferences: async () => {
        const response = await fetch(`${API_BASE_URL}/api/v1/referral-templates/preferences/current`, {
            method: 'GET',
            headers: getAuthHeaders(),
        });

        if (!response.ok) {
            throw new Error('Failed to fetch preferences');
        }

        return response.json();
    },

    // Update user preferences
    updatePreferences: async (preferences: any) => {
        const response = await fetch(`${API_BASE_URL}/api/v1/referral-templates/preferences`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify(preferences),
        });

        if (!response.ok) {
            throw new Error('Failed to update preferences');
        }

        return response.json();
    },
};