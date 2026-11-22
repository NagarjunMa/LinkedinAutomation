import { expect, test, type Page } from '@playwright/test';
import path from 'node:path';
import type { components } from '../../src/generated/api/types';
import { seedResumeSession } from './resume-session';

type Schemas = components['schemas'];
const owner = 'resume-test-user';
const source = (version: number) => ({ source_id: 'profile-export', source_version: version });
const target: Schemas['CareerTarget'] = {
  schema_version: 1, owner_id: owner, target_id: 'target-platform', status: 'active',
  role_family: 'Platform Engineer', seniority: 'Senior',
};
const reference = { evidence_id: 'scheduler', revision: 2 };
const recommendation: Schemas['LinkedInRecommendation'] = {
  section: 'headline', text: 'Built a scheduler', evidence_revisions: [reference],
};
const snapshot = (version: number): Schemas['LinkedInUpload'] => ({
  source: source(version), pdf_sha256: 'a'.repeat(64), state: 'ready',
  created_at: `2026-11-${10 + version}T12:00:00Z`,
  document: {
    schema_version: 1, source: source(version), coverage: 'uploaded_export_only',
    raw_text: 'Unclassified private fixture', parse_status: version === 1 ? 'partial' : 'parsed',
    not_found_in_export: version === 1 ? ['skills'] : [],
    sections: [{ name: 'about', page: 1, locator: 'About on page 1',
      text: version === 1 ? 'Maintained job queues' : 'Owned job queues' }],
  },
});

async function stubReview(page: Page, pauseAfterAppend = false) {
  await page.addInitScript(() => {
    Object.defineProperty(AbortSignal, 'any', { value: undefined });
    Object.defineProperty(AbortSignal, 'timeout', { value: undefined });
  });
  await page.route('**/api/v1/jobs/stats?**', route => route.fulfill({ json: {} }));
  await page.route('**/api/v1/jobs/recent-applications?**', route => route.fulfill({ json: [] }));
  await page.route('**/api/v1/user-profiles/**', route => route.fulfill({ json: {} }));
  await page.route('**/api/v1/career/sessions?**', route => route.fulfill({ json: [] }));
  const item: Schemas['CareerEvidenceItem'] = {
    schema_version: 1, evidence_id: reference.evidence_id, owner_id: owner, revision: reference.revision,
    lifecycle: 'confirmed', claim: recommendation.text, category: 'action', ownership: 'individual',
    support: 'candidate_statement', is_private: false, sources: [],
  };
  const current = { ...item, revision: 3, claim: 'Maintained the scheduler' };
  await page.route('**/api/v1/career/evidence**', route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/history')) return route.fulfill({ json: { revisions: [item, current], decisions: [] } });
    return route.fulfill({ json: path.endsWith('/evidence') ? [current] : current });
  });
  let versions = [1];
  let targets: Schemas['CareerTarget'][] = [];
  let revoked = false;
  let rejectUpload = true;
  let pauseList = false;
  let releaseList = () => {};
  const listMayFinish = new Promise<void>(resolve => { releaseList = resolve; });
  await page.route('**/api/v1/career/targets**', route => {
    if (route.request().method() === 'POST') {
      expect(route.request().postDataJSON()).toEqual({
        role_family: 'Platform Engineer', seniority: 'Senior', desired_work: ['Task scheduling'],
      });
      targets = [target];
      return route.fulfill({ status: 201, json: target });
    }
    return route.fulfill({ json: targets });
  });
  await page.route('**/api/v1/career/linkedin-profiles**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const method = request.method();
    expect(request.headers().authorization).toBe('Bearer synthetic-resume-test-token');
    if (method === 'DELETE') {
      expect(path).toMatch(/\/linkedin-profiles\/profile-export$/);
      versions = [];
      return route.fulfill({ status: 204 });
    }
    if (path.endsWith('/review')) {
      expect(request.postDataJSON()).toEqual({ target_id: target.target_id });
      return route.fulfill({ json: {
        schema_version: 1, document: source(versions[0]), target_id: target.target_id,
        parser_version: 'linkedin-pdf-v1', findings: [{
          kind: 'communication_gap', explanation: 'Make scheduler ownership clearer.',
          document_locator: 'About on page 1', evidence_revisions: [reference],
        }],
      } });
    }
    if (path.endsWith('/recommendations/copy')) {
      expect(request.postDataJSON()).toEqual({
        target_id: target.target_id, selection: { section: 'headline', evidence_revisions: [reference] },
      });
      return revoked ? route.fulfill({ status: 409, json: {} })
        : route.fulfill({ json: { ...recommendation, text: 'Built a scheduler with retry handling' } });
    }
    if (path.endsWith('/recommendations')) {
      return route.fulfill({ json: revoked ? [] : [recommendation] });
    }
    if (method === 'POST') {
      const initial = path.endsWith('/linkedin-profiles');
      if (!initial) expect(path).toMatch(/\/profile-export\/versions\/1$/);
      expect(request.headers()['content-type']).toContain('multipart/form-data; boundary=');
      expect(request.postDataBuffer()?.toString('utf8')).toContain('filename="linkedin-style.pdf"');
      if (rejectUpload) {
        rejectUpload = false;
        return route.fulfill({ status: 422, json: {} });
      }
      versions = initial ? [1] : [2, 1];
      pauseList = pauseAfterAppend && !initial;
      return route.fulfill({ status: 201, json: snapshot(versions[0]) });
    }
    if (path.endsWith('/linkedin-profiles')) {
      if (pauseList) await listMayFinish;
      return route.fulfill({ json: versions.map(version => {
        const { document: _document, ...summary } = snapshot(version);
        void _document;
        return summary;
      }) });
    }
    return route.fulfill({ json: snapshot(Number(path.split('/').at(-1))) });
  });
  return { revoke: () => { revoked = true; }, releaseList };
}

