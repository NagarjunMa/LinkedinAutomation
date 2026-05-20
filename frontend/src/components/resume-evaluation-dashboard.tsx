"use client"

import React, { useState } from 'react'
import { Upload, ArrowRight, FileText, Calendar } from 'lucide-react'
import type { ResumeFile } from '@/app/lib/api/types'
import {
  Dialog,
  DialogContent,
} from "@/components/ui/dialog"
import { ResumeAnalysisPanel } from './resume-analysis-panel'
import { Button } from '@/components/ui/button'

interface ResumeEvaluationDashboardProps {
  onStartEvaluation: () => void
  onUploadResume: () => void
  resumes: ResumeFile[]
  onResumeUpdate: (resume: ResumeFile) => void
}

export function ResumeEvaluationDashboard({
  onStartEvaluation: _onStartEvaluation,
  onUploadResume,
  resumes,
  onResumeUpdate
}: ResumeEvaluationDashboardProps) {
  const [selectedResume, setSelectedResume] = useState<ResumeFile | null>(null)

  return (
    <div className="max-w-6xl mx-auto px-10 py-12 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
        <div>
          <h2 className="text-4xl font-black tracking-tighter text-foreground">
            The Hub.
          </h2>
          <p className="text-sm font-medium text-muted-foreground mt-2 max-w-md">
            Precision intelligence for high-stakes engineering applications. Analyze, refine, and optimize your professional artifact.
          </p>
        </div>
        <button
          onClick={onUploadResume}
          className="flex items-center gap-3 px-8 py-4 bg-primary text-primary-foreground rounded-2xl font-black text-xs uppercase tracking-widest shadow-xl hover:bg-primary/90 transition-all active:scale-95"
        >
          <Upload className="w-4 h-4" />
          Ingest Artifact
        </button>
      </div>

      {/* Resume List */}
      <div className="space-y-4 mb-16">
        <h3 className="text-sm font-black uppercase tracking-widest text-muted-foreground mb-4">
          Artifact Registry ({resumes.length})
        </h3>

        {resumes.length === 0 ? (
          <div className="p-12 text-center border-2 border-dashed border-border rounded-3xl bg-muted/10">
            <p className="text-muted-foreground font-medium">No artifacts ingested yet.</p>
            <Button variant="link" onClick={onUploadResume} className="mt-2 text-primary font-bold">
              Upload your first resume
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {resumes.map((resume) => (
              <div
                key={resume.id}
                className="group relative bg-card hover:bg-accent/5 border border-border rounded-2xl p-6 transition-all duration-300 hover:shadow-lg hover:border-primary/20"
              >
                <div className="flex items-center justify-between gap-6">
                  {/* File Info */}
                  <div className="flex items-center gap-4 flex-1">
                    <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                      <FileText className="w-6 h-6" />
                    </div>
                    <div>
                      <h4 className="font-bold text-lg tracking-tight text-foreground truncate max-w-[300px]">
                        {resume.filename}
                      </h4>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="flex items-center gap-1.5 text-[10px] font-bold text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                          <Calendar className="w-3 h-3" />
                          {new Date(resume.uploaded_at).toLocaleDateString()}
                        </span>
                        <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                          {Math.round(resume.file_size / 1024)} KB
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Status & Score */}
                  <div className="flex items-center gap-8">
                    <div className="flex flex-col items-end">
                      <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground mb-1">
                        Protocol Status
                      </span>
                      <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${resume.evaluation_status === 'completed'
                        ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-600'
                        : resume.evaluation_status === 'failed'
                          ? 'bg-red-500/10 border-red-500/20 text-red-600'
                          : 'bg-blue-500/10 border-blue-500/20 text-blue-600'
                        }`}>
                        <div className={`w-1.5 h-1.5 rounded-full ${resume.evaluation_status === 'completed' ? 'bg-emerald-500' :
                          resume.evaluation_status === 'failed' ? 'bg-red-500' : 'bg-blue-500 animate-pulse'
                          }`}></div>
                        <span className="text-[10px] font-black uppercase tracking-wide">
                          {resume.evaluation_status}
                        </span>
                      </div>
                    </div>

                    <div className="flex flex-col items-end min-w-[80px]">
                      <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground mb-1">
                        Score
                      </span>
                      <div className="text-2xl font-black font-mono tracking-tighter">
                        {resume.evaluation_result ? Math.round(resume.evaluation_result.ats_compliance_score / 10) : '—'}
                        <span className="text-sm opacity-20">/10</span>
                      </div>
                    </div>

                    {/* Action Button */}
                    <Button
                      onClick={() => setSelectedResume(resume)}
                      className="h-12 w-12 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 shadow-lg group-hover:scale-105 transition-all"
                    >
                      <ArrowRight className="w-5 h-5" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}

            {/* Resume Analysis Modal */}
            <Dialog open={!!selectedResume} onOpenChange={(open) => !open && setSelectedResume(null)}>
              <DialogContent className="max-w-5xl h-[90vh] p-0 overflow-hidden bg-card border-none rounded-3xl">
                {selectedResume && (
                  <div className="h-full overflow-hidden flex flex-col">
                    <ResumeAnalysisPanel
                      resume={selectedResume}
                      onBack={() => setSelectedResume(null)}
                      onResumeUpdate={(updatedResume) => {
                        // Update local state
                        setSelectedResume(updatedResume)
                        // Update parent list via a new prop (which we need to add to ResumeEvaluationDashboardProps)
                        // But since we don't have that prop yet, let's just rely on the parent re-render? 
                        // No, we need to pass a callback up.
                        onResumeUpdate(updatedResume)
                      }}
                    />
                  </div>
                )}
              </DialogContent>
            </Dialog>
          </div>
        )}
      </div>
    </div>
  )
}