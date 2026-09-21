import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProtectedRoute } from './protected-route';

const state = vi.hoisted(() => ({
  auth: { user: { id: 'alice' } as { id: string } | null,
    session: { user: { id: 'alice' }, access_token: 'alice-token' }, loading: false },
  push: vi.fn(),
}));
vi.mock('@/contexts/auth-context', () => ({ useAuth: () => state.auth }));
vi.mock('next/navigation', () => ({ useRouter: () => ({ push: state.push }) }));

describe('authenticated account setup boundary', () => {
  beforeEach(() => {
    state.auth = { user: { id: 'alice' }, session: { user: { id: 'alice' }, access_token: 'alice-token' }, loading: false };
    document.cookie = 'test-bypass-auth=; Max-Age=0; path=/';
  });
  afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers(); });

  it('does not mount feature consumers until setup succeeds on a restored session', async () => {
    let complete!: (response: Response) => void;
    const fetchMock = vi.fn(() => new Promise<Response>(resolve => { complete = resolve; }));
    vi.stubGlobal('fetch', fetchMock);
    render(<ProtectedRoute><div>Private dashboard</div></ProtectedRoute>);
    expect(screen.queryByText('Private dashboard')).not.toBeInTheDocument();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());
    expect(fetchMock.mock.calls[0]).toEqual([
      expect.stringContaining('/api/v1/auth/bootstrap'),
      expect.objectContaining({ method: 'POST', headers: { Authorization: 'Bearer alice-token' } }),
    ]);
    await act(async () => complete(new Response(null, { status: 204 })));
    expect(screen.getByText('Private dashboard')).toBeInTheDocument();
  });

  it('offers safe retry without mounting consumers after a failed setup', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(new Response('private database error', { status: 503 }))
      .mockResolvedValueOnce(new Response(null, { status: 204 })));
    render(<ProtectedRoute><div>Private dashboard</div></ProtectedRoute>);
    fireEvent.click(await screen.findByRole('button', { name: 'Try again' }));
    expect(screen.queryByText('private database error')).not.toBeInTheDocument();
    expect(await screen.findByText('Private dashboard')).toBeInTheDocument();
  });

  it('ignores old success after switching accounts or logging out', async () => {
    const completions: Array<(response: Response) => void> = [];
    vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>(resolve => completions.push(resolve))));
    const { rerender } = render(<ProtectedRoute><div>Private dashboard</div></ProtectedRoute>);
    state.auth = { user: { id: 'bob' }, session: { user: { id: 'bob' }, access_token: 'bob-token' }, loading: false };
    rerender(<ProtectedRoute><div>Private dashboard</div></ProtectedRoute>);
    await act(async () => completions[0](new Response(null, { status: 204 })));
    expect(screen.queryByText('Private dashboard')).not.toBeInTheDocument();
    state.auth.user = null;
    rerender(<ProtectedRoute><div>Private dashboard</div></ProtectedRoute>);
    await act(async () => completions[1](new Response(null, { status: 204 })));
    expect(screen.queryByText('Private dashboard')).not.toBeInTheDocument();
  });

  it('preserves mounted dashboard state across routine token refresh', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal('fetch', fetchMock);
    const view = <ProtectedRoute><input aria-label="Unsaved draft" defaultValue="" /></ProtectedRoute>;
    const { rerender } = render(view);
    fireEvent.change(await screen.findByRole('textbox'), { target: { value: 'keep my work' } });
    state.auth.session.access_token = 'refreshed-token';
    rerender(<ProtectedRoute><input aria-label="Unsaved draft" defaultValue="" /></ProtectedRoute>);
    expect(screen.getByRole('textbox')).toHaveValue('keep my work');
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it('aborts a stalled setup and offers retry after the bounded timeout', async () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn((_url: string, options: RequestInit) => new Promise<Response>((_resolve, reject) => {
      options.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
    }));
    vi.stubGlobal('fetch', fetchMock);
    render(<ProtectedRoute><div>Private dashboard</div></ProtectedRoute>);
    await act(async () => { await vi.advanceTimersByTimeAsync(15000); });
    expect(fetchMock.mock.calls[0][1].signal?.aborted).toBe(true);
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument();
    expect(screen.queryByText('Private dashboard')).not.toBeInTheDocument();
  });
});
