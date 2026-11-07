// frontend/src/components/resume/resume-upload-dropzone.tsx
"use client";
import { useCallback, useLayoutEffect, useRef, useState } from 'react';
import { Upload, FileText, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useUploadResume } from '@/hooks/use-resume';
import type { UploadResponse } from '@/app/lib/api';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/auth-context';

const MAX_BYTES = 10 * 1024 * 1024; // 10 MB
const ALLOWED = ['.pdf', '.docx'];

export interface ResumeUploadDropzoneProps {
  onUploaded: (res: UploadResponse) => void;
}

export function ResumeUploadDropzone({ onUploaded }: ResumeUploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const mounted = useRef(false);
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const upload = useUploadResume();
  const { toast } = useToast();
  const { user, isCurrentUser } = useAuth();

  useLayoutEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  const validate = (f: File): string | null => {
    const ext = '.' + f.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED.includes(ext)) return 'Only PDF and DOCX files are supported';
    if (f.size > MAX_BYTES) return 'File too large (max 10 MB)';
    return null;
  };

  const onPick = useCallback((f: File) => {
    const err = validate(f);
    if (err) {
      toast({ title: 'Invalid file', description: err, variant: 'destructive' });
      return;
    }
    setFile(f);
  }, [toast]);

  const onSubmit = async () => {
    if (!file || !user?.id || !isCurrentUser(user.id)) return;
    try {
      const res = await upload.mutateAsync({ file, userId: user.id });
      if (!mounted.current || !isCurrentUser(user.id)) return;
      toast({
        title: 'Uploaded',
        description: 'Résumé parsed successfully.',
      });
      onUploaded(res);
    } catch (e: any) {
      if (!mounted.current || !isCurrentUser(user.id)) return;
      toast({
        title: 'Upload failed',
        description: e?.message ?? 'Try again',
        variant: 'destructive',
      });
    }
  };

  return (
    <div
      data-testid="resume-dropzone"
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        const f = e.dataTransfer.files[0];
        if (f) onPick(f);
      }}
      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
        dragging ? 'border-app-accent bg-app-accent/5' : 'border-app-text/20'
      }`}
    >
      {!file ? (
        <>
          <Upload className="mx-auto mb-3 w-8 h-8 opacity-50" />
          <p className="text-sm mb-3">Drag PDF or DOCX here, or</p>
          <Button variant="outline" onClick={() => inputRef.current?.click()}>
            Choose file
          </Button>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && onPick(e.target.files[0])}
          />
        </>
      ) : (
        <div className="flex items-center justify-center gap-3">
          <FileText className="w-5 h-5" />
          <span className="text-sm">{file.name}</span>
          <button onClick={() => setFile(null)} aria-label="Remove file">
            <X className="w-4 h-4 opacity-60" />
          </button>
          <Button onClick={onSubmit} disabled={!user?.id || upload.isPending}>
            {upload.isPending ? 'Uploading…' : 'Upload'}
          </Button>
        </div>
      )}
    </div>
  );
}
