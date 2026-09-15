import { describe, it, expect } from 'vitest';
import { server, http, HttpResponse } from '@/test-utils/msw-server';
import { exportsApi } from '@/app/lib/api/exports';

describe('exportsApi.exportPdf', () => {
  it('posts resume_version_id + template_id and returns download_url', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/exports', async ({ request }) => {
        const body = await request.json() as Record<string, unknown>;
        expect(body.resume_version_id).toBe('ver-1');
        expect(body.template_id).toBe('us-swe');
        return HttpResponse.json({
          export_id: 'exp-1',
          download_url: 'https://storage.example.com/resumes/resume-acme.pdf?token=abc',
          filename: 'resume-acme.pdf',
          expires_at: '2026-09-14T12:00:00Z', country: 'US', role_template: 'swe',
        }, { status: 201 });
      })
    );
    const result = await exportsApi.exportPdf({
      resume_version_id: 'ver-1',
      template_id: 'us-swe',
    });
    expect(result.export_id).toBe('exp-1');
    expect(result.download_url).toContain('storage.example.com');
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
          download_url: 'https://storage.example.com/resumes/resume.pdf?token=xyz',
          filename: 'resume.pdf',
          expires_at: '2026-09-14T12:00:00Z', country: 'US', role_template: 'swe',
        }, { status: 201 });
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

  it('downloads exported PDF bytes through the authenticated API route', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/exports/exp-1/download', () => {
        return new HttpResponse('%PDF-test', {
          headers: { 'Content-Type': 'application/pdf' },
        });
      })
    );

    const blob = await exportsApi.downloadPdf('exp-1');
    expect(blob.type).toBe('application/pdf');
  });

  it('throws parsed API errors from the authenticated download route', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/exports/exp-missing/download', () => {
        return HttpResponse.json({ detail: 'export not found' }, { status: 404 });
      })
    );

    await expect(exportsApi.downloadPdf('exp-missing')).rejects.toThrow('export not found');
  });

  it('throws plain-text API errors from the authenticated download route', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/exports/exp-failed/download', () => {
        return new HttpResponse('download failed', { status: 500 });
      })
    );

    await expect(exportsApi.downloadPdf('exp-failed')).rejects.toThrow('download failed');
  });
});
