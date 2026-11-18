'use client';

import { useEffect, useId, useRef, useState, type Ref } from 'react';
import { ArrowUp, MessageSquare, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useAuth } from '@/contexts/auth-context';
import type { Session, StartSession } from './api';
import { EvidenceReview } from './evidence-review';
import { useCareerCoach } from './use-career-coach';

const modes: Record<Session['mode'], string> = {
  foundation: 'Foundation interview', target_calibration: 'Target calibration',
  application_gap: 'Application gaps', career_refresh: 'Career refresh',
};
const stages = {
  student: 'Student', new_graduate: 'New graduate', early_career: 'Early career',
  experienced_ic: 'Experienced individual contributor', manager_or_leader: 'Manager or leader',
  senior_staff_or_founder: 'Senior staff or founder', career_switcher: 'Changing careers',
  returning_professional: 'Returning to work',
} satisfies Record<NonNullable<StartSession['candidate_stage']>, string>;
type SelectedStage = keyof typeof stages | '';

export function CareerCoach() {
  const { user, isCurrentUser } = useAuth();
  return user ? <CoachWorkspace key={user.id} owner={user.id} isCurrentUser={isCurrentUser} /> : null;
}

function CoachWorkspace({ owner, isCurrentUser }: { owner: string; isCurrentUser: (id: string) => boolean }) {
  const coach = useCareerCoach(owner, isCurrentUser);
  const { session, activity, loading, recovery, needsConversationRefresh, stopWaiting } = coach;
  const busy = loading || Boolean(activity);
  const [stage, setStage] = useState<SelectedStage>('');
  const [existingStage, setExistingStage] = useState<SelectedStage>('');
  const transcript = useRef<HTMLOListElement>(null);
  const conversationHeading = useRef<HTMLHeadingElement>(null);
  const conversationTrigger = useRef<{ element: HTMLElement | null; previous: Session | undefined } | null>(null);
  const sessionsHeading = useRef<HTMLHeadingElement>(null);
  const sessionsRetryTrigger = useRef<HTMLButtonElement>(null);
  const replyInput = useRef<HTMLTextAreaElement>(null);
  const retryButton = useRef<HTMLButtonElement>(null);
  const refreshButton = useRef<HTMLButtonElement>(null);
  const stopButton = useRef<HTMLButtonElement>(null);
  const restoreTurnFocus = useRef<'turn' | 'transcript' | null>(null);
  const title = session ? modes[session.mode] : 'Conversation';
  const status = loading ? 'Loading your sessions…' : activity || coach.notice;
  const mayResend = recovery && !recovery.saved && !recovery.request.retry;

  useEffect(() => {
    if (transcript.current) transcript.current.scrollTop = transcript.current.scrollHeight;
  }, [coach.messages]);

  useEffect(() => {
    const trigger = conversationTrigger.current;
    if (busy || !trigger) return;
    conversationTrigger.current = null;
    const active = document.activeElement;
    if (active !== document.body && active !== trigger.element) return;
    if (session && session !== trigger.previous) conversationHeading.current?.focus();
    else if (active === document.body) {
      const target = trigger.element?.isConnected ? trigger.element : refreshButton.current;
      target?.focus();
    }
  }, [busy, session, coach.error]);

  useEffect(() => {
    const trigger = sessionsRetryTrigger.current;
    if (busy || !trigger) return;
    sessionsRetryTrigger.current = null;
    if (document.activeElement === document.body || document.activeElement === trigger) {
      (coach.sessionsUnavailable ? trigger : sessionsHeading.current)?.focus();
    }
  }, [busy, coach.sessionsUnavailable]);

  useEffect(() => {
    if (!restoreTurnFocus.current) return;
    const active = document.activeElement;
    const lostFocus = active === document.body || active?.closest('[hidden]') || active?.matches(':disabled');
    if (busy) {
      if (lostFocus && stopButton.current) stopButton.current.focus();
      else if (lostFocus && transcript.current) {
        restoreTurnFocus.current = 'transcript';
        transcript.current.focus();
      }
      return;
    }
    const onTemporaryTarget = restoreTurnFocus.current === 'transcript' && active === transcript.current;
    restoreTurnFocus.current = null;
    if (lostFocus || onTemporaryTarget) {
      const next = needsConversationRefresh ? refreshButton.current : recovery ? retryButton.current : replyInput.current;
      (next?.matches(':enabled') ? next : transcript.current)?.focus();
    }
  }, [busy, recovery, needsConversationRefresh, stopWaiting]);

  function enterConversation(element: HTMLElement | null, action: () => void) {
    conversationTrigger.current = { element, previous: session };
    action();
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <header className="border-b border-border pb-5">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Career Coach</h1>
        <p className="mt-2 max-w-prose text-sm leading-relaxed text-muted-foreground">
          Talk through your experience one question at a time. Review the details you want to keep as career evidence.
        </p>
      </header>
      <div role="status" className={status ? 'text-sm text-muted-foreground' : 'sr-only'}>
        {status}
      </div>
      <div role="status" aria-label="Coach reply" className="sr-only">{coach.announcement}</div>
      <p role="alert" className={coach.error ? 'rounded-lg border border-border p-3 text-sm' : 'sr-only'}>{coach.error}</p>
      <div className="grid items-start gap-6 md:grid-cols-[minmax(10rem,13rem)_minmax(0,1fr)] min-[1550px]:grid-cols-[13rem_minmax(0,1fr)_17rem]">
        <section aria-labelledby="coach-sessions" className="min-w-0 space-y-4">
          <form className="space-y-3" onSubmit={event => {
            event.preventDefault();
            if (!busy && stage) enterConversation((event.nativeEvent as SubmitEvent).submitter,
              () => void coach.start({ mode: 'foundation', candidate_stage: stage }));
          }}>
            <h2 ref={sessionsHeading} id="coach-sessions" tabIndex={-1}
              className="text-base font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring">Sessions</h2>
            <StageSelect value={stage} onChange={setStage} disabled={busy} label="Career stage" />
            <Button type="submit" className="w-full" disabled={busy || !stage}><Plus aria-hidden="true" />Start session</Button>
          </form>
          <ul className="divide-y divide-border">
            {[...coach.sessions].sort((a, b) => b.updated_at.localeCompare(a.updated_at)).map(row => (
              <li key={row.session_id}>
                <button type="button" aria-pressed={row.session_id === session?.session_id} disabled={busy}
                  className="w-full rounded-md p-3 text-left text-sm hover:bg-muted aria-pressed:bg-muted focus-visible:outline-2 focus-visible:outline-ring disabled:opacity-60"
                  onClick={event => {
                    setExistingStage('');
                    enterConversation(event.currentTarget, () => void coach.open(row.session_id));
                  }}>
                  <span className="block font-medium">{modes[row.mode]}</span>
                  <span className="block text-xs capitalize text-muted-foreground">
                    <time dateTime={row.updated_at}>{new Date(row.updated_at).toLocaleDateString()}</time> · {row.status}
                  </span>
                </button>
              </li>
            ))}
          </ul>
          <Pager count={coach.sessions.length} offset={coach.sessionOffset} size={coach.pageSize} busy={busy}
            label="sessions" go={offset => void coach.page('sessions', offset)} />
          {coach.sessionsUnavailable ? (
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Saved sessions are unavailable.</p>
              <Button size="sm" variant="outline" disabled={busy} onClick={event => {
                sessionsRetryTrigger.current = event.currentTarget;
                void coach.page('sessions', 0);
              }}>
                Retry loading sessions
              </Button>
            </div>
          ) : !loading && !coach.sessions.length && !coach.sessionOffset && (
            <p className="text-sm text-muted-foreground">No saved sessions yet.</p>
          )}
        </section>
        <section aria-labelledby="coach-conversation" className="min-w-0 overflow-hidden rounded-xl border border-border bg-card">
          <header className="flex flex-wrap items-start justify-between gap-2 border-b border-border px-4 py-3 sm:px-5">
            <div>
              <h2 ref={conversationHeading} id="coach-conversation" tabIndex={-1}
                className="font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring">{title}</h2>
              {session && <p className="mt-1 text-sm capitalize text-muted-foreground">{session.chapter.replaceAll('_', ' ')} · {session.status}</p>}
            </div>
            {session && <Button ref={refreshButton} size="sm" variant="outline" disabled={busy}
              onClick={event => enterConversation(event.currentTarget, () => void coach.open(session.session_id))}>
              Refresh conversation
            </Button>}
          </header>
          {!session ? (
            <div className="space-y-2 p-5 text-sm text-muted-foreground">
              <MessageSquare aria-hidden="true" className="size-5" />
              <p>Start a session or open one you’ve already saved.</p>
            </div>
          ) : (
            <>
              <ol ref={transcript} aria-label="Conversation transcript" tabIndex={0}
                className="max-h-[28rem] space-y-4 overflow-y-auto p-4 focus-visible:outline-2 focus-visible:outline-inset focus-visible:outline-ring sm:p-5">
                {!coach.messages.length && (
                  <li className="text-sm text-muted-foreground">Tell the coach about a project or a piece of work you’d like to explore.</li>
                )}
                {coach.messages.map(message => (
                  <li key={message.position} className={message.role === 'user' ? 'ml-auto max-w-[90%]' : 'max-w-[65ch]'}>
                    <p className="mb-1 text-xs font-medium text-muted-foreground">{message.role === 'user' ? 'You' : 'Coach'}</p>
                    <p className="whitespace-pre-wrap rounded-lg bg-muted px-3 py-2 text-sm leading-relaxed [overflow-wrap:anywhere]">{message.content}</p>
                  </li>
                ))}
              </ol>
              <div className="space-y-3 border-t border-border p-4 sm:p-5">
                {session.status === 'active' && session.chapter === 'introduction' && !session.candidate_stage
                  && recovery?.request.candidate_stage === undefined && (
                    <StageSelect value={existingStage} onChange={setExistingStage} disabled={busy}
                      label={recovery ? 'Career stage used for this reply (if any)' : 'Confirm your career stage'} />
                  )}
                {stopWaiting ? (
                  <Button ref={stopButton} type="button" variant="outline" onClick={stopWaiting}>Stop waiting</Button>
                ) : recovery && !needsConversationRefresh ? (
                  <>
                    <Button ref={retryButton} variant="outline" disabled={busy}
                      aria-describedby={mayResend ? 'coach-recovery-explanation' : undefined} onClick={() => {
                        restoreTurnFocus.current = 'turn';
                        void coach.retry(existingStage || undefined);
                      }}>
                      {recovery.request.retry ? 'Retry reply' : mayResend ? 'Check or send reply' : 'Check turn status'}
                    </Button>
                    {mayResend && <p id="coach-recovery-explanation" className="text-sm text-muted-foreground">
                      This sends your original reply if the server has yet to receive it.
                    </p>}
                  </>
                ) : session.status === 'paused' && !needsConversationRefresh ? (
                  <Button disabled={busy}
                    onClick={event => enterConversation(event.currentTarget, () => void coach.open(session.session_id, true))}>
                    Resume conversation
                  </Button>
                ) : null}
                {session.status === 'active' && (
                  <div hidden={Boolean(recovery) || needsConversationRefresh}>
                    <Composer key={`${session.session_id}:${coach.acceptedKey}`}
                      inputRef={replyInput}
                      busy={busy || (session.chapter === 'introduction' && !session.candidate_stage && !existingStage)}
                      send={text => {
                        restoreTurnFocus.current = 'turn';
                        void coach.send(text, session.chapter === 'introduction' && !session.candidate_stage
                          ? existingStage || undefined : undefined);
                      }} />
                  </div>
                )}
              </div>
            </>
          )}
        </section>
        <div className="space-y-3 md:col-start-2 min-[1550px]:col-start-3">
          <EvidenceReview items={coach.evidence} busy={busy} loading={loading} unavailable={coach.evidenceUnavailable} decide={coach.decide}
            refresh={() => void coach.page('evidence', coach.evidenceOffset)} />
          <Pager count={coach.evidence.length} offset={coach.evidenceOffset} size={coach.pageSize} busy={busy}
            label="evidence" go={offset => void coach.page('evidence', offset)} />
        </div>
      </div>
    </div>
  );
}

