export interface JobStats {
    totalJobs: number;
    appliedJobs: number;
    pendingJobs: number;
    responseRate: number;
    applicationsByDate: {
        date: string;
        jobs_extracted: number;
        jobs_applied: number;
        jobs_from_url?: number;
        jobs_from_extension?: number;
    }[];
}

export type TimeRange = 'last_7_days' | 'last_30_days' | 'last_3_months' | 'all_time'; 