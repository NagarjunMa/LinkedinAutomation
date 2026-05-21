// frontend/tests/e2e/resume-polish.spec.ts
import { test, expect } from '@playwright/test';
import path from 'path';

const UPLOAD_RESPONSE = {
  resume_document_id: 'doc-1',
  contact: { name: 'Jane Doe', email: 'jane@example.com', phone: null, links: [] },
  summary: 'Engineer.',
  experience: [
    {
      company: 'Acme',
      role: 'SWE',
      dates: '2022—now',
      location: null,
      bullets: [
        { id: 'b1', text: 'Built backend services', raw_text: 'Built backend services' },
      ],
    },
  ],
  education: [],
  skills: { hard: ['Python'], soft: [] },
  projects: [],
  certifications: [],
  raw_text: 'Jane Doe\nAcme — SWE\n- Built backend services',
};

const EVAL_RESPONSE = {
  evaluation_id: 'eval-1',
  overall_score: 62,
  bullet_flags: [
    {
      bullet_id: 'b1',
      severity: 'critical',
      reason: 'No quantification',
      category: 'quantification',
    },
  ],
  format_issues: [],
  summary_critique: 'Weak summary',
  ats_parseability: 88,
  ats_raw_text: 'Jane Doe\nSWE at Acme',
};

const REWRITE_RESPONSE = {
  rewritten: 'Built backend services serving [N users]',
  placeholders: [{ token: '[N users]', what: 'number of users' }],
  applied_changes: ['Added scope placeholder'],
};

const VERSION_RESPONSE = { version_id: 'ver-1' };

test('resume polish happy path', async ({ page, context }) => {
  await context.addCookies([{
    name: 'test-bypass-auth', value: '1', url: 'http://localhost:3000',
  }]);
  await page.route('**/api/v1/resumes/upload', (route) =>
    route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(UPLOAD_RESPONSE) }));
  await page.route('**/api/v1/resumes/doc-1/evaluate', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(EVAL_RESPONSE) }));
  await page.route('**/api/v1/resumes/doc-1/rewrite/b1', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(REWRITE_RESPONSE) }));
  await page.route('**/api/v1/resumes/doc-1/versions', (route) =>
    route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(VERSION_RESPONSE) }));
  await page.route('**/api/v1/credits/balance', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ balance: 10 }) }));

  await page.goto('/dashboard/resume');

  const file = path.resolve('tests/fixtures/sample-resume.pdf');
  await page.setInputFiles('input[type=file]', file);
  await page.getByRole('button', { name: 'Upload' }).click();

  await expect(page).toHaveURL(/\/dashboard\/resume\/doc-1\/edit$/);

  await page.getByRole('button', { name: /Evaluate \(1 credit\)/ }).click();
  await expect(page.getByTestId('bullet-b1')).toHaveAttribute('data-severity', 'critical');

  await page.getByTestId('bullet-b1').click();
  await expect(page.getByText('Built backend services serving [N users]')).toBeVisible();
  await page.getByTestId('placeholder-[N users]').fill('1000');
  await page.getByRole('button', { name: 'Accept' }).click();

  await page.getByRole('button', { name: /Save version \(1\)/ }).click();
  await expect(page.getByRole('button', { name: /Save version \(0\)/ })).toBeVisible();
});
