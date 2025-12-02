// Enhanced API wrapper using the new error handling system
import { apiRequest, ApiError } from './api-error-handler';
import type { JobFilters } from '../app/types/job';
import type { JobStats, TimeRange } from '../app/types/stats';
import {
  UserProfile,
  UserSettings,
  ProfileChangeHistory,
  ResumeFile,
  ResumeEvaluation,
  RecentApplication,
  JobApiResponse,
  DailyStatsResponse,
  RecentApplicationResponse,
  ResumeListItemResponse,
  JobApplicationStatusUpdate
} from '../app/lib/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface JobCountsResponse {
  total_jobs?: number;
  applied_count?: number;
  want_to_apply_count?: number;
  maybe_later_count?: number;
  not_interested_count?: number;
  pending_count?: number;
}

interface JobStatsApiResponse {
  total_jobs?: number;
  total_applied?: number;
  success_rate?: number;
  success_rate_change?: number;
  interview_count?: number;
  interviews?: number;
  today_applications?: number;
  today_profiles?: number;
  today_messages?: number;
  daily_stats?: DailyStatsResponse[];
}

interface ResumeUploadResponse {
  id: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  uploaded_at: string;
  evaluation_status: string;
}

interface ResumeListResponse {
  resumes: ResumeListItemResponse[];
  total_count?: number;
  totalCount?: number;
}

interface ResumeDetailResponse {
  resume: ResumeFile;
  evaluation?: ResumeEvaluation;
}

interface StorageInfoResponse {
  total_count: number;
  storage_used: number;
  storage_limit: number;
}

// Enhanced Email Agent API endpoints with error handling
export const enhancedEmailAgentApi = {
  // Get configuration status
  getConfigStatus: async () => {
    return apiRequest.get(`${API_BASE_URL}/api/v1/email-agent/config/status`, {
      silentErrors: [404] // Don't show error toast for 404s
    });
  },

  // Connect Gmail
  connectGmail: async (userId: string, userEmail?: string) => {
    console.log('Connecting Gmail...', userId, userEmail);
    return apiRequest.post(`${API_BASE_URL}/api/v1/email-agent/connect`, {
      user_id: userId,
      user_email: userEmail
    }, {
      timeout: 60000, // 60 second timeout for auth flow
      retries: { maxRetries: 1 } // Don't retry auth requests
    });
  },

  // Get Gmail status
  getGmailStatus: async (userId: string) => {
    return apiRequest.get(`${API_BASE_URL}/api/v1/email-agent/status/${userId}`, {
      silentErrors: [404]
    });
  },

  // Process emails
  processEmails: async (userId: string, userEmail?: string) => {
    const body: Record<string, string> = {};
    if (userEmail) {
      body.user_email = userEmail;
    }

    return apiRequest.post(`${API_BASE_URL}/api/v1/email-agent/process/${userId}`, body, {
      timeout: 120000, // 2 minute timeout for processing
      retries: { maxRetries: 1 } // Limit retries for long operations
    });
  },

  // Disconnect Gmail
  disconnectGmail: async (userId: string) => {
    return apiRequest.delete(`${API_BASE_URL}/api/v1/email-agent/disconnect/${userId}`, {
      retries: { maxRetries: 1 }
    });
  },

  // Get email summary
  getEmailSummary: async (userId: string) => {
    return apiRequest.get(`${API_BASE_URL}/api/v1/email-agent/summary/${userId}`, {
      silentErrors: [404]
    });
  },

  // Get email events
  getEmailEvents: async (userId: string, limit = 50, offset = 0, emailType?: string) => {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    if (emailType) params.append('email_type', emailType);

    return apiRequest.get(`${API_BASE_URL}/api/v1/email-agent/events/${userId}?${params}`, {
      silentErrors: [404]
    });
  },

  // Mark event as reviewed
  markEventReviewed: async (eventId: number) => {
    return apiRequest.post(`${API_BASE_URL}/api/v1/email-agent/events/${eventId}/review`);
  }
};

