const prefix = 'prism.resume:';
const legacyRecentKey = 'prism.recentResumes';

export const recentResumesKey = (userId: string) => `${prefix}${userId}:recent`;
export const resumeDocKey = (userId: string, id: string) => `${prefix}${userId}:doc:${id}`;
export const resumeEditorKey = (userId: string, id: string) => `${prefix}${userId}:editor:${id}`;

export function clearResumeCache(legacyOnly = false) {
  // Storage can be unavailable in a restricted browser. Sign-out must still proceed.
  try {
    for (const key of Object.keys(localStorage)) {
      if (key === legacyRecentKey || (!legacyOnly && key.startsWith(prefix))) {
        localStorage.removeItem(key);
      }
    }
  } catch {}
  try {
    for (const key of Object.keys(sessionStorage)) {
      if (key.startsWith('resumeDoc:') || key.startsWith('resumeEditor:') ||
          (!legacyOnly && key.startsWith(prefix))) {
        sessionStorage.removeItem(key);
      }
    }
  } catch {}
}
