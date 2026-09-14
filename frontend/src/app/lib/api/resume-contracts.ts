import type { components, paths } from '@/generated/api/types';

type Schemas = components['schemas'];
type Upload = paths['/api/v1/resumes/upload']['post'];
type Evaluate = paths['/api/v1/resumes/{resume_document_id}/evaluate']['post'];
type Rewrite = paths['/api/v1/resumes/{resume_document_id}/rewrite/{bullet_id}']['post'];
type Version = paths['/api/v1/resumes/{resume_document_id}/versions']['post'];
type Document = paths['/api/v1/resumes/{resume_document_id}'];

export type ResumeUploadResponse = Upload['responses'][201]['content']['application/json'];
export type EvaluationResponse = Evaluate['responses'][200]['content']['application/json'];
export type EvaluationRequest = Evaluate['requestBody']['content']['application/json'];
export type RewriteRequest = Rewrite['requestBody']['content']['application/json'];
export type RewriteResult = Rewrite['responses'][200]['content']['application/json'];
type VersionTransportRequest = Version['requestBody']['content']['application/json'];
export type VersionResponse = Version['responses'][201]['content']['application/json'];
export type ResumeDetailResponse = Document['get']['responses'][200]['content']['application/json'];
export type ResumeListResponse = paths['/api/v1/resumes/list']['get']['responses'][200]['content']['application/json'];
export type ResumeDeleteResponse = Document['delete']['responses'][204]['content'];
export type Bullet = Schemas['Bullet'];
export type BulletFlag = Schemas['BulletFlag'];
export type BulletCategory = BulletFlag['category'];
export type Severity = BulletFlag['severity'];
export type FormatIssue = Schemas['FormatIssue'];
export type Placeholder = Schemas['Placeholder'];

// The wire schema permits incomplete changes that the backend silently ignores.
// UI commands require each action's non-null fields and forbid other actions' fields.
type ChangeTransport = Schemas['ChangeItem'];
type ChangeCommand<Kind extends ChangeTransport['type'], Fields extends Exclude<keyof ChangeTransport, 'type'>> =
  { type: Kind }
  & { [Key in Fields]-?: NonNullable<ChangeTransport[Key]> }
  & { [Key in Exclude<keyof ChangeTransport, Fields | 'type'>]?: never };
export type ChangeItem =
  | ChangeCommand<'bullet_update', 'bullet_id' | 'new_text'>
  | ChangeCommand<'skills_reorder', 'new_skills_order'>
  | ChangeCommand<'summary_update', 'new_summary'>;
export type VersionRequest = Omit<VersionTransportRequest, 'change_set'> & { change_set: ChangeItem[] };

// The editor expects present collections/nulls. Only the parser applies these
// declared defaults; required facts and IDs must never receive fallback values.
type Present<T> = T extends (infer Item)[] ? Present<Item>[]
  : T extends object ? { [Key in keyof T]-?: Present<T[Key]> } : T;
export type ResumeDocumentJSON = Present<Omit<ResumeUploadResponse, 'resume_document_id'>>;
export type UploadResponse = ResumeDocumentJSON & Pick<ResumeUploadResponse, 'resume_document_id'>;
export type Contact = ResumeDocumentJSON['contact'];
export type ExperienceEntry = ResumeDocumentJSON['experience'][number];
export type EducationEntry = ResumeDocumentJSON['education'][number];
export type Skills = ResumeDocumentJSON['skills'];
export type ProjectEntry = ResumeDocumentJSON['projects'][number];