// Enhanced Jobs API
export async function enhancedFetchJobs(filters?: JobFilters & {
  page?: number;
  limit?: number;
  applied?: boolean;
}) {
  try {
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

    const data = await apiRequest.get<JobApiResponse[]>(url, {
      retries: { maxRetries: 2 }
    });

    return data.map((job) => ({
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
      application_status: job.application_status || 'pending',
      application_notes: job.application_notes,
      application_context: job.application_context,
      compatibility_score: job.compatibility_score,
      ai_insights: job.ai_insights,
    }));
  } catch (error) {
    if (error instanceof Error && (error as ApiError).status === 404) {
      return []; // Return empty array for 404s
    }
    throw error;
  }
}

export async function enhancedFetchJobCounts(filters?: JobFilters) {
  try {
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

    const data = await apiRequest.get<JobCountsResponse>(url, {
      retries: { maxRetries: 2 }
    });

    return {
      total: data.total_jobs || 0,
      applied: data.applied_count || 0,
      want_to_apply: data.want_to_apply_count || 0,
      maybe_later: data.maybe_later_count || 0,
      not_interested: data.not_interested_count || 0,
      pending: data.pending_count || 0
    };
  } catch (error) {
    if (error instanceof Error && (error as ApiError).status === 404) {
      return {
        total: 0,
        applied: 0,
        want_to_apply: 0,
        maybe_later: 0,
        not_interested: 0,
        pending: 0
      };
    }
    throw error;
  }
}

