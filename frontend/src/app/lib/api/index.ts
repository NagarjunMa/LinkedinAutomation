// Main API exports - organized by feature
export * from './types';
export * from './config';
export * from './jobs';
export * from './resume';
export * from './profile';

// Re-export for backwards compatibility
export { resumeApi } from './resume';
export { profileApi } from './profile';

// Phase 3 exports
export * from './types-v2';
export { resumeV2Api } from './resume-v2';
export { jdApi } from './jd';
export { creditsApi } from './credits';
