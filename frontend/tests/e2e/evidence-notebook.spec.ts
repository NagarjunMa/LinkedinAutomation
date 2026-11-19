import { expect, test } from '@playwright/test';
import type { components } from '../../src/generated/api/types';
import { seedResumeSession } from './resume-session';

type Evidence = components['schemas']['CareerEvidenceItem'];
type Decision = components['schemas']['EvidenceDecisionInput'];
const owner = 'resume-test-user';
const literal = '<img src=x onerror=alert(1)> from the project notes';
const item: Evidence = {
  schema_version: 1, evidence_id: 'scheduler', owner_id: owner, revision: 1, lifecycle: 'proposed',
  category: 'action', claim: 'Built a scheduler', ownership: 'shared', support: 'candidate_statement',
  is_private: false, sources: [{ source_id: 'note', source_version: 2, relationship: 'supports',
    locator: 'Project notes', excerpt: literal, extraction: 'candidate' }],
};

test('reviews, edits, confirms and excludes evidence with revision history', async ({ page, context }) => {
  await seedResumeSession(context);
  await page.route('**/api/v1/jobs/stats?**', route => route.fulfill({ json: {} }));
  await page.route('**/api/v1/jobs/recent-applications?**', route => route.fulfill({ json: [] }));
  await page.route('**/api/v1/user-profiles/**', route => route.fulfill({ json: {} }));
  let current = item;
  const requests: Decision[] = [];
  const revisions = [item];
  await page.route('**/api/v1/career/evidence**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/history')) return route.fulfill({ json: { revisions, decisions: requests.map((decision, index) => ({
      action: decision.action, resulting_revision: index + 2, decided_at: '2026-11-18T12:00:00Z', actor_id: owner,
      evidence: { evidence_id: item.evidence_id, revision: index + 1 }, schema_version: 1,
    })) } });
    if (path.endsWith('/decision')) {
      const decision = route.request().postDataJSON() as Decision;
      expect(decision.revision).toBe(current.revision);
      requests.push(decision);
      current = { ...current, revision: current.revision + 1, supersedes_revision: current.revision,
        lifecycle: decision.action === 'edit' ? 'proposed' : decision.action === 'confirm' ? 'confirmed' : 'private',
        is_private: decision.action === 'mark_private', measurement: decision.measurement ?? current.measurement };
      revisions.push(current);
      return route.fulfill({ json: current });
    }
    return route.fulfill({ json: path.endsWith('/evidence') ? [current, {
      ...item, claim: 'Owned an unrelated parser', evidence_id: 'parser', lifecycle: 'rejected',
    }] : current });
  });

  await page.goto('/dashboard/evidence');
  await expect(page.getByRole('heading', { name: 'Evidence Notebook' })).toBeVisible();
  await page.getByLabel('Search loaded evidence').fill('scheduler');
  await page.getByLabel('Status').selectOption('proposed');
  await page.getByLabel('Support').selectOption('candidate_statement');
  await expect(page.getByText('Owned an unrelated parser')).toHaveCount(0);
  await page.getByRole('button', { name: 'Built a scheduler' }).press('Enter');
  const detail = page.getByRole('region', { name: 'Evidence details' });
  await expect(detail.getByText(literal, { exact: true })).toBeVisible();
  await expect(detail.locator('img')).toHaveCount(0);
  await expect(detail.getByText(/Confidential work can still be valid evidence/)).toBeVisible();
  await expect(detail.getByText('Excluded from generation', { exact: true })).toBeVisible();

  await detail.getByRole('button', { name: 'Edit evidence' }).click();
  await detail.getByLabel('Measurement method').fill('Timing samples');
  await detail.getByLabel('Measurement scope').fill('Weekly runs');
  await detail.getByLabel('Estimated measurement').check();
  await detail.getByRole('button', { name: 'Save edit' }).click();
  await expect(detail.getByText('Timing samples')).toBeVisible();
  expect(requests[0]).toEqual({ action: 'edit', revision: 1,
    measurement: { method: 'Timing samples', scope: 'Weekly runs', estimated: true } });

  await detail.getByRole('button', { name: 'Confirm evidence' }).click();
  await expect(detail.getByText('Eligible for generation', { exact: true })).toBeVisible();
  await detail.getByRole('button', { name: 'Mark private' }).click();
  const warning = page.getByRole('alertdialog');
  await expect(warning.getByText(/can make prior generated material unavailable/)).toBeVisible();
  await warning.getByRole('button', { name: 'Cancel' }).press('Enter');
  expect(requests).toHaveLength(2);
  await detail.getByRole('button', { name: 'Mark private' }).click();
  await warning.getByRole('button', { name: 'Mark private' }).click();
  await expect(detail.getByText('Excluded from generation', { exact: true })).toBeVisible();
  await detail.getByRole('button', { name: 'Show history' }).click();
  await expect(detail.getByText('Revision 4 · Marked private')).toBeVisible();
  await expect(detail.getByText('Eligible for generation', { exact: true })).toHaveCount(0);
  expect(requests).toHaveLength(3);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize()!.width);
});

