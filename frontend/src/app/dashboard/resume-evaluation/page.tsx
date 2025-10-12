"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { CheckCircle, AlertCircle, TrendingUp, FileText, Target, Zap, Upload, Star, Clock, Award, TrendingDown, Lightbulb, Users, Calendar } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { resumeApi, ResumeFile, ResumeEvaluation } from "@/app/lib/api"
import { ResumeImprovementModal } from "@/components/resume-improvement-modal"
import { EnhancedResumeAnalysis } from "@/components/enhanced-resume-analysis"
import { ResumeUploadModal } from "@/components/resume-upload-modal"
import { PrimaryResumeModal } from "@/components/primary-resume-modal"
import { ResumeListDropdown } from "@/components/resume-list-dropdown"
import { RealTimeResumeLoader } from "@/components/real-time-resume-loader"

export default function ResumeEvaluationPage() {
  const [resumes, setResumes] = useState<ResumeFile[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedResume, setSelectedResume] = useState<ResumeFile | null>(null)
  const [showEnhancedAnalysis, setShowEnhancedAnalysis] = useState(false)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showPrimaryModal, setShowPrimaryModal] = useState(false)
  const [evaluatingResume, setEvaluatingResume] = useState<string | null>(null)
  const [showEvaluationLoader, setShowEvaluationLoader] = useState(false)
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
    setShowEvaluationLoader(true)

    try {
      // Trigger evaluation via API
      await resumeApi.evaluateResume(resumeId)
      toast({
        title: "Evaluation Started",
        description: "AI is analyzing your resume with advanced multi-agent system.",
      })
    } catch (error) {
      setShowEvaluationLoader(false)
      toast({
        title: "Evaluation Failed",
        description: "Failed to start evaluation. Please try again.",
        variant: "destructive",
      })
      setEvaluatingResume(null)
    }
  }

  const handleEvaluationComplete = () => {
    setShowEvaluationLoader(false)
    setEvaluatingResume(null)
    loadResumes()
    toast({
      title: "Evaluation Complete! 🎉",
      description: "Your resume has been analyzed. Check the results below.",
    })
  }

  const handleUploadSuccess = (resume: ResumeFile) => {
    setResumes(prev => [resume, ...prev])
    toast({
      title: "Resume Uploaded Successfully! 🎉",
      description: "Your resume has been uploaded and is ready for AI evaluation.",
    })
  }

  const handleEvaluationStart = (resumeId: string) => {
    setEvaluatingResume(resumeId)
    setShowEvaluationLoader(true)
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
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading resumes...</p>
          </div>
        </div>
      </div>
    )
  }

  const latestResume = getLatestResume()
  const primaryResume = getPrimaryResume()

  return (
    <div className="min-h-screen bg-primary-950">
      {/* Constrain content width for large monitors */}
      <div className="max-w-7xl mx-auto py-4 sm:py-6 lg:py-8 px-4 sm:px-6 lg:px-8">
        {/* Header with Latest Resume Summary */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 sm:mb-6 gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl lg:text-4xl xl:text-4xl 2xl:text-4xl font-bold tracking-tight text-gradient-warm">
                Resume Evaluation Center
              </h1>
              <p className="text-sm sm:text-base lg:text-xl xl:text-xl 2xl:text-xl text-cream-200 mt-2">
                Expert AI-powered resume analysis by experienced recruiters
              </p>
            </div>
          <Button
            onClick={() => setShowUploadModal(true)}
            size="lg"
            className="bg-gradient-warm hover:bg-gradient-gold text-white glow-orange hover:glow-gold transition-all duration-300 w-full sm:w-auto"
          >
            <Upload className="w-5 h-5 mr-2" />
            Upload New Resume
          </Button>
        </div>

        {/* Latest Resume Status Card */}
        {latestResume && (
          <Card className="bg-gradient-card border-accent-500/20 mb-6 glow-orange">
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                <div className="text-center">
                  <div className="flex items-center justify-center gap-2 mb-3">
                    <Clock className="w-6 h-6 text-blue-600" />
                    <h3 className="text-lg font-semibold text-cream-50">Latest Resume</h3>
                  </div>
                  <div className="text-2xl font-bold text-accent-400 mb-2">
                    {latestResume.filename}
                  </div>
                  <p className="text-cream-300 text-sm">
                    Uploaded {new Date(latestResume.uploaded_at).toLocaleDateString()}
                  </p>
                </div>

                <div className="text-center">
                  <div className="flex items-center justify-center gap-2 mb-3">
                    <Target className="w-6 h-6 text-green-600" />
                    <h3 className="text-lg font-semibold text-cream-50">Evaluation Status</h3>
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
                    <div className="space-y-3">
                      <div className="text-2xl font-bold text-green-400">
                        Score: {latestResume.evaluation_result.overall_score}/100
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedResume(latestResume)
                          setShowEnhancedAnalysis(true)
                        }}
                        className="w-full"
                      >
                        View Detailed Analysis
                      </Button>
                    </div>
                  )}
                </div>

                <div className="text-center">
                  <div className="flex items-center justify-center gap-2 mb-3">
                    <Star className="w-6 h-6 text-yellow-600" />
                    <h3 className="text-lg font-semibold text-cream-50">Primary Resume</h3>
                  </div>
                  {primaryResume ? (
                    <div>
                      <div className="text-lg font-semibold text-gold-400 mb-2">
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
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-2 2xl:grid-cols-2 gap-4 sm:gap-6 mb-6 sm:mb-8 max-w-4xl mx-auto">
          <Card className="premium-card hover:scale-105 transition-all duration-300 cursor-pointer border-2 border-transparent hover:border-accent-500">
            <CardContent className="pt-6 text-center">
              <div className="w-16 h-16 bg-gradient-warm rounded-full flex items-center justify-center mx-auto mb-4 glow-orange">
                <Target className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-semibold mb-2 text-cream-50">Evaluate Resume</h3>
              <p className="text-sm text-cream-200 mb-4">
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

          <Card className="premium-card hover:scale-105 transition-all duration-300 cursor-pointer border-2 border-transparent hover:border-green-400">
            <CardContent className="pt-6 text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-green-600 rounded-full flex items-center justify-center mx-auto mb-4 glow-green">
                <Upload className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-semibold mb-2 text-cream-50">Upload Resume</h3>
              <p className="text-sm text-cream-200 mb-4">
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
        </div>
      </div>

      {/* Resume List with Dropdown */}
      <ResumeListDropdown
        resumes={resumes}
        onViewDetailedAnalysis={(resume) => {
          setSelectedResume(resume)
          setShowEnhancedAnalysis(false) // Use regular modal by default
        }}
        onViewEnhancedAnalysis={(resume) => {
          setSelectedResume(resume)
          setShowEnhancedAnalysis(true) // Use enhanced analysis
        }}
        onDownloadResume={(resumeId) => window.open(`/api/v1/resumes/${resumeId}/download`, '_blank')}
        onEvaluateResume={handleEvaluateResume}
        evaluatingResume={evaluatingResume}
        onResumeDeleted={loadResumes}
      />

      {/* Modals */}
      <ResumeImprovementModal
        resume={selectedResume}
        open={!!selectedResume && !showEnhancedAnalysis}
        onOpenChange={(open) => !open && setSelectedResume(null)}
      />

      <EnhancedResumeAnalysis
        resume={selectedResume}
        open={showEnhancedAnalysis}
        onOpenChange={(open) => {
          setShowEnhancedAnalysis(open)
          if (!open) setSelectedResume(null)
        }}
      />

      <ResumeUploadModal
        open={showUploadModal}
        onOpenChange={setShowUploadModal}
        onUploadSuccess={handleUploadSuccess}
        onEvaluationStart={handleEvaluationStart}
      />

      <PrimaryResumeModal
        resumes={resumes}
        open={showPrimaryModal}
        onOpenChange={setShowPrimaryModal}
        onPrimaryChange={loadResumes}
      />

      {/* Real-Time Evaluation Loader */}
      <RealTimeResumeLoader
        isVisible={showEvaluationLoader}
        resumeId={evaluatingResume || undefined}
        onComplete={handleEvaluationComplete}
      />
      </div>
    </div>
  )
}
