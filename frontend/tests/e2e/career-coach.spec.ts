import { expect, test } from '@playwright/test';
import { seedResumeSession } from './resume-session';

test('starts and resumes a Career Coach session, recovers a turn, and reviews evidence', async ({ page, context }) => {
  await seedResumeSession(context);
  await page.clock.install();
  const created = '2026-11-16T20:00:00Z';
  const owner = 'resume-test-user';
  const literalQuestion = '<img src=x onerror=alert(1)> What did you build?';
  const session = {
    schema_version: 1, owner_id: owner, session_id: 'starter', mode: 'foundation',
    status: 'active', chapter: 'introduction', candidate_stage: 'early_career', state_version: 1, prompt_version: 'unassigned',
    turns_remaining: 0, tokens_remaining: 0, created_at: created, updated_at: created,
  };
  let started = false;
  let version = 1;
  let status = 'active';
  let rejectStale = true;
  const messages: object[] = [];
  const sends: Record<string, unknown>[] = [];
  let releaseDecision!: () => void;
  const decisionGate = new Promise<void>(resolve => { releaseDecision = resolve; });
  let releaseFirstTurn!: () => void;
  const firstTurnGate = new Promise<void>(resolve => { releaseFirstTurn = resolve; });
  const proposal = {
    schema_version: 1, owner_id: owner, evidence_id: 'evidence-1', revision: 1,
    claim: 'I wrote the scheduling service.', category: 'action', ownership: 'individual',
    lifecycle: 'proposed', support: 'candidate_statement', is_private: false,
    sources: [{
      source_id: 'note-1', source_version: 1, relationship: 'supports', locator: 'chars:0-31',
      excerpt: null, excerpt_sha256: 'a'.repeat(64), extraction: 'candidate',
    }],
  };
  await page.route('**/api/v1/career/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    expect(request.headers().authorization).toBe('Bearer synthetic-resume-test-token');
    const state = { ...session, status, state_version: version };
    if (path.endsWith('/evidence')) return route.fulfill({ json: [proposal] });
    if (path.endsWith('/decision')) {
      expect(request.postDataJSON()).toEqual({ action: 'confirm', revision: 1 });
      await decisionGate;
      return route.fulfill({ json: { ...proposal, lifecycle: 'confirmed', revision: 2 } });
    }
    if (path.endsWith('/sessions') && request.method() === 'POST') {
      expect(request.postDataJSON()).toEqual({ mode: 'foundation', candidate_stage: 'early_career' });
      started = true;
      return route.fulfill({ json: state, status: 201 });
    }
    if (path.endsWith('/sessions')) return route.fulfill({ json: started ? [state] : [] });
    if (path.endsWith('/messages')) return route.fulfill({ json: messages });
    if (path.endsWith('/resume')) {
      expect(request.method()).toBe('POST');
      status = 'active';
      return route.fulfill({ json: { ...state, status, state_version: ++version } });
    }
    if (path.endsWith('/starter')) return route.fulfill({ json: state });
    if (path.endsWith('/turns')) {
      const payload = request.postDataJSON();
      if (new TextEncoder().encode(request.postData() ?? '').byteLength > 8192) {
        return route.fulfill({ status: 413, json: { detail: 'Reply too large' } });
      }
      if (payload.content === 'Career turns are temporarily disabled.') {
        return route.fulfill({ status: 503, json: {
          code: 'service_unavailable', message: 'Service unavailable.', detail: 'Service unavailable.',
          request_id: '7018a0a3-9431-4bc4-b4ce-719a579588a1', retryable: false,
        } });
      }
      sends.push(payload);
      if (sends.length === 1) {
        await firstTurnGate;
        return route.abort();
      }
      if (rejectStale) {
        rejectStale = false;
        version++;
        return route.fulfill({ status: 409, json: { detail: 'Stale session version' } });
      }
      const message = { role: 'user', key: payload.key, content: payload.content, created_at: created, position: 1 };
      if (payload.content === 'The stream closed after saving this reply.') {
        version += 2;
        messages.push({ ...message, position: 3, processing_status: 'complete' }, {
          role: 'assistant', key: payload.key, position: 4, processing_status: 'complete',
          content: 'That reply was saved.', created_at: created,
        });
        return route.fulfill({ contentType: 'text/event-stream', body: 'data: {"type":"turn.started"}\n\n' });
      }
      let event: object;
      if (!payload.retry) {
        version = 3;
        messages.splice(0, 1, { ...message, processing_status: 'interrupted' });
        event = { type: 'turn.interrupted', key: payload.key, state_version: version, can_retry: true };
      } else {
        version = 4;
        status = 'paused';
        const reply = { role: 'assistant', key: payload.key, content: literalQuestion,
          created_at: created, position: 2, processing_status: 'complete' };
        messages.splice(0, 1, { ...message, processing_status: 'complete' }, reply);
        event = { type: 'turn.replayed', state: { ...state, status, state_version: version }, message: reply, recovered: true };
      }
      return route.fulfill({ contentType: 'text/event-stream', body: `data: ${JSON.stringify(event)}\n\n` });
    }
    return route.abort();
  });

  await page.goto('/dashboard/career');
  await expect(page.getByRole('button', { name: 'Start session' })).toBeDisabled();
  await page.getByLabel('Career stage', { exact: true }).selectOption('early_career');
  await page.getByRole('button', { name: 'Start session' }).click();
  const oversized = '漢'.repeat(3000);
  await page.getByLabel('Your reply').fill(oversized);
  await page.getByRole('button', { name: 'Send' }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'is too large' })).toBeVisible();
  await expect(page.getByLabel('Your reply')).toHaveValue(oversized);
  await page.getByLabel('Your reply').fill('Career turns are temporarily disabled.');
  await page.getByRole('button', { name: 'Send' }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'Career Coach is currently unavailable' })).toBeVisible();
  await expect(page.getByLabel('Your reply')).toHaveValue('Career turns are temporarily disabled.');
  await page.getByLabel('Your reply').fill('I built a scheduler for our test team.');
  await page.getByRole('button', { name: 'Send' }).click();
  await expect.poll(() => sends.length).toBe(1);
  await page.clock.fastForward(66_000);
  await expect(page.getByRole('alert').filter({ hasText: 'The request took too long' })).toBeVisible();
  releaseFirstTurn();
  await page.getByRole('button', { name: 'Check turn status' }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'This record has changed' })).toBeVisible();
  expect(sends[1].key).toBe(sends[0].key);
  await page.getByRole('button', { name: /Foundation interview/ }).click();
  await expect(page.getByLabel('Your reply')).toHaveValue('I built a scheduler for our test team.');
  await page.getByRole('button', { name: 'Send' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Reply interrupted' })).toBeVisible();
  await page.reload();
  await page.getByRole('button', { name: /Foundation interview/ }).click();
  await page.getByRole('button', { name: 'Check turn status' }).click();
  await page.getByRole('button', { name: 'Retry reply' }).click();
  await expect(page.getByText(literalQuestion, { exact: true })).toBeVisible();
  expect(sends[4]).toMatchObject({ key: sends[2].key, content: sends[2].content, retry: true, expected_state_version: 3 });
  await page.reload();
  await page.getByRole('button', { name: /Foundation interview/ }).click();
  await expect(page.getByText(literalQuestion, { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Resume conversation' }).click();
  await expect(page.getByLabel('Your reply')).toBeEnabled();
  await page.getByLabel('Your reply').fill('The stream closed after saving this reply.');
  await page.getByRole('button', { name: 'Send' }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'The request did not finish' })).toBeVisible();
  await page.getByRole('button', { name: /Foundation interview/ }).click();
  await expect(page.getByText('That reply was saved.')).toBeVisible();
  await expect(page.getByLabel('Your reply')).toHaveValue('');

  const evidence = page.getByRole('region', { name: 'Evidence review' });
  await expect(evidence.getByText('chars:0-31 · Source version 1')).toBeVisible();
  await expect(evidence.getByText('Excerpt unavailable')).toBeVisible();
  await evidence.getByRole('button', { name: 'Confirm' }).click();
  await expect(evidence.getByText(/^proposed$/i)).toBeVisible();
  releaseDecision();
  await expect(evidence.getByText(/^confirmed$/i)).toBeVisible();
  await expect(page.getByRole('status').filter({ hasText: 'Evidence decision saved' })).toBeVisible();
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(0);
  if (process.env.PRI42_SCREENSHOTS) {
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await page.screenshot({ path: `${process.env.PRI42_SCREENSHOTS}/${test.info().project.name}.png`, fullPage: true, animations: 'disabled' });
  }
});

test('recovers the saved introduction stage and skips legacy messages without a recovery record', async ({ page, context }) => {
  await seedResumeSession(context);
  await page.clock.install();
  const timestamp = '2026-11-16T20:00:00Z';
  const state = {
    schema_version: 1, owner_id: 'resume-test-user', session_id: 'introduction', mode: 'foundation',
    status: 'active', chapter: 'introduction', candidate_stage: null, state_version: 2, prompt_version: '2',
    turns_remaining: 39, tokens_remaining: 800000, created_at: timestamp, updated_at: timestamp,
  };
  const legacy = { ...state, session_id: 'legacy', mode: 'career_refresh' };
  const pending = { key: 'saved-turn', role: 'user', content: 'I built a scheduler.', position: 1, created_at: timestamp };
  const finished = { ...state, candidate_stage: 'early_career', chapter: 'career_story', state_version: 3 };
  let recovered = false;
  let firstEvidenceRead = true;
  let releaseEvidence!: () => void;
  const evidenceGate = new Promise<void>(resolve => { releaseEvidence = resolve; });
  await page.route('**/api/v1/career/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/sessions')) return route.fulfill({ json: [state, legacy] });
    if (path.endsWith('/evidence')) {
      if (firstEvidenceRead) {
        firstEvidenceRead = false;
        await evidenceGate;
        return route.abort();
      }
      return route.fulfill({ json: [] });
    }
    if (path.endsWith('/legacy')) return route.fulfill({ json: legacy });
    if (path.endsWith('/legacy/messages')) {
      return route.fulfill({ json: [{ ...pending, processing_status: 'interrupted', turn_recovery: null }] });
    }
    if (path.endsWith('/introduction')) return route.fulfill({ json: recovered ? finished : state });
    if (path.endsWith('/introduction/messages')) {
      return route.fulfill({ json: recovered
        ? [{ ...pending, processing_status: 'complete', turn_recovery: null },
          { ...pending, position: 2, role: 'assistant', content: 'How did you verify it?', processing_status: 'complete', turn_recovery: null }]
        : [{ ...pending, processing_status: 'interrupted', turn_recovery: { candidate_stage: 'early_career' } }] });
    }
    const data = route.request().postDataJSON();
    expect(data).toMatchObject({ key: pending.key, content: pending.content, candidate_stage: 'early_career', expected_state_version: 2 });
    recovered = data.retry === true;
    const result = recovered ? { type: 'turn.replayed', state: finished, recovered: true }
      : { type: 'turn.interrupted', key: pending.key, state_version: 2, can_retry: true };
    return route.fulfill({ contentType: 'text/event-stream', body: `data: ${JSON.stringify(result)}\n\n` });
  });

  const sessionsResponse = page.waitForResponse(response => new URL(response.url()).pathname.endsWith('/career/sessions'));
  await page.goto('/dashboard/career');
  await sessionsResponse;
  await expect.poll(() => firstEvidenceRead).toBe(false);
  await page.clock.fastForward(66_000);
  await expect(page.getByRole('alert').filter({ hasText: 'saved records took too long' })).toBeVisible();
  releaseEvidence();
  await page.getByRole('button', { name: /Career refresh/ }).click();
  await expect(page.getByRole('status').filter({ hasText: 'earlier reply can’t be retried' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Check turn status' })).toHaveCount(0);
  await page.getByRole('button', { name: /Foundation interview/ }).click();
  await page.getByRole('button', { name: 'Check turn status' }).click();
  await page.getByRole('button', { name: 'Retry reply' }).click();
  await expect(page.getByText('How did you verify it?')).toBeVisible();
  await expect(page.getByLabel('Your reply')).toBeFocused();
});
