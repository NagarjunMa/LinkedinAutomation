'use client';

import { useEffect, useEffectEvent, useRef, useState } from 'react';
import { APIError } from '@/app/lib/api/config';
import { careerApi, pageSize, type Decision, type Evidence, type Message, type Session, type StartSession, type Turn } from './api';

const initial = {
  sessions: [] as Session[], evidence: [] as Evidence[], sessionOffset: 0, evidenceOffset: 0,
  sessionsUnavailable: false, evidenceUnavailable: false,
};
// Allow the server's turn lease to expire before releasing an uncertain request.
const requestDeadlineMs = 65_000;
type Activity = { label: string; stopWaiting?: () => void };
type Recovery = { request: Turn; saved: boolean };

export function useCareerCoach(owner: string, isCurrentUser: (id: string) => boolean) {
  const [lists, setLists] = useState(initial);
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState<Session>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [acceptedKey, setAcceptedKey] = useState('');
  const [recovery, setRecovery] = useState<Recovery>();
  const [activity, setActivity] = useState<Activity>();
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [announcement, setAnnouncement] = useState('');
  const [needsConversationRefresh, setNeedsConversationRefresh] = useState(false);
  const operation = useRef<AbortController | null>(null);
  const submitted = useRef<{ id: string; key: string; rejected: boolean } | undefined>(undefined);
  const unretryable = useRef<{ id: string; key: string } | null>(null);
  const ownerIsCurrent = useEffectEvent(() => isCurrentUser(owner));

  useEffect(() => {
    const controller = new AbortController();
    const api = careerApi(owner, controller.signal);
    const records = { ...initial, sessionsUnavailable: true, evidenceUnavailable: true };
    const showRecords = (errorMessage: string) => {
      if (controller.signal.aborted || !ownerIsCurrent()) return;
      setLists({ ...records });
      setError(errorMessage);
      setLoading(false);
    };
    const deadline = window.setTimeout(() => {
      showRecords('Some saved records took too long to load. Retry in the affected section.');
      controller.abort();
    }, requestDeadlineMs);
    void Promise.allSettled([
      api.sessions(0).then(rows => {
        records.sessions = rows.filter(row => row.owner_id === owner);
        records.sessionsUnavailable = false;
      }),
      api.evidence(0).then(rows => {
        records.evidence = rows.filter(row => row.owner_id === owner);
        records.evidenceUnavailable = false;
      }),
    ]).then(results => {
      window.clearTimeout(deadline);
      showRecords(results.some(result => result.status === 'rejected')
        ? 'Some saved records could not be loaded. Retry in the affected section.' : '');
    });
    return () => {
      window.clearTimeout(deadline);
      controller.abort();
      operation.current?.abort();
    };
  }, [owner]);

  async function run(
    label: string,
    action: (api: ReturnType<typeof careerApi>, current: () => boolean,
      updateActivity: (label: string, stoppable?: boolean) => void) => Promise<void>,
    stoppable = false,
  ) {
    if (operation.current || !isCurrentUser(owner)) return;
    const controller = new AbortController();
    operation.current = controller;
    const current = () => !controller.signal.aborted && isCurrentUser(owner);
    setError('');
    const abort = (userStopped: boolean) => {
      if (operation.current !== controller) return;
      window.clearTimeout(deadline);
      if (current()) {
        setActivity(undefined);
        if (userStopped) setNotice('Stopped waiting. Use the recovery control to continue.');
        else setError('The request took too long. Try again.');
      }
      operation.current = null;
      controller.abort();
    };
    const stopWaiting = stoppable ? () => abort(true) : undefined;
    const updateActivity = (label: string, canStop = stoppable) => {
      if (current()) setActivity({ label, stopWaiting: canStop ? stopWaiting : undefined });
    };
    updateActivity(label);
    const deadline = window.setTimeout(() => abort(false), requestDeadlineMs);
    try {
      await action(careerApi(owner, controller.signal), current, updateActivity);
    } catch (failure) {
      if (current()) {
        setError(failure instanceof APIError && failure.status === 409
          ? 'This record has changed. Refresh the conversation or evidence before trying again.'
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
        if (current()) setActivity(undefined);
      }
    }
  }

  async function readConversation(api: ReturnType<typeof careerApi>, id: string, resume = false) {
    let row = resume ? await api.resume(id) : await api.session(id);
    for (let attempt = 0; attempt < 2; attempt++) {
      if (row.owner_id !== owner || row.session_id !== id) throw new Error('Unexpected session');
      const transcript = await api.messages(id);
      const after = await api.session(id);
      if (after.owner_id !== owner || after.session_id !== id) throw new Error('Unexpected session');
      // The turn may commit between the separate session and transcript requests.
      if (after.state_version === row.state_version) return { row: after, transcript };
      row = after;
    }
    throw new APIError('Conversation changed during refresh.', 409);
  }

  function showSession(row: Session, transcript: Message[], completedReply?: Message) {
    if (row.owner_id !== owner) throw new Error('Session owner changed');
    const last = transcript.at(-1);
    const unfinished = last?.role === 'user' && last.processing_status !== 'complete';
    const canCheck = unfinished && last.turn_recovery !== null
      && !(unretryable.current?.id === row.session_id && unretryable.current.key === last.key);
    const local = submitted.current;
    const saved = local?.id === row.session_id && transcript.find(message =>
      message.role === 'assistant' && message.key === local.key && message.processing_status === 'complete');
    if (saved && local) {
      setAcceptedKey(local.key);
      submitted.current = undefined;
    }
    const uncertain = !saved && local?.id === row.session_id && !local.rejected && recovery?.request.key === local.key;
    const reply = completedReply ?? (session?.session_id === row.session_id && saved);
    setAnnouncement(reply ? `Coach: ${reply.content}` : '');
    setNeedsConversationRefresh(false);
    setSession(row);
    setMessages(transcript);
    setRecovery(canCheck ? { saved: true, request: {
      key: last.key, content: last.content, expected_state_version: row.state_version,
      candidate_stage: last.turn_recovery ? last.turn_recovery.candidate_stage
        : recovery?.request.key === last.key ? recovery.request.candidate_stage : undefined,
    },
    } : uncertain ? recovery : undefined);
    setNotice(canCheck || uncertain ? 'Continue with your last reply before sending another.'
      : unfinished ? 'This earlier reply can’t be retried. You can continue with a new reply.' : '');
    setLists(previous => ({ ...previous, sessions: previous.sessions.map(item =>
      item.session_id === row.session_id ? row : item) }));
  }

  function open(id: string, resume = false) {
    return run('Opening session…', async (api, current) => {
      const { row, transcript } = await readConversation(api, id, resume).catch(failure => {
        if (current() && session?.session_id === id && failure instanceof APIError && failure.status === 409) {
          setNeedsConversationRefresh(true);
        }
        throw failure;
      });
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
    if (!session || session.status !== 'active' || recovery || needsConversationRefresh || !content.trim()) return;
    return submit(session.session_id, {
      key: crypto.randomUUID(), content: content.trim(), expected_state_version: session.state_version,
      ...(stage ? { candidate_stage: stage } : {}),
    }, { fresh: true });
  }

  function submit(id: string, request: Turn, { fresh = false, saved = false } = {}) {
    const label = request.retry ? 'Retrying reply…' : saved ? 'Checking turn status…' : 'Sending reply…';
    return run(label, async (api, current, updateActivity) => {
      if (fresh) submitted.current = { id, key: request.key, rejected: false };
      setAnnouncement('');
      const pending = { request: { ...request, retry: false }, saved };
      setRecovery(pending);
      setNotice('Continue with your last reply before sending another.');
      const outcome = await api.turn(id, request, () => {
        if (!current()) return;
        setRecovery(previous => previous?.saved ? previous : { ...pending, saved: true });
        updateActivity('Preparing the next question…');
      }).catch(failure => {
        if (current() && failure instanceof APIError) {
          if (failure.status === 409) setNeedsConversationRefresh(true);
          if (submitted.current?.key === request.key) {
            const unavailable = failure.status === 503 && failure.code === 'service_unavailable';
            const rejected = (!request.retry && failure.status === 409)
              || (!saved && (unavailable || [413, 422, 429].includes(failure.status ?? 0)));
            if (rejected) submitted.current.rejected = true;
            if (rejected && failure.status !== 409) {
              setRecovery(undefined);
              setNotice('');
            }
          }
        }
        throw failure;
      });
      if (!current()) return;
      switch (outcome.type) {
        case 'turn.completed':
        case 'turn.replayed': {
          if (outcome.state.session_id !== id || outcome.state.owner_id !== owner) throw new Error('Unexpected turn');
          setRecovery({ ...pending, saved: true });
          const { row, transcript } = await readConversation(api, id);
          if (current()) {
            const reply = transcript.find(message =>
              message.role === 'assistant' && message.key === request.key && message.processing_status === 'complete');
            if (!reply) throw new Error('Saved reply missing from transcript');
            showSession(row, transcript, reply);
            setNotice(outcome.type === 'turn.replayed' && outcome.recovered ? 'Reply recovered.' : 'Reply received.');
            updateActivity('Refreshing evidence…', false);
            await refreshEvidence(api, current, lists.evidenceOffset);
          }
          break;
        }
        case 'turn.pending':
          if (outcome.key !== request.key) throw new Error('Unexpected turn key');
          setRecovery({ ...pending, saved: true });
          setNotice('Your reply is still being processed.');
          break;
        case 'turn.interrupted':
          if (outcome.key !== request.key) throw new Error('Unexpected turn key');
          if (outcome.can_retry) {
            setRecovery({ saved: true, request: { ...request, retry: true, expected_state_version: outcome.state_version } });
          } else {
            unretryable.current = { id, key: request.key };
            if (submitted.current?.key === request.key) submitted.current.rejected = true;
            setNeedsConversationRefresh(true);
          }
          setNotice(outcome.can_retry ? 'Reply interrupted. You can retry it.' : 'This reply can no longer be retried. Refresh the conversation to continue.');
          break;
        case 'turn.failed':
          setNotice('The reply was interrupted. Check its status to recover it.');
          break;
      }
    }, true);
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
        if (current()) setLists(previous => ({
          ...previous, sessionOffset: offset, sessions: rows.filter(row => row.owner_id === owner), sessionsUnavailable: false,
        }));
      } else {
        await refreshEvidence(api, current, offset);
      }
    });
  }

  async function refreshEvidence(api: ReturnType<typeof careerApi>, current: () => boolean, offset: number) {
    try {
      const rows = await api.evidence(offset);
      if (current()) setLists(previous => ({
        ...previous, evidenceOffset: offset, evidence: rows.filter(row => row.owner_id === owner), evidenceUnavailable: false,
      }));
    } catch {
      if (current()) setError('Your evidence could not be refreshed. Try refreshing it again.');
    }
  }

  return { ...lists, pageSize, loading, session, messages, acceptedKey, recovery, activity: activity?.label, notice, error,
    announcement, needsConversationRefresh, stopWaiting: activity?.stopWaiting, open, start, send, decide, page,
    retry: (stage?: NonNullable<Turn['candidate_stage']>) => session && recovery && !needsConversationRefresh
      && submit(session.session_id, {
        ...recovery.request, candidate_stage: recovery.request.candidate_stage === undefined ? stage : recovery.request.candidate_stage,
      }, { saved: recovery.saved }) };
}
