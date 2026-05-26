import { describe, it, expect } from 'vitest';
import { server, http, HttpResponse } from '@/test-utils/msw-server';
import { jdApi } from '@/app/lib/api/jd';

describe('jdApi.analyze', () => {
  it('posts resume_document_id + jd_text and returns jd_evaluation_id', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/jd/analyze', async ({ request }) => {
        const body = await request.json() as Record<string, unknown>;
        expect(body.resume_document_id).toBe('rdoc-1');
        expect(body.jd_text).toBe('We are looking for a Senior SWE...');
        return HttpResponse.json({
          jd_evaluation_id: 'jd-1',
          extracted_requirements: {
            must_have: [],
            good_to_have: [],
            soft_skills: [],
            seniority: 'senior',
            primary_role_category: 'SWE',
            country_hint: 'US',
            red_flags: [],
          },
          diff_plan: {
            match_score: 72,
            must_have_coverage_found: [],
            must_have_coverage_missing: [],
            good_to_have_coverage_found: [],
            good_to_have_coverage_missing: [],
            bullets: [],
            skills_reorder: null,
            summary_rewrite: null,
            suggested_additions: [],
          },
        });
      })
    );
    const result = await jdApi.analyze({
      resume_document_id: 'rdoc-1',
      jd_text: 'We are looking for a Senior SWE...',
    });
    expect(result.jd_evaluation_id).toBe('jd-1');
    expect(result.diff_plan.match_score).toBe(72);
  });

  it('throws on 402 (insufficient credits)', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/jd/analyze', () => {
        return HttpResponse.json({ detail: 'insufficient credits' }, { status: 402 });
      })
    );
    await expect(
      jdApi.analyze({ resume_document_id: 'rdoc-1', jd_text: 'desc' })
    ).rejects.toThrow();
  });
});

describe('jdApi.applyTailor', () => {
  it('posts accepted_changes + template_id and returns version_id + preview_html', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/jd/jd-1/apply', async ({ request }) => {
        const body = await request.json() as Record<string, unknown>;
        expect(Array.isArray(body.accepted_changes)).toBe(true);
        expect(body.template_id).toBe('us-swe');
        return HttpResponse.json({
          version_id: 'ver-1',
          preview_html: '<html><body>Resume</body></html>',
          company_name: 'Acme Corp',
          suggested_template: 'us-swe',
          filename_hint: 'resume-acme.pdf',
        });
      })
    );
    const result = await jdApi.applyTailor('jd-1', {
      accepted_changes: [],
      template_id: 'us-swe',
    });
    expect(result.version_id).toBe('ver-1');
    expect(result.preview_html).toContain('<html>');
    expect(result.company_name).toBe('Acme Corp');
  });

  it('throws on 404 when jd_evaluation_id not found', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/jd/missing-jd/apply', () => {
        return HttpResponse.json({ detail: 'not found' }, { status: 404 });
      })
    );
    await expect(
      jdApi.applyTailor('missing-jd', { accepted_changes: [] })
    ).rejects.toThrow();
  });
});
