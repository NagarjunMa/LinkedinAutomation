import { afterEach, describe, expect, expectTypeOf, it, vi } from 'vitest';
import type { components, paths } from '@/generated/api/types';
import { resumeV2Api } from '../resume-v2';
import type { ChangeItem, VersionRequest, ApplyTailorRequest } from '../types-v2';
import { server, http, HttpResponse } from '@/test-utils/msw-server';

const API = 'http://localhost:8000/api/v1/resumes';
const upload = {
  resume_document_id: 'doc-1', contact: { name: 'Synthetic candidate' }, raw_text: 'Synthetic',
} satisfies components['schemas']['ResumeUploadResponse'];
const evaluation = {
  evaluation_id: 'eval-1', overall_score: 70, readiness_label: 'minor_edits',
  score_breakdown: { content_quality: 70, role_fit: 70, evidence_strength: 70, recruiter_readability: 70 },
  score_explanation: [], top_actions_before_applying: [], parser_confidence: 'medium',
  bullet_flags: [], format_issues: [], summary_critique: null, ats_parseability: 80, ats_raw_text: 'Synthetic',
} satisfies components['schemas']['ResumeEvaluationResponse'];
const row = {
  id: 'doc-1', resume_document_id: 'doc-1', filename: 'r.pdf', original_filename: 'r.pdf',
  file_size: 0, file_type: 'pdf', uploaded_at: null, evaluation_status: 'pending',
  is_primary: true, evaluation_result: null,
} satisfies components['schemas']['ResumeListItem'];
const listing = { resumes: [row], total_count: 1, totalCount: 1 };
const detail = { resume: row, evaluation: null };
const rewrite = { rewritten: 'Built services', placeholders: [], applied_changes: [] };
const version = { version_id: 'version-1' };
const file = () => new File(['synthetic'], 'r.pdf', { type: 'application/pdf' });
const cases = [
  { name: 'upload', method: http.post, path: '/upload', status: 201, payload: upload, call: () => resumeV2Api.upload(file()) },
  { name: 'list', method: http.get, path: '/list', status: 200, payload: listing, call: () => resumeV2Api.list() },
  { name: 'detail', method: http.get, path: '/doc-1', status: 200, payload: detail, call: () => resumeV2Api.get('doc-1') },
  { name: 'evaluate', method: http.post, path: '/doc-1/evaluate', status: 200, payload: evaluation, call: () => resumeV2Api.evaluate('doc-1', 'Engineer') },
  { name: 'rewrite', method: http.post, path: '/doc-1/rewrite/b1', status: 200, payload: rewrite, call: () => resumeV2Api.rewriteBullet('doc-1', 'b1', { target_role: 'Engineer', country: 'US' }) },
  { name: 'version', method: http.post, path: '/doc-1/versions', status: 201, payload: version, call: () => resumeV2Api.createVersion('doc-1', { change_set: [] }) },
];
const safeError = { name: 'APIError', message: 'Invalid resume response', data: undefined };

afterEach(() => vi.restoreAllMocks());

describe.each(cases)('$name response boundary', ({ method, path, status, payload, call }) => {
  it('accepts the declared success response', async () => {
    server.use(method(API + path, () => HttpResponse.json(payload, { status })));
    expect(await call()).toMatchObject(payload);
  });

  it('rejects missing critical fields without logging or retrying', async () => {
    const errorLog = vi.spyOn(console, 'error');
    const warnLog = vi.spyOn(console, 'warn');
    let requests = 0;
    server.use(method(API + path, () => {
      requests++;
      return HttpResponse.json({ private: 'private-resume-sentinel' }, { status });
    }));
    await expect(call()).rejects.toMatchObject(safeError);
    expect(requests).toBe(1);
    expect(errorLog).not.toHaveBeenCalled();
    expect(warnLog).not.toHaveBeenCalled();
  });

  it('sanitizes JSON parse errors', async () => {
    server.use(method(API + path, () => new HttpResponse('private-resume-sentinel', { status })));
    await expect(call()).rejects.toMatchObject(safeError);
  });

  it('rejects an unexpected successful status rather than reporting completion', async () => {
    server.use(method(API + path, () => HttpResponse.json(payload, { status: 202 })));
    await expect(call()).rejects.toMatchObject(safeError);
  });
});

it('normalizes only declared optional document fields for existing renderers', async () => {
  server.use(http.post(API + '/upload', () => HttpResponse.json(upload, { status: 201 })));
  expect(await resumeV2Api.upload(file())).toEqual({
    ...upload, contact: { name: 'Synthetic candidate', email: null, phone: null, links: [] },
    summary: null, experience: [], education: [], skills: { hard: [], soft: [] }, projects: [], certifications: [],
  });
});

it.each([
  { ...upload, resume_document_id: '' },
  { ...upload, contact: { name: 'Candidate', links: [42] } },
  { ...upload, experience: [{ company: 'Acme', role: 'Engineer', bullets: [{ id: 'b1', text: null, raw_text: 'Original' }] }] },
  { ...upload, skills: null },
])('rejects malformed upload nested fields', async (payload) => {
  server.use(http.post(API + '/upload', () => HttpResponse.json(payload, { status: 201 })));
  await expect(resumeV2Api.upload(file())).rejects.toMatchObject(safeError);
});