function StageSelect({ value, onChange, disabled, label }: {
  value: SelectedStage; onChange: (stage: SelectedStage) => void; disabled: boolean; label: string;
}) {
  const id = useId();
  return (
    <div>
      <label htmlFor={id} className="block text-sm text-muted-foreground">{label}</label>
      <select id={id} value={value} disabled={disabled} onChange={event => onChange(event.target.value as SelectedStage)}
        className="mt-1 block min-h-10 w-full rounded-md border border-input bg-background px-2 text-sm text-foreground">
        <option value="">Choose a stage</option>
        {Object.entries(stages).map(([key, name]) => <option key={key} value={key}>{name}</option>)}
      </select>
    </div>
  );
}

function Composer({ busy, inputRef, send }: { busy: boolean; inputRef: Ref<HTMLTextAreaElement>; send: (body: string) => void }) {
  const [draft, setDraft] = useState('');
  return (
    <form className="space-y-2" onSubmit={event => {
      event.preventDefault();
      if (!busy && draft.trim()) send(draft);
    }}>
      <label className="block text-sm font-medium">
        Your reply
        <Textarea ref={inputRef} className="mt-1" rows={3} maxLength={4000} value={draft} disabled={busy}
          onChange={event => setDraft(event.target.value)} />
      </label>
      <div className="flex justify-end">
        <Button type="submit" disabled={busy || !draft.trim()}><ArrowUp aria-hidden="true" />Send</Button>
      </div>
    </form>
  );
}

function Pager({ count, size, offset, busy, label, go }: {
  count: number; size: number; offset: number; busy: boolean; label: string; go: (offset: number) => void;
}) {
  if (!offset && count < size) return null;
  return (
    <div className="flex flex-wrap gap-2">
      <Button size="sm" variant="outline" disabled={busy || !offset} onClick={() => go(offset - size)}>Previous {label}</Button>
      <Button size="sm" variant="outline" disabled={busy || count < size} onClick={() => go(offset + size)}>Next {label}</Button>
    </div>
  );
}
