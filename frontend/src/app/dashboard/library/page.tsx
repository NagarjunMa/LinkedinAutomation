"use client";

import { TailoredResumeLibrary } from "@/components/tailored-resumes/library";

export default function LibraryPage() {
  return (
    <div className="min-h-screen bg-app-bg py-10 text-app-text">
      <TailoredResumeLibrary
        mode="page"
        title="Company Resume Library"
        description="Every accepted JD-tailored resume lives here with the company, role, source JD, accepted changes, and JSON-backed resume content for interview review."
      />
    </div>
  );
}
