import type { Evidence } from '@/features/career-coach/api';

export const statuses = {
  proposed: 'Proposed', confirmed: 'Confirmed', rejected: 'Rejected',
  contradicted: 'Contradicted', private: 'Private', unavailable: 'Unavailable',
} satisfies Record<Evidence['lifecycle'], string>;

export const supportLevels = {
  candidate_statement: 'Candidate statement', document_backed: 'Document-backed',
  artifact_linked: 'Linked artifact', independently_verified: 'Independently verified',
} satisfies Record<Evidence['support'], string>;

export function evidenceStatus(item: Evidence) {
  return statuses[item.lifecycle] + (item.is_private && item.lifecycle !== 'private' ? ' · Private' : '');
}

export type EvidenceOwner = { owner: string; isCurrentUser: (id: string) => boolean };

export function checkEvidenceOwner(
  { owner, isCurrentUser }: EvidenceOwner, items: Evidence[], evidenceId?: string,
) {
  if (!isCurrentUser(owner) || items.some(item =>
    item.owner_id !== owner || (evidenceId !== undefined && item.evidence_id !== evidenceId)
  )) throw new Error('Evidence is unavailable');
}
