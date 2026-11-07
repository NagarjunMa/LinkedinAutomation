// frontend/tests/e2e/jd-tailor.spec.ts
import { test, expect } from '@playwright/test';
import path from 'path';
import { seedResumeSession } from './resume-session';

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

const APPLY_RESPONSE = {
  version_id: 'ver-2',
  company_name: null,
  preview_html: '<html><body><p>Built Python services.</p></body></html>',
  suggested_template: 'us-swe',
  filename_hint: 'tailored-resume.pdf',
};

test('JD tailor flow', async ({ page, context }) => {
  await seedResumeSession(context);
  await page.route('**/api/v1/resumes/upload', (r) =>
    r.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(UPLOAD_RESPONSE) }));
  await page.route('**/api/v1/jd/analyze', (r) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ANALYZE_RESPONSE) }));
  await page.route('**/api/v1/jd/jd-1/apply', (r) =>
    r.fulfill({ json: APPLY_RESPONSE }));
  await page.route('**/api/v1/credits/balance', (r) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ balance: 10 }) }));

  await page.goto('/dashboard/resume/tailor');

  const file = path.resolve('tests/fixtures/sample-resume.pdf');
  await page.setInputFiles('input[type=file]', file);
  await page.getByRole('button', { name: 'Upload' }).click();

  const jdText = 'We are hiring a Python engineer. ' + 'Must have Python and REST experience. '.repeat(3);
  await page.locator('#jd').fill(jdText);
  await page.getByRole('button', { name: /Analyze \(2 credits\)/ }).click();

  await expect(page.getByTestId('change-bullet-b1')).toBeVisible();
  await page.getByLabel('Generated pointer text').fill('Built Python services.');

  await page.getByTestId('tailor-apply').click();
  await expect(page.getByRole('button', { name: 'Download PDF' })).toBeVisible();
});
