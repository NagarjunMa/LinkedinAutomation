import { makeAPIRequest } from '@/app/lib/api/config';
import type { components } from '@/generated/api/types';
import { z } from 'zod';

type Schemas = components['schemas'];
export type Session = Schemas['SessionView'];
export type StartSession = Schemas['SessionInput'];
export type Message = Schemas['MessageView'];
export type Turn = Schemas['TurnInput'];
export type Evidence = Schemas['CareerEvidenceItem'];
export type Decision = Schemas['EvidenceDecisionInput'];

const state = z.object({ session_id: z.string(), owner_id: z.string() });
const completed = z.discriminatedUnion('type', [
  z.object({ type: z.literal('turn.completed'), state }),
  z.object({ type: z.literal('turn.replayed'), state, recovered: z.boolean() }),
  z.object({ type: z.literal('turn.pending'), key: z.string() }),
  z.object({ type: z.literal('turn.interrupted'), key: z.string(), state_version: z.number().int().positive(), can_retry: z.boolean() }),
  z.object({ type: z.literal('turn.failed'), code: z.enum(['state_changed', 'turn_unavailable']) }),
]);

export async function readTurn(response: Response, onProgress: () => void) {
  if (!response.headers.get('content-type')?.startsWith('text/event-stream') || !response.body) {
    throw new Error('Expected a Career turn stream');
  }
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = '';
  try {
    while (true) {
      const chunk = await reader.read();
      if (chunk.done) throw new Error('Turn stream closed before its outcome');
      buffer += chunk.value;
      let boundary = /\r?\n\r?\n/.exec(buffer);
      while (boundary) {
        const data = buffer.slice(0, boundary.index).split(/\r?\n/)
          .filter(line => line.startsWith('data:')).map(line => line.slice(5).replace(/^ /, '')).join('\n');
        buffer = buffer.slice(boundary.index + boundary[0].length);
        if (data) {
          if (data.length > 64_000) throw new Error('Career event exceeds the limit');
          const event = JSON.parse(data);
          if (event?.type === 'turn.started' || event?.type === 'analysis.progress') onProgress();
          const outcome = completed.safeParse(event);
          if (outcome.success) return outcome.data;
        }
        boundary = /\r?\n\r?\n/.exec(buffer);
      }
      if (buffer.length > 64_000) throw new Error('Career event exceeds the limit');
    }
  } finally {
    void reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}

const sessions = '/api/v1/career/sessions';
const evidence = '/api/v1/career/evidence';
export const pageSize = 50;

export function careerApi(owner: string, signal?: AbortSignal) {
  const options = { expectedUserId: owner, signal, cache: 'no-store' as const };
  const sessionPath = (id: string) => `${sessions}/${encodeURIComponent(id)}`;
  const page = (offset: number) => `?limit=${pageSize}&offset=${offset}`;
  return {
    sessions: (offset: number) => makeAPIRequest<Session[]>(sessions + page(offset), options),
    start: (body: StartSession) => makeAPIRequest<Session>(sessions, { ...options, method: 'POST', body: JSON.stringify(body) }),
    session: (id: string) => makeAPIRequest<Session>(sessionPath(id), options),
    resume: (id: string) => makeAPIRequest<Session>(sessionPath(id) + '/resume', { ...options, method: 'POST' }),
    messages: (id: string) => makeAPIRequest<Message[]>(sessionPath(id) + '/messages?limit=100', options),
    turn: (id: string, body: Turn, onProgress: () => void) =>
      makeAPIRequest(sessionPath(id) + '/turns', { ...options, method: 'POST', body: JSON.stringify(body) },
        response => readTurn(response, onProgress)),
    evidence: (offset: number) => makeAPIRequest<Evidence[]>(evidence + page(offset), options),
    decide: (id: string, body: Decision) => makeAPIRequest<Evidence>(
      `${evidence}/${encodeURIComponent(id)}/decision`, { ...options, method: 'PATCH', body: JSON.stringify(body) }),
  };
}
