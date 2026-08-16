import { describe, expect, it } from 'vitest';
import { HttpResponse, http } from 'msw';
import { fetchJobDetails, fetchRecentApplications } from '@/app/lib/api/jobs';
import { server } from '@/test-utils/msw-server';

describe('jobs API', () => {
  it('normalizes numeric recent-application identifiers', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/jobs/recent-applications', ({ request }) => {
        expect(new URL(request.url).searchParams.get('limit')).toBe('50');
        return HttpResponse.json([{ id: 42, title: 'Engineer', company: 'Acme' }]);
      }),
    );

    const result = await fetchRecentApplications(50);
    expect(result[0].id).toBe('42');
  });

  it('loads job details from the authenticated canonical endpoint', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/jobs/42', () => HttpResponse.json({
        id: 42,
        title: 'Engineer',
        company: 'Acme',
        skills: ['Python'],
      })),
    );

    const result = await fetchJobDetails('42');
    expect(result).toMatchObject({ id: 42, title: 'Engineer' });
  });
});
