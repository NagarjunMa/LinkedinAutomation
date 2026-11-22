import { makeAPIRequest } from '@/app/lib/api/config';
import type { components } from '@/generated/api/types';

type Schemas = components['schemas'];
export type Source = Schemas['SourceRef'];
export type Upload = Schemas['LinkedInUpload'];
export type UploadSummary = Schemas['LinkedInUploadSummary'];
export type Target = Schemas['CareerTarget'];
export type TargetInput = Schemas['CareerTargetInput'];
export type Review = Schemas['LinkedInReviewPreview'];
export type Recommendation = Schemas['LinkedInRecommendation'];
export type EvidenceRevision = Schemas['EvidenceRevisionRef'];

export const pageSize = 50;
export const sourceKey = (source: Source) => `${source.source_id}:${source.source_version}`;
export type ReviewOwner = { owner: string; isCurrentUser: (id: string) => boolean };

const profiles = '/api/v1/career/linkedin-profiles';
const targets = '/api/v1/career/targets';
const historyPath = (id: string) => `${profiles}/${encodeURIComponent(id)}`;
const versionPath = (source: Source) => `${historyPath(source.source_id)}/versions/${source.source_version}`;

export function linkedInApi({ owner, isCurrentUser }: ReviewOwner, signal?: AbortSignal) {
  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const result = await makeAPIRequest<T>(path, { ...init, expectedUserId: owner, signal, cache: 'no-store' });
    signal?.throwIfAborted();
    if (!isCurrentUser(owner)) throw new Error('Sign-in changed');
    return result;
  }

  const page = (offset: number) => `?limit=${pageSize}&offset=${offset}`;
  function post<T>(path: string, body: object) {
    return request<T>(path, { method: 'POST', body: JSON.stringify(body) });
  }

  function ownedTarget(target: Target) {
    if (target.owner_id !== owner || target.status !== 'active') throw new Error('Target is unavailable');
    return target;
  }

  return {
    uploads: (offset: number) => request<UploadSummary[]>(profiles + page(offset)),
    targets: async (offset: number) => (await request<Target[]>(targets + page(offset))).map(ownedTarget),
    createTarget: async (target: TargetInput) => ownedTarget(await post<Target>(targets, target)),
    async upload(file: File, previous?: Source) {
      const body = new FormData();
      body.append('file', file);
      const row = await request<Upload>(previous ? versionPath(previous) : profiles, { method: 'POST', body });
      if (row.state !== 'ready' || (previous
        ? sourceKey(row.source) !== sourceKey({ ...previous, source_version: previous.source_version + 1 })
        : row.source.source_version !== 1)) throw new Error('Upload result is unavailable');
      return { source: row.source, pdf_sha256: row.pdf_sha256, created_at: row.created_at, state: row.state };
    },
    async document(source: Source) {
      const result = await request<Upload>(versionPath(source));
      if (result.state !== 'ready' || sourceKey(result.source) !== sourceKey(source)
        || sourceKey(result.document.source) !== sourceKey(source)) throw new Error('PDF version is unavailable');
      return result.document;
    },
    deleteHistory: (id: string) => request<void>(historyPath(id), { method: 'DELETE' }),
    async review(source: Source, target_id: string) {
      const path = versionPath(source);
      const [review, recommendations] = await Promise.all([
        post<Review>(path + '/review', { target_id }),
        post<Recommendation[]>(path + '/recommendations', { target_id }),
      ]);
      if (review.target_id !== target_id || sourceKey(review.document) !== sourceKey(source)) {
        throw new Error('Review selection has changed');
      }
      return { review, recommendations };
    },
    async copy(source: Source, target_id: string, { section, evidence_revisions }: Recommendation) {
      const copy = await post<Recommendation>(versionPath(source) + '/recommendations/copy', {
        target_id, selection: { section, evidence_revisions },
      } satisfies Schemas['LinkedInCopyRequest']);
      if (copy.section !== section || copy.evidence_revisions.length !== evidence_revisions.length
        || evidence_revisions.some(({ evidence_id, revision }, index) => (
          copy.evidence_revisions[index].evidence_id !== evidence_id || copy.evidence_revisions[index].revision !== revision
        )) || typeof copy.text !== 'string' || !copy.text.trim()) throw new Error('Copy text is unavailable');
      return copy.text;
    },
  };
}
