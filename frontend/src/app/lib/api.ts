

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
    uploadResume: async (file: File, targetRole?: string, targetIndustry?: string): Promise<ResumeFile> => {
        const formData = new FormData();
        formData.append('file', file);
        if (targetRole) formData.append('target_role', targetRole);
        if (targetIndustry) formData.append('target_industry', targetIndustry);

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
    evaluateResume: async (resumeId: string, targetRole?: string, targetIndustry?: string): Promise<void> => {
        const response = await fetch(`${API_BASE_URL}/api/v1/resumes/${resumeId}/evaluate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                resume_id: resumeId,
                target_role: targetRole || null,
                target_industry: targetIndustry || null
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to start resume evaluation');
        }
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