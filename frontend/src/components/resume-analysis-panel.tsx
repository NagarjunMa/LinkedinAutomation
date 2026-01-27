"use client"

import React, { useState } from 'react'
import {
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Zap,
  MessageSquare,
  Layout,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { COLORS, MOCK_FEEDBACK } from '@/lib/constants/resume-evaluation-design'
import type { ResumeFile } from '@/app/lib/api/types'

interface ResumeAnalysisPanelProps {
  resume?: ResumeFile | null
  onBack?: () => void
}

interface FeedbackSection {
  id: string
  icon: React.ComponentType<{ className?: string }>
  title: string
  content: React.ReactNode
}

export function ResumeAnalysisPanel({ resume, onBack }: ResumeAnalysisPanelProps) {
  const [expandedSection, setExpandedSection] = useState<string | null>('strengths')

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section)
  }

  // Use real data if available, otherwise use mock data
  const feedback = resume?.evaluation_result || MOCK_FEEDBACK
  const overallScore = feedback.overall_score || MOCK_FEEDBACK.overallScore
  const maxScore = feedback.max_score || MOCK_FEEDBACK.maxScore

  const sections: FeedbackSection[] = [
    {
      id: 'strengths',
      icon: CheckCircle2,
      title: 'Optical Strengths',
      content: (
        <div className="space-y-2">
          {(feedback.strengths || MOCK_FEEDBACK.strengths).map((strength: string, i: number) => (
            <div key={i} className="flex items-start gap-3 p-3 bg-muted/30 rounded-2xl border border-border/50 text-xs text-muted-foreground">
              <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0 opacity-20"></div>
              {strength}
            </div>
          ))}
        </div>
      )
    },
    {
      id: 'wording',
      icon: MessageSquare,
      title: 'Linguistic Delta',
      content: (
        <div className="space-y-4">
          {(feedback.improvements || MOCK_FEEDBACK.wordingSuggestions).map((suggestion: any, i: number) => (
            <div key={i} className="rounded-2xl border border-border overflow-hidden text-[11px]">
              <div className="p-3 bg-red-500/10 border-b border-border">
                <span className="text-[10px] font-black uppercase text-red-500 mr-2 opacity-60">- Original</span>
                <p className="text-muted-foreground mt-1 line-through">
                  {suggestion.original || suggestion}
                </p>
              </div>
              <div className="p-3 bg-emerald-500/10">
                <span className="text-[10px] font-black uppercase text-emerald-500 mr-2">+ Suggested</span>
                <p className="text-foreground font-bold mt-1">
                  {suggestion.suggested || `Improved version of: ${suggestion}`}
                </p>
              </div>
            </div>
          ))}
        </div>
      )
    },
    {
      id: 'ats',
      icon: Layout,
      title: 'ATS Compatibility',
      content: (
        <div className="space-y-6">
          <div className="px-2">
            <div className="flex justify-between items-center mb-3">
              <span className="text-[10px] font-black uppercase text-muted-foreground">Vector Matching</span>
              <span className="text-xs font-black text-primary">
                {Math.round((feedback.ats_compliance_score || MOCK_FEEDBACK.atsOptimization.score * 10))}%
              </span>
            </div>
            <div className="h-1 w-full bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-1000"
                style={{
                  width: `${Math.round((feedback.ats_compliance_score || MOCK_FEEDBACK.atsOptimization.score * 10))}%`
                }}
              ></div>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-3">
            {(feedback.ats_checklist || MOCK_FEEDBACK.atsOptimization.checklist).map((item: string, i: number) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-card border border-border rounded-xl text-[10px] font-bold text-muted-foreground">
                <div className="w-4 h-4 border border-muted-foreground/30 rounded flex items-center justify-center bg-muted/50">
                  <CheckCircle2 className="w-2.5 h-2.5 opacity-40" />
                </div>
                {item}
              </div>
            ))}
          </div>
        </div>
      )
    }
  ]

  return (
    <div className="flex-[2] flex flex-col bg-card border-l border-border h-full">
      {/* Header */}
      <div className="p-8 border-b border-border flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-black tracking-tighter text-foreground">
            Precision Analysis
          </h3>
          <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mt-1">
            Artifact Evaluation Engine 1.0
          </p>
        </div>

        <div className="flex flex-col items-end">
          <div className="text-4xl font-black font-mono tracking-tighter flex items-baseline gap-1 text-primary">
            {overallScore}
            <span className="text-sm font-bold opacity-30">/{maxScore}</span>
          </div>
          <div className="text-[10px] font-black uppercase tracking-tighter px-2 py-0.5 bg-emerald-500/10 text-emerald-600 rounded mt-1 border border-emerald-500/20">
            Optimal Score
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-8 space-y-6">
        {/* Executive Summary */}
        <div className="p-6 bg-muted/30 border border-border rounded-3xl">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="w-4 h-4 text-primary" />
            <span className="text-[10px] font-black uppercase tracking-widest text-foreground">
              Executive Summary
            </span>
          </div>
          <p className="text-sm leading-relaxed text-muted-foreground italic">
            "{feedback.executive_summary || MOCK_FEEDBACK.executiveSummary}"
          </p>
        </div>

        {/* Analysis Sections */}
        <div className="space-y-4">
          {sections.map((section) => {
            const Icon = section.icon
            const isExpanded = expandedSection === section.id

            return (
              <div
                key={section.id}
                className="border border-border rounded-3xl overflow-hidden shadow-sm hover:shadow-md transition-shadow"
              >
                <button
                  onClick={() => toggleSection(section.id)}
                  className="w-full flex items-center justify-between p-5 bg-card group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="font-black text-xs uppercase tracking-widest text-foreground">
                      {section.title}
                    </span>
                  </div>
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 opacity-30" />
                  ) : (
                    <ChevronDown className="w-4 h-4 opacity-30" />
                  )}
                </button>
                {isExpanded && (
                  <div className="px-5 pb-5 bg-card">
                    {section.content}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Footer Actions */}
      <div className="p-8 border-t border-border bg-muted/20">
        <Button
          onClick={onBack}
          className="w-full py-5 bg-primary text-primary-foreground font-black text-xs uppercase tracking-ultra-wide rounded-2xl shadow-xl hover:bg-primary/90 transition-all active:scale-95"
        >
          Lock Evaluation & Exit
        </Button>
      </div>
    </div>
  )
}