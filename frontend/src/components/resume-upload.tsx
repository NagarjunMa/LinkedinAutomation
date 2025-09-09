"use client"

import { useState, useCallback, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { useToast } from "@/components/ui/use-toast"
import { Upload, FileText, Trash2, Eye, Download, AlertCircle, Star, TrendingUp, Target, CheckCircle, XCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { resumeApi, type ResumeFile, type ResumeEvaluation } from "@/app/lib/api"

export function ResumeUpload() {
  const [resumes, setResumes] = useState<ResumeFile[]>([])
  const [uploading, setUploading] = useState(false)
  const [evaluating, setEvaluating] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
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
        // If resume has evaluation results but status is still evaluating, fix it
        if (resume.evaluation_result && resume.evaluation_status === 'evaluating') {
          console.log('Fixing evaluation status for resume:', resume.id)
          return {
            ...resume,
            evaluation_status: 'completed'
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

      toast({
        title: "Upload Successful",
        description: `${file.name} has been uploaded successfully. AI evaluation started.`,
      })

      // Refresh the list to get updated status
      setTimeout(() => {
        loadResumes()
      }, 2000)

    } catch (error) {
      console.error('Upload failed:', error)
      toast({
        title: "Upload Failed",
        description: error instanceof Error ? error.message : "Failed to upload resume. Please try again.",
        variant: "destructive",
      })
    } finally {
      setUploading(false)
      // Reset file input
      event.target.value = ''
    }
  }, [resumes, toast, loadResumes])

  const evaluateResume = async (resumeId: string) => {
    setEvaluating(resumeId)

    try {
      // Update status to evaluating
      setResumes(prev => prev.map(r =>
        r.id === resumeId ? { ...r, evaluation_status: 'evaluating' } : r
      ))

      // Simulate AI evaluation - replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 3000))

      const mockEvaluation: ResumeEvaluation = {
        overall_score: 78,
        ats_compliance_score: 16,
        content_quality_score: 24,
        experience_points_score: 20,
        job_relevance_score: 12,
        quality_checks_score: 6,
        strengths: [
          "Strong technical skills section with relevant technologies",
          "Good use of action verbs in experience descriptions",
          "Clear project outcomes with measurable impacts"
        ],
        improvements: [
          "Add more specific metrics to achievements",
          "Include industry-specific keywords",
          "Strengthen professional summary with quantifiable results"
        ],
        ats_compatibility: 'good',
        detailed_feedback: "This resume shows good technical depth but could benefit from more specific quantifiable achievements and industry keyword optimization.",
        keyword_analysis: {
          relevant: ["React", "Node.js", "Python", "AWS"],
          missing: ["microservices", "CI/CD", "agile"],
          score: 7.5
        }
      }

      setResumes(prev => prev.map(r =>
        r.id === resumeId ? {
          ...r,
          evaluation_status: 'completed',
          evaluation_result: mockEvaluation
        } : r
      ))

      toast({
        title: "Evaluation Complete",
        description: "Resume has been analyzed by AI.",
      })

    } catch (error) {
      console.error('Evaluation failed:', error)
      setResumes(prev => prev.map(r =>
        r.id === resumeId ? { ...r, evaluation_status: 'failed' } : r
      ))

      toast({
        title: "Evaluation Failed",
        description: "Failed to evaluate resume. Please try again.",
        variant: "destructive",
      })
    } finally {
      setEvaluating(null)
    }
  }

  const deleteResume = async (resumeId: string) => {
    try {
      await resumeApi.deleteResume(resumeId)

      // Remove from local state
      setResumes(prev => prev.filter(r => r.id !== resumeId))

      toast({
        title: "Resume Deleted",
        description: "Resume has been removed from storage.",
      })
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
          return { ...resume, evaluation_status: 'completed' }
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

  const getStatusBadge = (status: ResumeFile['evaluation_status']) => {
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
    <div className="space-y-6">
      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload Resume
          </CardTitle>
          <CardDescription>
            Upload your resume for AI-powered ATS evaluation and scoring. Maximum 5 resumes allowed.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <Label htmlFor="resume-upload" className="sr-only">
                  Choose resume file
                </Label>
                <Input
                  id="resume-upload"
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileUpload}
                  disabled={uploading || resumes.length >= 5}
                  className="cursor-pointer"
                />
              </div>
              <Button
                onClick={() => document.getElementById('resume-upload')?.click()}
                disabled={uploading || resumes.length >= 5}
              >
                {uploading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4 mr-2" />
                    Choose File
                  </>
                )}
              </Button>
            </div>

            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>Storage: {resumes.length}/5 resumes</span>
              <span>Max file size: 10MB</span>
            </div>

            {resumes.length >= 5 && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Storage limit reached. Delete a resume to upload a new one.
                </AlertDescription>
              </Alert>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Resumes List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                My Resumes ({resumes.length}/5)
              </CardTitle>
              <CardDescription>
                Manage and view your uploaded resumes and AI-powered ATS evaluations.
              </CardDescription>
            </div>
            <Button onClick={refreshAndFixStatus} variant="outline" size="sm">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2" />
              Refresh & Fix Status
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
              <p>Loading resumes...</p>
            </div>
          ) : resumes.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No resumes uploaded yet.</p>
              <p className="text-sm">Upload your first resume to get started with AI-powered ATS evaluation.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {resumes.map((resume) => (
                <div key={resume.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-blue-600" />
                      <div>
                        <h4 className="font-medium">{resume.filename || resume.original_filename || 'Untitled Resume'}</h4>
                        <p className="text-sm text-muted-foreground">
                          {formatFileSize(resume.file_size)} • Uploaded {formatDate(resume.uploaded_at)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {/* Show completed status if we have results, regardless of status field */}
                      {resume.evaluation_result ? (
                        <Badge variant="default">Completed</Badge>
                      ) : (
                        getStatusBadge(resume.evaluation_status)
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => deleteResume(resume.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Evaluation Progress */}
                  {resume.evaluation_status === 'evaluating' && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span>AI ATS Evaluation in progress...</span>
                        <span>{evaluating === resume.id ? 'Processing...' : 'Complete'}</span>
                      </div>
                      <Progress value={evaluating === resume.id ? 65 : 100} className="h-2" />
                    </div>
                  )}

                  {/* Evaluation Results */}
                  {resume.evaluation_status === 'completed' && resume.evaluation_result && (
                    <div className="mt-4 space-y-6">
                      {/* Overall Score */}
                      <div className="text-center p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border">
                        <div className="flex items-center justify-center gap-2 mb-2">
                          {getScoreIcon(resume.evaluation_result.overall_score)}
                          <span className="text-sm font-medium text-muted-foreground">Overall ATS Score</span>
                        </div>
                        <div className={`text-4xl font-bold ${getScoreColor(resume.evaluation_result.overall_score)}`}>
                          {resume.evaluation_result.overall_score}/100
                        </div>
                        <div className="text-sm font-medium text-muted-foreground">
                          {getScoreLabel(resume.evaluation_result.overall_score)}
                        </div>
                      </div>

                      {/* Detailed Scores Grid */}
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <div className="text-lg font-bold text-blue-600">{resume.evaluation_result.ats_compliance_score}/20</div>
                          <div className="text-xs text-muted-foreground">ATS Compliance</div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {getScoreLabel(resume.evaluation_result.ats_compliance_score * 5)}
                          </div>
                        </div>
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <div className="text-lg font-bold text-green-600">{resume.evaluation_result.content_quality_score}/25</div>
                          <div className="text-xs text-muted-foreground">Content Quality</div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {getScoreLabel(resume.evaluation_result.content_quality_score * 4)}
                          </div>
                        </div>
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <div className="text-lg font-bold text-purple-600">{resume.evaluation_result.experience_points_score}/20</div>
                          <div className="text-xs text-muted-foreground">Experience Points</div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {getScoreLabel(resume.evaluation_result.experience_points_score * 5)}
                          </div>
                        </div>
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <div className="text-lg font-bold text-orange-600">{resume.evaluation_result.job_relevance_score}/15</div>
                          <div className="text-xs text-muted-foreground">Job Relevance</div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {getScoreLabel(resume.evaluation_result.job_relevance_score * 6.67)}
                          </div>
                        </div>
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <div className="text-lg font-bold text-indigo-600">{resume.evaluation_result.quality_checks_score}/10</div>
                          <div className="text-xs text-muted-foreground">Quality Checks</div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {getScoreLabel(resume.evaluation_result.quality_checks_score * 10)}
                          </div>
                        </div>
                      </div>

                      {/* Strengths and Improvements */}
                      <div className="grid md:grid-cols-2 gap-6">
                        <div className="space-y-3">
                          <h5 className="font-semibold text-green-700 flex items-center gap-2">
                            <CheckCircle className="h-4 w-4" />
                            Key Strengths
                          </h5>
                          <ul className="space-y-2">
                            {resume.evaluation_result.strengths.map((strength, index) => (
                              <li key={index} className="text-sm flex items-start gap-2 p-2 bg-green-50 rounded-md">
                                <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0" />
                                {strength}
                              </li>
                            ))}
                          </ul>
                        </div>
                        <div className="space-y-3">
                          <h5 className="font-semibold text-orange-700 flex items-center gap-2">
                            <Target className="h-4 w-4" />
                            Areas for Improvement
                          </h5>
                          <ul className="space-y-2">
                            {resume.evaluation_result.improvements.map((improvement, index) => (
                              <li key={index} className="text-sm flex items-start gap-2 p-2 bg-orange-50 rounded-md">
                                <div className="w-2 h-2 bg-orange-500 rounded-full mt-2 flex-shrink-0" />
                                {improvement}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      {/* ATS Compatibility */}
                      <div className="border-t pt-4">
                        <div className="flex items-center justify-between mb-3">
                          <h5 className="font-semibold">ATS Compatibility Assessment</h5>
                          <Badge variant={
                            resume.evaluation_result.ats_compatibility === 'excellent' ? 'default' :
                              resume.evaluation_result.ats_compatibility === 'good' ? 'secondary' :
                                resume.evaluation_result.ats_compatibility === 'fair' ? 'outline' : 'destructive'
                          }>
                            {resume.evaluation_result.ats_compatibility.charAt(0).toUpperCase() +
                              resume.evaluation_result.ats_compatibility.slice(1)}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground leading-relaxed">
                          {resume.evaluation_result.detailed_feedback}
                        </p>
                      </div>

                      {/* Keyword Analysis */}
                      <div className="border-t pt-4">
                        <h5 className="font-semibold mb-3">Keyword Analysis & Optimization</h5>
                        <div className="grid md:grid-cols-3 gap-4 text-sm">
                          <div className="text-center p-3 bg-blue-50 rounded-lg">
                            <div className="text-lg font-bold text-blue-600">{resume.evaluation_result.keyword_analysis.score}/10</div>
                            <div className="text-xs text-muted-foreground">Keyword Score</div>
                          </div>
                          <div className="p-3 bg-green-50 rounded-lg">
                            <div className="text-xs font-medium text-green-700 mb-2">Relevant Keywords Found</div>
                            <div className="text-xs text-green-600">
                              {resume.evaluation_result.keyword_analysis.relevant.join(', ')}
                            </div>
                          </div>
                          <div className="p-3 bg-orange-50 rounded-lg">
                            <div className="text-xs font-medium text-orange-700 mb-2">Missing Keywords</div>
                            <div className="text-xs text-orange-600">
                              {resume.evaluation_result.keyword_analysis.missing.join(', ')}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Pending Evaluation */}
                  {resume.evaluation_status === 'pending' && (
                    <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-blue-700 font-medium">Ready for AI Evaluation</p>
                          <p className="text-xs text-blue-600 mt-1">Click evaluate to start ATS scoring analysis</p>
                        </div>
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => evaluateResume(resume.id)}
                          disabled={evaluating === resume.id}
                        >
                          {evaluating === resume.id ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                              Evaluating...
                            </>
                          ) : (
                            <>
                              <Star className="h-4 w-4 mr-2" />
                              Evaluate Resume
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Failed Evaluation */}
                  {resume.evaluation_status === 'failed' && (
                    <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                      <p className="text-sm text-red-700 mb-2">
                        Evaluation failed. Please try uploading the resume again.
                      </p>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => evaluateResume(resume.id)}
                        disabled={evaluating === resume.id}
                      >
                        {evaluating === resume.id ? 'Retrying...' : 'Retry Evaluation'}
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 