test('refreshes a conflicting decision and returns resolved evidence to review', async ({ page, context }) => {
  await seedResumeSession(context);
  await page.route('**/api/v1/jobs/stats?**', route => route.fulfill({ json: {} }));
  await page.route('**/api/v1/jobs/recent-applications?**', route => route.fulfill({ json: [] }));
  await page.route('**/api/v1/user-profiles/**', route => route.fulfill({ json: {} }));
  const conflictingSource: Evidence['sources'][number] = {
    source_id: 'handoff', source_version: 1, relationship: 'contradicts', extraction: 'candidate',
    locator: 'Handoff note', excerpt_sha256: 'a'.repeat(64),
  };
  let current: Evidence = {
    ...item, lifecycle: 'contradicted', sources: [...item.sources, conflictingSource],
  };
  const requests: Decision[] = [];
  await page.route('**/api/v1/career/evidence**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/decision')) {
      const decision = route.request().postDataJSON() as Decision;
      requests.push(decision);
      if (requests.length === 1) {
        current = { ...current, revision: 2, claim: 'Co-built a scheduler' };
        return route.fulfill({ status: 409, json: {} });
      }
      expect(decision).toEqual({ action: 'resolve_contradiction', revision: 2 });
      current = { ...current, revision: 3, lifecycle: 'proposed', sources: item.sources };
      return route.fulfill({ json: current });
    }
    return route.fulfill({ json: path.endsWith('/evidence') ? [current] : current });
  });
  await page.route('**/api/v1/career/sessions?**', route => route.fulfill({ json: [] }));
  await page.goto('/dashboard/career');
  await expect(page.getByRole('heading', { name: 'Career Coach' })).toBeVisible();
  const notebook = page.getByRole('link', { name: 'Evidence Notebook' });
  const openNavigation = page.getByRole('button', { name: 'Open navigation' });
  if (await openNavigation.isVisible()) await openNavigation.click();
  await notebook.click();
  await expect(page).toHaveURL(/\/dashboard\/evidence$/);
  await page.getByRole('button', { name: 'Built a scheduler' }).click();
  const detail = page.getByRole('region', { name: 'Evidence details' });
  await expect(detail.getByRole('heading', { name: 'Evidence details' })).toBeFocused();
  await expect(detail.getByText('Conflicts with claim')).toBeVisible();
  await expect(detail.getByText(/retains an excerpt fingerprint/)).toBeVisible();
  await expect(detail.getByRole('button', { name: 'Confirm evidence' })).toHaveCount(0);
  const resolve = detail.getByRole('button', { name: 'Resolve contradiction' });
  const dialog = page.getByRole('alertdialog');
  await resolve.click();
  await dialog.getByRole('button', { name: 'Resolve contradiction' }).click();
  await expect(detail.getByRole('alert')).toContainText('changed in another tab');
  await expect(resolve).toHaveCount(0);
  await detail.getByRole('button', { name: 'Refresh evidence' }).click();
  await expect(detail.getByText('Co-built a scheduler', { exact: true })).toBeVisible();
  await resolve.click();
  await dialog.getByRole('button', { name: 'Resolve contradiction' }).click();
  await expect(detail.getByRole('button', { name: 'Confirm evidence' })).toBeVisible();
  await expect(detail.getByText('Excluded from generation', { exact: true })).toBeVisible();
  expect(requests).toHaveLength(2);
});
