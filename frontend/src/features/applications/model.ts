import type { JobApiResponse, RecentApplication } from '@/app/lib/api/types';

export type ApplicationStatus =
  | 'applied'
  | 'interview_scheduled'
  | 'want_to_apply'
  | 'not_interested'
  | string;

export interface TrackedApplication {
  id: string;
  title: string;
  company: string;
  location: string;
  salary: string;
  status: ApplicationStatus;
  appliedDate: string | null;
  source: string;
  compatibilityScore: number;
  notes: string;
  sourceUrl?: string;
  extractedAt?: string;
}

export interface ApplicationStats {
  total: number;
  applied: number;
  interviews: number;
  averageCompatibilityScore: number;
}

export interface ExtractedJobPayload {
  job_id?: string;
  id?: string;
  extracted_job?: {
    title?: string;
    company?: string;
    location?: string;
    application_url?: string;
  };
  title?: string;
  company?: string;
  location?: string;
  original_url?: string;
}

export interface JobDetails {
  id: string;
  title: string;
  company: string;
  location: string;
  jobType?: string;
  experienceLevel?: string;
  salaryRange?: string;
  postedDate?: string;
  description?: string;
  requirements?: string;
  skills: string[];
  applicationUrl?: string;
}

export function normalizeApplicationStatus(status?: string): ApplicationStatus {
  return status ? status.toLowerCase().replace(/\s+/g, '_') : 'applied';
}

function deriveSource(source?: string): string {
  if (!source) return 'Manual';
  return source === 'url_extraction' ? 'URL Extraction' : source;
}

export function mapRecentApplication(app: RecentApplication): TrackedApplication {
  return {
    id: app.id,
    title: app.title || 'Unknown Position',
    company: app.company || 'Unknown Company',
    location: app.location || 'Remote',
    salary: app.salary || 'TBD',
    status: normalizeApplicationStatus(app.status),
    appliedDate: app.appliedAt ? app.appliedAt.split('T')[0] : null,
    source: deriveSource(app.applicationSource),
    compatibilityScore: app.compatibilityScore || 0,
    notes: '',
    sourceUrl: app.sourceUrl,
  };
}

export function mapJobDetails(job: JobApiResponse): JobDetails {
  return {
    id: String(job.id),
    title: job.title || 'Unknown Position',
    company: job.company || 'Unknown Company',
    location: job.location || 'Remote',
    jobType: job.job_type,
    experienceLevel: job.experience_level,
    salaryRange: job.salary_range,
    postedDate: job.posted_date,
    description: job.description,
    requirements: job.requirements,
    skills: Array.isArray(job.skills) ? job.skills : [],
    applicationUrl: job.application_url || job.source_url,
  };
}

export function createExtractedApplication(job: ExtractedJobPayload): TrackedApplication {
  const fallbackId = job.job_id || job.id || (
    typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : `${Date.now()}`
  );
  const now = new Date().toISOString();

  return {
    id: String(fallbackId),
    title: job.extracted_job?.title || job.title || 'Unknown Position',
    company: job.extracted_job?.company || job.company || 'Unknown Company',
    location: job.extracted_job?.location || job.location || 'Remote',
    salary: 'TBD',
    status: 'applied',
    appliedDate: now,
    source: 'URL Extraction',
    compatibilityScore: 0,
    notes: '',
    sourceUrl: job.extracted_job?.application_url || job.original_url,
    extractedAt: now,
  };
}

export function filterApplications(
  applications: TrackedApplication[],
  searchTerm: string,
  statusFilter: string,
): TrackedApplication[] {
  const normalizedSearch = searchTerm.trim().toLowerCase();
  return applications.filter((application) => {
    const matchesSearch = !normalizedSearch
      || application.title.toLowerCase().includes(normalizedSearch)
      || application.company.toLowerCase().includes(normalizedSearch);
    const matchesStatus = statusFilter === 'all' || application.status === statusFilter;
    return matchesSearch && matchesStatus;
  });
}

export function summarizeApplications(applications: TrackedApplication[]): ApplicationStats {
  const compatibilityTotal = applications.reduce(
    (total, application) => total + application.compatibilityScore,
    0,
  );

  return {
    total: applications.length,
    applied: applications.filter((application) => application.status === 'applied').length,
    interviews: applications.filter(
      (application) => application.status === 'interview_scheduled',
    ).length,
    averageCompatibilityScore: applications.length
      ? Math.round(compatibilityTotal / applications.length)
      : 0,
  };
}
