

import { JobStats, TimeRange } from '../types/stats';
import type { JobFilters } from '../types/job';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchJobs(filters?: JobFilters) {
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
    }));
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
                jobs_applied: stat.jobs_applied || 0
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