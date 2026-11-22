import { EvidenceNotebook } from '@/features/evidence/evidence-notebook';

export default async function EvidenceNotebookPage({ searchParams }: {
  searchParams: Promise<{ evidence?: string | string[]; revision?: string | string[] }>;
}) {
  const { evidence, revision } = await searchParams;
  const selected = typeof evidence === 'string' && /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/.test(evidence) ? evidence : undefined;
  const number = typeof revision === 'string' && /^[1-9][0-9]*$/.test(revision) ? Number(revision) : 0;
  const citedRevision = selected && Number.isSafeInteger(number) && number > 0 ? number : undefined;
  return <EvidenceNotebook key={`${selected ?? ''}|${citedRevision ?? ''}`} initialEvidence={selected} citedRevision={citedRevision} />;
}
