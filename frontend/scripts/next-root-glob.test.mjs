import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { createRequire } from 'node:module';
import { test } from 'node:test';

const require = createRequire(import.meta.url);
const pluginRequire = createRequire(require.resolve('@next/eslint-plugin-next'));
const { getRootDirs } = pluginRequire('./utils/get-root-dirs.js');
const { globSync } = pluginRequire('fast-glob');

test('Next ESLint discovers project roots without changing directory matching', async t => {
  const original = process.cwd();
  const fixture = mkdtempSync(join(tmpdir(), 'prism-root-glob-'));
  t.after(() => { process.chdir(original); rmSync(fixture, { recursive: true, force: true }); });
  for (const path of ['apps/web/pages', 'apps/admin/pages', 'apps/.hidden', 'packages/ui', 'space app/pages']) {
    mkdirSync(join(fixture, path), { recursive: true });
  }
  writeFileSync(join(fixture, 'apps/readme.md'), 'fixture');
  symlinkSync('web', join(fixture, 'apps/linked'), 'dir');
  process.chdir(fixture);
  const context = rootDir => ({ cwd: fixture, settings: { next: { rootDir } } });
  const cases = [
    ['default', undefined, [fixture]],
    ['literal', 'apps/web', ['apps/web']],
    ['leading dot', './apps/web', ['./apps/web']],
    ['trailing slash', 'apps/web/', ['apps/web/']],
    ['wildcard ignores files and hidden directories', 'apps/*', ['apps/admin', 'apps/linked', 'apps/web']],
    ['recursive', 'apps/**', ['apps/admin', 'apps/admin/pages', 'apps/linked', 'apps/linked/pages', 'apps/web', 'apps/web/pages']],
    ['recursive leaves', 'apps/**/pages', ['apps/admin/pages', 'apps/linked/pages', 'apps/web/pages']],
    ['brace alternatives', 'apps/{web,admin}', ['apps/admin', 'apps/web']],
    ['extglob', 'apps/@(web|admin)', ['apps/admin', 'apps/web']],
    ['explicit hidden root', 'apps/.hidden', ['apps/.hidden']],
    ['spaces', 'space app', ['space app']],
    ['missing root', 'absent/*', []],
    ['file is not a root', 'apps/readme.md', []],
    ['absolute', resolve('apps/web'), [resolve('apps/web')]],
    ['absolute wildcard', resolve('apps/*'), ['admin', 'linked', 'web'].map(name => resolve('apps', name))],
    ['root array', ['apps/web', 'packages/*'], ['apps/web', 'packages/ui']],
    ['windows separators normalized by Next', 'apps\\web', ['apps/web']],
  ];
  for (const [name, pattern, expected] of cases) {
    await t.test(name, () => assert.deepEqual(getRootDirs(context(pattern)).sort(), expected.sort()));
  }
  await t.test('Next rule reports internal links discovered through wildcard roots', async () => {
    writeFileSync(join(fixture, 'apps/web/pages/profile.tsx'), 'export default function Page() {}');
    const { ESLint } = require('eslint');
    const nextPlugin = require('@next/eslint-plugin-next');
    const eslint = new ESLint({
      cwd: fixture,
      overrideConfigFile: true,
      overrideConfig: [{
        files: ['**/*.jsx'],
        languageOptions: { parserOptions: { ecmaFeatures: { jsx: true } } },
        plugins: { '@next/next': nextPlugin },
        settings: { next: { rootDir: 'apps/{web,admin}' } },
        rules: { '@next/next/no-html-link-for-pages': 'error' },
      }],
    });
    const [result] = await eslint.lintText('const Link = () => <a href="/profile">Profile</a>;', { filePath: 'test.jsx' });
    assert.equal(result.errorCount, 1);
    assert.equal(result.messages[0].ruleId, '@next/next/no-html-link-for-pages');
    const [external] = await eslint.lintText('const Link = () => <a href="https://example.com">External</a>;', { filePath: 'test.jsx' });
    assert.equal(external.errorCount, 0);
  });
});

test('root glob boundary rejects excessive nesting before matching', () => {
  assert.throws(() => globSync('{'.repeat(65) + 'apps/web' + '}'.repeat(65), { onlyDirectories: true }), /nesting limit/);
});

test('root glob boundary rejects excessive length before matching', () => {
  assert.throws(() => globSync('a'.repeat(4097), { onlyDirectories: true }), /length limit/);
});

 test('root glob boundary rejects unsupported consumer APIs', () => {
  assert.throws(() => globSync(['apps/*'], { onlyDirectories: true }), /non-empty string/);
  assert.throws(() => globSync('apps/*', { onlyDirectories: true, dot: true }), /supports only/);
});
