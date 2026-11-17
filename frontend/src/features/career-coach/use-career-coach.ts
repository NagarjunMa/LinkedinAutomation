'use client';

import { useEffect, useEffectEvent, useRef, useState } from 'react';
import { APIError } from '@/app/lib/api/config';
import { careerApi, pageSize, type Decision, type Evidence, type Message, type Session, type StartSession, type Turn } from './api';

const initial = { sessions: [], evidence: [], sessionOffset: 0, evidenceOffset: 0 } as {
  sessions: Session[]; evidence: Evidence[]; sessionOffset: number; evidenceOffset: number;
};
// Allow the server's turn lease to expire before releasing an uncertain request.
const requestDeadlineMs = 65_000;

export function useCareerCoach(owner: string, isCurrentUser: (id: string) => boolean) {
  const [lists, setLists] = useState(initial);
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState<Session>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [acceptedKey, setAcceptedKey] = useState('');
  const [recovery, setRecovery] = useState<Turn>();
  const [activity, setActivity] = useState('');
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const operation = useRef<AbortController | null>(null);
  const submitted = useRef<{ id: string; key: string; rejected: boolean } | undefined>(undefined);
  const ownerIsCurrent = useEffectEvent(() => isCurrentUser(owner));

  useEffect(() => {
    const controller = new AbortController();
    const api = careerApi(owner, controller.signal);
    const records = { ...initial };
    const showRecords = (errorMessage: string) => {
      if (controller.signal.aborted || !ownerIsCurrent()) return;
      setLists({ ...records });
      setError(errorMessage);
      setLoading(false);
    };
    const deadline = window.setTimeout(() => {
      showRecords('Some saved records took too long to load. Reload to try again.');
      controller.abort();
    }, requestDeadlineMs);
    void Promise.allSettled([
      api.sessions(0).then(rows => { records.sessions = rows.filter(row => row.owner_id === owner); }),
      api.evidence(0).then(rows => { records.evidence = rows.filter(row => row.owner_id === owner); }),
    ]).then(results => {
      window.clearTimeout(deadline);
      showRecords(results.some(result => result.status === 'rejected')
        ? 'Some saved records could not be loaded. Reload to try again.' : '');
    });
    return () => {
      window.clearTimeout(deadline);
      controller.abort();
      operation.current?.abort();
    };
  }, [owner]);

  async function run(label: string, action: (api: ReturnType<typeof careerApi>, current: () => boolean) => Promise<void>) {
    if (operation.current || !isCurrentUser(owner)) return;
    const controller = new AbortController();
    operation.current = controller;
    const current = () => !controller.signal.aborted && isCurrentUser(owner);
    setActivity(label);
    setError('');
    const deadline = window.setTimeout(() => {
      if (operation.current !== controller) return;
      if (current()) {
        setActivity('');
        setError('The request took too long. Try again.');
      }
      operation.current = null;
      controller.abort();
    }, requestDeadlineMs);
    try {
      await action(careerApi(owner, controller.signal), current);
    } catch (failure) {
      if (current()) {
        setError(failure instanceof APIError && failure.status === 409
          ? 'This record has changed. Reopen the session or refresh evidence before trying again.'
          : failure instanceof APIError && failure.status === 503
            ? 'Career Coach is currently unavailable. Try again later.'
            : failure instanceof APIError && failure.status === 413
              ? 'This reply or claim is too large. Shorten it and try again.'
              : 'The request did not finish. Try again.');
      }
    } finally {
      window.clearTimeout(deadline);
      if (operation.current === controller) {
        operation.current = null;
        if (current()) setActivity('');
      }
    }
  }

  function showSession(row: Session, transcript: Message[]) {
    if (row.owner_id !== owner) throw new Error('Session owner changed');
    const last = transcript.at(-1);
    const unfinished = last?.role === 'user' && last.processing_status !== 'complete';
    const canCheck = unfinished && last.turn_recovery !== null;
    const local = submitted.current;
    const saved = local?.id === row.session_id && transcript.some(message =>
      message.role === 'assistant' && message.key === local.key && message.processing_status === 'complete');
    if (saved && local) {
      setAcceptedKey(local.key);
      submitted.current = undefined;
    }
    const uncertain = !saved && local?.id === row.session_id && !local.rejected && recovery?.key === local.key;
    setSession(row);
    setMessages(transcript);
    setRecovery(canCheck ? { key: last.key, content: last.content, expected_state_version: row.state_version,
      candidate_stage: last.turn_recovery ? last.turn_recovery.candidate_stage
        : recovery?.key === last.key ? recovery.candidate_stage : undefined,
    } : uncertain ? recovery : undefined);
    setNotice(canCheck || uncertain ? 'Check the status of your last reply before sending another.'
      : unfinished ? 'This earlier reply can’t be retried. You can continue with a new reply.' : '');
    setLists(previous => ({ ...previous, sessions: previous.sessions.map(item =>
      item.session_id === row.session_id ? row : item) }));
  }

  function open(id: string, resume = false) {
    return run('Opening session…', async (api, current) => {
      const row = resume ? await api.resume(id) : await api.session(id);
      if (row.owner_id !== owner || row.session_id !== id) throw new Error('Unexpected session');
      const transcript = await api.messages(id);
      if (current()) showSession(row, transcript);
    });
  }

  function start(input: StartSession) {
    return run('Starting session…', async (api, current) => {
      const row = await api.start(input);
      if (!current()) return;
      showSession(row, []);
      setLists(previous => ({ ...previous, sessions: [row, ...previous.sessions] }));
    });
  }

  function send(content: string, stage?: NonNullable<Turn['candidate_stage']>) {
    if (!session || session.status !== 'active' || recovery || !content.trim()) return;
    return submit(session.session_id, {
      key: crypto.randomUUID(), content: content.trim(), expected_state_version: session.state_version,
      ...(stage ? { candidate_stage: stage } : {}),
    }, true);
  }

  function submit(id: string, request: Turn, fresh = false) {
    return run('Sending reply…', async (api, current) => {
      if (fresh) submitted.current = { id, key: request.key, rejected: false };
      setRecovery({ ...request, retry: false });
      setNotice('Check the status of your last reply before sending another.');
      const outcome = await api.turn(id, request, () => { if (current()) setActivity('Preparing the next question…'); }).catch(failure => {
        if (current() && failure instanceof APIError && submitted.current?.key === request.key) {
          const unavailable = failure.status === 503 && failure.code === 'service_unavailable';
          const rejected = (!request.retry && failure.status === 409)
            || (fresh && (unavailable || [413, 422, 429].includes(failure.status ?? 0)));
          if (rejected) submitted.current.rejected = true;
          if (rejected && failure.status !== 409) {
            setRecovery(undefined);
            setNotice('');
          }
        }
        throw failure;
      });
      if (!current()) return;
      switch (outcome.type) {
        case 'turn.completed':
        case 'turn.replayed': {
          if (outcome.state.session_id !== id || outcome.state.owner_id !== owner) throw new Error('Unexpected turn');
          const [row, transcript] = await Promise.all([api.session(id), api.messages(id)]);
          if (row.session_id !== id) throw new Error('Unexpected session');
          if (current()) {
            showSession(row, transcript);
            setNotice(outcome.type === 'turn.replayed' && outcome.recovered ? 'Reply recovered.' : 'Reply received.');
            await refreshEvidence(api, current, lists.evidenceOffset);
          }
          break;
        }
        case 'turn.pending':
          if (outcome.key !== request.key) throw new Error('Unexpected turn key');
          setNotice('Your reply is still being processed.');
          break;
        case 'turn.interrupted':
          if (outcome.key !== request.key) throw new Error('Unexpected turn key');
          setRecovery(outcome.can_retry ? { ...request, retry: true, expected_state_version: outcome.state_version } : undefined);
          setNotice(outcome.can_retry ? 'Reply interrupted. You can retry it.' : 'This reply can no longer be retried. Reopen the session to see what changed.');
          break;
        case 'turn.failed':
          setNotice('The reply was interrupted. Check its status to recover it.');
          break;
      }
    });
  }

  function decide(item: Evidence, action: Decision['action'], claim?: string) {
    return run('Saving evidence decision…', async (api, current) => {
      const next = await api.decide(item.evidence_id, { revision: item.revision, action, ...(claim === undefined ? {} : { claim }) });
      if (next.owner_id !== owner || next.evidence_id !== item.evidence_id || next.revision <= item.revision) {
        throw new Error('Unexpected evidence revision');
      }
      if (current()) {
        setLists(previous => ({ ...previous, evidence: previous.evidence.map(row =>
          row.evidence_id === next.evidence_id ? next : row) }));
        setNotice('Evidence decision saved.');
      }
    });
  }

  function page(kind: 'sessions' | 'evidence', offset: number) {
    return run('Loading records…', async (api, current) => {
      if (kind === 'sessions') {
        const rows = await api.sessions(offset);
        if (current()) setLists(previous => ({ ...previous, sessionOffset: offset, sessions: rows.filter(row => row.owner_id === owner) }));
      } else {
        await refreshEvidence(api, current, offset);
      }
    });
  }

  async function refreshEvidence(api: ReturnType<typeof careerApi>, current: () => boolean, offset: number) {
    try {
      const rows = await api.evidence(offset);
      if (current()) setLists(previous => ({ ...previous, evidenceOffset: offset, evidence: rows.filter(row => row.owner_id === owner) }));
    } catch {
      if (current()) setError('Your evidence could not be refreshed. Try refreshing it again.');
    }
  }

  return { ...lists, pageSize, loading, session, messages, acceptedKey, recovery, activity, notice, error, open, start, send, decide, page,
    retry: (stage?: NonNullable<Turn['candidate_stage']>) => session && recovery && submit(session.session_id, {
      ...recovery, candidate_stage: recovery.candidate_stage === undefined ? stage : recovery.candidate_stage,
    }) };
}
