"use client"

import React, { useState, useEffect } from 'react'
import { ResumeDocumentViewer } from './resume-document-viewer'
import { ResumeAnalysisPanel } from './resume-analysis-panel'
import { ResumeEvaluationDashboard } from './resume-evaluation-dashboard'
import { ResumeUploadModal } from './resume-upload-modal'
import { resumeApi } from '@/app/lib/api/resume'
import { type ResumeFile } from '@/app/lib/api/types'
import { useToast } from '@/components/ui/use-toast'


type ViewMode = 'DASHBOARD' | 'EVALUATOR'

interface ResumeEvaluatorProps {
  initialView?: ViewMode
}

export function ResumeEvaluator({ initialView = 'DASHBOARD' }: ResumeEvaluatorProps) {
  const [view, setView] = useState<ViewMode>(initialView)
  const [resumes, setResumes] = useState<ResumeFile[]>([])
  const [selectedResume, setSelectedResume] = useState<ResumeFile | null>(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    loadResumes()
  }, [])

  const loadResumes = async () => {
    try {
      setLoading(true)
      const data = await resumeApi.listResumes()
      setResumes(data.resumes)

      // Auto-select the latest resume if none selected
      if (data.resumes.length > 0 && !selectedResume) {
        const latest = data.resumes.sort((a, b) =>
          new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime()
        )[0]
        setSelectedResume(latest)
      }
    } catch (error) {
      console.error('Failed to load resumes:', error)
      toast({
        title: "Error",
        description: "Failed to load resumes. Please try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleStartEvaluation = () => {
    if (selectedResume) {
      setView('EVALUATOR')
    } else {
      toast({
        title: "No Resume Selected",
        description: "Please upload a resume first to start evaluation.",
        variant: "destructive",
      })
      setShowUploadModal(true)
    }
  }

  const handleBackToDashboard = () => {
    setView('DASHBOARD')
  }

  const handleUploadSuccess = (resume: ResumeFile) => {
    setResumes(prev => [resume, ...prev])
    setSelectedResume(resume)
    toast({
      title: "Resume Uploaded Successfully! 🎉",
      description: "Your resume has been uploaded and is ready for AI evaluation.",
    })
  }

  const handleOpenUpload = () => {
    setShowUploadModal(true)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground font-medium">Loading resumes...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col font-sans text-foreground relative bg-background">
      {/* Film Grain Overlay - Optional, keeping for texture if globally desired, otherwise remove or adjust */}
      <div className="grain-overlay opacity-[0.03] pointer-events-none fixed inset-0 z-50" />

      <main className="flex-1">
        {view === 'DASHBOARD' ? (
          <ResumeEvaluationDashboard
            onStartEvaluation={handleStartEvaluation}
            onUploadResume={handleOpenUpload}
            resumes={resumes}
            onResumeUpdate={(updatedResume) => {
              setResumes(prev => prev.map(r =>
                r.id === updatedResume.id ? updatedResume : r
              ))
              if (selectedResume?.id === updatedResume.id) {
                setSelectedResume(updatedResume)
              }
            }}
          />
        ) : (
          <div className="flex h-[calc(100vh-64px)] overflow-hidden bg-background">
            <ResumeDocumentViewer
              fileUrl={selectedResume?.id ? `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/resumes/${selectedResume.id}/download` : undefined}
              fileName={selectedResume?.filename}
              onBack={handleBackToDashboard}
            />
            <ResumeAnalysisPanel
              resume={selectedResume}
              onBack={handleBackToDashboard}
              onResumeUpdate={(updatedResume) => {
                setSelectedResume(updatedResume)
                // Update the resumes list as well
                setResumes(prev => prev.map(r =>
                  r.id === updatedResume.id ? updatedResume : r
                ))
              }}
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="py-8 px-6 text-center text-muted-foreground text-xs bg-transparent">
        &copy; {new Date().getFullYear()} Prism Pro • Premium Resume Intelligence
      </footer>

      {/* Upload Modal */}
      <ResumeUploadModal
        open={showUploadModal}
        onOpenChange={setShowUploadModal}
        onUploadSuccess={handleUploadSuccess}
      />
    </div>
  )
}