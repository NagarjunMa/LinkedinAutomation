const { statSync } = require('node:fs');
const { isAbsolute } = require('node:path');
const { globSync: matchDirectories, hasMagic } = require('glob');

function isDirectory(path) {
  try { return statSync(path).isDirectory(); }
  catch (error) {
    if (error.code === 'ENOENT' || error.code === 'ENOTDIR') return false;
    throw error;
  }
}

// This is deliberately scoped to Next ESLint's getRootDirs consumer. It is not
// a general fast-glob replacement. Fail visibly if that consumer changes API.
function globSync(pattern, options) {
  if (typeof pattern !== 'string' || pattern.length === 0) {
    throw new TypeError('Next root glob requires a non-empty string');
  }
  if (!options || options.onlyDirectories !== true || Object.keys(options).length !== 1) {
    throw new TypeError('Next root glob supports only { onlyDirectories: true }');
  }
  if (pattern.length > 4096) throw new RangeError('Next root glob exceeds length limit (4096)');
  let depth = 0;
  for (let index = 0; index < pattern.length; index += 1) {
    const character = pattern[index];
    if (character === '\\') { index += 1; continue; }
    if ('{[('.includes(character) && ++depth > 64) {
      throw new RangeError('Next root glob exceeds nesting limit (64)');
    }
    if ('}])'.includes(character)) depth = Math.max(0, depth - 1);
  }

  // Literal roots must retain their spelling and must not expand descendants.
  if (!hasMagic(pattern, { magicalBraces: true })) {
    return isDirectory(pattern) ? [pattern] : [];
  }

  // fast-glob walks descendants for a terminal globstar, excluding its base.
  // Apply this also to terminal globstars inside brace alternatives.
  const descendants = pattern.replace(/(^|\/)\*\*(?=\/?(?:$|[,}]))/g, '$1**/*');
  return matchDirectories(descendants, {
    follow: true,
    absolute: isAbsolute(pattern),

  }).filter(isDirectory).map(directory => {
    const trimmed = directory.replace(/\/$/, '');
    return pattern.startsWith('./') ? `./${trimmed}` : trimmed;
  });
}

module.exports = { globSync };
