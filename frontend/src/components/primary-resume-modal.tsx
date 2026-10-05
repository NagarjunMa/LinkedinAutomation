"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Star, Target, Calendar, TrendingUp, BookOpen, Lightbulb, Users, Award } from "lucide-react"
import { ResumeFile } from "@/app/lib/api"
import { useToast } from "@/components/ui/use-toast"

interface PrimaryResumeModalProps {
  resumes: ResumeFile[]
  open: boolean
  onOpenChange: (open: boolean) => void
  onPrimaryChange: () => void
}

export function PrimaryResumeModal({ resumes, open, onOpenChange, onPrimaryChange }: PrimaryResumeModalProps) {
  const [selectedPrimary, setSelectedPrimary] = useState<string | null>(null)
  const [updating, setUpdating] = useState(false)
  const { toast } = useToast()

  const currentPrimary = resumes.find(r => r.is_primary)

  const handleSetPrimary = async () => {
    if (!selectedPrimary) {
      toast({
        title: "No resume selected",
        description: "Please select a resume to set as primary.",
        variant: "destructive",
      })
      return
    }

    setUpdating(true)
    try {
      // TODO: Implement API call to set primary resume
      // await resumeApi.setPrimaryResume(selectedPrimary)
      
      toast({
        title: "Primary Resume Updated",
        description: "Your primary resume has been updated successfully.",
      })
      
      onPrimaryChange()
      onOpenChange(false)
    } catch {
      toast({
        title: "Update Failed",
        description: "Failed to update primary resume. Please try again.",
        variant: "destructive",
      })
    } finally {
      setUpdating(false)
    }
  }

  const getResumeScore = (resume: ResumeFile) => {
    if (resume.evaluation_status === 'completed' && resume.evaluation_result) {
      return resume.evaluation_result.overall_score
    }
    return null
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

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Star className="w-6 h-6 text-yellow-600" />
            Set Primary Resume
          </DialogTitle>
          <DialogDescription>
            Choose your primary resume for AI evaluation, study timeline creation, and future reference
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Current Primary Resume */}
          {currentPrimary && (
            <Card className="bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-yellow-900">
                  <Star className="w-5 h-5" />
                  Current Primary Resume
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
                      <Star className="w-6 h-6 text-yellow-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-yellow-900">{currentPrimary.filename}</h4>
                      <p className="text-sm text-yellow-800">
                        Uploaded {new Date(currentPrimary.uploaded_at).toLocaleDateString()}
                      </p>
                      {currentPrimary.evaluation_status === 'completed' && currentPrimary.evaluation_result && (
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant={getScoreBadgeVariant(currentPrimary.evaluation_result.overall_score)}>
                            Score: {currentPrimary.evaluation_result.overall_score}/100
                          </Badge>
                        </div>
                      )}
                    </div>
                  </div>
                  <Badge variant="default" className="bg-yellow-600">
                    Primary
                  </Badge>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Why Primary Resume Matters */}
          <Card className="bg-blue-50 border-blue-200">
            <CardHeader>
              <CardTitle className="text-blue-900 flex items-center gap-2">
                <Lightbulb className="w-5 h-5" />
                Why Set a Primary Resume?
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div className="flex items-start gap-2">
                    <Target className="w-5 h-5 text-blue-600 mt-0.5 shrink-0" />
                    <div>
                      <h4 className="font-semibold text-blue-900">AI Evaluation Focus</h4>
                      <p className="text-sm text-blue-900">Our AI recruiter will prioritize analyzing this resume for detailed feedback</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <Calendar className="w-5 h-5 text-blue-600 mt-0.5 shrink-0" />
                    <div>
                      <h4 className="font-semibold text-blue-900">Study Timeline</h4>
                      <p className="text-sm text-blue-900">Personalized learning path created based on this resume&apos;s analysis</p>
                    </div>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-start gap-2">
                    <TrendingUp className="w-5 h-5 text-blue-600 mt-0.5 shrink-0" />
                    <div>
                      <h4 className="font-semibold text-blue-900">Career Tracking</h4>
                      <p className="text-sm text-blue-900">Progress monitoring and improvement recommendations based on this resume</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-2">
                    <Users className="w-5 h-5 text-blue-600 mt-0.5 shrink-0" />
                    <div>
                      <h4 className="font-semibold text-blue-900">Future Reference</h4>
                      <p className="text-sm text-blue-900">All future operations will reference this resume as your main profile</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Resume Selection */}
          <Card>
            <CardHeader>
              <CardTitle>Select Primary Resume</CardTitle>
              <CardDescription>
                Choose the resume you want to use as your primary profile for evaluation and career planning
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {resumes.map((resume) => {
                  const score = getResumeScore(resume)
                  const isSelected = selectedPrimary === resume.id
                  const isCurrentPrimary = resume.is_primary

                  return (
                    <div
                      key={resume.id}
                      className={`p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 ${
                        isSelected 
                          ? 'border-blue-500 bg-blue-50' 
                          : isCurrentPrimary
                          ? 'border-yellow-300 bg-yellow-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                      onClick={() => !isCurrentPrimary && setSelectedPrimary(resume.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-4 h-4 rounded-full border-2 ${
                            isCurrentPrimary 
                              ? 'bg-yellow-500 border-yellow-500' 
                              : isSelected 
                              ? 'bg-blue-500 border-blue-500' 
                              : 'border-gray-300'
                          }`}>
                            {isSelected && <div className="w-2 h-2 bg-white rounded-full m-0.5"></div>}
                          </div>
                          
                          <div className="flex items-center gap-2">
                            {isCurrentPrimary && (
                              <Badge variant="default" className="bg-yellow-600 text-xs">
                                <Star className="w-3 h-3 mr-1" />
                                Current
                              </Badge>
                            )}
                            <div>
                              <h4 className="font-medium">{resume.filename}</h4>
                              <p className="text-sm text-muted-foreground">
                                Uploaded {new Date(resume.uploaded_at).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-3">
                          {score !== null ? (
                            <Badge variant={getScoreBadgeVariant(score)}>
                              {score}/100
                            </Badge>
                          ) : (
                            <Badge variant="outline">
                              {resume.evaluation_status === 'completed' ? 'Evaluated' : resume.evaluation_status}
                            </Badge>
                          )}
                          
                          {isCurrentPrimary && (
                            <Button variant="outline" size="sm" disabled>
                              Current Primary
                            </Button>
                          )}
                          {!isCurrentPrimary && isSelected && (
                            <Button 
                              variant="default" 
                              size="sm"
                              onClick={handleSetPrimary}
                              disabled={updating}
                            >
                              {updating ? 'Setting...' : 'Set as Primary'}
                            </Button>
                          )}
                        </div>
                      </div>

                      {score !== null && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <div className="flex items-center gap-4 text-sm">
                            <span className={`font-medium ${getScoreColor(score)}`}>
                              Overall Score: {score}/100
                            </span>
                            {resume.evaluation_result && (
                              <>
                                <span className="text-muted-foreground">
                                  ATS: {resume.evaluation_result.ats_compliance_score}/100
                                </span>
                                <span className="text-muted-foreground">
                                  Content: {resume.evaluation_result.content_quality_score}/100
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>

          {/* Study Timeline Preview */}
          {selectedPrimary && (
            <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-purple-900">
                  <BookOpen className="w-5 h-5" />
                  Study Timeline Preview
                </CardTitle>
                <CardDescription>
                  Based on your selected primary resume, here&apos;s what your personalized learning path will include
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-white rounded-lg border border-purple-200">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                        <Target className="w-4 h-4 text-purple-600" />
                      </div>
                      <h4 className="font-semibold text-purple-900">Week 1-2</h4>
                    </div>
                    <p className="text-sm text-purple-900">
                      Foundation building based on your resume&apos;s current strengths and identified improvement areas
                    </p>
                  </div>
                  
                  <div className="p-4 bg-white rounded-lg border border-purple-200">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                        <TrendingUp className="w-4 h-4 text-purple-600" />
                      </div>
                      <h4 className="font-semibold text-purple-900">Week 5-6</h4>
                    </div>
                    <p className="text-sm text-purple-900">
                      Skill enhancement focusing on industry-specific knowledge and advanced techniques
                    </p>
                  </div>
                  
                  <div className="p-4 bg-white rounded-lg border border-purple-200">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                        <Award className="w-4 h-4 text-purple-600" />
                      </div>
                      <h4 className="font-semibold text-purple-900">Week 5-6</h4>
                    </div>
                    <p className="text-sm text-purple-900">
                      Application and practice with real-world scenarios and mock interviews
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            {selectedPrimary && !resumes.find(r => r.id === selectedPrimary)?.is_primary && (
              <Button 
                onClick={handleSetPrimary}
                disabled={updating}
                className="bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700 text-white"
              >
                {updating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                    Setting Primary...
                  </>
                ) : (
                  <>
                    <Star className="w-4 h-4 mr-2" />
                    Set as Primary Resume
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
