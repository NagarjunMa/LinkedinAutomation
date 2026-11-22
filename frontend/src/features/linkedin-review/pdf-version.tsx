import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { linkedInApi, sourceKey, type ReviewOwner, type Source, type Upload } from './api';

const parseLabels = { parsed: 'Parsed', partial: 'Partially parsed', unreadable: 'No readable text found' };

function exportSections(document: Upload['document']) {
  const sections = new Map<string, string[]>();
  for (const { name, text } of document.sections) {
    if (name === 'identity' || name === 'contact' || name === 'unclassified') continue;
    const parts = sections.get(name);
    if (parts) parts.push(text);
    else sections.set(name, [text]);
  }
  return new Map([...sections].map(([name, parts]) => [name, parts.join('\n\n')]));
}

function Comparison({ current, previous }: { current: Upload['document']; previous: Upload['document'] }) {
  const before = exportSections(previous);
  const after = exportSections(current);
  const changes = [...new Set([...before.keys(), ...after.keys()])].filter(name => before.get(name) !== after.get(name));
  return (
    <section aria-label="PDF version comparison" className="space-y-3">
      <h3 className="font-medium">Version {previous.source.source_version} compared with version {current.source.source_version}</h3>
      {!changes.length && <p className="text-sm">No changes in the extracted professional sections.</p>}
      {changes.map(name => (
        <div key={name} className="space-y-2">
          <h4 className="text-sm font-medium capitalize">{name}</h4>
          <div className="grid gap-2 sm:grid-cols-2">
            {[previous, current].map((document, index) => (
              <div key={document.source.source_version} className="min-w-0 rounded-md border p-3">
                <p className="mb-1 text-xs font-medium">Version {document.source.source_version}</p>
                <p className="whitespace-pre-wrap text-sm [overflow-wrap:anywhere]">
                  {(index === 0 ? before : after).get(name) ?? 'Section not found in this export.'}
                </p>
              </div>
            ))}
          </div>
        </div>
      ))}
    </section>
  );
}

export function PdfVersion({ session, source }: { session: ReviewOwner; source: Source }) {
  const [compare, setCompare] = useState(false);
  const previous = { ...source, source_version: source.source_version - 1 };
  const document = useQuery({
    queryKey: ['linkedin-pdf-document', session.owner, sourceKey(source)],
    queryFn: ({ signal }) => linkedInApi(session, signal).document(source),
    retry: false, gcTime: 0,
  });
  const olderDocument = useQuery({
    queryKey: ['linkedin-pdf-document', session.owner, sourceKey(previous)],
    queryFn: ({ signal }) => linkedInApi(session, signal).document(previous),
    enabled: compare && previous.source_version > 0,
    retry: false, gcTime: 0,
  });
  if (document.isPending) return <p role="status" className="text-sm">Loading PDF version…</p>;
  if (document.isError) return (
    <div className="space-y-2">
      <p role="alert" className="text-sm text-destructive">The saved PDF version could not be loaded.</p>
      <Button variant="outline" size="sm" onClick={() => void document.refetch()}>Retry PDF version</Button>
    </div>
  );

  const preview = document.data.sections.find(section => section.name === 'about')
    ?? document.data.sections.find(section => section.name === 'headline');
  return (
    <div className="space-y-3">
      <p className="text-sm">Parsing status · {parseLabels[document.data.parse_status ?? 'parsed']}</p>
      {preview && <p className="line-clamp-3 text-sm [overflow-wrap:anywhere]">
        <span className="font-medium capitalize">{preview.name} excerpt · </span>{preview.text}
      </p>}
      {!!document.data.not_found_in_export?.length && (
        <p className="text-sm text-muted-foreground [overflow-wrap:anywhere]">
          Sections not found in this export · {document.data.not_found_in_export.join(', ')}
        </p>
      )}
      {previous.source_version > 0 && <>
        <Button variant="outline" size="sm" aria-expanded={compare} onClick={() => setCompare(value => !value)}>
          {compare ? 'Hide comparison' : `Compare with version ${previous.source_version}`}
        </Button>
        {compare && olderDocument.isPending && <p role="status" className="text-sm">Loading previous version…</p>}
        {compare && olderDocument.isError && (
          <div className="space-y-2">
            <p role="alert" className="text-sm text-destructive">The previous version could not be loaded.</p>
            <Button variant="outline" size="sm" onClick={() => void olderDocument.refetch()}>Retry comparison</Button>
          </div>
        )}
        {compare && olderDocument.isSuccess && <Comparison current={document.data} previous={olderDocument.data} />}
      </>}
    </div>
  );
}
