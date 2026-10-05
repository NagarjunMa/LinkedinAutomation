"use client"

import { useState, useCallback, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { useToast } from "@/components/ui/use-toast"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Upload, FileText, Trash2, Eye, AlertCircle, Star, TrendingUp, Target, CheckCircle, XCircle, Sparkles, Loader2, Clock, Shield } from "lucide-react"
import { resumeApi, type ResumeFile } from "@/app/lib/api"
import Confetti from "react-confetti"
import { LoadingFillText } from "@/components/ui/loading-fill-text"

export function ResumeUpload() {
  const [resumes, setResumes] = useState<ResumeFile[]>([])
  const [uploading, setUploading] = useState(false)
  const [evaluating, setEvaluating] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showEvaluationModal, setShowEvaluationModal] = useState(false)
  const [showConfetti, setShowConfetti] = useState(false)
  const [evaluationProgress, setEvaluationProgress] = useState(0)
  const [currentEvaluatingResume, setCurrentEvaluatingResume] = useState<ResumeFile | null>(null)
  const [recentlyUploadedResume, setRecentlyUploadedResume] = useState<ResumeFile | null>(null)
  const [deleteConfirmResume, setDeleteConfirmResume] = useState<ResumeFile | null>(null)
  const { toast } = useToast()

  // Fix evaluation status for resumes that have results but wrong status
  const fixEvaluationStatus = (resume: ResumeFile) => {
    if (resume.evaluation_result && resume.evaluation_status === 'evaluating') {
      console.log('Auto-fixing evaluation status for resume:', resume.id)
      setResumes(prev => prev.map(r =>
        r.id === resume.id ? { ...r, evaluation_status: 'completed' } : r
      ))
      return true
    }
    return false
  }

  // Load resumes on component mount
  useEffect(() => {
    loadResumes()
  }, [])

  // Reset stuck evaluations on component mount and every 30 seconds
  useEffect(() => {
    const resetStuckEvaluations = () => {
      setResumes(prev => prev.map(resume => {
        const uploadTime = new Date(resume.uploaded_at).getTime()
        const now = new Date().getTime()
        const minutesSinceUpload = (now - uploadTime) / (1000 * 60)

        if (resume.evaluation_status === 'evaluating' && minutesSinceUpload > 5) {
          console.log(`Resetting stuck evaluation for resume ${resume.id} (${minutesSinceUpload.toFixed(1)} minutes old)`)
          return { ...resume, evaluation_status: 'failed' as const }
        }
        return resume
      }))
    }

    // Reset immediately
    resetStuckEvaluations()

    // Reset every 30 seconds
    const interval = setInterval(resetStuckEvaluations, 30000)

    return () => clearInterval(interval)
  }, [])

  // Auto-fix evaluation status when resumes change
  useEffect(() => {
    resumes.forEach(resume => {
      fixEvaluationStatus(resume)
    })
  }, [resumes])

  // Poll for status updates when evaluations are in progress
  useEffect(() => {
    const hasEvaluatingResumes = resumes.some(r => r.evaluation_status === 'evaluating')

    if (hasEvaluatingResumes) {
      const interval = setInterval(() => {
        console.log('Polling for evaluation status updates...')
        loadResumes()
      }, 5000) // Poll every 5 seconds

      return () => clearInterval(interval)
    }
  }, [resumes])

  const loadResumes = async () => {
    try {
      setLoading(true)
      const data = await resumeApi.listResumes()
      console.log('Loaded resumes:', data)

      // Fix evaluation status for resumes that have results but wrong status
      const fixedResumes = data.resumes.map((resume: ResumeFile) => {
        console.log(`Resume ${resume.id}: status=${resume.evaluation_status}, hasResult=${!!resume.evaluation_result}`)

        // If resume has evaluation results but status is still evaluating, fix it
        if (resume.evaluation_result && resume.evaluation_status === 'evaluating') {
          console.log('Fixing evaluation status for resume:', resume.id)
          return {
            ...resume,
            evaluation_status: 'completed' as const
          }
        }

        // If resume has been evaluating for more than 5 minutes, mark as failed
        const uploadTime = new Date(resume.uploaded_at).getTime()
        const now = new Date().getTime()
        const minutesSinceUpload = (now - uploadTime) / (1000 * 60)

        if (resume.evaluation_status === 'evaluating' && minutesSinceUpload > 5) {
          console.log(`Marking stuck evaluation as failed for resume ${resume.id} (${minutesSinceUpload.toFixed(1)} minutes old)`)
          return {
            ...resume,
            evaluation_status: 'failed' as const
          }
        }

        return resume
      })

      setResumes(fixedResumes)
    } catch (error) {
      console.error('Failed to load resumes:', error)
      toast({
        title: "Error",
        description: "Failed to load resumes",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    // Check storage limit
    if (resumes.length >= 5) {
      toast({
        title: "Storage Limit Reached",
        description: "You can only store 5 resumes. Please delete one before uploading a new one.",
        variant: "destructive",
      })
      return
    }

    const file = files[0]

    // Validate file type
    if (!file.type.includes('pdf') && !file.type.includes('word') && !file.type.includes('document')) {
      toast({
        title: "Invalid File Type",
        description: "Please upload a PDF or Word document.",
        variant: "destructive",
      })
      return
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      toast({
        title: "File Too Large",
        description: "Please upload a file smaller than 10MB.",
        variant: "destructive",
      })
      return
    }

    setUploading(true)

    try {
      // Upload file using API
      const newResume = await resumeApi.uploadResume(file)

      // Add to local state
      setResumes(prev => [...prev, newResume])
      setRecentlyUploadedResume(newResume)

      toast({
        title: "Upload Successful",
        description: `${file.name} has been uploaded successfully.`,
      })

      // Show upload confirmation modal instead of auto-evaluating
      setShowUploadModal(true)

      // No need to refresh since we already added to local state
      // The setTimeout refresh was causing the uploaded resume to disappear temporarily

    } catch (error) {
      console.error('Upload failed:', error)

      // Check if it's a storage limit error
      if (error instanceof Error && (
        error.message.includes('Storage limit reached') ||
        error.message.includes('storage limit') ||
        error.message.includes('Maximum 5 resumes allowed')
      )) {
        toast({
          title: "Storage Limit Reached",
          description: "You can only store 5 resumes. Please delete one before uploading a new one.",
          variant: "destructive",
        })
      } else {
        toast({
          title: "Upload Failed",
          description: error instanceof Error ? error.message : "Failed to upload resume. Please try again.",
          variant: "destructive",
        })
      }
    } finally {
      setUploading(false)
      // Reset file input
      event.target.value = ''
    }
  }, [resumes, toast])

  const evaluateResume = async (resumeId: string) => {
    const resume = resumes.find(r => r.id === resumeId)
    if (!resume) return

    // Check if resume is already being evaluated
    if (resume.evaluation_status === 'evaluating') {
      toast({
        title: "Evaluation In Progress",
        description: "This resume is already being evaluated. Please wait for it to complete.",
        variant: "destructive",
      })
      return
    }

    setEvaluating(resumeId)
    setCurrentEvaluatingResume(resume)
    setShowEvaluationModal(true)
    setEvaluationProgress(0)

    try {
      // Update status to evaluating immediately (optimistic update)
      setResumes(prev => prev.map(r =>
        r.id === resumeId ? { ...r, evaluation_status: 'evaluating' } : r
      ))

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setEvaluationProgress(prev => {
          if (prev >= 90) return prev
          return prev + Math.random() * 15
        })
      }, 500)

      // Call the API to start evaluation (now returns process info)
      const evaluationResponse = await resumeApi.evaluateResume(resumeId)
      console.log('Evaluation started:', evaluationResponse)

      // Poll for completion with improved error handling
      let attempts = 0
      const maxAttempts = 60 // 5 minutes max
      let evaluationResult = null

      while (attempts < maxAttempts && !evaluationResult) {
        await new Promise(resolve => setTimeout(resolve, 5000)) // Wait 5 seconds between checks

        try {
          // Refresh the resume list to get updated status
          const updatedResumes = await resumeApi.listResumes()
          const updatedResume = updatedResumes.resumes.find(r => r.id === resumeId)

          if (updatedResume?.evaluation_result) {
            evaluationResult = updatedResume.evaluation_result as any
            break
          }

          // If status changed to failed, break the polling
          if (updatedResume?.evaluation_status === 'failed') {
            throw new Error('Evaluation failed on server')
          }

        } catch (error) {
          console.error('Error checking evaluation status:', error)
          // Don't break on polling errors, continue trying
        }

        attempts++
      }

      clearInterval(progressInterval)
      setEvaluationProgress(100)

      // Wait a moment to show 100% progress
      await new Promise(resolve => setTimeout(resolve, 1000))

      if (evaluationResult) {
        setResumes(prev => prev.map(r =>
          r.id === resumeId ? {
            ...r,
            evaluation_status: 'completed' as const,
            evaluation_result: evaluationResult
          } : r
        ))

        // Show confetti celebration
        setShowConfetti(true)
        setTimeout(() => setShowConfetti(false), 5000)

        toast({
          title: "🎉 Evaluation Complete!",
          description: `Resume scored ${(evaluationResult as any)?.overall_score || 0}/100 with detailed analysis.`,
        })

        // Close evaluation modal after a short delay
        setTimeout(() => {
          setShowEvaluationModal(false)
          setCurrentEvaluatingResume(null)
          setEvaluationProgress(0)
        }, 2000)

      } else {
        // Timeout - mark as failed
        setResumes(prev => prev.map(r =>
          r.id === resumeId ? { ...r, evaluation_status: 'failed' as const } : r
        ))
        throw new Error('Evaluation timed out')
      }

    } catch (error) {
      console.error('Evaluation failed:', error)

      // Handle specific error cases
      let errorMessage = "Failed to evaluate resume. Please try again."
      if (error instanceof Error) {
        if (error.message.includes('currently being evaluated')) {
          errorMessage = "Resume is already being evaluated by another process. Please wait."
        } else if (error.message.includes('timed out')) {
          errorMessage = "Evaluation took too long to complete. Please try again."
        } else {
          errorMessage = error.message
        }
      }

      setResumes(prev => prev.map(r =>
        r.id === resumeId ? { ...r, evaluation_status: 'failed' } : r
      ))

      toast({
        title: "Evaluation Failed",
        description: errorMessage,
        variant: "destructive",
      })

      setShowEvaluationModal(false)
      setCurrentEvaluatingResume(null)
      setEvaluationProgress(0)
    } finally {
      setEvaluating(null)
    }
  }

  const confirmDeleteResume = (resume: ResumeFile) => {
    setDeleteConfirmResume(resume)
  }

  const deleteResume = async () => {
    if (!deleteConfirmResume) return

    try {
      await resumeApi.deleteResume(deleteConfirmResume.id)

      // Remove from local state
      setResumes(prev => prev.filter(r => r.id !== deleteConfirmResume.id))

      toast({
        title: "Resume Deleted",
        description: `${deleteConfirmResume.filename || deleteConfirmResume.original_filename} has been removed from storage.`,
      })

      setDeleteConfirmResume(null)
    } catch (error) {
      console.error('Delete failed:', error)
      toast({
        title: "Delete Failed",
        description: "Failed to delete resume. Please try again.",
        variant: "destructive",
      })
    }
  }

  const refreshAndFixStatus = async () => {
    try {
      await loadResumes()

      // Force fix any stuck evaluation statuses
      setResumes(prev => prev.map(resume => {
        if (resume.evaluation_result && resume.evaluation_status === 'evaluating') {
          return { ...resume, evaluation_status: 'completed' as const }
        }
        // Reset evaluations that have been stuck for more than 10 minutes
        const uploadTime = new Date(resume.uploaded_at).getTime()
        const now = new Date().getTime()
        const minutesSinceUpload = (now - uploadTime) / (1000 * 60)

        if (resume.evaluation_status === 'evaluating' && minutesSinceUpload > 10) {
          return { ...resume, evaluation_status: 'failed' as const }
        }
        return resume
      }))

      toast({
        title: "Status Refreshed",
        description: "Evaluation statuses have been updated.",
      })
    } catch (error) {
      console.error('Failed to refresh status:', error)
      toast({
        title: "Refresh Failed",
        description: "Failed to refresh evaluation statuses.",
        variant: "destructive",
      })
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) {
        return 'Recently uploaded'
      }
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    } catch {
      return 'Recently uploaded'
    }
  }

  const _getStatusBadge = (status: ResumeFile['evaluation_status']) => {
    const variants = {
      pending: 'secondary',
      evaluating: 'default',
      completed: 'default',
      failed: 'destructive'
    } as const

    const labels = {
      pending: 'Pending',
      evaluating: 'Evaluating...',
      completed: 'Completed',
      failed: 'Failed'
    }

    return <Badge variant={variants[status]}>{labels[status]}</Badge>
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Excellent'
    if (score >= 60) return 'Good'
    if (score >= 40) return 'Fair'
    return 'Poor'
  }

  const getScoreIcon = (score: number) => {
    if (score >= 80) return <Star className="h-4 w-4 text-green-600" />
    if (score >= 60) return <TrendingUp className="h-4 w-4 text-yellow-600" />
    if (score >= 40) return <Target className="h-4 w-4 text-orange-600" />
    return <XCircle className="h-4 w-4 text-red-600" />
  }

  return (
    <div className="space-y-8">
      {/* Confetti Effect */}
      {showConfetti && (
        <Confetti
          width={window.innerWidth}
          height={window.innerHeight}
          recycle={false}
          numberOfPieces={200}
          gravity={0.3}
        />
      )}

      {/* Upload Section - Dark Theme */}
      <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-8">
        <div className="text-center space-y-6">
          <div className="space-y-2">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto">
              <Upload className="h-8 w-8 text-white" />
            </div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
              Resume Review Center
            </h2>
            <p className="text-cream-300 text-lg">
              Expert AI-powered resume analysis by experienced recruiters
            </p>
          </div>

          <div className="flex items-center justify-center gap-4">
            <div className="flex-1 max-w-md">
              <Label htmlFor="resume-upload" className="sr-only">
                Choose resume file
              </Label>
              <Input
                id="resume-upload"
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={handleFileUpload}
                disabled={uploading || resumes.length >= 5}
                className="cursor-pointer bg-primary-800/50 border-primary-600 text-cream-50 file:bg-primary-700 file:text-cream-50 file:border-0 file:rounded-md file:px-4 file:py-2 file:mr-4"
              />
            </div>
            <Button
              onClick={() => document.getElementById('resume-upload')?.click()}
              disabled={uploading || resumes.length >= 5}
              className="bg-gradient-warm hover:bg-gradient-gold text-white px-8 py-3 rounded-xl font-semibold glow-orange hover:glow-gold transition-all duration-300"
            >
              {uploading ? (
                <>
                  <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-5 w-5 mr-2" />
                  Upload Resume
                </>
              )}
            </Button>
          </div>

          <div className="flex items-center justify-center gap-8 text-sm text-cream-300">
            <span>Storage: {resumes.length}/5 resumes</span>
            <span>Max file size: 10MB</span>
          </div>

          {resumes.length >= 5 && (
            <div className="bg-gradient-to-r from-red-900/30 to-orange-900/30 border border-red-500/50 rounded-xl p-6 text-center">
              <div className="flex items-center justify-center gap-3 text-red-400 mb-3">
                <AlertCircle className="h-6 w-6" />
                <span className="font-bold text-lg">Storage Limit Reached</span>
              </div>
              <p className="text-red-300 text-base mb-4">
                You have reached the maximum of 5 resumes. Delete one to upload a new resume.
              </p>
              <div className="flex items-center justify-center gap-2 text-sm text-cream-300">
                <span>Current: {resumes.length}/5 resumes</span>
                <span>•</span>
                <span>Click the trash icon on any resume to delete it</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Resumes List - Dark Theme */}
      <div className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-2xl font-bold text-white flex items-center gap-3">
              <FileText className="h-6 w-6 text-blue-400" />
              My Resumes ({resumes.length}/5)
            </h3>
            <p className="text-cream-300 mt-1">
              Manage and view your uploaded resumes and AI-powered ATS evaluations.
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={refreshAndFixStatus}
              className="bg-primary-700/50 hover:bg-primary-600/50 text-cream-50 border-primary-500"
              size="sm"
            >
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2" />
              Refresh
            </Button>
            <Button
              onClick={() => {
                setResumes(prev => prev.map(resume =>
                  resume.evaluation_status === 'evaluating'
                    ? { ...resume, evaluation_status: 'failed' as const }
                    : resume
                ))
                toast({
                  title: "Stuck Evaluations Reset",
                  description: "All stuck evaluations have been marked as failed.",
                })
              }}
              className="bg-orange-700/50 hover:bg-orange-600/50 text-orange-300 border-orange-600"
              size="sm"
            >
              <XCircle className="h-4 w-4 mr-2" />
              Reset Stuck
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4" />
            <p className="text-gray-400">Loading resumes...</p>
          </div>
        ) : resumes.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-800/50 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <FileText className="h-8 w-8 text-gray-500" />
            </div>
            <h4 className="text-xl font-semibold text-white mb-2">No resumes uploaded yet</h4>
            <p className="text-gray-400">Upload your first resume to get started with AI-powered ATS evaluation.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {resumes.map((resume) => (
              <div key={resume.id} className="bg-gray-800/30 backdrop-blur-xl rounded-xl border border-white/10 p-6 hover:bg-gray-700/50 transition-all duration-300">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-xl flex items-center justify-center">
                      <FileText className="h-6 w-6 text-blue-400" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-white text-lg">
                        {resume.filename || resume.original_filename || 'Untitled Resume'}
                      </h4>
                      <p className="text-gray-400 text-sm">
                        {formatFileSize(resume.file_size)} • Uploaded {formatDate(resume.uploaded_at)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {/* Show status based on evaluation_status field */}
                    {resume.evaluation_status === 'completed' || resume.evaluation_result ? (
                      <div className="flex items-center gap-2 bg-green-900/30 text-green-400 px-3 py-1 rounded-full border border-green-500/30">
                        <CheckCircle className="h-4 w-4" />
                        <span className="text-sm font-medium">Completed</span>
                      </div>
                    ) : resume.evaluation_status === 'evaluating' ? (
                      <div className="flex items-center gap-2 bg-blue-900/30 text-blue-400 px-3 py-1 rounded-full border border-blue-500/30">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm font-medium">Evaluating</span>
                      </div>
                    ) : resume.evaluation_status === 'failed' ? (
                      <div className="flex items-center gap-2 bg-red-900/30 text-red-400 px-3 py-1 rounded-full border border-red-500/30">
                        <XCircle className="h-4 w-4" />
                        <span className="text-sm font-medium">Failed</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 bg-yellow-900/30 text-yellow-400 px-3 py-1 rounded-full border border-yellow-500/30">
                        <Clock className="h-4 w-4" />
                        <span className="text-sm font-medium">Pending</span>
                      </div>
                    )}

                    {/* Action Buttons - Always visible */}
                    <div className="flex items-center gap-2">
                      {/* Delete Button - Always visible */}
                      <Button
                        onClick={() => confirmDeleteResume(resume)}
                        className="bg-red-600 hover:bg-red-700 text-white border-red-600 hover:scale-105 transition-all duration-200 shadow-lg min-w-[40px] h-10"
                        size="sm"
                        title="Delete resume"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>

                      {/* Action buttons based on status */}
                      {resume.evaluation_status === 'pending' && (
                        <Button
                          onClick={() => evaluateResume(resume.id)}
                          disabled={evaluating === resume.id}
                          className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-4 py-2 rounded-lg font-semibold"
                          size="sm"
                        >
                          {evaluating === resume.id ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Evaluating...
                            </>
                          ) : (
                            <>
                              <Star className="h-4 w-4 mr-2" />
                              Evaluate
                            </>
                          )}
                        </Button>
                      )}

                      {resume.evaluation_status === 'evaluating' && (
                        <Button
                          onClick={() => {
                            setResumes(prev => prev.map(r =>
                              r.id === resume.id ? { ...r, evaluation_status: 'failed' as const } : r
                            ))
                            toast({
                              title: "Evaluation Stopped",
                              description: "The evaluation has been stopped.",
                            })
                          }}
                          className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg font-semibold"
                          size="sm"
                        >
                          <XCircle className="h-4 w-4 mr-2" />
                          Stop
                        </Button>
                      )}

                      {resume.evaluation_status === 'failed' && (
                        <Button
                          onClick={() => evaluateResume(resume.id)}
                          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-semibold"
                          size="sm"
                        >
                          <Star className="h-4 w-4 mr-2" />
                          Retry
                        </Button>
                      )}

                      {resume.evaluation_status === 'completed' && resume.evaluation_result && (
                        <Button
                          variant="outline"
                          className="bg-primary-700/50 hover:bg-primary-600/50 text-cream-50 border-primary-500 px-4 py-2 rounded-lg"
                          size="sm"
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View
                        </Button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Evaluation Progress */}
                {resume.evaluation_status === 'evaluating' && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-300">AI ATS Evaluation in progress...</span>
                      <span className="text-blue-400">{evaluating === resume.id ? 'Processing...' : 'Complete'}</span>
                    </div>
                    <Progress value={evaluating === resume.id ? 65 : 100} className="h-2 bg-gray-700" />
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex items-center gap-3 mt-4">
                  {resume.evaluation_status === 'pending' && (
                    <Button
                      onClick={() => evaluateResume(resume.id)}
                      disabled={evaluating === resume.id}
                      className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-2 rounded-lg font-semibold"
                    >
                      {evaluating === resume.id ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Evaluating...
                        </>
                      ) : (
                        <>
                          <Star className="h-4 w-4 mr-2" />
                          Start Evaluation
                        </>
                      )}
                    </Button>
                  )}

                  {resume.evaluation_status === 'evaluating' && (
                    <div className="flex gap-2">
                      <Button
                        onClick={() => {
                          setResumes(prev => prev.map(r =>
                            r.id === resume.id ? { ...r, evaluation_status: 'failed' as const } : r
                          ))
                          toast({
                            title: "Evaluation Stopped",
                            description: "The evaluation has been stopped.",
                          })
                        }}
                        className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg font-semibold"
                      >
                        <XCircle className="h-4 w-4 mr-2" />
                        Stop
                      </Button>
                      <Button
                        onClick={() => evaluateResume(resume.id)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-semibold"
                      >
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Refreshing...
                      </Button>
                    </div>
                  )}

                  {resume.evaluation_status === 'completed' && resume.evaluation_result && (
                    <Button
                      variant="outline"
                      className="bg-primary-700/50 hover:bg-primary-600/50 text-cream-50 border-primary-500 px-6 py-2 rounded-lg"
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      View Analysis
                    </Button>
                  )}

                  {resume.evaluation_status === 'failed' && (
                    <Button
                      onClick={() => evaluateResume(resume.id)}
                      className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-semibold"
                    >
                      <Star className="h-4 w-4 mr-2" />
                      Retry Evaluation
                    </Button>
                  )}
                </div>

                {/* Evaluation Results - Dark Theme */}
                {resume.evaluation_status === 'completed' && resume.evaluation_result && (
                  <div className="mt-6 space-y-6">
                    {/* Overall Score */}
                    <div className="text-center p-6 bg-gradient-to-r from-blue-900/20 to-purple-900/20 rounded-xl border border-blue-500/20">
                      <div className="flex items-center justify-center gap-2 mb-3">
                        {getScoreIcon(resume.evaluation_result.overall_score)}
                        <span className="text-sm font-medium text-gray-300">Overall ATS Score</span>
                      </div>
                      <div className={`text-5xl font-bold ${getScoreColor(resume.evaluation_result.overall_score)}`}>
                        {resume.evaluation_result.overall_score}/100
                      </div>
                      <div className="text-lg font-medium text-gray-300">
                        {getScoreLabel(resume.evaluation_result.overall_score)}
                      </div>
                    </div>

                    {/* Detailed Scores Grid - Dark Theme */}
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      <div className="text-center p-4 bg-gray-800/50 rounded-xl border border-gray-700">
                        <div className="text-xl font-bold text-blue-400">{resume.evaluation_result.ats_compliance_score}/20</div>
                        <div className="text-sm text-gray-300">ATS Compliance</div>
                        <div className="text-xs text-gray-400 mt-1">
                          {getScoreLabel(resume.evaluation_result.ats_compliance_score * 5)}
                        </div>
                      </div>
                      <div className="text-center p-4 bg-gray-800/50 rounded-xl border border-gray-700">
                        <div className="text-xl font-bold text-green-400">{resume.evaluation_result.content_quality_score}/25</div>
                        <div className="text-sm text-gray-300">Content Quality</div>
                        <div className="text-xs text-gray-400 mt-1">
                          {getScoreLabel(resume.evaluation_result.content_quality_score * 4)}
                        </div>
                      </div>
                      <div className="text-center p-4 bg-gray-800/50 rounded-xl border border-gray-700">
                        <div className="text-xl font-bold text-purple-400">{resume.evaluation_result.experience_points_score}/20</div>
                        <div className="text-sm text-gray-300">Experience Points</div>
                        <div className="text-xs text-gray-400 mt-1">
                          {getScoreLabel(resume.evaluation_result.experience_points_score * 5)}
                        </div>
                      </div>
                      <div className="text-center p-4 bg-gray-800/50 rounded-xl border border-gray-700">
                        <div className="text-xl font-bold text-orange-400">{resume.evaluation_result.job_relevance_score}/15</div>
                        <div className="text-sm text-gray-300">Job Relevance</div>
                        <div className="text-xs text-gray-400 mt-1">
                          {getScoreLabel(resume.evaluation_result.job_relevance_score * 6.67)}
                        </div>
                      </div>
                      <div className="text-center p-4 bg-gray-800/50 rounded-xl border border-gray-700">
                        <div className="text-xl font-bold text-indigo-400">{resume.evaluation_result.quality_checks_score}/10</div>
                        <div className="text-sm text-gray-300">Quality Checks</div>
                        <div className="text-xs text-gray-400 mt-1">
                          {getScoreLabel(resume.evaluation_result.quality_checks_score * 10)}
                        </div>
                      </div>
                    </div>

                    {/* Enhanced Detailed Analysis - Dark Theme */}
                    <div className="space-y-6">
                      {/* Executive Summary */}
                      <div className="p-6 bg-gradient-to-r from-blue-900/20 to-purple-900/20 rounded-xl border border-blue-500/20">
                        <h5 className="font-semibold text-blue-400 flex items-center gap-2 mb-3">
                          <FileText className="h-5 w-5" />
                          Executive Summary
                        </h5>
                        <p className="text-gray-300 leading-relaxed">
                          {resume.evaluation_result.detailed_feedback}
                        </p>
                      </div>

                      {/* Detailed Improvements with Specific Fixes */}
                      <div className="space-y-4">
                        <h5 className="font-semibold text-orange-400 flex items-center gap-2 text-lg">
                          <Target className="h-5 w-5" />
                          Priority Improvements
                        </h5>
                        <p className="text-sm text-gray-400 mb-4">
                          Focus on these areas for maximum score improvement
                        </p>

                        {/* Immediate Fixes */}
                        {resume.evaluation_result.critical_issues?.immediate_fixes && resume.evaluation_result.critical_issues.immediate_fixes.length > 0 && (
                          <div className="space-y-3">
                            <h6 className="font-medium text-red-400 flex items-center gap-2">
                              <AlertCircle className="h-4 w-4" />
                              Critical Fixes (Immediate Impact)
                            </h6>
                            <div className="space-y-3">
                              {resume.evaluation_result.critical_issues.immediate_fixes.map((fix: string, index: number) => (
                                <div key={index} className="p-4 bg-red-900/20 rounded-lg border border-red-500/20">
                                  <div className="flex items-start gap-3">
                                    <div className="w-6 h-6 bg-red-600 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                                      <span className="text-white text-xs font-bold">{index + 1}</span>
                                    </div>
                                    <div className="flex-1">
                                      <p className="text-gray-300 text-sm leading-relaxed">{fix}</p>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Strategic Improvements */}
                        {resume.evaluation_result.critical_issues?.strategic_improvements && resume.evaluation_result.critical_issues.strategic_improvements.length > 0 && (
                          <div className="space-y-3">
                            <h6 className="font-medium text-orange-400 flex items-center gap-2">
                              <Target className="h-4 w-4" />
                              Strategic Improvements (High Impact)
                            </h6>
                            <div className="space-y-3">
                              {resume.evaluation_result.critical_issues.strategic_improvements.map((improvement: string, index: number) => (
                                <div key={index} className="p-4 bg-orange-900/20 rounded-lg border border-orange-500/20">
                                  <div className="flex items-start gap-3">
                                    <div className="w-6 h-6 bg-orange-600 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                                      <span className="text-white text-xs font-bold">{index + 1}</span>
                                    </div>
                                    <div className="flex-1">
                                      <p className="text-gray-300 text-sm leading-relaxed">{improvement}</p>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Timeline Issues */}
                        {((resume.evaluation_result.critical_issues as Record<string, unknown>)?.timeline_issues as string[] | undefined) && ((resume.evaluation_result.critical_issues as Record<string, unknown>).timeline_issues as string[]).length > 0 && (
                          <div className="space-y-3">
                            <h6 className="font-medium text-yellow-400 flex items-center gap-2">
                              <Clock className="h-4 w-4" />
                              Timeline Issues
                            </h6>
                            <div className="space-y-3">
                              {((resume.evaluation_result.critical_issues as Record<string, unknown>).timeline_issues as string[]).map((issue: string, index: number) => (
                                <div key={index} className="p-4 bg-yellow-900/20 rounded-lg border border-yellow-500/20">
                                  <div className="flex items-start gap-3">
                                    <div className="w-6 h-6 bg-yellow-600 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                                      <span className="text-white text-xs font-bold">{index + 1}</span>
                                    </div>
                                    <div className="flex-1">
                                      <p className="text-gray-300 text-sm leading-relaxed">{issue}</p>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* ATS Critical Fixes */}
                        {((resume.evaluation_result.critical_issues as Record<string, unknown>)?.ats_critical_fixes as string[] | undefined) && ((resume.evaluation_result.critical_issues as Record<string, unknown>).ats_critical_fixes as string[]).length > 0 && (
                          <div className="space-y-3">
                            <h6 className="font-medium text-purple-400 flex items-center gap-2">
                              <Shield className="h-4 w-4" />
                              ATS Critical Fixes
                            </h6>
                            <div className="space-y-3">
                              {((resume.evaluation_result.critical_issues as Record<string, unknown>).ats_critical_fixes as string[]).map((fix: string, index: number) => (
                                <div key={index} className="p-4 bg-purple-900/20 rounded-lg border border-purple-500/20">
                                  <div className="flex items-start gap-3">
                                    <div className="w-6 h-6 bg-purple-600 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                                      <span className="text-white text-xs font-bold">{index + 1}</span>
                                    </div>
                                    <div className="flex-1">
                                      <p className="text-gray-300 text-sm leading-relaxed">{fix}</p>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Nice to Have */}
                        {resume.evaluation_result.critical_issues?.nice_to_have && resume.evaluation_result.critical_issues.nice_to_have.length > 0 && (
                          <div className="space-y-3">
                            <h6 className="font-medium text-blue-400 flex items-center gap-2">
                              <Star className="h-4 w-4" />
                              Nice to Have (Polish)
                            </h6>
                            <div className="space-y-3">
                              {resume.evaluation_result.critical_issues.nice_to_have.map((enhancement: string, index: number) => (
                                <div key={index} className="p-4 bg-blue-900/20 rounded-lg border border-blue-500/20">
                                  <div className="flex items-start gap-3">
                                    <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                                      <span className="text-white text-xs font-bold">{index + 1}</span>
                                    </div>
                                    <div className="flex-1">
                                      <p className="text-gray-300 text-sm leading-relaxed">{enhancement}</p>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Key Strengths */}
                      <div className="space-y-3">
                        <h5 className="font-semibold text-green-400 flex items-center gap-2">
                          <CheckCircle className="h-4 w-4" />
                          Key Strengths
                        </h5>
                        <ul className="space-y-2">
                          {resume.evaluation_result.strengths.map((strength, index) => (
                            <li key={index} className="text-sm flex items-start gap-2 p-3 bg-green-900/20 rounded-lg border border-green-500/20">
                              <div className="w-2 h-2 bg-green-400 rounded-full mt-2 shrink-0" />
                              <span className="text-gray-300">{strength}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* ATS Compatibility - Dark Theme */}
                    <div className="border-t border-gray-700 pt-6">
                      <div className="flex items-center justify-between mb-4">
                        <h5 className="font-semibold text-white">ATS Compatibility Assessment</h5>
                        <div className={`px-3 py-1 rounded-full text-sm font-medium ${resume.evaluation_result.ats_compatibility === 'excellent' ? 'bg-green-900/30 text-green-400 border border-green-500/30' :
                          resume.evaluation_result.ats_compatibility === 'good' ? 'bg-blue-900/30 text-blue-400 border border-blue-500/30' :
                            resume.evaluation_result.ats_compatibility === 'fair' ? 'bg-yellow-900/30 text-yellow-400 border border-yellow-500/30' :
                              'bg-red-900/30 text-red-400 border border-red-500/30'
                          }`}>
                          {resume.evaluation_result.ats_compatibility.charAt(0).toUpperCase() +
                            resume.evaluation_result.ats_compatibility.slice(1)}
                        </div>
                      </div>
                      <p className="text-sm text-gray-300 leading-relaxed">
                        {resume.evaluation_result.detailed_feedback}
                      </p>
                    </div>

                    {/* Keyword Analysis - Dark Theme */}
                    <div className="border-t border-gray-700 pt-6">
                      <h5 className="font-semibold text-white mb-4">Keyword Analysis & Optimization</h5>
                      <div className="grid md:grid-cols-3 gap-4 text-sm">
                        <div className="text-center p-4 bg-blue-900/20 rounded-xl border border-blue-500/20">
                          <div className="text-xl font-bold text-blue-400">{resume.evaluation_result.keyword_analysis.score}/10</div>
                          <div className="text-xs text-gray-300">Keyword Score</div>
                        </div>
                        <div className="p-4 bg-green-900/20 rounded-xl border border-green-500/20">
                          <div className="text-xs font-medium text-green-400 mb-2">Relevant Keywords Found</div>
                          <div className="text-xs text-green-300">
                            {resume.evaluation_result.keyword_analysis.relevant.join(', ')}
                          </div>
                        </div>
                        <div className="p-4 bg-orange-900/20 rounded-xl border border-orange-500/20">
                          <div className="text-xs font-medium text-orange-400 mb-2">Missing Keywords</div>
                          <div className="text-xs text-orange-300">
                            {resume.evaluation_result.keyword_analysis.missing.join(', ')}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upload Confirmation Modal */}
      <Dialog open={showUploadModal} onOpenChange={setShowUploadModal}>
        <DialogContent className="bg-gray-900 border-gray-700 text-white">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3 text-2xl">
              <div className="w-12 h-12 bg-green-500 rounded-xl flex items-center justify-center">
                <CheckCircle className="h-6 w-6 text-white" />
              </div>
              Upload Successful!
            </DialogTitle>
            <DialogDescription className="text-gray-300 text-lg">
              {recentlyUploadedResume?.filename || recentlyUploadedResume?.original_filename || 'Your resume'} has been uploaded successfully.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
              <div className="flex items-center gap-3">
                <FileText className="h-8 w-8 text-blue-400" />
                <div>
                  <h4 className="font-semibold text-white">
                    {recentlyUploadedResume?.filename || recentlyUploadedResume?.original_filename || 'Resume'}
                  </h4>
                  <p className="text-sm text-gray-400">
                    {recentlyUploadedResume && formatFileSize(recentlyUploadedResume.file_size)} • Ready for evaluation
                  </p>
                </div>
              </div>
            </div>
            <div className="flex gap-3">
              <Button
                onClick={() => {
                  setShowUploadModal(false)
                  if (recentlyUploadedResume) {
                    evaluateResume(recentlyUploadedResume.id)
                  }
                }}
                className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
              >
                <Star className="h-4 w-4 mr-2" />
                Evaluate Now
              </Button>
              <Button
                onClick={() => setShowUploadModal(false)}
                variant="outline"
                className="bg-primary-700/50 hover:bg-primary-600/50 text-cream-50 border-primary-500"
              >
                Later
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Evaluation Progress Modal */}
      <Dialog open={showEvaluationModal} onOpenChange={setShowEvaluationModal}>
        <DialogContent className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 border-gray-700 text-white max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-center text-2xl mb-4">
              <div className="flex flex-col items-center space-y-4">
                <div className="relative">
                  <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center">
                    <Sparkles className="h-8 w-8 text-white animate-pulse" />
                  </div>
                  <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl blur opacity-30 animate-pulse"></div>
                </div>
                Resume Review
              </div>
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-8">
            {/* Animated Loading Text */}
            <div className="flex justify-center">
              <LoadingFillText
                text="ANALYZING"
                className="text-center"
                duration={3000}
              />
            </div>

            {currentEvaluatingResume && (
              <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700 backdrop-blur-sm">
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <FileText className="h-10 w-10 text-blue-400" />
                    <div className="absolute -inset-1 bg-blue-400/20 rounded-lg blur"></div>
                  </div>
                  <div>
                    <h4 className="font-semibold text-white text-lg">
                      {currentEvaluatingResume.filename || currentEvaluatingResume.original_filename || 'Resume'}
                    </h4>
                    <p className="text-gray-400">
                      {formatFileSize(currentEvaluatingResume.file_size)} • Processing with AI agents...
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Enhanced Progress Section */}
            <div className="space-y-4">
              <div className="flex justify-between text-sm">
                <span className="text-gray-300 font-medium">Evaluation Progress</span>
                <span className="text-blue-400 font-bold">{Math.round(evaluationProgress)}%</span>
              </div>
              <div className="relative">
                <Progress value={evaluationProgress} className="h-4 bg-gray-700" />
                <div className="absolute inset-0 h-4 bg-gradient-to-r from-blue-500/20 to-purple-600/20 rounded-full animate-pulse"></div>
              </div>
            </div>

            {/* AI Analysis Steps */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center gap-3 p-3 bg-gray-800/30 rounded-lg">
                <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
                <span className="text-gray-300">ATS Compatibility</span>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gray-800/30 rounded-lg">
                <div className="w-3 h-3 bg-blue-400 rounded-full animate-pulse" />
                <span className="text-gray-300">Content Analysis</span>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gray-800/30 rounded-lg">
                <div className="w-3 h-3 bg-purple-400 rounded-full animate-pulse" />
                <span className="text-gray-300">Experience Scoring</span>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gray-800/30 rounded-lg">
                <div className="w-3 h-3 bg-orange-400 rounded-full animate-pulse" />
                <span className="text-gray-300">Market Positioning</span>
              </div>
            </div>

            {/* Status Message */}
            <div className="text-center bg-gray-800/30 p-4 rounded-xl border border-gray-700">
              <div className="flex items-center justify-center gap-2 mb-2">
                <Clock className="h-4 w-4 text-blue-400" />
                <span className="text-gray-300 text-sm">Our AI agents are working...</span>
              </div>
              <p className="text-gray-400 text-xs">
                Multiple specialized AI agents are analyzing different aspects of your resume.
                This typically takes 30-90 seconds for comprehensive evaluation.
              </p>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Modal */}
      <Dialog open={!!deleteConfirmResume} onOpenChange={() => setDeleteConfirmResume(null)}>
        <DialogContent className="bg-gray-900 border-gray-700 text-white">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3 text-2xl">
              <div className="w-12 h-12 bg-red-500 rounded-xl flex items-center justify-center">
                <Trash2 className="h-6 w-6 text-white" />
              </div>
              Delete Resume
            </DialogTitle>
            <DialogDescription className="text-gray-300 text-lg">
              Are you sure you want to delete this resume? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {deleteConfirmResume && (
              <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                <div className="flex items-center gap-3">
                  <FileText className="h-8 w-8 text-red-400" />
                  <div>
                    <h4 className="font-semibold text-white">
                      {deleteConfirmResume.filename || deleteConfirmResume.original_filename}
                    </h4>
                    <p className="text-sm text-gray-400">
                      {formatFileSize(deleteConfirmResume.file_size)} • Uploaded {formatDate(deleteConfirmResume.uploaded_at)}
                    </p>
                  </div>
                </div>
              </div>
            )}
            <div className="flex gap-3">
              <Button
                onClick={deleteResume}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete Resume
              </Button>
              <Button
                onClick={() => setDeleteConfirmResume(null)}
                variant="outline"
                className="bg-primary-700/50 hover:bg-primary-600/50 text-cream-50 border-primary-500"
              >
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
} 