import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { renderArtifacts, syncArtifacts } from './api-contracts.mjs';

const schema = {
  openapi: '3.1.0', info: { title: 'Synthetic contract', version: '1' }, paths: {},
  components: { schemas: { Evidence: { type: 'object', required: ['state'], properties: {
    state: { type: 'string', enum: ['proposed', 'confirmed'] },
    note: { anyOf: [{ type: 'string' }, { type: 'null' }] },
  } } } },
};

test('generation preserves enum/nullable semantics and is byte-repeatable', async () => {
  const first = await renderArtifacts(schema);
  assert.match(first['types.ts'] ?? '', /state: "proposed" \| "confirmed"/);
  assert.match(first['types.ts'], /note\?: string \| null/);
  assert.match(first['types.ts'], /DO NOT EDIT/);
  assert.deepEqual(first, await renderArtifacts(schema));
  assert.deepEqual(JSON.parse(first['openapi.json']), schema);
});

test('backend schema changes propagate into generated TypeScript', async () => {
  const changed = structuredClone(schema);
  changed.components.schemas.Evidence.properties.state.enum.push('private');
  const before = await renderArtifacts(schema);
  const after = await renderArtifacts(changed);
  assert.notEqual(before['types.ts'], after['types.ts']);
});

test('external refs are rejected before the generator can resolve them', async () => {
  const changed = structuredClone(schema);
  changed.components.schemas.Evidence = { $ref: 'https://example.invalid/secret.json' };
  await assert.rejects(renderArtifacts(changed), /External references/);
});

test('check fails on missing or stale artifacts without modifying them', async (t) => {
  const directory = await mkdtemp(join(tmpdir(), 'prism-contract-test-'));
  t.after(() => rm(directory, { recursive: true, force: true }));
  const artifacts = { 'openapi.json': '{}\n', 'types.ts': 'export type State = string;\n' };
  await assert.rejects(syncArtifacts(directory, artifacts, true), /Contract drift/);
  await syncArtifacts(directory, artifacts, false);
  await syncArtifacts(directory, artifacts, true);
  for (const name of Object.keys(artifacts)) {
    await writeFile(join(directory, name), 'stale\n');
    await assert.rejects(syncArtifacts(directory, artifacts, true), /Contract drift/);
    assert.equal(await readFile(join(directory, name), 'utf8'), 'stale\n');
    await syncArtifacts(directory, artifacts, false);
  }
});
