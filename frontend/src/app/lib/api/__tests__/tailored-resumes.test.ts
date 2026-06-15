import { describe, expect, it } from 'vitest';
import { server, http, HttpResponse } from '@/test-utils/msw-server';
import { tailoredResumesApi } from '@/app/lib/api/tailored-resumes';

describe('tailoredResumesApi', () => {
  it('lists and gets tailored resume details', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/tailored-resumes', () => {
        return HttpResponse.json([
          {
            version_id: 'ver-1',
            resume_document_id: 'doc-1',
            source_filename: 'base.pdf',
            company_name: 'Acme',
            target_role_title: 'Senior Backend Engineer',
            role_category: 'SWE',
            seniority: 'senior',
            country_hint: 'US',
            match_score: 88,
            template_id: 'us-swe',
            accepted_change_count: 2,
            created_at: '2026-06-15T00:00:00Z',
            accepted_at: '2026-06-15T00:00:00Z',
          },
        ]);
      }),
      http.get('http://localhost:8000/api/v1/tailored-resumes/ver-1', () => {
        return HttpResponse.json({
          version_id: 'ver-1',
          resume_document_id: 'doc-1',
          source_filename: 'base.pdf',
          company_name: 'Acme',
          target_role_title: 'Senior Backend Engineer',
          role_category: 'SWE',
          seniority: 'senior',
          country_hint: 'US',
          match_score: 88,
          template_id: 'us-swe',
          accepted_change_count: 2,
          created_at: '2026-06-15T00:00:00Z',
          accepted_at: '2026-06-15T00:00:00Z',
          resume_json: {
            contact: { name: 'Test User', email: null, phone: null, links: [] },
            summary: null,
            experience: [],
            education: [],
            skills: { hard: [], soft: [] },
            projects: [],
            certifications: [],
            raw_text: 'Test User',
          },
          source_jd_text: 'JD text',
          extracted_requirements: { company_name: 'Acme' },
          diff_plan: {},
          accepted_changes: [],
        });
      })
    );

    const list = await tailoredResumesApi.list();
    expect(list[0].company_name).toBe('Acme');

    const detail = await tailoredResumesApi.get('ver-1');
    expect(detail.resume_json.contact.name).toBe('Test User');
    expect(detail.source_jd_text).toBe('JD text');
  });

  it('downloads PDF bytes from saved JSON route', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/tailored-resumes/ver-1/download', async ({ request }) => {
        const body = await request.json() as Record<string, unknown>;
        expect(body.template_id).toBe('us-swe');
        return new HttpResponse('%PDF-test', {
          headers: { 'Content-Type': 'application/pdf' },
        });
      })
    );

    const blob = await tailoredResumesApi.downloadPdf('ver-1', { template_id: 'us-swe' });
    expect(blob.type).toBe('application/pdf');
  });
});
