"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { CheckCircle, AlertCircle, TrendingUp, FileText, Target, Zap, Upload, Star, Clock, Award, TrendingDown, Lightbulb, Users, Calendar, BookOpen } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { resumeApi, ResumeFile, ResumeEvaluation } from "@/app/lib/api"
import { ProtectedRoute } from "@/components/protected-route"
import { ResumeImprovementModal } from "@/components/resume-improvement-modal"
import { ResumeUploadModal } from "@/components/resume-upload-modal"
import { PrimaryResumeModal } from "@/components/primary-resume-modal"
import { ResumeListDropdown } from "@/components/resume-list-dropdown"

export default function ResumeEvaluationPage() {
  const [resumes, setResumes] = useState<ResumeFile[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedResume, setSelectedResume] = useState<ResumeFile | null>(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showPrimaryModal, setShowPrimaryModal] = useState(false)
  const [evaluatingResume, setEvaluatingResume] = useState<string | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    loadResumes()
  }, [])

  const loadResumes = async () => {
    try {
      setLoading(true)
      const data = await resumeApi.listResumes()
      console.log('Loaded resumes:', data)
      setResumes(data.resumes)
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

  const getLatestResume = () => {
    if (resumes.length === 0) return null
    return resumes.sort((a, b) =>
      new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime()
    )[0]
  }

  const getPrimaryResume = () => {
    return resumes.find(r => r.is_primary) || getLatestResume()
  }

  const handleEvaluateResume = async (resumeId: string) => {
    setEvaluatingResume(resumeId)
    try {
      // Trigger evaluation via API
      await resumeApi.evaluateResume(resumeId)
      toast({
        title: "Evaluation Started",
        description: "AI is analyzing your resume. This may take a few minutes.",
      })
      // Refresh after a delay
      setTimeout(() => loadResumes(), 5000)
    } catch (error) {
      toast({
        title: "Evaluation Failed",
        description: "Failed to start evaluation. Please try again.",
        variant: "destructive",
      })
    } finally {
      setEvaluatingResume(null)
    }
  }

  const handleUploadSuccess = (resume: ResumeFile) => {
    setResumes(prev => [resume, ...prev])
    toast({
      title: "Resume Uploaded Successfully! 🎉",
      description: "Your resume has been uploaded and is ready for AI evaluation.",
    })
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600"
    if (score >= 60) return "text-yellow-600"
    return "text-red-600"
  }

  const getScoreBadgeVariant = (score: number) => {
    if (score >= 80) return "default"
    if (score >= 60) return "secondary"
    return "destructive"
  }

  const getATSCompatibilityBadgeVariant = (compatibility: string) => {
    switch (compatibility) {
      case 'excellent': return 'default'
      case 'good': return 'secondary'
      case 'fair': return 'outline'
      case 'poor': return 'destructive'
      default: return 'outline'
    }
  }

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="container mx-auto py-8">
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading resumes...</p>
            </div>
          </div>
        </div>
      </ProtectedRoute>
    )
  }

  const latestResume = getLatestResume()
  const primaryResume = getPrimaryResume()

  return (
    <ProtectedRoute>
      <div className="container mx-auto py-8">
        {/* Header with Latest Resume Summary */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Resume Evaluation Center
              </h1>
              <p className="text-xl text-muted-foreground mt-2">
                Expert AI-powered resume analysis by experienced recruiters
              </p>
            </div>
            <Button
              onClick={() => setShowUploadModal(true)}
              size="lg"
              className="bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white"
            >
              <Upload className="w-5 h-5 mr-2" />
              Upload New Resume
            </Button>
          </div>

          {/* Latest Resume Status Card */}
          {latestResume && (
            <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200 mb-6">
              <CardContent className="pt-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-2 mb-3">
                      <Clock className="w-6 h-6 text-blue-600" />
                      <h3 className="text-lg font-semibold text-blue-800">Latest Resume</h3>
                    </div>
                    <div className="text-2xl font-bold text-blue-700 mb-2">
                      {latestResume.filename}
                    </div>
                    <p className="text-blue-600 text-sm">
                      Uploaded {new Date(latestResume.uploaded_at).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="text-center">
                    <div className="flex items-center justify-center gap-2 mb-3">
                      <Target className="w-6 h-6 text-green-600" />
                      <h3 className="text-lg font-semibold text-green-800">Evaluation Status</h3>
                    </div>
                    <Badge
                      variant={
                        latestResume.evaluation_status === 'completed' ? 'default' :
                          latestResume.evaluation_status === 'evaluating' ? 'secondary' :
                            latestResume.evaluation_status === 'failed' ? 'destructive' : 'outline'
                      }
                      className="text-lg px-4 py-2 mb-3"
                    >
                      {latestResume.evaluation_status === 'completed' && <CheckCircle className="w-4 h-4 mr-2" />}
                      {latestResume.evaluation_status === 'evaluating' && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>}
                      {latestResume.evaluation_status === 'failed' && <AlertCircle className="w-4 h-4 mr-2" />}
                      {latestResume.evaluation_status.charAt(0).toUpperCase() + latestResume.evaluation_status.slice(1)}
                    </Badge>
                    {latestResume.evaluation_status === 'completed' && latestResume.evaluation_result && (
                      <div className="text-2xl font-bold text-green-700">
                        Score: {latestResume.evaluation_result.overall_score}/100
                      </div>
                    )}
                  </div>

                  <div className="text-center">
                    <div className="flex items-center justify-center gap-2 mb-3">
                      <Star className="w-6 h-6 text-yellow-600" />
                      <h3 className="text-lg font-semibold text-yellow-800">Primary Resume</h3>
                    </div>
                    {primaryResume ? (
                      <div>
                        <div className="text-lg font-semibold text-yellow-700 mb-2">
                          {primaryResume.filename}
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setShowPrimaryModal(true)}
                        >
                          Change Primary
                        </Button>
                      </div>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowPrimaryModal(true)}
                      >
                        Set Primary Resume
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <Card className="hover:shadow-lg transition-all duration-300 cursor-pointer border-2 border-transparent hover:border-blue-200">
              <CardContent className="pt-6 text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Target className="w-8 h-8 text-blue-600" />
                </div>
                <h3 className="text-lg font-semibold mb-2">Evaluate Resume</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Get AI-powered analysis and improvement recommendations
                </p>
                {latestResume && latestResume.evaluation_status !== 'evaluating' && (
                  <Button
                    onClick={() => handleEvaluateResume(latestResume.id)}
                    disabled={evaluatingResume === latestResume.id}
                    className="w-full"
                  >
                    {evaluatingResume === latestResume.id ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                        Evaluating...
                      </>
                    ) : (
                      'Start Evaluation'
                    )}
                  </Button>
                )}
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-all duration-300 cursor-pointer border-2 border-transparent hover:border-green-200">
              <CardContent className="pt-6 text-center">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Upload className="w-8 h-8 text-green-600" />
                </div>
                <h3 className="text-lg font-semibold mb-2">Upload Resume</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Add a new resume for evaluation and comparison
                </p>
                <Button
                  onClick={() => setShowUploadModal(true)}
                  variant="outline"
                  className="w-full"
                >
                  Upload Now
                </Button>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-all duration-300 cursor-pointer border-2 border-transparent hover:border-purple-200">
              <CardContent className="pt-6 text-center">
                <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <BookOpen className="w-8 h-8 text-purple-600" />
                </div>
                <h3 className="text-lg font-semibold mb-2">Study Timeline</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Create personalized learning path based on your resume
                </p>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setShowPrimaryModal(true)}
                >
                  View Timeline
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Resume List with Dropdown */}
        <ResumeListDropdown
          resumes={resumes}
          onViewDetailedAnalysis={setSelectedResume}
          onDownloadResume={(resumeId) => window.open(`/api/v1/resumes/${resumeId}/download`, '_blank')}
          onEvaluateResume={handleEvaluateResume}
          evaluatingResume={evaluatingResume}
        />

        {/* Modals */}
        <ResumeImprovementModal
          resume={selectedResume}
          open={!!selectedResume}
          onOpenChange={(open) => !open && setSelectedResume(null)}
        />

        <ResumeUploadModal
          open={showUploadModal}
          onOpenChange={setShowUploadModal}
          onUploadSuccess={handleUploadSuccess}
        />

        <PrimaryResumeModal
          resumes={resumes}
          open={showPrimaryModal}
          onOpenChange={setShowPrimaryModal}
          onPrimaryChange={loadResumes}
        />
      </div>
    </ProtectedRoute>
  )
}
