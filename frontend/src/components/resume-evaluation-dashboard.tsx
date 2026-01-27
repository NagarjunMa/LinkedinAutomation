"use client"

import React from 'react'
import { Upload, Target, ChevronDown } from 'lucide-react'
import { COLORS } from '@/lib/constants/resume-evaluation-design'
import type { ResumeFile } from '@/app/lib/api/types'

interface ResumeEvaluationDashboardProps {
  onStartEvaluation: () => void
  onUploadResume: () => void
  resumes: ResumeFile[]
}

export function ResumeEvaluationDashboard({
  onStartEvaluation,
  onUploadResume,
  resumes
}: ResumeEvaluationDashboardProps) {
  // Get the most recent resume or mock data
  const latestResume = resumes.length > 0 ? resumes[0] : null

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

      {/* Resume Status Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-16">
        <div className="lg:col-span-3 bg-card p-10 rounded-3xl border border-border shadow-sm flex flex-col md:flex-row gap-12 items-center relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-96 h-96 bg-muted/30 rounded-full -mr-32 -mt-32 opacity-50 group-hover:scale-110 transition-transform duration-700"></div>

          <div className="flex-1 z-10">
            <div className="flex items-center gap-3 mb-4">
              <div className="px-3 py-1 bg-orange-500/10 text-orange-600 text-[10px] font-black uppercase tracking-widest rounded-full border border-orange-500/20">
                Active Node
              </div>
              <div className="text-[10px] font-bold text-muted-foreground">
                ID: {latestResume?.id.slice(0, 6) || 'DEMO01'}XF
              </div>
            </div>
            <h3 className="text-3xl font-black tracking-tighter text-foreground mb-1">
              {latestResume?.filename || 'NagarjunMallesh.pdf'}
            </h3>
            <p className="text-xs font-bold text-muted-foreground">
              Last Synchronized: {latestResume ? new Date(latestResume.uploaded_at).toLocaleDateString() : '1/21/2026'} at {latestResume ? new Date(latestResume.uploaded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '14:22 GMT'}
            </p>
          </div>

          <div className="flex flex-wrap gap-8 z-10">
            <div className="flex flex-col">
              <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground mb-2">
                Integrity Score
              </span>
              <div className="text-2xl font-black font-mono text-foreground">
                {latestResume?.evaluation_result?.overall_score || '7.2'}
                <span className="text-sm opacity-20">/{latestResume?.evaluation_result?.max_score || '10'}</span>
              </div>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground mb-2">
                File Size
              </span>
              <div className="text-lg font-bold text-foreground">
                {latestResume ? `${Math.round(latestResume.file_size / 1024)} KB` : '123.7 KB'}
              </div>
            </div>
            <div className="flex flex-col min-w-[140px]">
              <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground mb-2">
                Protocol Status
              </span>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full animate-pulse ${latestResume?.evaluation_status === 'failed' ? 'bg-red-500' : 'bg-emerald-400'}`}></div>
                <span className="text-xs font-black uppercase tracking-widest text-foreground">
                  {latestResume?.evaluation_status === 'completed' ? 'Evaluated' :
                    latestResume?.evaluation_status === 'evaluating' ? 'Processing' :
                      latestResume?.evaluation_status === 'failed' ? 'Failed' : 'Ready'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Initiate Evaluation Card */}
        <div
          onClick={onStartEvaluation}
          className="bg-card border border-border p-12 rounded-3xl group cursor-pointer hover:border-primary/50 transition-all shadow-sm hover:shadow-xl hover:bg-accent/5"
        >
          <div className="w-16 h-16 bg-primary rounded-2xl flex items-center justify-center text-primary-foreground mb-8 group-hover:rotate-6 transition-transform">
            <Target className="w-8 h-8" />
          </div>
          <h3 className="text-3xl font-black tracking-tighter mb-3 text-foreground">
            Initiate Evaluation.
          </h3>
          <p className="text-sm font-medium text-muted-foreground leading-relaxed mb-8">
            Execute a full-spectrum heuristic analysis on your current resume artifact.
          </p>
          <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-primary">
            Launch Protocol{' '}
            <ChevronDown className="w-4 h-4 -rotate-90 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>

        {/* Compare Artifacts Card */}
        <div
          onClick={onUploadResume}
          className="bg-primary p-12 rounded-3xl text-primary-foreground group cursor-pointer shadow-xl hover:shadow-2xl transition-all hover:bg-primary/95"
        >
          <div className="w-16 h-16 bg-background rounded-2xl flex items-center justify-center text-primary mb-8 group-hover:-rotate-6 transition-transform">
            <Upload className="w-8 h-8" />
          </div>
          <h3 className="text-3xl font-black tracking-tighter mb-3 text-primary-foreground">
            Compare Artifacts.
          </h3>
          <p className="text-sm font-medium text-primary-foreground/60 leading-relaxed mb-8">
            Upload a variant for differential analysis against baseline industry standards.
          </p>
          <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-primary-foreground">
            A/B Sync{' '}
            <ChevronDown className="w-4 h-4 -rotate-90 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>
      </div>
    </div>
  )
}