export async function enhancedFetchJobStats(timeRange: TimeRange = 'last_30_days'): Promise<JobStats> {
  try {
    console.log('Fetching job stats for time range:', timeRange);

    const data = await apiRequest.get<JobStatsApiResponse>(`${API_BASE_URL}/api/v1/jobs/stats?time_range=${timeRange}`, {
      retries: { maxRetries: 2 },
      timeout: 30000
    });

    console.log('Raw API response:', data);

    const mappedData = {
      totalJobs: data.total_jobs || 0,
      appliedJobs: data.total_applied || 0,
      pendingJobs: Math.max(0, (data.total_jobs || 0) - (data.total_applied || 0)),
      responseRate: data.success_rate || 0,
      successRate: data.success_rate || 0,
      successRateChange: data.success_rate_change || 0,
      interviews: data.interview_count || data.interviews || 0,
      todayApplications: data.today_applications || 0,
      todayProfiles: data.today_profiles || 0,
      todayMessages: data.today_messages || 0,
      applicationsByDate: (data.daily_stats || []).map((stat: DailyStatsResponse) => ({
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
    console.error('Error in enhancedFetchJobStats:', error);

    // Return default values for certain errors instead of failing
    if (error instanceof Error && (error as ApiError).status === 404) {
      return {
        totalJobs: 0,
        appliedJobs: 0,
        pendingJobs: 0,
        responseRate: 0,
        successRate: 0,
        successRateChange: 0,
        interviews: 0,
        todayApplications: 0,
        todayProfiles: 0,
        todayMessages: 0,
        applicationsByDate: []
      };
    }
    throw error;
  }
}

export async function enhancedUpdateJobStatus(jobId: string, applied: boolean) {
  return apiRequest.put(`${API_BASE_URL}/api/v1/jobs/${jobId}/status`, { applied }, {
    retries: { maxRetries: 2 }
  });
}

export async function enhancedUpdateJobApplicationStatus(jobId: string, statusUpdate: JobApplicationStatusUpdate) {
  return apiRequest.put(`${API_BASE_URL}/api/v1/jobs/${jobId}/application-status`, statusUpdate, {
    retries: { maxRetries: 2 }
  });
}

export async function enhancedFetchRecentApplications(limit: number = 5): Promise<RecentApplication[]> {
  try {
    const data = await apiRequest.get<RecentApplicationResponse[]>(`${API_BASE_URL}/api/v1/jobs/recent-applications?limit=${limit}`, {
      silentErrors: [404]
    });

    return data.map((app) => ({
      id: app.id,
      title: app.title,
      company: app.company,
      appliedAt: app.applied_date,
      extracted_date: app.extracted_date,
      status: app.status || 'Applied',
      companyLogo: app.company_logo,
      location: app.location,
      salary: app.salary_range,
      applicationSource: app.application_source,
      sourceUrl: app.source_url,
      compatibilityScore: app.compatibility_score
    }));
  } catch (error) {
    if (error instanceof Error && (error as ApiError).status === 404) {
      return [];
    }
    throw error;
  }
}

// Enhanced Resume API endpoints
export const enhancedResumeApi = {
  // Upload resume with enhanced error handling
  uploadResume: async (file: File, targetRole?: string, targetSeniority?: string): Promise<ResumeFile> => {
    const formData = new FormData();
    formData.append('file', file);
    if (targetRole) formData.append('target_role', targetRole);
    if (targetSeniority) formData.append('target_seniority', targetSeniority);

    const data = await apiRequest.post<ResumeUploadResponse>(`${API_BASE_URL}/api/v1/resumes/upload`, formData, {
      headers: {}, // Let browser set Content-Type for FormData
      timeout: 60000, // 60s timeout for uploads
      retries: { maxRetries: 1 } // Limited retries for uploads
    });

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

  // Evaluate resume with specialized error handling
  evaluateResume: async (resumeId: string, targetRole?: string, targetSeniority?: string): Promise<{message: string, process_id: string, status: string}> => {
    try {
      return await apiRequest.post(`${API_BASE_URL}/api/v1/resumes/${resumeId}/evaluate`, {
        resume_id: resumeId,
        target_role: targetRole || null,
        target_seniority: targetSeniority || null
      }, {
        timeout: 120000, // 2 minute timeout
        retries: { maxRetries: 1 }
      });
    } catch (error) {
      // Handle 409 conflicts (resume already being evaluated)
      if (error instanceof Error && (error as ApiError).status === 409) {
        throw new Error('Resume is currently being evaluated by another process. Please wait and try again.');
      }
      throw error;
    }
  },

  getEvaluationProgress: async (resumeId: string) => {
    return apiRequest.get(`${API_BASE_URL}/api/v1/resumes/${resumeId}/evaluation-progress`, {
      timeout: 10000,
      retries: { maxRetries: 3 }
    });
  },

  // List resumes with error handling
  listResumes: async (): Promise<{ resumes: ResumeFile[]; totalCount: number }> => {
    try {
      const data = await apiRequest.get<ResumeListResponse>(`${API_BASE_URL}/api/v1/resumes/list`, {
        retries: { maxRetries: 2 }
      });

      console.log('API response:', data);

      // Process resumes with detailed evaluations
      const resumesWithEvaluations = await Promise.all(
        data.resumes.map(async (r: ResumeListItemResponse) => {
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

          // Fetch detailed evaluation if completed
          if (baseResume.evaluation_status === 'completed') {
            try {
              const detailedData = await apiRequest.get<ResumeDetailResponse>(`${API_BASE_URL}/api/v1/resumes/${r.id}`, {
                silentErrors: [404, 500], // Don't fail the whole list if one evaluation fails
                retries: { maxRetries: 1 }
              });

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
                  agent_results: detailedData.evaluation.agent_results,
                  critical_issues: detailedData.evaluation.critical_issues,
                  market_positioning: detailedData.evaluation.market_positioning,
                  evaluation_metadata: detailedData.evaluation.evaluation_metadata,
                };
              }
            } catch (error) {
              console.error(`Failed to fetch evaluation for resume ${r.id}:`, error);
              // Continue with other resumes
            }
          }

          return baseResume;
        })
      );

      return {
        resumes: resumesWithEvaluations,
        totalCount: data.total_count || data.totalCount || 0,
      };
    } catch (error) {
      if (error instanceof Error && (error as ApiError).status === 404) {
        return { resumes: [], totalCount: 0 };
      }
      throw error;
    }
  },

  // Get resume with evaluation
  getResume: async (resumeId: string): Promise<ResumeFile & { evaluationResult?: ResumeEvaluation }> => {
    const data = await apiRequest.get<ResumeDetailResponse>(`${API_BASE_URL}/api/v1/resumes/${resumeId}`, {
      retries: { maxRetries: 2 }
    });

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
        agent_results: data.evaluation.agent_results,
        critical_issues: data.evaluation.critical_issues,
        market_positioning: data.evaluation.market_positioning,
        evaluation_metadata: data.evaluation.evaluation_metadata,
      } : undefined,
    };
  },

  // Delete resume
  deleteResume: async (resumeId: string): Promise<void> => {
    await apiRequest.delete(`${API_BASE_URL}/api/v1/resumes/${resumeId}`, {
      retries: { maxRetries: 2 }
    });
  },

  // Get storage info
  getStorageInfo: async (): Promise<{ totalCount: number; storageUsed: number; storageLimit: number }> => {
    const data = await apiRequest.get<StorageInfoResponse>(`${API_BASE_URL}/api/v1/resumes/storage-info`, {
      retries: { maxRetries: 2 }
    });

    return {
      totalCount: data.total_count,
      storageUsed: data.storage_used,
      storageLimit: data.storage_limit,
    };
  },
};

// Enhanced Profile API
export const enhancedProfileApi = {
  getProfile: async (userId: string = 'current'): Promise<UserProfile> => {
    return apiRequest.get(`${API_BASE_URL}/api/v1/user-profiles/${userId}`, {
      retries: { maxRetries: 2 }
    });
  },

  createProfile: async (userId: string, profileData: Partial<UserProfile>): Promise<UserProfile> => {
    return apiRequest.post(`${API_BASE_URL}/api/v1/user-profiles/${userId}`, profileData, {
      retries: { maxRetries: 1 }
    });
  },

  updateProfile: async (profileData: Partial<UserProfile>, userId: string = 'current'): Promise<UserProfile> => {
    return apiRequest.put(`${API_BASE_URL}/api/v1/user-profiles/${userId}`, profileData, {
      retries: { maxRetries: 2 }
    });
  },

  getSettings: async (userId: string): Promise<UserSettings> => {
    return apiRequest.get(`${API_BASE_URL}/api/v1/user-profiles/${userId}/settings`, {
      retries: { maxRetries: 2 }
    });
  },

  updateSettings: async (userId: string, settingsData: Partial<UserSettings>): Promise<UserSettings> => {
    return apiRequest.put(`${API_BASE_URL}/api/v1/user-profiles/${userId}/settings`, settingsData, {
      retries: { maxRetries: 2 }
    });
  },

  updateNotifications: async (userId: string, notifications: Partial<UserSettings['email_notifications']>): Promise<UserSettings> => {
    return apiRequest.put(`${API_BASE_URL}/api/v1/user-profiles/${userId}/settings/notifications`, notifications, {
      retries: { maxRetries: 2 }
    });
  },

  updateEmailTracking: async (userId: string, emailSettings: { email_forwarding_enabled?: string; forwarding_address?: string; notification_frequency?: string }): Promise<UserSettings> => {
    return apiRequest.put(`${API_BASE_URL}/api/v1/user-profiles/${userId}/settings/email-tracking`, emailSettings, {
      retries: { maxRetries: 2 }
    });
  },

  updatePrivacy: async (userId: string, privacySettings: { data_retention_days?: number; analytics_enabled?: string }): Promise<UserSettings> => {
    return apiRequest.put(`${API_BASE_URL}/api/v1/user-profiles/${userId}/settings/privacy`, privacySettings, {
      retries: { maxRetries: 2 }
    });
  },

  getChangeHistory: async (userId: string, limit: number = 50): Promise<ProfileChangeHistory[]> => {
    return apiRequest.get(`${API_BASE_URL}/api/v1/user-profiles/${userId}/change-history?limit=${limit}`, {
      retries: { maxRetries: 2 }
    });
  },
};