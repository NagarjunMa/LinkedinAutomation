import { test, expect } from '@playwright/test';
import path from 'path';
import type { components } from '../../src/generated/api/types';

const API = 'http://localhost:8000';
const APP = `http://localhost:${process.env.E2E_PORT ?? '3000'}`;

const UPLOAD_RESPONSE = {
  resume_document_id: 'doc-2',
  original_filename: 'sample-resume.pdf',
  contact: { name: 'Jane Doe', email: 'jane@example.com', phone: null, links: [] },
  summary: 'Software engineer',
  experience: [
    {
      company: 'Acme',
      role: 'SWE',
      dates: '2022-2024',
      location: 'Remote',
      bullets: [{ id: 'b1', text: 'Built services', raw_text: 'Built services' }],
    },
  ],
  education: [],
  skills: { hard: ['Python'], soft: [] },
  projects: [],
  certifications: [],
  raw_text: 'Jane Doe\nBuilt services',
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
    company_name: 'Acme',
    job_title: 'Software Engineer',
  },
  diff_plan: {
    match_score: 75,
    must_have_coverage_found: ['Python'],
    must_have_coverage_missing: [],
    good_to_have_coverage_found: [],
    good_to_have_coverage_missing: [],
    content_budget: {
      source_page_estimate: 1,
      target_max_pages: 1,
      current_bullet_count: 1,
      recommended_bullet_budget: 8,
      page_fit_risk: 'low',
      guidance: 'Keep the strongest role-relevant evidence.',
    },
    bullet_fit: [{
      bullet_id: 'b1',
      relevance_score: 88,
      evidence_level: 'medium',
      recommendation: 'rewrite',
      matched_requirements: ['Python'],
      noise_flags: [],
      rationale: 'Relevant to the JD.',
    }],
    bullets: [
      {
        bullet_id: 'b1',
        old: 'Built services',
        new: 'Built Python services serving [N users]',
        reason: 'JD emphasizes Python services',
        placeholders: [{ token: '[N users]', what: 'scale' }],
        options: [
          {
            option_id: 'conservative',
            text: 'Built Python services for internal workflows.',
            reason: 'Close to original evidence.',
            placeholders: [],
          },
          {
            option_id: 'impact',
            text: 'Built Python services improving workflow reliability for [N users].',
            reason: 'Adds measurable placeholder.',
            placeholders: [{ token: '[N users]', what: 'user count' }],
          },
          {
            option_id: 'keyword',
            text: 'Developed Python backend services aligned to REST workflows.',
            reason: 'Aligns JD keywords.',
            placeholders: [],
          },
        ],
      },
    ],
    skills_reorder: null,
    summary_rewrite: null,
    suggested_additions: [],
  },
} satisfies components['schemas']['JDAnalysisResponse'];

const APPLY_RESPONSE = {
  version_id: 'ver-2',
  company_name: null,
  preview_html: '<html><body><h1>Jane Doe</h1><p>Built Python services.</p></body></html>',
  suggested_template: 'us-swe',
  filename_hint: 'jane-doe-acme-swe.pdf',
} satisfies components['schemas']['ApplyTailorResponse'];

test('protected dashboard route redirects when unauthenticated', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page).toHaveURL(/\/$/);
});

test('authenticated dashboard loads with non-production bypass', async ({ page, context }) => {
  const pageErrors: Error[] = [];
  page.on('pageerror', (error) => pageErrors.push(error));
  await context.addCookies([{ name: 'test-bypass-auth', value: '1', url: APP }]);
  await page.route(`${API}/api/v1/credits/balance`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ balance: 90 }) }));
  await page.route(`${API}/api/v1/jobs/stats**`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      total_jobs: 0,
      total_applied: 0,
      success_rate: 0,
      period_jobs: 0,
      period_applied: 0,
      time_range: 'last_30_days',
      daily_stats: [],
    }) }));
  await page.route(`${API}/api/v1/jobs/recent-applications**`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) }));

  await page.goto('/dashboard');
  await expect(page.locator('body')).toBeVisible();
  expect(pageErrors.map((error) => error.message)).not.toEqual(
    expect.arrayContaining([expect.stringContaining('Hydration failed')]),
  );
});

test('tailor MVP flow uploads, edits pointer, applies, and exposes download contract', async ({ page, context }) => {
  await context.addCookies([{ name: 'test-bypass-auth', value: '1', url: APP }]);

  await page.route(`${API}/api/v1/credits/balance`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ balance: 90 }) }));
  await page.route(`${API}/api/v1/resumes/upload`, (route) =>
    route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(UPLOAD_RESPONSE) }));
  await page.route(`${API}/api/v1/jd/analyze`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ANALYZE_RESPONSE) }));

  let applyPayload: unknown = null;
  await page.route(`${API}/api/v1/jd/jd-1/apply`, async (route) => {
    applyPayload = await route.request().postDataJSON();
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(APPLY_RESPONSE) });
  });
  await page.route(`${API}/api/v1/tailored-resumes/ver-2/download`, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/pdf',
      headers: { 'content-disposition': 'attachment; filename="jane-doe-acme-swe.pdf"' },
      body: Buffer.from('%PDF-1.4 smoke'),
    }));

  await page.goto('/dashboard/resume/tailor');

  const file = path.resolve('tests/fixtures/sample-resume.pdf');
  await page.getByRole('button', { name: 'Choose file' }).click();
  await page.locator('input[type=file]').setInputFiles(file);
  await page.getByRole('button', { name: 'Upload' }).click();

  await page.locator('#jd').fill('We are hiring a Python software engineer. '.repeat(3));
  await page.getByRole('button', { name: /Analyze \(2 credits\)/ }).click();

  await expect(page.getByTestId('change-bullet-b1')).toBeVisible();
  await page.getByLabel('Generated pointer text').fill('Edited Python services pointer for Acme.');

  await page.getByTestId('tailor-apply').click();
  await expect(page.getByRole('button', { name: 'Download PDF' })).toBeVisible();
  expect(applyPayload).toEqual({
    accepted_changes: [{
      type: 'bullet_update',
      bullet_id: 'b1',
      new_text: 'Edited Python services pointer for Acme.',
    }],
  });
});

