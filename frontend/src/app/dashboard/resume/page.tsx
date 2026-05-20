// frontend/src/app/dashboard/resume/page.tsx
"use client";
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ResumeUploadDropzone } from '@/components/resume/resume-upload-dropzone';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { UploadResponse } from '@/app/lib/api';

interface RecentItem {
  id: string;
  name: string;
  uploaded_at: string;
}

const LS_KEY = 'prism.recentResumes';

function loadRecent(): RecentItem[] {
  if (typeof window === 'undefined') return [];
  try {
    return JSON.parse(localStorage.getItem(LS_KEY) || '[]');
  } catch {
    return [];
  }
}

function pushRecent(item: RecentItem) {
  const next = [item, ...loadRecent().filter((r) => r.id !== item.id)].slice(0, 10);
  localStorage.setItem(LS_KEY, JSON.stringify(next));
}

export default function ResumeLibraryPage() {
  const router = useRouter();
  const [recent, setRecent] = useState<RecentItem[]>([]);

  useEffect(() => { setRecent(loadRecent()); }, []);

  const onUploaded = (res: UploadResponse) => {
    const item: RecentItem = {
      id: res.resume_document_id,
      name: res.contact.name || 'Resume',
      uploaded_at: new Date().toISOString(),
    };
    pushRecent(item);
    sessionStorage.setItem(`resumeDoc:${res.resume_document_id}`, JSON.stringify(res));
    router.push(`/dashboard/resume/${res.resume_document_id}/edit`);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <header>
        <h1 className="text-2xl font-bold">Resume</h1>
        <p className="text-sm opacity-70">Upload a PDF or DOCX to get recruiter-grade feedback.</p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Upload</CardTitle>
        </CardHeader>
        <CardContent>
          <ResumeUploadDropzone onUploaded={onUploaded} />
        </CardContent>
      </Card>

      {recent.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {recent.map((r) => (
                <li key={r.id}>
                  <Link
                    href={`/dashboard/resume/${r.id}/edit`}
                    className="text-sm hover:underline"
                  >
                    {r.name} — {new Date(r.uploaded_at).toLocaleString()}
                  </Link>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
