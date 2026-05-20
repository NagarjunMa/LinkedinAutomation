import { JobStats, TimeRange } from '../../types/stats';
import type { JobFilters } from '../../types/job';
import {
    JobApiResponse,
    DailyStatsResponse,
    RecentApplicationResponse,
    RecentApplication,
    JobApplicationStatusUpdate
} from './types';
import { makeAPIRequest } from './config';

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

    const url = `/api/v1/jobs/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const data = await makeAPIRequest<JobApiResponse[]>(url);

    return data.map((job) => ({
        id: job.id,
        title: job.title,
        company: job.company,
        location: job.location ?? '',
        type: job.job_type ?? '',
        description: job.description ?? '',
        url: job.application_url ?? '',
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

    const url = `/api/v1/jobs/counts${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const data = await makeAPIRequest<Record<string, number>>(url);

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
    const url = `/api/v1/jobs/stats?time_range=${timeRange}`;
    const data = await makeAPIRequest<Record<string, unknown>>(url);

    // Map backend response to frontend interface
    return {
        totalJobs: (typeof data.total_jobs === 'number' ? data.total_jobs : 0) || 0,
        appliedJobs: (typeof data.total_applied === 'number' ? data.total_applied : 0) || 0,
        pendingJobs: Math.max(0, ((typeof data.total_jobs === 'number' ? data.total_jobs : 0) || 0) - ((typeof data.total_applied === 'number' ? data.total_applied : 0) || 0)),
        responseRate: (typeof data.success_rate === 'number' ? data.success_rate : 0) || 0,
        successRate: (typeof data.success_rate === 'number' ? data.success_rate : 0) || 0,
        successRateChange: (typeof data.success_rate_change === 'number' ? data.success_rate_change : 0) || 0,
        interviews: ((typeof data.interview_count === 'number' ? data.interview_count : 0) || (typeof data.interviews === 'number' ? data.interviews : 0)) || 0,
        todayApplications: (typeof data.today_applications === 'number' ? data.today_applications : 0) || 0,
        todayProfiles: (typeof data.today_profiles === 'number' ? data.today_profiles : 0) || 0,
        todayMessages: (typeof data.today_messages === 'number' ? data.today_messages : 0) || 0,
        applicationsByDate: ((Array.isArray(data.daily_stats) ? data.daily_stats : []) as DailyStatsResponse[]).map((stat) => ({
            date: stat.date,
            jobs_extracted: stat.jobs_extracted || 0,
            jobs_applied: stat.jobs_applied || 0,
            jobs_from_url: stat.jobs_from_url || 0,
            jobs_from_extension: stat.jobs_from_extension || 0
        }))
    };
}

export async function updateJobStatus(jobId: string, applied: boolean) {
    const url = `/api/v1/jobs/${jobId}/status`;
    return makeAPIRequest(url, {
        method: 'PUT',
        body: JSON.stringify({ applied }),
    });
}

export async function updateJobApplicationStatus(jobId: string, statusUpdate: JobApplicationStatusUpdate) {
    const url = `/api/v1/jobs/${jobId}/application-status`;
    return makeAPIRequest(url, {
        method: 'PUT',
        body: JSON.stringify(statusUpdate),
    });
}

export async function fetchRecentApplications(limit: number = 5): Promise<RecentApplication[]> {
    const url = `/api/v1/jobs/recent-applications?limit=${limit}`;
    const data = await makeAPIRequest<RecentApplicationResponse[]>(url);

    // Map backend response to frontend interface
    return data.map((app) => ({
        id: app.id,
        title: app.title ?? 'Unknown Position',
        company: app.company ?? 'Unknown Company',
        appliedAt: app.applied_date || '',
        extracted_date: app.extracted_date || '',
        status: app.status || 'Applied',
        companyLogo: app.company_logo,
        location: (typeof app.location === 'string' ? app.location : 'Remote') || 'Remote',
        salary: (typeof app.salary_range === 'string' ? app.salary_range : 'Not specified') || 'Not specified',
        applicationSource: (typeof app.application_source === 'string' ? app.application_source : 'Manual') || 'Manual',
        sourceUrl: (typeof app.source_url === 'string' ? app.source_url : undefined),
        compatibilityScore: (typeof app.compatibility_score === 'number' ? app.compatibility_score : 0) || 0
    }));
}