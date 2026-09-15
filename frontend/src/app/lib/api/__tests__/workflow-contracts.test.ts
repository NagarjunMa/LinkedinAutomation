import { expect, expectTypeOf, it, vi } from 'vitest';
import type { components } from '@/generated/api/types';
import type { ApplyTailorRequest, ExportPdfRequest } from '../types-v2';
import { jdApi } from '../jd';
import { exportsApi } from '../exports';
import { creditsApi } from '../credits';
import { server, http, HttpResponse } from '@/test-utils/msw-server';

const API = 'http://localhost:8000/api/v1';
const input = { resume_document_id: 'doc-1', jd_text: 'Synthetic private JD text' };
const bullet = { bullet_id: 'b1', old: 'Built services', new: 'Built Python services', reason: 'Clarify' };
const analysis = {
  jd_evaluation_id: 'jd-1',
  extracted_requirements: {
    must_have: [{ skill: 'Python', evidence_from_jd: 'Python engineer', type: 'technical' }],
    good_to_have: [], seniority: 'mid', primary_role_category: 'SWE', country_hint: 'US',
  },
  diff_plan: {
    match_score: 75, must_have_coverage_found: ['Python'], must_have_coverage_missing: [],
    good_to_have_coverage_found: [], good_to_have_coverage_missing: [], bullets: [bullet],
  },
} satisfies components['schemas']['JDAnalysisResponse'];
const applied = {
  version_id: 'ver-1', preview_html: '<p>Synthetic preview</p>', company_name: null,
  suggested_template: 'us-swe', filename_hint: 'resume.pdf', warning: null,
} satisfies components['schemas']['ApplyTailorResponse'];
const exported = {
  export_id: 'exp-1', download_url: 'https://storage.example/resume.pdf?token=synthetic',
  expires_at: '2026-09-14T12:00:00Z', country: 'US', role_template: 'swe', filename: null,
} satisfies components['schemas']['ExportResponse'];

it('normalizes only UI collections/nulls, not IDs or truth verification', async () => {
  server.use(http.post(API + '/jd/analyze', () => HttpResponse.json(analysis)));
  const result = await jdApi.analyze(input);
  expect(result.extracted_requirements).toMatchObject({ soft_skills: [], red_flags: [] });
  expect(result.diff_plan).toMatchObject({ skills_reorder: null, summary_rewrite: null, suggested_additions: [] });
  expect(result.diff_plan.bullets[0]).toMatchObject({ ...bullet, placeholders: [] });
  expect(result.diff_plan.bullets[0].truth_check).toBeUndefined();
});

it('preserves complete apply commands and adapts nullable warnings for the UI', async () => {
  const body = { accepted_changes: [
    { type: 'bullet_update', bullet_id: 'b1', new_text: 'Built services' },
    { type: 'skills_reorder', new_skills_order: [] },
    { type: 'summary_update', new_summary: '' },
  ], template_id: 'us-swe' } satisfies ApplyTailorRequest;
  server.use(http.post(API + '/jd/jd-1/apply', async ({ request }) => {
    expect(await request.json()).toEqual(body);
    return HttpResponse.json(applied);
  }));
  await expect(jdApi.applyTailor('jd-1', body)).resolves.toEqual({ ...applied, warning: undefined });
});

it('preserves the generated export envelope including nullable filename', async () => {
  const body = { resume_version_id: 'ver-1', template_id: 'us-swe', filename: 'custom.pdf' };
  server.use(http.post(API + '/exports', async ({ request }) => {
    expect(await request.json()).toEqual(body);
    return HttpResponse.json(exported, { status: 201 });
  }));
  await expect(exportsApi.exportPdf(body)).resolves.toEqual(exported);
});

const endpoints = [
  { method: http.post, path: '/jd/analyze', run: () => jdApi.analyze(input), status: 200, error: 'Invalid JD response' },
  { method: http.post, path: '/jd/jd-1/apply', run: () => jdApi.applyTailor('jd-1', { accepted_changes: [] }), status: 200, error: 'Invalid JD response' },
  { method: http.post, path: '/jd/jd-1/bullets/b1/options', run: () => jdApi.regenerateBulletOptions('jd-1', 'b1'), status: 200, error: 'Invalid JD response' },
  { method: http.post, path: '/exports', run: () => exportsApi.exportPdf({ resume_version_id: 'ver-1' }), status: 201, error: 'Invalid export response' },
  { method: http.get, path: '/credits/balance', run: () => creditsApi.getBalance(), status: 200, error: 'Invalid credit response' },
];

