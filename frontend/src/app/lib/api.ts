

import { JobStats, TimeRange } from '../types/stats';
import type { JobFilters } from '../types/job';

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
        processing_time_seconds: number;
        successful_agents: number;
        total_agents: number;
        confidence_percentage: number;
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