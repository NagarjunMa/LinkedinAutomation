// frontend/tests/e2e/jd-tailor.spec.ts
import { test, expect } from '@playwright/test';
import path from 'path';

const UPLOAD_RESPONSE = {
  resume_document_id: 'doc-2',
  contact: { name: 'Jane Doe', email: null, phone: null, links: [] },
  summary: null,
  experience: [
    {
      company: 'Acme', role: 'SWE', dates: null, location: null,
      bullets: [{ id: 'b1', text: 'Built services', raw_text: 'Built services' }],
    },
  ],
  education: [],
  skills: { hard: [], soft: [] },
  projects: [],
  certifications: [],
  raw_text: '',
};

const ANALYZE_RESPONSE = {
  jd_evaluation_id: 'jd-1',
  extracted_requirements: {
    must_have: [{ skill: 'Python', evidence_from_jd: 'required', type: 'technical' }],
    good_to_have: [],
    soft_skills: [],
    seniority: 'mid',
    primary_role_category: 'SWE',
    country_hint: 'US',
    red_flags: [],
  },
  diff_plan: {
    match_score: 75,
    must_have_coverage_found: ['Python'],
    must_have_coverage_missing: [],
    good_to_have_coverage_found: [],
    good_to_have_coverage_missing: [],
    bullets: [
      {
        bullet_id: 'b1',
        old: 'Built services',
        new: 'Built Python services serving [N users]',
        reason: 'JD emphasizes scale',
        placeholders: [{ token: '[N users]', what: 'scale' }],
      },
    ],
    skills_reorder: null,
    summary_rewrite: null,
    suggested_additions: [],
  },
};

const VERSION_RESPONSE = { version_id: 'ver-2' };

test('JD tailor flow', async ({ page, context }) => {
  await context.addCookies([{
    name: 'test-bypass-auth', value: '1', url: 'http://localhost:3000',
  }]);
  await page.route('**/api/v1/resumes/upload', (r) =>
    r.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(UPLOAD_RESPONSE) }));
  await page.route('**/api/v1/jd/analyze', (r) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ANALYZE_RESPONSE) }));
  await page.route('**/api/v1/resumes/doc-2/versions', (r) =>
    r.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(VERSION_RESPONSE) }));
  await page.route('**/api/v1/credits/balance', (r) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ balance: 10 }) }));

  await page.goto('/dashboard/resume/tailor');

  const file = path.resolve('tests/fixtures/sample-resume.pdf');
  await page.setInputFiles('input[type=file]', file);
  await page.getByRole('button', { name: 'Upload' }).click();

  const jdText = 'We are hiring a Python engineer. ' + 'Must have Python and REST experience. '.repeat(3);
  await page.locator('#jd').fill(jdText);
  await page.getByRole('button', { name: /Analyze \(2 credits\)/ }).click();

  await expect(page.getByTestId('match-score')).toHaveText('75');
  await expect(page.getByTestId('change-bullet-b1')).toBeVisible();

  const versionResponse = page.waitForResponse((r) =>
    r.url().includes('/api/v1/resumes/doc-2/versions') && r.status() === 201
  );
  await page.getByTestId('apply-changes').click();
  await versionResponse;
});
