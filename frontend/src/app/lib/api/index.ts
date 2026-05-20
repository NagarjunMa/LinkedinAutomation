// Main API exports - organized by feature
export * from './types';
export * from './config';
export * from './jobs';
export * from './resume';
export * from './profile';

// Re-export for backwards compatibility
export { resumeApi } from './resume';
export { profileApi } from './profile';
