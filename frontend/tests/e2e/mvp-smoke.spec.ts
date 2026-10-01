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

test('landing and login deliver a nonce CSP without blocking hydration', async ({ page }) => {
  const blockedScripts: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error' && /Content Security Policy.*script|Refused to execute.*script/i.test(message.text())) {
      blockedScripts.push(message.text());
    }
  });

  const landing = await page.goto('/');
  const policy = landing?.headers()['content-security-policy'] ?? '';
  const nonce = policy.match(/script-src[^;]*'nonce-([^']+)'/)?.[1];
  expect(nonce).toBeTruthy();
  expect(policy).not.toMatch(/script-src[^;]*'unsafe-inline'/);
  expect(policy).toContain("frame-ancestors 'none'");
  expect(policy).toContain("object-src 'none'");
  expect(landing?.headers()['x-xss-protection']).toBeUndefined();
  expect(landing?.headers()['cross-origin-embedder-policy']).toBeUndefined();
  expect(await page.locator('#prismpro-structured-data').evaluate((script: HTMLScriptElement) => script.nonce)).toBe(nonce);
  await page.getByRole('button', { name: /toggle theme/i }).click();

  const login = await page.goto('/login');
  expect(login?.headers()['content-security-policy']).toMatch(/script-src[^;]*'nonce-[^']+'/);
  expect(blockedScripts).toEqual([]);
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
  await expect(page.getByText(/neither predicts a hiring outcome/)).toBeVisible();
  await expect(page.getByText(/get.*ATS score/i)).toHaveCount(0);
  expect(pageErrors.map((error) => error.message)).not.toEqual(
    expect.arrayContaining([expect.stringContaining('Hydration failed')]),
  );
});

test('shared layout reserves sidebar space only on desktop, including collapse and resize', async ({ page, context }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await context.addCookies([{ name: 'test-bypass-auth', value: '1', url: APP }]);
  await page.route(`${API}/api/v1/credits/balance`, route => route.fulfill({ json: { balance: 90 } }));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/dashboard/resume');
  const main = page.getByRole('main');
  await expect(main).toHaveCSS('margin-left', '0px');
  for (const width of [768, 1023, 1024, 1280]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(main).toHaveCSS('margin-left', width >= 1024 ? '280px' : '0px');
  }
  // The existing sidebar toggle is icon-only; scope it to the desktop navigation.
  await page.locator('nav:visible button').first().click();
  await expect(main).toHaveCSS('margin-left', '80px');
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(main).toHaveCSS('margin-left', '0px');
  await expect(main).toHaveCSS('transition-property', 'none');
  await page.setViewportSize({ width: 1280, height: 900 });
  await expect(main).toHaveCSS('margin-left', '80px');
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await expect(main).toHaveCSS('transition-duration', '0.6s');
  // Exercise keyboard expansion; the dev server's toolbar overlays this footer.
  await page.locator('nav:visible button').last().focus();
  await page.keyboard.press('Enter');
  await expect(main).toHaveCSS('margin-left', '280px');
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
  await expect(page.getByTestId('match-score')).toHaveCount(0);
  await expect(page.getByText(/Only add a skill.*actual experience/)).toBeVisible();
  await page.getByLabel('Generated pointer text').fill('Edited Python services pointer for Acme.');

  await page.getByTestId('tailor-apply').click();
  await expect(page.getByRole('button', { name: 'Download PDF' })).toBeVisible();
  const resumePreview = page.getByTitle('Resume preview');
  await expect(resumePreview).toBeVisible();
  await expect(page.frameLocator('iframe[title="Resume preview"]').locator('h1')).toHaveText('Jane Doe');
  expect(applyPayload).toEqual({
    accepted_changes: [{
      type: 'bullet_update',
      bullet_id: 'b1',
      new_text: 'Edited Python services pointer for Acme.',
    }],
  });
});

