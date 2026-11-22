'use client';

import { useLayoutEffect, useRef, useState, type FormEvent } from 'react';
import { useInfiniteQuery, useQueryClient, type InfiniteData } from '@tanstack/react-query';
import { APIError } from '@/app/lib/api/config';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription,
  AlertDialogFooter, AlertDialogTitle, AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useAuth } from '@/contexts/auth-context';
import { linkedInApi, pageSize, sourceKey, type ReviewOwner, type Source, type Target, type UploadSummary } from './api';
import { PdfVersion } from './pdf-version';
import { ReviewResults } from './review-results';

const stateLabels = { ready: 'Available', pending: 'Upload incomplete', deleting: 'Deletion pending', canceling: 'Cleanup pending' };
const selectStyle = 'mt-1 block h-9 w-full rounded-md border border-input bg-background px-2';
const historyLabel = (id: string) => `PDF history ${id.slice(0, 8)}`;
const uploadDate = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'medium' });

function nextPage(length: number, offset: number) {
  return length >= pageSize && offset < 1_000_000 ? offset + pageSize : undefined;
}

function uploadError(error: unknown) {
  const status = error instanceof APIError ? error.status : undefined;
  if (status === 413) return 'The PDF is too large. Choose a smaller export.';
  if (status === 415 || status === 422 || status === 400) return 'The file could not be read as a LinkedIn profile PDF.';
  if (status === 404 || status === 409) return 'The PDF history changed. Select its latest available version and try again.';
  return 'The upload could not be verified. Check the saved PDF list before trying again.';
}

export function LinkedInReview() {
  const { user, isCurrentUser } = useAuth();
  return user && isCurrentUser(user.id)
    ? <ReviewDashboard key={user.id} owner={user.id} isCurrentUser={isCurrentUser} /> : null;
}

