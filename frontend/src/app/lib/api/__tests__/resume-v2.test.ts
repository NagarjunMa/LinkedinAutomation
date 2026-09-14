import { describe, it, expect, vi } from 'vitest';
import { server, http, HttpResponse } from '@/test-utils/msw-server';
import { resumeV2Api } from '@/app/lib/api/resume-v2';

describe('resumeV2Api.upload', () => {
  it('sends multipart FormData and returns resume_document_id', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/resumes/upload', async ({ request }) => {
        const ct = request.headers.get('content-type') || '';
        expect(ct).toContain('multipart/form-data');
        return HttpResponse.json({
          resume_document_id: 'rdoc-1',
          contact: { name: 'Test User', email: null, phone: null, links: [] },
          summary: null,
          experience: [],
          education: [],
          skills: { hard: [], soft: [] },
          projects: [],
          certifications: [],
          raw_text: 'test',
        }, { status: 201 });
      })
    );
    const file = new File(['pdf content'], 'resume.pdf', { type: 'application/pdf' });
    const result = await resumeV2Api.upload(file);
    expect(result.resume_document_id).toBe('rdoc-1');
  });

  it('throws APIError on 4xx', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/resumes/upload', () => {
        return HttpResponse.json({ detail: 'unsupported file type' }, { status: 400 });
      })
    );
    const file = new File(['bad'], 'bad.exe', { type: 'application/octet-stream' });
    await expect(resumeV2Api.upload(file)).rejects.toThrow();
  });

  it('falls back to localhost when API URL env is absent', async () => {
    const originalApiUrl = process.env.NEXT_PUBLIC_API_URL;
    delete process.env.NEXT_PUBLIC_API_URL;
    vi.resetModules();

    const { resumeV2Api: freshApi } = await import('@/app/lib/api/resume-v2');
    server.use(
      http.post('http://localhost:8000/api/v1/resumes/upload', () => {
        return HttpResponse.json({
          resume_document_id: 'fallback-doc',
          contact: { name: 'Test User', email: null, phone: null, links: [] },
          summary: null,
          experience: [],
          education: [],
          skills: { hard: [], soft: [] },
          projects: [],
          certifications: [],
          raw_text: 'test',
        }, { status: 201 });
      })
    );

    const file = new File(['pdf content'], 'resume.pdf', { type: 'application/pdf' });
    const result = await freshApi.upload(file);

    expect(result.resume_document_id).toBe('fallback-doc');
    if (originalApiUrl === undefined) {
      delete process.env.NEXT_PUBLIC_API_URL;
    } else {
      process.env.NEXT_PUBLIC_API_URL = originalApiUrl;
    }
    vi.resetModules();
  });
});

describe('resumeV2Api.evaluate', () => {
  it('posts target_role and returns evaluation_id', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/resumes/rdoc-1/evaluate', async ({ request }) => {
        const body = await request.json() as Record<string, unknown>;
        expect(body.target_role).toBe('Senior SWE');
        return HttpResponse.json({
          evaluation_id: 'eval-1',
          overall_score: 78,
          readiness_label: 'minor_edits',
          score_breakdown: {
            content_quality: 80,
            role_fit: 72,
            evidence_strength: 68,
            recruiter_readability: 76,
          },
          score_explanation: [
            {
              category: 'evidence_strength',
              score: 68,
              reason: 'Some bullets need stronger evidence.',
              evidence: ['Improved latency'],
              before_applying_action: 'Add verified scope.',
            },
          ],
          top_actions_before_applying: ['Add verified scope.'],
          parser_confidence: 'high',
          bullet_flags: [],
          format_issues: [],
          summary_critique: null,
          ats_parseability: 90,
          ats_raw_text: 'raw text',
        });
      })
    );
    const result = await resumeV2Api.evaluate('rdoc-1', 'Senior SWE');
    expect(result.evaluation_id).toBe('eval-1');
    expect(result.overall_score).toBe(78);
    expect(result.score_breakdown.evidence_strength).toBe(68);
  });

  it('throws on 500', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/resumes/rdoc-1/evaluate', () => {
        return HttpResponse.json({ detail: 'server error' }, { status: 500 });
      })
    );
    await expect(resumeV2Api.evaluate('rdoc-1', 'SWE')).rejects.toThrow();
  });
});

describe('resumeV2Api.rewriteBullet', () => {
  it('posts bullet body and returns rewritten text', async () => {
    server.use(
      http.post(
        'http://localhost:8000/api/v1/resumes/rdoc-1/rewrite/bullet-42',
        async ({ request }) => {
          const body = await request.json() as Record<string, unknown>;
          expect(body.target_role).toBe('Data Scientist');
          expect(body.country).toBe('US');
          return HttpResponse.json({
            rewritten: 'Improved bullet text',
            placeholders: [],
            applied_changes: ['quantification'],
          });
        }
      )
    );
    const result = await resumeV2Api.rewriteBullet('rdoc-1', 'bullet-42', {
      target_role: 'Data Scientist',
      country: 'US',
    });
    expect(result.rewritten).toBe('Improved bullet text');
    expect(result.applied_changes).toContain('quantification');
  });
});

describe('resumeV2Api.createVersion', () => {
  it('posts change_set and returns version_id', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/resumes/rdoc-1/versions', async ({ request }) => {
        const body = await request.json() as Record<string, unknown>;
        expect(Array.isArray(body.change_set)).toBe(true);
        return HttpResponse.json({ version_id: 'ver-1' }, { status: 201 });
      })
    );
    const result = await resumeV2Api.createVersion('rdoc-1', { change_set: [] });
    expect(result.version_id).toBe('ver-1');
  });
});
