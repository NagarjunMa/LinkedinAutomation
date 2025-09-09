export interface Job {
  id: string
  title: string
  company: string
  location: string
  postedAt: string
  type: string
  applied: boolean
  appliedAt?: string
  url?: string
  description?: string
  salary?: string
  experience?: string
  job_type?: string
  experience_level?: string
  requirements?: string
  salary_range?: string
  posted_date?: string
  application_url?: string
  source_url?: string
  source?: string
  is_active?: boolean
  extracted_date?: string
  // New status system
  application_status?: 'applied' | 'want_to_apply' | 'maybe_later' | 'not_interested'
  application_notes?: string
  application_context?: string
  compatibility_score?: number
  ai_insights?: string
}

export interface JobFilters {
    title?: string
    company?: string
    location?: string
    job_type?: string
    experience_level?: string
    sortBy?: 'newest' | 'oldest'
    applicationStatus?: 'all' | 'applied' | 'not_applied' | 'want_to_apply' | 'maybe_later' | 'not_interested'
    dateRange?: {
        from: Date
        to: Date
    }
}

// New interface for status updates
export interface JobStatusUpdate {
  status: 'applied' | 'want_to_apply' | 'maybe_later' | 'not_interested'
  date?: string // ISO date string for applied status
  notes?: string
  context?: string
}

export interface JobSearchParams {
    title?: string
    location?: string
    keywords?: string
    job_type?: string
    experience_level?: string
    date_posted?: string
    salary_range?: string
}

export interface SearchQuery {
    id: number
    title: string
    location?: string
    keywords?: string
    job_type?: string
    experience_level?: string
    created_at: string
    is_active: boolean
    schedule?: string
    last_run?: string
}

export interface ChartDataItem {
    date: string
    jobs_extracted: number
    jobs_applied: number
} 