it.each([
  { ...evaluation, overall_score: 101 },
  { ...evaluation, readiness_label: 'guaranteed' },
  { ...evaluation, score_breakdown: { ...evaluation.score_breakdown, role_fit: '70' } },
  { ...evaluation, bullet_flags: [{ bullet_id: 'b1', severity: 'critical', category: 'invented', reason: 'Test' }] },
])('rejects malformed evaluation fields', async (payload) => {
  server.use(http.post(API + '/doc-1/evaluate', () => HttpResponse.json(payload)));
  await expect(resumeV2Api.evaluate('doc-1', 'Engineer')).rejects.toMatchObject(safeError);
});

it('preserves nulls and zero counts on an empty list', async () => {
  server.use(http.get(API + '/list', () => HttpResponse.json({ resumes: [], total_count: 0, totalCount: 0 })));
  await expect(resumeV2Api.list()).resolves.toEqual({ resumes: [], total_count: 0, totalCount: 0 });
  server.use(http.get(API + '/doc-1', () => HttpResponse.json(detail)));
  await expect(resumeV2Api.get('doc-1')).resolves.toEqual(detail);
});

it('rejects malformed list rows instead of fabricating IDs or empty success', async () => {
  server.use(http.get(API + '/list', () => HttpResponse.json({ ...listing, resumes: [{ ...row, id: null }] })));
  await expect(resumeV2Api.list()).rejects.toMatchObject(safeError);
});

it('rejects malformed rewrite placeholders before rendering', async () => {
  server.use(http.post(API + '/doc-1/rewrite/b1', () => HttpResponse.json({ ...rewrite, placeholders: [null] })));
  await expect(resumeV2Api.rewriteBullet('doc-1', 'b1', { target_role: 'Engineer' })).rejects.toMatchObject(safeError);
});

it('accepts delete only as empty 204', async () => {
  server.use(http.delete(API + '/doc-1', () => new HttpResponse(null, { status: 204 })));
  await expect(resumeV2Api.delete('doc-1')).resolves.toBeUndefined();
  server.use(http.delete(API + '/doc-1', () => HttpResponse.json({ deleted: false })));
  await expect(resumeV2Api.delete('doc-1')).rejects.toMatchObject(safeError);
});

it('preserves HTTP failures from the shared client', async () => {
  server.use(http.post(API + '/doc-1/evaluate', () => HttpResponse.json({
    code: 'insufficient_credits', message: 'Insufficient credits.', detail: 'Insufficient credits.',
    request_id: '7018a0a3-9431-4bc4-b4ce-719a579588a1', retryable: false,
  }, { status: 402 })));
  await expect(resumeV2Api.evaluate('doc-1', 'Engineer')).rejects.toMatchObject({
    name: 'APIError', status: 402, message: 'Insufficient credits.', data: undefined,
    code: 'insufficient_credits', requestId: '7018a0a3-9431-4bc4-b4ce-719a579588a1', retryable: false,
  });
});

const saved = {
  id: 'eval-1', resume_id: 'doc-1', resume_document_id: 'doc-1', overall_score: 70,
  readiness_label: 'minor_edits', score_breakdown: evaluation.score_breakdown,
  score_explanation: [{ category: 'role_fit', score: 70, reason: 'Synthetic', evidence: ['Source'], before_applying_action: 'Review' }],
  top_actions_before_applying: ['Review'], parser_confidence: 'medium', bullet_flags: [], format_issues: [],
  ats_score: 80, ats_compliance_score: 80, content_quality_score: 70, experience_points_score: 70,
  job_relevance_score: 70, quality_checks_score: 70, strengths: [], improvements: ['Review'],
  ats_compatibility: 'good', detailed_feedback: null,
  keyword_analysis: { relevant: [], missing: [], score: 70 }, created_at: '2026-09-13T12:34:56.123456',
} satisfies components['schemas']['ResumeSavedEvaluation'];

it('preserves populated saved evaluations, aliases, timestamps and nullable feedback', async () => {
  const payload = { resume: { ...row, evaluation_status: 'completed', evaluation_result: saved }, evaluation: saved };
  server.use(http.get(API + '/doc-1', () => HttpResponse.json(payload)));
  await expect(resumeV2Api.get('doc-1')).resolves.toEqual(payload);
  const listPayload = { ...listing, resumes: [payload.resume] };
  server.use(http.get(API + '/list', () => HttpResponse.json(listPayload)));
  await expect(resumeV2Api.list()).resolves.toEqual(listPayload);
});

it.each([
  { ...saved, detailed_feedback: 42 },
  { ...saved, keyword_analysis: { relevant: [], missing: null, score: 70 } },
  { ...saved, score_explanation: [{ ...saved.score_explanation[0], evidence: [42] }] },
  { ...saved, score_explanation: [{ ...saved.score_explanation[0], evidence: null }] },
])('rejects nested saved-evaluation corruption in both list and detail', async (badEvaluation) => {
  server.use(http.get(API + '/doc-1', () => HttpResponse.json({ ...detail, evaluation: badEvaluation })));
  await expect(resumeV2Api.get('doc-1')).rejects.toMatchObject(safeError);
  server.use(http.get(API + '/list', () => HttpResponse.json({ ...listing, resumes: [{ ...row, evaluation_result: badEvaluation }] })));
  await expect(resumeV2Api.list()).rejects.toMatchObject(safeError);
});