it.each(endpoints)('rejects malformed success privately and without retry: $path', async ({ method, path, run, status, error }) => {
  const log = vi.spyOn(console, 'error').mockImplementation(() => {});
  const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
  let calls = 0;
  server.use(method(API + path, () => { calls++; return HttpResponse.json({ private: 'private-jd-sentinel' }, { status }); }));
  try {
    const failure = await run().then(() => { throw new Error('Expected rejection'); }, error => error);
    expect(failure).toMatchObject({ name: 'APIError', message: error, data: undefined });
    expect(failure).not.toHaveProperty('cause');
    expect(calls).toBe(1);
    expect(JSON.stringify([log.mock.calls, warn.mock.calls])).not.toContain('private-jd-sentinel');
  } finally { log.mockRestore(); warn.mockRestore(); }
});

it.each(endpoints)('rejects invalid JSON without exposing parser errors: $path', async ({ method, path, run, status, error }) => {
  server.use(method(API + path, () => new HttpResponse('private-jd-sentinel', { status })));
  await expect(run()).rejects.toMatchObject({ name: 'APIError', message: error, data: undefined });
});

it.each([
  { ...analysis, jd_evaluation_id: '' },
  { ...analysis, extracted_requirements: { ...analysis.extracted_requirements, must_have: [null] } },
  { ...analysis, extracted_requirements: { ...analysis.extracted_requirements, seniority: 'invented' } },
  { ...analysis, diff_plan: { ...analysis.diff_plan, match_score: 101 } },
  { ...analysis, diff_plan: { ...analysis.diff_plan, bullets: [{ ...bullet, truth_check: { numeric_claims: 'verified' } }] } },
  { ...analysis, diff_plan: { ...analysis.diff_plan, bullets: [{ ...bullet, options: [{ text: 'Missing ID' }] }] } },
  { ...analysis, diff_plan: { ...analysis.diff_plan, content_budget: { source_page_estimate: 0 } } },
])('rejects nested analysis corruption', async (payload) => {
  server.use(http.post(API + '/jd/analyze', () => HttpResponse.json(payload)));
  await expect(jdApi.analyze(input)).rejects.toThrow('Invalid JD response');
});

it.each([null, 1.5, '42'])('rejects non-integer credit balances: %s', async (balance) => {
  server.use(http.get(API + '/credits/balance', () => HttpResponse.json({ balance })));
  await expect(creditsApi.getBalance()).rejects.toThrow('Invalid credit response');
});

it('preserves negative integer balances without clamping', async () => {
  server.use(http.get(API + '/credits/balance', () => HttpResponse.json({ balance: -3 })));
  await expect(creditsApi.getBalance()).resolves.toEqual({ balance: -3 });
});

it.each([
  { body: '{}', type: 'application/json', status: 200 },
  { body: '', type: 'application/pdf', status: 200 },
  { body: '%PDF-synthetic', type: 'application/pdf', status: 206 },
])('rejects incorrect PDF responses ($type, $status)', async ({ body, type, status }) => {
  server.use(http.get(API + '/exports/exp-1/download', () => new HttpResponse(body, { status, headers: { 'Content-Type': type } })));
  await expect(exportsApi.downloadPdf('exp-1')).rejects.toThrow('Invalid export response');
});

it('preserves PDF bytes and keeps request identifiers in one path segment', async () => {
  const bytes = new Uint8Array([37, 80, 68, 70, 0, 255]);
  server.use(http.get(API + '/exports/:id/download', ({ request }) => {
    expect(new URL(request.url).pathname).toBe('/api/v1/exports/exp%2F1/download');
    return new HttpResponse(bytes, { headers: { 'Content-Type': 'application/pdf' } });
  }));
  const result = await exportsApi.downloadPdf('exp/1');
  expect(new Uint8Array(await result.arrayBuffer())).toEqual(bytes);
});

it('preserves HTTP failures rather than classifying them as response corruption', async () => {
  server.use(http.post(API + '/jd/analyze', () => HttpResponse.json({ detail: 'Insufficient credits' }, { status: 402 })));
  await expect(jdApi.analyze(input)).rejects.toMatchObject({ status: 402, message: 'Insufficient credits' });
});

