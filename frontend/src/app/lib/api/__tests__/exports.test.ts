import { describe, it, expect } from 'vitest';
import { server, http, HttpResponse } from '@/test-utils/msw-server';
import { exportsApi } from '@/app/lib/api/exports';

describe('exportsApi.exportPdf', () => {
  it('posts resume_version_id + template_id and returns signed_url', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/exports', async ({ request }) => {
        const body = await request.json() as Record<string, unknown>;
        expect(body.resume_version_id).toBe('ver-1');
        expect(body.template_id).toBe('us-swe');
        return HttpResponse.json({
          export_id: 'exp-1',
          signed_url: 'https://storage.example.com/resumes/resume-acme.pdf?token=abc',
          filename: 'resume-acme.pdf',
        });
      })
    );
    const result = await exportsApi.exportPdf({
      resume_version_id: 'ver-1',
      template_id: 'us-swe',
    });
    expect(result.export_id).toBe('exp-1');
    expect(result.signed_url).toContain('storage.example.com');
    expect(result.filename).toBe('resume-acme.pdf');
  });

  it('uses default template when template_id omitted', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/exports', async ({ request }) => {
        const body = await request.json() as Record<string, unknown>;
        expect(body.resume_version_id).toBe('ver-2');
        expect(body.template_id).toBeUndefined();
        return HttpResponse.json({
          export_id: 'exp-2',
          signed_url: 'https://storage.example.com/resumes/resume.pdf?token=xyz',
          filename: 'resume.pdf',
        });
      })
    );
    const result = await exportsApi.exportPdf({ resume_version_id: 'ver-2' });
    expect(result.export_id).toBe('exp-2');
  });

  it('throws on 402 when credits exhausted', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/exports', () => {
        return HttpResponse.json({ detail: 'insufficient credits' }, { status: 402 });
      })
    );
    await expect(
      exportsApi.exportPdf({ resume_version_id: 'ver-1', template_id: 'us-swe' })
    ).rejects.toThrow();
  });

  it('throws on 404 when version_id not found', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/exports', () => {
        return HttpResponse.json({ detail: 'version not found' }, { status: 404 });
      })
    );
    await expect(
      exportsApi.exportPdf({ resume_version_id: 'nonexistent' })
    ).rejects.toThrow();
  });
});
