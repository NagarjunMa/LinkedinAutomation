// frontend/src/components/jd/jd-input-form.tsx
"use client";
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { ResumeUploadDropzone } from '@/components/resume/resume-upload-dropzone';
import type { UploadResponse } from '@/app/lib/api';

export interface JdInputFormProps {
  onSubmit: (args: { resumeDocumentId: string; jdText: string }) => void;
  pending: boolean;
}

export function JdInputForm({ onSubmit, pending }: JdInputFormProps) {
  const [uploaded, setUploaded] = useState<UploadResponse | null>(null);
  const [jdText, setJdText] = useState('');
  const tooShort = jdText.trim().length < 50;

  return (
    <div className="space-y-4">
      {!uploaded ? (
        <ResumeUploadDropzone onUploaded={setUploaded} />
      ) : (
        <div className="text-sm">
          Using resume for <strong>{uploaded.contact.name || 'uploaded resume'}</strong>{' '}
          <button
            onClick={() => setUploaded(null)}
            className="underline text-xs opacity-70 ml-2"
          >
            change
          </button>
        </div>
      )}

      <div>
        <Label htmlFor="jd">Job description</Label>
        <Textarea
          id="jd"
          rows={10}
          placeholder="Paste the full job description here (min 50 chars)…"
          value={jdText}
          onChange={(e) => setJdText(e.target.value)}
        />
        {tooShort && jdText.length > 0 && (
          <p className="text-xs text-amber-500 mt-1">At least 50 characters required.</p>
        )}
      </div>

      <Button
        disabled={!uploaded || tooShort || pending}
        onClick={() => uploaded && onSubmit({ resumeDocumentId: uploaded.resume_document_id, jdText })}
      >
        {pending ? 'Analyzing…' : 'Analyze (2 credits)'}
      </Button>
    </div>
  );
}
