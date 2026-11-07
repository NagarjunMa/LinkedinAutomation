import type { BrowserContext } from '@playwright/test';

export async function seedResumeSession(context: BrowserContext) {
  const origin = `http://localhost:${process.env.E2E_PORT ?? '3000'}`;
  const project = new URL(process.env.NEXT_PUBLIC_SUPABASE_URL ?? 'https://test.supabase.co').hostname.split('.')[0];
  const session = {
    access_token: 'synthetic-resume-test-token',
    refresh_token: 'synthetic-resume-test-refresh',
    token_type: 'bearer',
    expires_at: Math.floor(Date.now() / 1000) + 3600,
    user: { id: 'resume-test-user', aud: 'authenticated', email: 'resume-test@example.test' },
  };
  const encodedSession = Buffer.from(JSON.stringify(session)).toString('base64url');
  await context.addCookies([
    { name: 'test-bypass-auth', value: '1', url: origin },
    { name: `sb-${project}-auth-token`, value: `base64-${encodedSession}`, url: origin },
  ]);
}
