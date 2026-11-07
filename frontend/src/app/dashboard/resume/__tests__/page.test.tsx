import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { onlineManager, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { expect, it, vi } from 'vitest';
import { http, HttpResponse, server } from '@/test-utils/msw-server';
import { recentResumesKey } from '@/lib/resume-cache';

const auth = vi.hoisted(() => ({ id: 'owner-a' }));
const actions = vi.hoisted(() => ({ toast: vi.fn(), push: vi.fn() }));
vi.mock('next/navigation', () => ({ useRouter: () => ({ push: actions.push }) }));
vi.mock('@/contexts/auth-context', () => ({ useAuth: () => ({
  user: { id: auth.id },
  isCurrentUser: (id: string) => auth.id === id,
}) }));
vi.mock('@/components/ui/use-toast', () => ({ useToast: () => ({ toast: actions.toast }) }));
vi.mock('@/lib/supabase', () => ({
  createClient: () => ({ auth: { getSession: async () => ({
    data: { session: { user: { id: auth.id }, access_token: `token-${auth.id}` } },
  }) } }),
}));
import ResumeLibraryPage from '../page';

it('isolates recent files and rejects an offline upload after the account changes', async () => {
  const upload = vi.fn();
  server.use(http.post('http://localhost:8000/api/v1/resumes/upload', ({ request }) => {
    upload(request.headers.get('authorization'));
    return HttpResponse.json({
      resume_document_id: 'doc-1', contact: { name: 'Synthetic' }, raw_text: 'Synthetic',
    }, { status: 201 });
  }));
  const client = new QueryClient();
  const element = () => <QueryClientProvider client={client}><ResumeLibraryPage /></QueryClientProvider>;
  localStorage.setItem(recentResumesKey('owner-a'), JSON.stringify([
    { id: 'doc-1', name: 'First account resume', uploaded_at: '2026-11-07T00:00:00Z' },
  ]));
  onlineManager.setOnline(false);
  const view = render(element());
  try {
    expect(screen.getByRole('link', { name: /First account resume/ })).toBeInTheDocument();
    const file = new File(['synthetic'], 'first-account.pdf', { type: 'application/pdf' });
    fireEvent.drop(screen.getByTestId('resume-dropzone'), { dataTransfer: { files: [file] } });
    fireEvent.click(screen.getByRole('button', { name: 'Upload' }));
    const mutation = client.getMutationCache().getAll()[0];
    await waitFor(() => expect(mutation.state.isPaused).toBe(true));

    auth.id = 'owner-b';
    view.rerender(element());
    expect(screen.queryByRole('link', { name: /First account resume/ })).not.toBeInTheDocument();
    await act(async () => onlineManager.setOnline(true));

    await waitFor(() => expect(mutation.state.status).not.toBe('pending'));
    expect(upload).not.toHaveBeenCalled();
    expect(mutation.state).toMatchObject({ status: 'error', error: { status: 401 } });
    expect(actions.push).not.toHaveBeenCalled();
    expect(actions.toast).not.toHaveBeenCalled();
  } finally {
    onlineManager.setOnline(true);
    view.unmount();
    auth.id = 'owner-a';
    localStorage.removeItem(recentResumesKey('owner-a'));
  }
});