it('normalizes nested optional collections without changing facts or explicit nulls', async () => {
  const payload = {
    ...upload, contact: { name: 'Candidate', email: null },
    experience: [{ company: 'Acme', role: 'Engineer', dates: null }],
    education: [{ school: 'School' }], projects: [{ name: 'Project' }], skills: { hard: ['Python'] },
  };
  server.use(http.post(API + '/upload', () => HttpResponse.json(payload, { status: 201 })));
  const result = await resumeV2Api.upload(file());
  expect(result.experience).toEqual([{ company: 'Acme', role: 'Engineer', dates: null, location: null, bullets: [] }]);
  expect(result.education).toEqual([{ school: 'School', degree: null, dates: null, gpa: null, location: null }]);
  expect(result.projects).toEqual([{ name: 'Project', bullets: [] }]);
  expect(result.skills).toEqual({ hard: ['Python'], soft: [] });
});

it('keeps all seven operations tied to generated contracts at compile time', () => {
  type Schemas = components['schemas'];
  expectTypeOf(resumeV2Api.upload).returns.resolves.toExtend<Schemas['ResumeUploadResponse']>();
  expectTypeOf(resumeV2Api.evaluate).returns.resolves.toEqualTypeOf<Schemas['ResumeEvaluationResponse']>();
  expectTypeOf(resumeV2Api.rewriteBullet).returns.resolves.toEqualTypeOf<Schemas['RewriteResult']>();
  expectTypeOf(resumeV2Api.createVersion).returns.resolves.toEqualTypeOf<Schemas['ResumeVersionResponse']>();
  expectTypeOf(resumeV2Api.list).returns.resolves.toEqualTypeOf<Schemas['ResumeListResponse']>();
  expectTypeOf(resumeV2Api.get).returns.resolves.toEqualTypeOf<Schemas['ResumeDetailResponse']>();
  expectTypeOf(resumeV2Api.delete).returns.resolves.toEqualTypeOf<paths['/api/v1/resumes/{resume_document_id}']['delete']['responses'][204]['content']>();
  // Editor commands narrow the wire contract without changing the payload shape.
  expectTypeOf(resumeV2Api.createVersion).parameter(1).toExtend<Schemas['VersionRequest']>();
  expectTypeOf(resumeV2Api.createVersion).parameter(1).toEqualTypeOf<VersionRequest>();
  expectTypeOf(resumeV2Api.rewriteBullet).parameter(2).toEqualTypeOf<Schemas['RewriteRequest']>();
});

it('requires complete action-specific commands and preserves valid request payloads', async () => {
  // Enforced by tsc/next build; Vitest alone does not check these type assertions.
  type InvalidChanges =
    | { type: 'bullet_update' }
    | { type: 'bullet_update'; bullet_id: string }
    | { type: 'bullet_update'; new_text: string }
    | { type: 'bullet_update'; bullet_id: null; new_text: string }
    | { type: 'bullet_update'; bullet_id: string; new_text: null }
    | { type: 'skills_reorder' }
    | { type: 'skills_reorder'; new_skills_order: null }
    | { type: 'summary_update' }
    | { type: 'summary_update'; new_summary: null }
    | { type: 'summary_update'; new_text: string }
    | { type: 'summary_update'; new_summary: string; new_text: string };
  expectTypeOf<Extract<InvalidChanges, ChangeItem>>().toBeNever();
  expectTypeOf<Extract<InvalidChanges, VersionRequest['change_set'][number]>>().toBeNever();
  expectTypeOf<Extract<InvalidChanges, ApplyTailorRequest['accepted_changes'][number]>>().toBeNever();
  expectTypeOf<components['schemas']['VersionRequest']>().not.toExtend<VersionRequest>();
  expectTypeOf<ChangeItem>().toExtend<components['schemas']['ChangeItem']>();
  expectTypeOf<ChangeItem['type']>().toEqualTypeOf<components['schemas']['ChangeItem']['type']>();

  const changes = [
    { type: 'bullet_update', bullet_id: 'b1', new_text: 'Built services' },
    { type: 'skills_reorder', new_skills_order: [] },
    { type: 'summary_update', new_summary: '' },
  ] satisfies ChangeItem[];
  const request = { parent_version_id: null, change_set: changes } satisfies VersionRequest;
  expectTypeOf(request).toExtend<components['schemas']['VersionRequest']>();
  let received: unknown;
  server.use(http.post(API + '/doc-1/versions', async ({ request: incoming }) => {
    received = await incoming.json();
    return HttpResponse.json(version, { status: 201 });
  }));
  await expect(resumeV2Api.createVersion('doc-1', request)).resolves.toEqual(version);
  expect(received).toEqual(request);
});
