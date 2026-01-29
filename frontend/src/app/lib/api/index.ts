// Main API exports - organized by feature
export * from './types';
export * from './config';
export * from './jobs';
export * from './resume';
export * from './profile';
export * from './referral';
export * from './email';

// Re-export for backwards compatibility
export { resumeApi } from './resume';
export { profileApi } from './profile';
export { referralApi, referralTemplatesAPI } from './referral';
export { emailAgentApi } from './email';

// Explicitly export missing functions for components