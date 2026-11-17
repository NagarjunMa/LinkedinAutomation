import { describe, expect, it, vi } from 'vitest';
import { readTurn } from './api';

function stream(...chunks: string[]) {
  return new Response(new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(new TextEncoder().encode(chunk));
      controller.close();
    },
  }), { headers: { 'Content-Type': 'text/event-stream; charset=utf-8' } });
}

describe('Career turn stream', () => {
  it('reads split event frames, announces progress, and returns the current retry version', async () => {
    const progress = vi.fn();
    await expect(readTurn(stream(
      'event: analysis.progress\r\ndata: {"type":"analysis.pro',
      'gress"}\r\n\r',
      '\ndata: {"type":"turn.interrupted","key":"same-key","state_version":2,"can_retry":true}\r\n\r\n',
    ), progress)).resolves.toEqual({ type: 'turn.interrupted', key: 'same-key', state_version: 2, can_retry: true });
    expect(progress).toHaveBeenCalledOnce();
  });

  it('treats a dropped stream as an uncertain turn rather than a completed one', async () => {
    await expect(readTurn(stream('data: {"type":"turn.started"}\n\n'), vi.fn())).rejects.toThrow('closed before');
  });

  it('rejects a malformed terminal event and a non-stream response', async () => {
    await expect(readTurn(stream(
      'data: {"type":"turn.interrupted","key":"same-key","state_version":"2","can_retry":true}\n\n',
    ), vi.fn())).rejects.toThrow('closed before');
    await expect(readTurn(Response.json({}), vi.fn())).rejects.toThrow('Expected a Career turn stream');
  });

  it('reads pending and replay as distinct server outcomes', async () => {
    await expect(readTurn(stream('data: {"type":"turn.pending","key":"same-key"}\n\n'), vi.fn()))
      .resolves.toEqual({ type: 'turn.pending', key: 'same-key' });
    const state = { session_id: 'session', owner_id: 'owner' };
    await expect(readTurn(stream(`data: ${JSON.stringify({ type: 'turn.replayed', state, recovered: false })}\n\n`), vi.fn()))
      .resolves.toEqual({ type: 'turn.replayed', state, recovered: false });
  });
});
