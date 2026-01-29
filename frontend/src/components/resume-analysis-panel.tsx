"use client"

import React, { useState, useEffect } from 'react'
import {
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Zap,
  MessageSquare,
  Layout,
  Play,
  Loader2,
  AlertTriangle,
  AlertCircle
} from 'lucide-react'
import { Button } from '@/components/ui/button'
// import { MOCK_FEEDBACK } from '@/lib/constants/resume-evaluation-design'
import { resumeApi } from '@/app/lib/api/resume'
import { useToast } from '@/components/ui/use-toast'
import type { ResumeFile } from '@/app/lib/api/types'
import {
  ResumeEvaluationError,
  ResumeEvaluationErrorBanner,
  determineErrorType
} from './resume-evaluation-error'

interface ResumeAnalysisPanelProps {
  resume?: ResumeFile | null
  onBack?: () => void
  onResumeUpdate?: (resume: ResumeFile) => void
}

interface FeedbackSection {
  id: string
  icon: React.ComponentType<{ className?: string }>
  title: string
  content: React.ReactNode
}

export function ResumeAnalysisPanel({ resume, onBack, onResumeUpdate }: ResumeAnalysisPanelProps) {
  const [expandedSection, setExpandedSection] = useState<string | null>('strengths')
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [evaluationProgress, setEvaluationProgress] = useState(0)
  const [currentResume, setCurrentResume] = useState<ResumeFile | null>(resume || null)
  const [evaluationError, setEvaluationError] = useState<string | null>(null)
  const [showErrorModal, setShowErrorModal] = useState(false)
  const [showErrorBanner, setShowErrorBanner] = useState(false)
  const { toast } = useToast()

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section)
  }

  // Update current resume when prop changes
  useEffect(() => {
    setCurrentResume(resume || null)
  }, [resume])

  // Start evaluation
  const handleStartEvaluation = async () => {
    if (!currentResume?.id) {
      toast({
        title: "Error",
        description: "No resume selected for evaluation",
        variant: "destructive"
      })
      return
    }

    setIsEvaluating(true)
    setEvaluationProgress(0)

    try {
      // Start evaluation
      await resumeApi.evaluateResume(currentResume.id)

      toast({
        title: "Evaluation Started! 🚀",
        description: "AI analysis in progress. This may take a few moments."
      })

      // Poll for progress
      await pollEvaluationProgress(currentResume.id)

    } catch (error) {
      console.error('Evaluation failed:', error)
      setIsEvaluating(false)
      setEvaluationProgress(0)
      setEvaluationError(error instanceof Error ? error.message : "Failed to start evaluation")
      setShowErrorModal(true)
    }
  }

  // Poll evaluation progress
  const pollEvaluationProgress = async (resumeId: string) => {
    const maxAttempts = 60 // 5 minutes max (5s interval)
    let attempts = 0

    const poll = async () => {
      try {
        attempts++
        const progressResponse = await resumeApi.getEvaluationProgress(resumeId)

        if (progressResponse.progress) {
          setEvaluationProgress(progressResponse.progress.overall_progress || 0)
        }

        if (progressResponse.evaluation_status === 'completed') {
          // Evaluation completed - fetch updated resume
          const updatedResume = await resumeApi.getResume(resumeId)
          setCurrentResume(updatedResume)
          if (onResumeUpdate) {
            onResumeUpdate(updatedResume)
          }

          setIsEvaluating(false)
          setEvaluationProgress(100)

          toast({
            title: "Evaluation Complete! ✨",
            description: "Your resume has been analyzed successfully."
          })
          return
        } else if (progressResponse.evaluation_status === 'failed') {
          setEvaluationError('Resume evaluation failed during processing')
          setShowErrorBanner(true)
          throw new Error('Evaluation failed on server')
        }

        // Continue polling if still in progress and under max attempts
        if (attempts < maxAttempts && progressResponse.evaluation_status === 'evaluating') {
          setTimeout(poll, 5000) // Poll every 5 seconds
        } else if (attempts >= maxAttempts) {
          throw new Error('Evaluation timeout - please try again')
        }

      } catch (error) {
        console.error('Polling error:', error)
        setIsEvaluating(false)
        setEvaluationProgress(0)
        setEvaluationError(error instanceof Error ? error.message : "Evaluation failed")
        setShowErrorModal(true)
      }
    }

    // Start polling with initial delay
    setTimeout(poll, 2000)
  }

  // Handle evaluation states
  const hasEvaluation = currentResume?.evaluation_status === 'completed' && !!currentResume?.evaluation_result
  const isEvaluationFailed = currentResume?.evaluation_status === 'failed'
  const isEvaluationPending = currentResume?.evaluation_status === 'pending' || !currentResume?.evaluation_status

  // Use real data if available
  const feedback = currentResume?.evaluation_result || {} as any
  const overallScore = hasEvaluation ? (feedback.ai_score ?? feedback.overall_score) : undefined
  const maxScore = hasEvaluation ? (feedback.max_score || 100) : 100

  // Resume polling if status is evaluating on mount
  useEffect(() => {
    if (currentResume?.evaluation_status === 'evaluating' && !isEvaluating) {
      setIsEvaluating(true)
      pollEvaluationProgress(currentResume.id)
    }
    // Show error banner for failed evaluations
    if (currentResume?.evaluation_status === 'failed') {
      setShowErrorBanner(true)
      setEvaluationError('Resume evaluation failed')
    }
  }, [currentResume?.evaluation_status, currentResume?.id])

  // Retry evaluation handler
  const handleRetryEvaluation = async () => {
    setEvaluationError(null)
    setShowErrorBanner(false)
    setShowErrorModal(false)
    await handleStartEvaluation()
  }

  const sections: FeedbackSection[] = [
    {
      id: 'strengths',
      icon: CheckCircle2,
      title: 'Optical Strengths',
      content: (
        <div className="space-y-2">
          {((feedback.optical_strengths && feedback.optical_strengths.length > 0) ? feedback.optical_strengths : feedback.strengths).map((strength: string, i: number) => (
            <div key={i} className="flex items-start gap-3 p-3 bg-muted/30 rounded-2xl border border-border/50 text-xs text-muted-foreground">
              <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0 opacity-20"></div>
              {strength}
            </div>
          ))}
        </div>
      )
    },
    {
      id: 'improvements',
      icon: Zap,
      title: 'Strategic Improvements',
      content: (
        <div className="space-y-2">
          {((feedback.strategic_improvements && feedback.strategic_improvements.length > 0) ? feedback.strategic_improvements : feedback.improvements).map((improvement: string, i: number) => (
            <div key={i} className="flex items-start gap-3 p-3 bg-amber-500/10 rounded-xl border border-amber-500/20 text-xs text-foreground font-medium">
              <div className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0"></div>
              {improvement}
            </div>
          ))}
        </div>
      )
    },
    {
      id: 'wording',
      icon: MessageSquare,
      title: 'Wording Suggestions',
      content: (
        <div className="space-y-4">
          {/* Fallback for perfect resumes (Score >= 95) */}
          {(!feedback.wording_suggestions || feedback.wording_suggestions.length === 0) && (overallScore || 0) >= 95 && (
            <div className="flex flex-col items-center justify-center p-8 bg-emerald-500/5 border border-emerald-500/10 rounded-3xl text-center">
              <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600 mb-3">
                <div className="w-6 h-6 border-[3px] border-emerald-600 rounded-full flex items-center justify-center">
                  <CheckCircle2 className="w-3 h-3 fill-emerald-600 text-white" />
                </div>
              </div>
              <h4 className="text-sm font-black text-emerald-700 mb-1">Top 1% Industry Standard Verified</h4>
              <p className="text-xs text-muted-foreground max-w-xs leading-relaxed">
                For the targeted roles, the resume contains all the required keywords and strong action verbs. No wording changes required.
              </p>
            </div>
          )}

          {/* Fallback for non-perfect resumes with missing suggestions (Error State) */}
          {(!feedback.wording_suggestions || feedback.wording_suggestions.length === 0) && (overallScore || 0) < 95 && (
            <div className="flex flex-col items-center justify-center p-6 bg-amber-500/5 border border-amber-500/10 rounded-3xl text-center">
              <AlertCircle className="w-8 h-8 text-amber-500 mb-2" />
              <h4 className="text-sm font-bold text-amber-700 mb-1">General Improvements Required</h4>
              <p className="text-xs text-muted-foreground max-w-xs leading-relaxed">
                While specific wording changes weren't generated, your score of {overallScore} indicates room for improvement. Please review the "Strategic Improvements" section above.
              </p>
            </div>
          )}

          {(feedback.wording_suggestions || []).map((suggestion: any, i: number) => (
            <div key={i} className="rounded-2xl border border-border overflow-hidden">
              {/* Original Text */}
              <div className="p-4 bg-red-500/5 border-b border-border/30">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[9px] font-black uppercase text-red-600 bg-red-100 px-2 py-1 rounded">
                    Original
                  </span>
                  <span className="text-[8px] text-muted-foreground uppercase tracking-wider">Needs Improvement</span>
                </div>
                <p className="text-xs text-muted-foreground italic leading-relaxed">
                  "{suggestion.original}"
                </p>
              </div>

              {/* Suggested Text */}
              <div className="p-4 bg-emerald-500/5">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[9px] font-black uppercase text-emerald-600 bg-emerald-100 px-2 py-1 rounded">
                    Suggested
                  </span>
                  <span className="text-[8px] text-muted-foreground uppercase tracking-wider">Improved Version</span>
                </div>
                <p className="text-xs text-foreground font-semibold leading-relaxed mb-3">
                  "{suggestion.suggested}"
                </p>

                {/* Rationale */}
                <div className="pt-2 border-t border-border/20">
                  <span className="text-[8px] font-black uppercase text-muted-foreground tracking-widest mb-1 block">
                    Why This Works Better
                  </span>
                  <p className="text-[10px] text-muted-foreground leading-relaxed">
                    {suggestion.rationale}
                  </p>
                </div>
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
                {feedback.ats_score ? Math.round(feedback.ats_score) : Math.round(feedback.ats_compliance_score)}/100
              </span>
            </div>
            <div className="h-1 w-full bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-1000"
                style={{
                  width: `${feedback.ats_score || feedback.ats_compliance_score}%`
                }}
              ></div>
            </div>
          </div>

          {/* Detailed ATS Feedback if available */}
          {feedback.ats_compatibility_details ? (
            <div className="space-y-4 pt-2">
              <div className="p-4 bg-muted/20 rounded-xl border border-border/50">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {feedback.ats_compatibility_details.analysis}
                </p>

                {feedback.ats_compatibility_details.missing_keywords && feedback.ats_compatibility_details.missing_keywords.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-border/30">
                    <h5 className="text-[10px] font-black uppercase text-red-500/80 mb-2">Missing Keywords</h5>
                    <div className="flex flex-wrap gap-2">
                      {feedback.ats_compatibility_details.missing_keywords.map((kw, i) => (
                        <span key={i} className="px-2 py-1 bg-red-500/5 text-red-600/80 rounded border border-red-500/10 text-[10px]">
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {(feedback.ats_checklist || []).map((item: string, i: number) => (
                <div key={i} className="flex items-center gap-3 p-3 bg-card border border-border rounded-xl text-[10px] font-bold text-muted-foreground">
                  <div className="w-4 h-4 border border-muted-foreground/30 rounded flex items-center justify-center bg-muted/50">
                    <CheckCircle2 className="w-2.5 h-2.5 opacity-40" />
                  </div>
                  {item}
                </div>
              ))}
            </div>
          )}
        </div>
      )
    }
  ]

  return (
    <div className="flex-[2] flex flex-col bg-card border-l border-border h-full">
      {/* Header */}
      <div className="p-8 border-b border-border">
        <div className="flex items-center justify-between mb-4">
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
              {hasEvaluation ? overallScore : (isEvaluationFailed ? '—' : '--')}
              <span className="text-sm font-bold opacity-30">/{maxScore}</span>
            </div>
            <div className={`text-[10px] font-black uppercase tracking-tighter px-2 py-0.5 rounded mt-1 border ${hasEvaluation
              ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20'
              : isEvaluationFailed
                ? 'bg-red-500/10 text-red-600 border-red-500/20'
                : 'bg-muted text-muted-foreground border-border'
              }`}>
              {hasEvaluation ? 'Evaluated' : isEvaluationFailed ? 'Failed' : 'Pending Analysis'}
            </div>
          </div>
        </div>

        {/* Error Banner for Failed Evaluations */}
        {showErrorBanner && isEvaluationFailed && (
          <ResumeEvaluationErrorBanner
            errorType={determineErrorType(evaluationError)}
            onRetry={handleRetryEvaluation}
            onDismiss={() => setShowErrorBanner(false)}
            resumeFilename={currentResume?.filename}
          />
        )}

        {/* Evaluation Controls */}
        {(isEvaluationPending || isEvaluationFailed) && (
          <div className="flex items-center justify-center">
            <Button
              onClick={isEvaluationFailed ? handleRetryEvaluation : handleStartEvaluation}
              disabled={isEvaluating || !currentResume?.id}
              className="flex items-center gap-2 px-8 py-3 bg-primary text-primary-foreground font-black text-xs uppercase tracking-ultra-wide rounded-xl shadow-xl hover:bg-primary/90 transition-all active:scale-95 disabled:opacity-50"
            >
              {isEvaluating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing ({evaluationProgress}%)
                </>
              ) : isEvaluationFailed ? (
                <>
                  <AlertTriangle className="w-4 h-4" />
                  Retry Evaluation
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Start AI Evaluation
                </>
              )}
            </Button>
          </div>
        )}

        {/* Progress Bar */}
        {isEvaluating && (
          <div className="mt-4 space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Analysis Progress</span>
              <span className="font-bold text-primary">{evaluationProgress}%</span>
            </div>
            <div className="w-full bg-muted rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all duration-1000"
                style={{ width: `${evaluationProgress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-8 space-y-6">
        {/* Show content only if evaluation is completed, otherwise show appropriate state */}
        {hasEvaluation ? (
          <>
            {/* Executive Summary */}
            <div className="p-6 bg-muted/30 border border-border rounded-3xl">
              <div className="flex items-center gap-2 mb-3">
                <Zap className="w-4 h-4 text-primary" />
                <span className="text-[10px] font-black uppercase tracking-widest text-foreground">
                  Executive Summary
                </span>
              </div>
              <p className="text-sm leading-relaxed text-muted-foreground italic">
                "{feedback.executive_summary || (feedback as any).executiveSummary || "Resume analysis completed..."}"
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
          </>
        ) : (
          /* Empty state for pending/failed evaluations */
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-16 h-16 rounded-full bg-muted/30 flex items-center justify-center mb-4">
              {isEvaluationFailed ? (
                <AlertTriangle className="w-8 h-8 text-red-500" />
              ) : (
                <Zap className="w-8 h-8 text-muted-foreground/50" />
              )}
            </div>
            <h3 className="text-lg font-black text-foreground mb-2">
              {isEvaluationFailed ? 'Evaluation Failed' : 'Analysis Pending'}
            </h3>
            <p className="text-sm text-muted-foreground max-w-md leading-relaxed">
              {isEvaluationFailed
                ? 'Your resume evaluation encountered an error. Please try again or contact support if the issue persists.'
                : 'Start your AI-powered resume evaluation to see detailed insights, scoring, and recommendations.'
              }
            </p>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="p-8 border-t border-border bg-muted/20">
        <Button
          onClick={onBack}
          className="w-full py-5 bg-primary text-primary-foreground font-black text-xs uppercase tracking-ultra-wide rounded-2xl shadow-xl hover:bg-primary/90 transition-all active:scale-95"
        >
          {hasEvaluation ? 'Lock Evaluation & Exit' : 'Exit Analysis'}
        </Button>
      </div>

      {/* Error Modal */}
      <ResumeEvaluationError
        isOpen={showErrorModal}
        onClose={() => setShowErrorModal(false)}
        onRetry={handleRetryEvaluation}
        errorType={determineErrorType(evaluationError)}
        errorMessage={evaluationError || undefined}
        resumeFilename={currentResume?.filename}
      />
    </div>
  )
}