for (const viewport of [{ width: 1280, height: 900 }, { width: 390, height: 844 }]) {
  test(`resume findings and document checks preserve evaluate/rewrite/save at ${viewport.width}px`, async ({ page, context }) => {
    await page.setViewportSize(viewport);
    await context.addCookies([{ name: 'test-bypass-auth', value: '1', url: APP }]);
    await page.route(`${API}/api/v1/credits/balance`, route => route.fulfill({ json: { balance: 90 } }));
    await page.route(`${API}/api/v1/resumes/upload`, route => route.fulfill({ status: 201, json: UPLOAD_RESPONSE }));
    await page.route(`${API}/api/v1/resumes/doc-2/evaluate`, route => route.fulfill({ json: {
      evaluation_id: 'eval-1', overall_score: 62, readiness_label: 'needs_work',
      score_breakdown: { content_quality: 60, role_fit: 65, evidence_strength: 60, recruiter_readability: 70 },
      score_explanation: [{ category: 'evidence_strength', score: 60, reason: 'Clarify your personal contribution.',
        evidence: [], before_applying_action: 'Describe the component you built.' }],
      top_actions_before_applying: ['Review ownership claims.'], parser_confidence: 'high',
      bullet_flags: [{ bullet_id: 'b1', severity: 'warning', reason: 'Clarify ownership', category: 'clarity' }],
      format_issues: [], summary_critique: 'Check suggestions against your actual work.',
      ats_parseability: 88, ats_raw_text: '<script>synthetic-source</script>',
    } satisfies components['schemas']['ResumeEvaluationResponse'] }));
    await page.route(`${API}/api/v1/resumes/doc-2/rewrite/b1`, route => route.fulfill({ json: {
      rewritten: 'Built backend services.', placeholders: [], applied_changes: ['Clarified contribution'],
    } }));
    let saved: unknown;
    await page.route(`${API}/api/v1/resumes/doc-2/versions`, async route => {
      saved = route.request().postDataJSON();
      await route.fulfill({ status: 201, json: { version_id: 'version-1' } });
    });
    await page.goto('/dashboard/resume');
    await page.locator('input[type=file]').setInputFiles(path.resolve('tests/fixtures/sample-resume.pdf'));
    await page.getByRole('button', { name: 'Upload', exact: true }).click();
    await expect(page).toHaveURL(/\/doc-2\/edit$/);
    await expect(page.getByRole('tab', { name: 'Document checks' })).toBeDisabled();
    await page.getByRole('button', { name: 'Evaluate (1 credit)' }).click();
    await expect(page.getByText('Clarify your personal contribution.')).toBeVisible();
    await expect(page.getByText('Review ownership claims.')).toBeVisible();
    await expect(page.getByText(/Overall:|Potential Score/)).toHaveCount(0);
    await expect(page.getByTestId('ats-raw-text')).toHaveCount(0);
    await test.info().attach(`content-findings-${viewport.width}`, { body: await page.screenshot({ fullPage: true }), contentType: 'image/png' });
    // Exercise keyboard tab activation, not only pointer navigation.
    await page.getByRole('tab', { name: 'Document checks' }).focus();
    await page.keyboard.press('Enter');
    await expect(page.getByText(/not measure candidate quality or hiring probability/)).toBeVisible();
    await expect(page.getByTestId('ats-raw-text')).toHaveText('<script>synthetic-source</script>');
    await expect(page.getByRole('progressbar', { name: 'PrismPro document parseability' })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await test.info().attach(`document-checks-${viewport.width}`, { body: await page.screenshot({ fullPage: true }), contentType: 'image/png' });
    await page.getByRole('tab', { name: 'Resume', exact: true }).click();
    await page.getByTestId('bullet-b1').click();
    await expect(page.getByText('Built backend services.', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Accept', exact: true }).click();
    await page.getByRole('button', { name: 'Save version (1)' }).click();
    await expect(page.getByRole('button', { name: 'Save version (0)' })).toBeVisible();
    expect(saved).toEqual({ change_set: [{ type: 'bullet_update', bullet_id: 'b1', new_text: 'Built backend services.' }] });
  });
}

test('docs explain document limits and evidence-backed terminology on mobile', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/docs');
  await page.getByRole('button', { name: /Document checks/ }).click();
  await expect(page.getByText(/not a replica of any ATS/)).toBeVisible();
  await page.getByRole('button', { name: /JD Tailoring/ }).click();
  await expect(page.getByText(/Only add job-description terms.*actual experience/)).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await test.info().attach('diagnostic-docs-mobile', { body: await page.screenshot({ fullPage: true }), contentType: 'image/png' });
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
      await route.fulfill({ status: 503, headers: { 'X-Request-ID': '7018a0a3-9431-4bc4-b4ce-719a579588a1' }, json: {
        code: 'service_unavailable', message: 'private-provider-sentinel', detail: 'private-provider-sentinel',
        request_id: '7018a0a3-9431-4bc4-b4ce-719a579588a1', retryable: false,
      } satisfies components['schemas']['APIErrorEnvelope'] });
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
  // This page renders a generic inline recovery banner; APIError copy and
  // diagnostic metadata are asserted at the shared-client boundary.
  await expect(page.getByText('private-provider-sentinel', { exact: false })).toHaveCount(0);
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