it('preserves populated nested evidence, qualifiers and fit metadata', async () => {
  const truth = { numeric_claims: 'placeholder_used', new_skill_status: 'resume_supported',
    unsupported_claims: [], placeholders_used: ['[N]'], source_evidence: ['b1'], verified_numbers: [], verified_skills: ['Python'] } as const;
  const payload = {
    ...analysis,
    extracted_requirements: { ...analysis.extracted_requirements, company_name: null, job_title: 'Engineer', soft_skills: [], red_flags: [] },
    diff_plan: { ...analysis.diff_plan,
      bullets: [{ ...bullet, placeholders: [{ token: '[N]', what: 'Candidate to confirm' }], truth_check: truth,
        options: [{ option_id: 'o1', text: 'Contributed to Python services', reason: 'Bounded ownership', placeholders: [], truth_check: truth }] }],
      skills_reorder: { new_order: ['Python'], rationale: 'Relevant' },
      summary_rewrite: { old: null, new: 'Engineer', reason: 'Target clarity' },
      suggested_additions: [{ section: 'Projects', item: 'Explain project', reason: 'Context missing' }],
      bullet_fit: [{ bullet_id: 'b1', relevance_score: 75, evidence_level: 'medium', recommendation: 'keep',
        matched_requirements: ['Python'], noise_flags: [], rationale: 'Relevant', why_stronger: '',
        matched_jd_phrases: ['Python engineer'], source_resume_evidence: ['Built services'], page_cost: 'low', truth_risk: 'medium' }],
      content_budget: { source_page_estimate: 1.5, target_max_pages: 2, recommended_bullet_budget: 8,
        current_bullet_count: 1, page_fit_risk: 'low', guidance: 'Keep readable' },
    },
  };
  server.use(http.post(API + '/jd/analyze', () => HttpResponse.json(payload)));
  await expect(jdApi.analyze(input)).resolves.toEqual(payload);
});

it.each(endpoints)('rejects unexpected successful statuses: $path', async ({ method, path, run, error }) => {
  const payload = path === '/jd/analyze' ? analysis : path.endsWith('/apply') ? applied
    : path.endsWith('/options') ? bullet : path === '/exports' ? exported : { balance: 5 };
  server.use(method(API + path, () => HttpResponse.json(payload, { status: 202 })));
  await expect(run()).rejects.toThrow(error);
});

it('normalizes optional nested arrays without inventing truth status', async () => {
  const payload = { ...bullet, truth_check: { numeric_claims: 'placeholder_used', new_skill_status: 'none' },
    options: [{ option_id: 'o1', text: 'Services', reason: 'Shorter' }] };
  server.use(http.post(API + '/jd/jd-1/bullets/b1/options', () => HttpResponse.json(payload)));
  const result = await jdApi.regenerateBulletOptions('jd-1', 'b1');
  expect(result.truth_check).toEqual({ ...payload.truth_check, unsupported_claims: [], placeholders_used: [],
    source_evidence: [], verified_numbers: [], verified_skills: [] });
  expect(result.options?.[0]).toEqual({ ...payload.options[0], placeholders: [] });
});

it('keeps JD path IDs encoded and option regeneration bodyless', async () => {
  server.use(http.post(API + '/jd/:id/bullets/:bullet/options', async ({ request }) => {
    expect(new URL(request.url).pathname).toBe('/api/v1/jd/jd%2F1/bullets/b%3F1/options');
    expect(await request.text()).toBe('');
    return HttpResponse.json(bullet);
  }));
  await expect(jdApi.regenerateBulletOptions('jd/1', 'b?1')).resolves.toMatchObject(bullet);
});

it('keeps complete UI commands and version export requirements at compile time', () => {
  type InvalidChange = { type: 'bullet_update'; bullet_id: string } | { type: 'summary_update'; new_summary: null };
  expectTypeOf<Extract<InvalidChange, ApplyTailorRequest['accepted_changes'][number]>>().toBeNever();
  expectTypeOf<ApplyTailorRequest>().toExtend<components['schemas']['ApplyTailorRequest']>();
  expectTypeOf<ExportPdfRequest>().toExtend<components['schemas']['ExportRequest']>();
  expectTypeOf<components['schemas']['ExportRequest']>().not.toExtend<ExportPdfRequest>();
  expectTypeOf(jdApi.analyze).parameter(0).toEqualTypeOf<components['schemas']['AnalyzeRequest']>();
  expectTypeOf(jdApi.analyze).returns.resolves.toExtend<components['schemas']['JDAnalysisResponse']>();
  expectTypeOf(exportsApi.exportPdf).returns.resolves.toEqualTypeOf<components['schemas']['ExportResponse']>();
  expectTypeOf(creditsApi.getBalance).returns.resolves.toEqualTypeOf<components['schemas']['CreditBalanceResponse']>();
});