test('failed re-analysis clears old suggestions and preview until a manual retry succeeds', async ({ page, context }) => {
  await context.addCookies([{ name: 'test-bypass-auth', value: '1', url: APP }]);
  await page.route(`${API}/api/v1/credits/balance`, route =>
    route.fulfill({ json: { balance: 90 } }));
  await page.route(`${API}/api/v1/resumes/upload`, route =>
    route.fulfill({ status: 201, json: UPLOAD_RESPONSE }));
  let analyses = 0;
  let releaseFailure!: () => void;
  const failureGate = new Promise<void>(resolve => { releaseFailure = resolve; });
  await page.route(`${API}/api/v1/jd/analyze`, async route => {
    analyses += 1;
    if (analyses === 2) {
      await failureGate;
      await route.fulfill({ status: 503, json: { detail: 'Analysis unavailable' } });
    } else {
      await route.fulfill({ json: { ...ANALYZE_RESPONSE, jd_evaluation_id: `jd-${analyses}` } });
    }
  });
  const appliedEvaluations: string[] = [];
  await page.route(`${API}/api/v1/jd/*/apply`, async route => {
    appliedEvaluations.push(new URL(route.request().url()).pathname);
    await route.fulfill({ json: APPLY_RESPONSE });
  });

  await page.goto('/dashboard/resume/tailor');
  await page.getByRole('button', { name: 'Choose file' }).click();
  await page.locator('input[type=file]').setInputFiles(path.resolve('tests/fixtures/sample-resume.pdf'));
  await page.getByRole('button', { name: 'Upload' }).click();
  await page.locator('#jd').fill('We are hiring a Python software engineer. '.repeat(3));
  await page.getByRole('button', { name: /Analyze \(2 credits\)/ }).click();
  await expect(page.getByTestId('change-bullet-b1')).toBeVisible();
  await page.getByTestId('tailor-apply').click();
  await expect(page.getByRole('button', { name: 'Download PDF' })).toBeVisible();

  const newJd = 'A new role needs Python backend development experience. '.repeat(3);
  await page.locator('#jd').fill(newJd);
  await page.getByRole('button', { name: /Analyze \(2 credits\)/ }).click();
  try {
    await expect(page.getByRole('button', { name: 'Analyzing…' })).toBeDisabled();
    await expect(page.getByTestId('change-bullet-b1')).toHaveCount(0);
    await expect(page.getByTestId('tailor-apply')).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Download PDF' })).toHaveCount(0);
  } finally {
    releaseFailure();
  }
  await expect(page.getByText('Analyze failed', { exact: true })).toBeVisible();
  await expect(page.locator('#jd')).toHaveValue(newJd);
  await expect(page.getByTestId('change-bullet-b1')).toHaveCount(0);
  await expect(page.getByTestId('tailor-apply')).toHaveCount(0);
  expect(analyses).toBe(2);

  // Recovery instructions must remain readable in both supported themes.
  const transitions = await page.addStyleTag({ content: '* { transition: none !important; }' });
  for (const theme of ['light', 'dark']) {
    await page.locator('html').evaluate((element, dark) => element.classList.toggle('dark', dark), theme === 'dark');
    const contrast = await page.getByRole('alert').filter({ hasText: 'Analyze failed' }).evaluate(element => {
      const luminance = (color: string) => {
        const channels = color.match(/[\d.]+/g)!.slice(0, 3).map(value => {
          const channel = Number(value) / 255;
          return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
        });
        return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
      };
      let surface: Element | null = element;
      while (surface && getComputedStyle(surface).backgroundColor === 'rgba(0, 0, 0, 0)') {
        surface = surface.parentElement;
      }
      if (!surface) throw new Error('No opaque recovery-message surface found');
      const foreground = luminance(getComputedStyle(element).color);
      const background = luminance(getComputedStyle(surface).backgroundColor);
      return (Math.max(foreground, background) + 0.05) / (Math.min(foreground, background) + 0.05);
    });
    expect(contrast, `${theme} recovery text contrast`).toBeGreaterThanOrEqual(4.5);
    await test.info().attach(`recovery-${theme}`, { body: await page.screenshot(), contentType: 'image/png' });
  }
  await transitions.evaluate(element => element.parentNode?.removeChild(element));

  await page.getByRole('button', { name: /Analyze \(2 credits\)/ }).click();
  await expect(page.getByTestId('change-bullet-b1')).toBeVisible();
  await page.getByTestId('tailor-apply').click();
  await expect(page.getByRole('button', { name: 'Download PDF' })).toBeVisible();
  expect(analyses).toBe(3);
  expect(appliedEvaluations).toEqual(['/api/v1/jd/jd-1/apply', '/api/v1/jd/jd-3/apply']);
});