test('opens LinkedIn Review, resubmits a failed PDF, compares versions, and confirms deletion', async ({ page, context }) => {
  await seedResumeSession(context);
  const { releaseList } = await stubReview(page, true);
  await page.goto('/dashboard/career');
  await expect(page.getByRole('heading', { name: 'Career Coach', exact: true })).toBeVisible();
  const navigation = page.getByRole('button', { name: 'Open navigation' });
  if (await navigation.isVisible()) await navigation.click();
  await page.getByRole('link', { name: 'LinkedIn Review' }).click();
  await expect(page).toHaveURL(/\/dashboard\/linkedin-review$/);
  await expect(page.getByRole('heading', { name: 'LinkedIn Review' })).toBeVisible();
  await page.getByLabel('Saved PDF version').selectOption('profile-export:1');
  await expect(page.getByText('Partially parsed')).toBeVisible();
  await expect(page.getByText('Unclassified private fixture')).toHaveCount(0);

  const file = page.getByLabel('PDF file');
  const fixture = path.join(__dirname, '../../../backend/tests/fixtures/anydoc/linkedin-style.pdf');
  await file.setInputFiles(fixture);
  await page.getByRole('button', { name: 'Upload new version' }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'could not be read' })).toBeVisible();
  await file.setInputFiles(fixture);
  await page.getByRole('button', { name: 'Upload new version' }).click();
  try {
    await expect(page.getByLabel('Saved PDF version')).toHaveValue('profile-export:2');
    await expect(page.getByRole('button', { name: 'Delete PDF history' })).toBeEnabled();
  } finally {
    releaseList();
  }
  await page.getByRole('button', { name: 'Compare with version 1' }).click();
  await expect(page.getByText('Maintained job queues')).toBeVisible();
  await expect(page.getByRole('region', { name: 'PDF version comparison' }).getByText('Owned job queues')).toBeVisible();

  await page.getByRole('button', { name: 'Delete PDF history' }).click();
  const confirmation = page.getByRole('alertdialog');
  await expect(confirmation.getByRole('heading', { name: 'Delete PDF history profile-?' })).toBeVisible();
  await expect(confirmation.getByText(/You selected version 2/)).toBeVisible();
  await confirmation.getByRole('button', { name: 'Cancel' }).press('Escape');
  await expect(page.getByRole('button', { name: 'Delete PDF history' })).toBeFocused();
  await page.getByRole('button', { name: 'Delete PDF history' }).click();
  await confirmation.getByRole('button', { name: 'Delete all versions' }).click();
  await expect(page.getByText('No LinkedIn PDFs uploaded yet.')).toBeVisible();
  await file.setInputFiles(fixture);
  await page.getByRole('button', { name: 'Upload as new PDF' }).click();
  await expect(page.getByLabel('Saved PDF version')).toHaveValue('profile-export:1');
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize()!.width);
});

test('reviews cited findings and leaves the clipboard unchanged when copy is revoked', async ({ page, context }) => {
  await seedResumeSession(context);
  const { revoke } = await stubReview(page);
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.goto('/dashboard/linkedin-review');
  await page.getByLabel('Saved PDF version').selectOption('profile-export:1');
  await page.getByRole('textbox', { name: 'Target role' }).fill('Platform Engineer');
  await page.getByLabel('Seniority').fill('Senior');
  await page.getByLabel('Target priorities').fill('Task scheduling');
  await page.getByRole('button', { name: 'Create target' }).click();
  await page.getByRole('button', { name: 'Run review' }).click();
  await expect(page.getByText('Make scheduler ownership clearer.')).toBeVisible();
  await expect(page.getByText('LinkedIn PDF · About on page 1')).toBeVisible();
  const citation = page.getByRole('region', { name: 'Review findings' }).getByRole('link', { name: 'Evidence revision 2' });
  await expect(citation).toHaveAttribute('href', '/dashboard/evidence?evidence=scheduler&revision=2');

  const copy = page.getByRole('button', { name: 'Copy headline' });
  await copy.click();
  await expect(page.getByText('Copied to clipboard.')).toBeVisible();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe('Built a scheduler with retry handling');
  await page.evaluate(() => navigator.clipboard.writeText('Keep this clipboard text'));
  revoke();
  await copy.click();
  await expect(page.getByRole('alert').filter({ hasText: 'Evidence changed' })).toBeVisible();
  await expect(copy).toHaveCount(0);
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe('Keep this clipboard text');
  await page.getByRole('button', { name: 'Refresh review' }).click();
  await expect(page.getByText('No copy-ready recommendations for this target.')).toBeVisible();
  await citation.click();
  const details = page.getByRole('region', { name: 'Evidence details' });
  await expect(details.getByText('Confirmed · Candidate statement · Revision 3', { exact: true })).toBeVisible();
  const cited = details.getByRole('listitem').filter({ hasText: 'Revision 2 · Confirmed' });
  await expect(cited).toHaveAttribute('aria-current', 'true');
  await expect(cited.getByText('Built a scheduler', { exact: true })).toBeVisible();
});