function ReviewDashboard(session: ReviewOwner) {
  const client = useQueryClient();
  const uploadsKey = ['linkedin-pdfs', session.owner];
  const targetsKey = ['linkedin-targets', session.owner];
  const [version, setVersion] = useState('');
  const [target, setTarget] = useState('');
  const [newTarget, setNewTarget] = useState<Target>();
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const fileInput = useRef<HTMLInputElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const operation = useRef<AbortController | null>(null);
  useLayoutEffect(() => () => {
    const pending = operation.current;
    operation.current = null;
    pending?.abort();
  }, []);

  const uploads = useInfiniteQuery({
    queryKey: uploadsKey,
    queryFn: ({ pageParam, signal }) => linkedInApi(session, signal).uploads(pageParam),
    initialPageParam: 0,
    getNextPageParam: (page: UploadSummary[], _, offset) => nextPage(page.length, offset),
    retry: false, gcTime: 0,
  });
  const targets = useInfiniteQuery({
    queryKey: targetsKey,
    queryFn: ({ pageParam, signal }) => linkedInApi(session, signal).targets(pageParam),
    initialPageParam: 0,
    getNextPageParam: (page: Target[], _, offset) => nextPage(page.length, offset),
    retry: false, gcTime: 0,
  });
  const versions = [...new Map(uploads.data?.pages.flat().map(row => [sourceKey(row.source), row])).values()];
  const targetsById = new Map(targets.data?.pages.flat().map(row => [row.target_id, row]));
  // Targets are paginated by ID, so a newly created target may be outside the loaded pages.
  if (newTarget && !targetsById.has(newTarget.target_id)) targetsById.set(newTarget.target_id, newTarget);
  const activeTargets = [...targetsById.values()];
  const selected = versions.find(row => sourceKey(row.source) === version);
  const selectedTarget = activeTargets.find(row => row.target_id === target);
  const ready = selected?.state === 'ready';
  const canAppend = ready && !versions.some(row => (
    row.source.source_id === selected.source.source_id && row.source.source_version > selected.source.source_version
  ));

  async function mutate<T>(
    message: string, key: string[], action: (signal: AbortSignal) => Promise<T>,
    success: (result: T) => void, failure: (error: unknown) => string,
  ) {
    if (operation.current || !session.isCurrentUser(session.owner)) return;
    const controller = new AbortController();
    operation.current = controller;
    const deadline = setTimeout(() => controller.abort(), 60_000);
    setBusy(message);
    setError('');
    setNotice('');
    const current = () => operation.current === controller && session.isCurrentUser(session.owner);
    try {
      const result = await action(controller.signal);
      if (!current()) return;
      await client.cancelQueries({ queryKey: key, exact: true });
      if (current()) success(result);
    } catch (error) {
      if (!current()) return;
      setError(failure(error));
    } finally {
      clearTimeout(deadline);
      if (current()) {
        setBusy('');
        void client.invalidateQueries({ queryKey: key, exact: true });
      }
      if (operation.current === controller) operation.current = null;
    }
  }

  function upload(previous?: Source) {
    const file = fileInput.current?.files?.[0];
    if (!file || !/\.pdf$/i.test(file.name) || !file.size) {
      setNotice('');
      setError('Choose a nonempty PDF file.');
      fileInput.current?.focus();
      return;
    }
    if (fileInput.current) fileInput.current.value = '';
    void mutate('Uploading and parsing PDF…', uploadsKey, signal => linkedInApi(session, signal).upload(file, previous), upload => {
      client.setQueryData<InfiniteData<UploadSummary[], number>>(uploadsKey, data => {
        const [first = [], ...rest] = data?.pages ?? [];
        return { pageParams: data?.pageParams ?? [0], pages: [[upload, ...first], ...rest] };
      });
      setVersion(sourceKey(upload.source));
      setNotice('PDF version saved.');
    }, uploadError);
  }

  function createTarget(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    const role_family = String(fields.get('role')).trim();
    const seniority = String(fields.get('seniority')).trim();
    const desired_work = String(fields.get('priorities')).split(/\r?\n/).map(line => line.trim()).filter(Boolean);
    if (!role_family || !seniority || desired_work.length > 20 || desired_work.some(line => line.length > 200)) {
      setNotice('');
      setError('Enter a role and seniority, with up to 20 priorities of 200 characters each.');
      return;
    }
    void mutate('Creating target…', targetsKey,
      signal => linkedInApi(session, signal).createTarget({ role_family, seniority, desired_work }),
      result => {
        form.reset();
        setNewTarget(result);
        setTarget(result.target_id);
        setNotice('Target created.');
      },
      () => 'The target could not be verified. Check the target list before trying again.');
  }

  function deleteHistory(id: string) {
    void mutate('Deleting PDF history…', uploadsKey, signal => linkedInApi(session, signal).deleteHistory(id), () => {
      client.setQueryData<InfiniteData<UploadSummary[], number>>(uploadsKey, data => data && ({
        ...data, pages: data.pages.map(page => page.filter(row => row.source.source_id !== id)),
      }));
      setVersion('');
      setNotice('PDF history deleted.');
      heading.current?.focus();
    }, () => 'The PDF history could not be deleted. You can retry deletion from the saved PDF list.');
  }

  return (
    <div className="mx-auto min-w-0 max-w-6xl space-y-6 px-4 py-6 sm:px-6">
      <header className="space-y-2">
        <h1 ref={heading} tabIndex={-1} className="text-2xl font-semibold tracking-tight">LinkedIn Review</h1>
        <p className="text-sm text-muted-foreground">
          Compare a LinkedIn profile PDF with your confirmed evidence and a target role. The review covers this export only.
          Activity, endorsements, and other live profile details may be missing. You can copy suggestions to use yourself.
        </p>
      </header>
      <div className="grid min-w-0 items-start gap-4 lg:grid-cols-2">
        <section aria-labelledby="linkedin-pdfs" className="min-w-0 space-y-4 rounded-lg border bg-card p-4">
          <h2 id="linkedin-pdfs" className="font-semibold">Profile PDFs</h2>
          {uploads.isPending && <p role="status" className="text-sm">Loading saved PDFs…</p>}
          {uploads.isError && <p role="alert" className="text-sm text-destructive">Saved PDFs could not be loaded.</p>}
          {uploads.isSuccess && !versions.length && <p className="text-sm text-muted-foreground">No LinkedIn PDFs uploaded yet.</p>}
          <label className="block min-w-0 text-sm font-medium">
            Saved PDF version
            <select className={selectStyle} value={selected ? version : ''} disabled={!!busy || !versions.length}
              onChange={event => {
                setVersion(event.target.value);
                if (fileInput.current) fileInput.current.value = '';
              }}>
              <option value="">Choose a version</option>
              {versions.map(row => (
                <option key={sourceKey(row.source)} value={sourceKey(row.source)}>
                  {historyLabel(row.source.source_id)} · Version {row.source.source_version} · {uploadDate.format(new Date(row.created_at))} · {stateLabels[row.state]}
                </option>
              ))}
            </select>
          </label>
          <div className="flex flex-wrap gap-2">
            <Button variant="ghost" size="sm" disabled={!!busy || uploads.isFetching} onClick={() => void uploads.refetch()}>Refresh PDFs</Button>
            {uploads.hasNextPage && <Button variant="outline" size="sm" disabled={!!busy || uploads.isFetching}
              onClick={() => void uploads.fetchNextPage()}>Load more PDF versions</Button>}
          </div>
          {selected && <>
            {!ready && <p className="text-sm">{stateLabels[selected.state]}. Refresh the list or delete this PDF history.</p>}
            {ready && <PdfVersion key={version} session={session} source={selected.source} />}
            <AlertDialog>
              <AlertDialogTrigger asChild><Button variant="outline" size="sm" disabled={!!busy}>Delete PDF history</Button></AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogTitle>Delete {historyLabel(selected.source.source_id)}?</AlertDialogTitle>
                <AlertDialogDescription>
                  You selected version {selected.source.source_version}, saved {uploadDate.format(new Date(selected.created_at))}.
                  This removes every saved version in this history. Evidence and reviews that depend on these PDFs may become unavailable.
                </AlertDialogDescription>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={() => deleteHistory(selected.source.source_id)}>Delete all versions</AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </>}
          <form className="space-y-2" onSubmit={event => { event.preventDefault(); upload(); }}>
            <label className="block text-sm font-medium">PDF file
              <Input ref={fileInput} className="mt-1" type="file" accept=".pdf,application/pdf" disabled={!!busy} required />
            </label>
            <div className="flex flex-wrap gap-2">
              <Button type="submit" variant={canAppend ? 'outline' : 'default'} size="sm" disabled={!!busy}>Upload as new PDF</Button>
              {canAppend && <Button type="button" size="sm" disabled={!!busy} onClick={() => upload(selected.source)}>Upload new version</Button>}
            </div>
            {canAppend && <p className="text-xs text-muted-foreground">Uploading a new version keeps the selected PDF in this history.</p>}
          </form>
        </section>
        <section aria-labelledby="linkedin-target" className="min-w-0 space-y-4 rounded-lg border bg-card p-4">
          <h2 id="linkedin-target" className="font-semibold">Target role</h2>
          {targets.isPending && <p role="status" className="text-sm">Loading targets…</p>}
          {targets.isError && <p role="alert" className="text-sm text-destructive">Targets could not be loaded.</p>}
          <label className="block min-w-0 text-sm font-medium">
            Saved target
            <select className={selectStyle} value={selectedTarget ? target : ''} disabled={!!busy || !activeTargets.length}
              onChange={event => setTarget(event.target.value)}>
              <option value="">Choose a target</option>
              {activeTargets.map(item => <option key={item.target_id} value={item.target_id}>{item.role_family} · {item.seniority}</option>)}
            </select>
          </label>
          {(targets.isError || targets.hasNextPage) && <div className="flex flex-wrap gap-2">
            {targets.isError && <Button variant="ghost" size="sm" disabled={!!busy || targets.isFetching}
              onClick={() => void targets.refetch()}>Retry targets</Button>}
            {targets.hasNextPage && <Button variant="outline" size="sm" disabled={!!busy || targets.isFetching}
              onClick={() => void targets.fetchNextPage()}>Load more targets</Button>}
          </div>}
          <form onSubmit={createTarget} className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block text-sm font-medium">Target role<Input className="mt-1" name="role" required maxLength={200} disabled={!!busy} /></label>
              <label className="block text-sm font-medium">Seniority<Input className="mt-1" name="seniority" required maxLength={200} disabled={!!busy} /></label>
            </div>
            <label className="block text-sm font-medium">Target priorities
              <Textarea className="mt-1" name="priorities" placeholder="Optional, one per line" maxLength={4020} disabled={!!busy} />
            </label>
            <Button type="submit" variant="outline" size="sm" disabled={!!busy}>Create target</Button>
          </form>
        </section>
      </div>
      <p role="status" className="text-sm text-muted-foreground empty:sr-only">{busy || notice}</p>
      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
      {!busy && (ready && selectedTarget
        ? <ReviewResults key={JSON.stringify([version, target])} session={session} source={selected.source} target={target} />
        : <p className="text-sm text-muted-foreground">Choose an available PDF version and a target to run a review.</p>)}
    </div>
  );
}
