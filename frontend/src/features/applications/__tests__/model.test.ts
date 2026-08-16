import { describe, expect, it } from 'vitest';
import {
  createExtractedApplication,
  filterApplications,
  mapJobDetails,
  mapRecentApplication,
  summarizeApplications,
  type TrackedApplication,
} from '../model';

const applications: TrackedApplication[] = [
  {
    id: '1',
    title: 'Backend Engineer',
    company: 'Acme',
    location: 'New York',
    salary: '$150k',
    status: 'applied',
    appliedDate: '2026-08-01',
    source: 'Manual',
    compatibilityScore: 80,
    notes: '',
  },
  {
    id: '2',
    title: 'ML Engineer',
    company: 'Northstar',
    location: 'Remote',
    salary: 'TBD',
    status: 'interview_scheduled',
    appliedDate: '2026-08-02',
    source: 'URL Extraction',
    compatibilityScore: 90,
    notes: '',
  },
];

describe('applications model', () => {
  it('maps recent API records into stable display values', () => {
    const result = mapRecentApplication({
      id: 'job-1',
      title: 'Platform Engineer',
      company: 'Acme',
      appliedAt: '2026-08-15T10:30:00Z',
      extracted_date: '2026-08-15T10:00:00Z',
      status: 'Interview Scheduled',
      applicationSource: 'url_extraction',
    });

    expect(result).toMatchObject({
      id: 'job-1',
      status: 'interview_scheduled',
      appliedDate: '2026-08-15',
      source: 'URL Extraction',
      location: 'Remote',
    });
  });

  it('filters by normalized search and status', () => {
    expect(filterApplications(applications, '  acme ', 'applied')).toEqual([applications[0]]);
    expect(filterApplications(applications, 'engineer', 'interview_scheduled')).toEqual([applications[1]]);
  });

  it('computes application summary values once for the view', () => {
    expect(summarizeApplications(applications)).toEqual({
      total: 2,
      applied: 1,
      interviews: 1,
      averageCompatibilityScore: 85,
    });
  });

  it('maps job details without coercing skill arrays into display strings', () => {
    expect(mapJobDetails({
      id: 42,
      title: 'Software Engineer',
      company: 'Prism',
      skills: ['Python', 'React'],
      source_url: 'https://example.com/jobs/42',
    })).toMatchObject({
      id: '42',
      skills: ['Python', 'React'],
      applicationUrl: 'https://example.com/jobs/42',
    });
  });

  it('creates immediate extraction feedback from the returned job payload', () => {
    const result = createExtractedApplication({
      job_id: 'job-9',
      extracted_job: {
        title: 'Founding Engineer',
        company: 'Launch Co',
        application_url: 'https://example.com/apply',
      },
    });

    expect(result).toMatchObject({
      id: 'job-9',
      title: 'Founding Engineer',
      company: 'Launch Co',
      source: 'URL Extraction',
      sourceUrl: 'https://example.com/apply',
    });
  });
});
