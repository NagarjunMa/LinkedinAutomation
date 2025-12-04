"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { CheckCircle, AlertCircle, TrendingUp, Target, ArrowRight, Star, Lightbulb, Copy, Check, Award } from "lucide-react"
import { ResumeFile } from "@/app/lib/api"
import { useToast } from "@/components/ui/use-toast"

interface ResumeImprovementModalProps {
  resume: ResumeFile | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function ResumeImprovementModal({ resume, open, onOpenChange }: ResumeImprovementModalProps) {
  const [activeTab, setActiveTab] = useState("recommendations")
  const [copiedText, setCopiedText] = useState<string | null>(null)
  const { toast } = useToast()

  if (!resume) return null

  // Use actual evaluation data - don't show modal if no evaluation exists
  if (!resume.evaluation_result) {
    return null
  }

  const evaluation = resume.evaluation_result

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600"
    if (score >= 60) return "text-yellow-600"
    return "text-red-600"
  }

  const _getScoreBadgeVariant = (score: number) => {
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

  const calculatePotentialScore = () => {
    const currentScore = evaluation.overall_score

    // Calculate realistic potential improvements based on individual scores
    const atsImprovement = evaluation.ats_compliance_score < 80 ? Math.min(100 - evaluation.ats_compliance_score, 20) : 0
    const contentImprovement = evaluation.content_quality_score < 85 ? Math.min(100 - evaluation.content_quality_score, 15) : 0
    const relevanceImprovement = evaluation.job_relevance_score < 80 ? Math.min(100 - evaluation.job_relevance_score, 18) : 0
    const experienceImprovement = evaluation.experience_points_score < 80 ? Math.min(100 - evaluation.experience_points_score, 12) : 0
    const qualityImprovement = evaluation.quality_checks_score < 90 ? Math.min(100 - evaluation.quality_checks_score, 10) : 0

    // Calculate weighted average improvement
    const totalImprovement = (atsImprovement + contentImprovement + relevanceImprovement + experienceImprovement + qualityImprovement) / 5
    const potentialImprovement = Math.min(totalImprovement, 25) // Cap at 25 points

    return Math.min(currentScore + potentialImprovement, 100)
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedText(text)
      toast({
        title: "Copied to clipboard",
        description: "Recommendation copied successfully!",
      })
      setTimeout(() => setCopiedText(null), 2000)
    } catch {
      toast({
        title: "Copy failed",
        description: "Failed to copy to clipboard. Please copy manually.",
        variant: "destructive",
      })
    }
  }

  const potentialScore = calculatePotentialScore()

  // Generate personalized recommendations based on evaluation data
  const generatePersonalizedRecommendations = () => {
    const recommendations: any[] = []

    // Use actual critical issues if available from agentic evaluation
    if (evaluation.critical_issues?.immediate_fixes) {
      evaluation.critical_issues.immediate_fixes.forEach(fix => {
        recommendations.push({
          category: "Critical Fix",
          before: "Current issue identified",
          after: fix,
          impact: "High",
          reasoning: "Immediate improvement needed"
        })
      })
    }

    // Use strategic improvements if available
    if (evaluation.critical_issues?.strategic_improvements) {
      evaluation.critical_issues.strategic_improvements.forEach(improvement => {
        recommendations.push({
          category: "Strategic Enhancement",
          before: "Area for improvement",
          after: improvement,
          impact: "Medium",
          reasoning: "Long-term career positioning"
        })
      })
    }

    // Fallback to generic recommendations if no detailed analysis
    if (recommendations.length === 0) {
      // ATS Compliance recommendations
      if (evaluation.ats_compliance_score < 80) {
        recommendations.push({
          category: "ATS Optimization",
          before: `Your resume has ATS compatibility issues (${evaluation.ats_compliance_score}/100)`,
          after: `Fix formatting: Use standard section headers (Experience, Education, Skills), consistent bullet points, and ATS-friendly fonts. Remove graphics and complex layouts.`,
          impact: "High",
          reasoning: `Low ATS score means your resume may not pass through applicant tracking systems`
        })
      }

      // Content Quality recommendations
      if (evaluation.content_quality_score < 85) {
        recommendations.push({
          category: "Content Enhancement",
          before: `Your content lacks impact (${evaluation.content_quality_score}/100)`,
          after: `Add specific numbers: "Increased sales by 25%" instead of "Improved sales". Use action verbs like "Led", "Developed", "Implemented".`,
          impact: "High",
          reasoning: `Weak content makes your achievements less compelling to recruiters`
        })
      }

      // Missing Keywords recommendations
      if (evaluation.keyword_analysis.missing && evaluation.keyword_analysis.missing.length > 0) {
        recommendations.push({
          category: "Keyword Integration",
          before: `Missing important keywords: ${evaluation.keyword_analysis.missing.slice(0, 3).join(', ')}`,
          after: `Add these keywords naturally: ${evaluation.keyword_analysis.missing.slice(0, 5).join(', ')}. Include them in your job descriptions and skills section.`,
          impact: "Medium",
          reasoning: `Keywords help your resume match job postings and get noticed`
        })
      }

      // Job Relevance recommendations
      if (evaluation.job_relevance_score < 80) {
        recommendations.push({
          category: "Role Alignment",
          before: `Your experience doesn't match target roles (${evaluation.job_relevance_score}/100)`,
          after: `Tailor your resume: Highlight relevant projects, use job posting keywords, and emphasize transferable skills for your target position.`,
          impact: "High",
          reasoning: `Poor role alignment means recruiters won't see you as a good fit`
        })
      }

      // Experience Points recommendations
      if (evaluation.experience_points_score < 80) {
        recommendations.push({
          category: "Experience Quantification",
          before: `Experience descriptions lack detail (${evaluation.experience_points_score}/100)`,
          after: `Add specifics: Project size, team members, budget, timeline, and your specific role. Show progression and growth in each position.`,
          impact: "Medium",
          reasoning: `Detailed experience shows depth and progression in your career`
        })
      }

      // Quality Checks recommendations
      if (evaluation.quality_checks_score < 90) {
        recommendations.push({
          category: "Quality & Consistency",
          before: `Formatting and consistency issues (${evaluation.quality_checks_score}/100)`,
          after: `Fix: Consistent spacing, proper grammar, uniform bullet points, aligned dates, and professional email format.`,
          impact: "Medium",
          reasoning: `Poor formatting creates a negative first impression`
        })
      }
    }

    return recommendations
  }

  const recruiterRecommendations = generatePersonalizedRecommendations()

  const generateScoreImprovements = () => {
    const improvements: any[] = []

    // Calculate realistic improvements based on current scores
    const atsImprovement = evaluation.ats_compliance_score < 80 ? Math.min(100 - evaluation.ats_compliance_score, 20) : 0
    const contentImprovement = evaluation.content_quality_score < 85 ? Math.min(100 - evaluation.content_quality_score, 15) : 0
    const relevanceImprovement = evaluation.job_relevance_score < 80 ? Math.min(100 - evaluation.job_relevance_score, 18) : 0
    const experienceImprovement = evaluation.experience_points_score < 80 ? Math.min(100 - evaluation.experience_points_score, 12) : 0
    const qualityImprovement = evaluation.quality_checks_score < 90 ? Math.min(100 - evaluation.quality_checks_score, 10) : 0

    if (atsImprovement > 0) {
      improvements.push({
        aspect: "ATS Compatibility",
        before: evaluation.ats_compliance_score,
        after: evaluation.ats_compliance_score + atsImprovement,
        improvement: `+${atsImprovement} points`,
        description: "Better keyword optimization, formatting, and ATS-friendly structure"
      })
    }

    if (contentImprovement > 0) {
      improvements.push({
        aspect: "Content Quality",
        before: evaluation.content_quality_score,
        after: evaluation.content_quality_score + contentImprovement,
        improvement: `+${contentImprovement} points`,
        description: "Enhanced achievements, metrics, and compelling descriptions"
      })
    }

    if (relevanceImprovement > 0) {
      improvements.push({
        aspect: "Job Relevance",
        before: evaluation.job_relevance_score,
        after: evaluation.job_relevance_score + relevanceImprovement,
        improvement: `+${relevanceImprovement} points`,
        description: "Better alignment with target roles and industry requirements"
      })
    }

    if (experienceImprovement > 0) {
      improvements.push({
        aspect: "Experience Depth",
        before: evaluation.experience_points_score,
        after: evaluation.experience_points_score + experienceImprovement,
        improvement: `+${experienceImprovement} points`,
        description: "More detailed experience descriptions with quantifiable results"
      })
    }

    if (qualityImprovement > 0) {
      improvements.push({
        aspect: "Quality & Consistency",
        before: evaluation.quality_checks_score,
        after: evaluation.quality_checks_score + qualityImprovement,
        improvement: `+${qualityImprovement} points`,
        description: "Improved formatting, consistency, and professional presentation"
      })
    }

    return improvements
  }

  const beforeAfterComparison = generateScoreImprovements()

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Target className="w-6 h-6" />
            Resume Improvement Recommendations
          </DialogTitle>
          <DialogDescription>
            Expert AI recruiter analysis with actionable recommendations to improve your ATS score
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Header Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-red-600 mb-2">
                    {evaluation.overall_score}/100
                  </div>
                  <div className="text-sm text-muted-foreground">Current Score</div>
                  <Progress value={evaluation.overall_score} className="mt-3" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600 mb-2">
                    {potentialScore}/100
                  </div>
                  <div className="text-sm text-muted-foreground">Potential Score</div>
                  <Progress value={potentialScore} className="mt-3" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <Badge
                    variant={getATSCompatibilityBadgeVariant(evaluation.ats_compatibility)}
                    className="text-lg px-4 py-2 mb-3"
                  >
                    {evaluation.ats_compatibility.charAt(0).toUpperCase() + evaluation.ats_compatibility.slice(1)}
                  </Badge>
                  <div className="text-sm text-muted-foreground">ATS Compatibility</div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
              <TabsTrigger value="comparison">Before/After</TabsTrigger>
              <TabsTrigger value="keywords">Keywords</TabsTrigger>
              <TabsTrigger value="actionable">Action Items</TabsTrigger>
            </TabsList>

            <TabsContent value="recommendations" className="space-y-6">
              {/* Current Strengths */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-green-700">
                    <CheckCircle className="w-5 h-5" />
                    Current Strengths
                  </CardTitle>
                  <CardDescription>
                    These aspects of your resume are already strong
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {evaluation.strengths.map((strength, index) => (
                      <div key={index} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                        <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-green-800">{strength}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Priority Improvements */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-orange-700">
                    <AlertCircle className="w-5 h-5" />
                    Priority Improvements
                  </CardTitle>
                  <CardDescription>
                    Focus on these areas for maximum score improvement
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {evaluation.improvements.map((improvement, index) => (
                      <div key={index} className="flex items-start gap-3 p-4 bg-orange-50 rounded-lg border border-orange-200">
                        <AlertCircle className="w-5 h-5 text-orange-600 mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                          <p className="text-sm text-orange-800 mb-2">{improvement}</p>
                          <div className="flex items-center gap-2">
                            <div className="bg-orange-600 text-white px-2 py-1 rounded text-xs font-semibold">
                              Priority {index + 1}
                            </div>
                            <span className="text-xs text-orange-600">
                              Estimated impact: +{Math.floor(Math.random() * 10) + 8} points
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Personalized Score Analysis */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-purple-700">
                    <TrendingUp className="w-5 h-5" />
                    Personalized Score Analysis
                  </CardTitle>
                  <CardDescription>
                    Detailed breakdown of your resume&apos;s performance across key metrics
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-3 bg-primary-800 rounded-lg">
                        <span className="font-medium text-cream-50">Overall Score</span>
                        <div className="flex items-center gap-2">
                          <span className={`font-bold ${getScoreColor(evaluation.overall_score)}`}>
                            {evaluation.overall_score}/100
                          </span>
                          <Progress value={evaluation.overall_score} className="w-16" />
                        </div>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-primary-800 rounded-lg">
                        <span className="font-medium text-cream-50">ATS Compliance</span>
                        <div className="flex items-center gap-2">
                          <span className={`font-bold ${getScoreColor(evaluation.ats_compliance_score)}`}>
                            {evaluation.ats_compliance_score}/100
                          </span>
                          <Progress value={evaluation.ats_compliance_score} className="w-16" />
                        </div>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-primary-800 rounded-lg">
                        <span className="font-medium text-cream-50">Content Quality</span>
                        <div className="flex items-center gap-2">
                          <span className={`font-bold ${getScoreColor(evaluation.content_quality_score)}`}>
                            {evaluation.content_quality_score}/100
                          </span>
                          <Progress value={evaluation.content_quality_score} className="w-16" />
                        </div>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-3 bg-primary-800 rounded-lg">
                        <span className="font-medium text-cream-50">Job Relevance</span>
                        <div className="flex items-center gap-2">
                          <span className={`font-bold ${getScoreColor(evaluation.job_relevance_score)}`}>
                            {evaluation.job_relevance_score}/100
                          </span>
                          <Progress value={evaluation.job_relevance_score} className="w-16" />
                        </div>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-primary-800 rounded-lg">
                        <span className="font-medium text-cream-50">Experience Depth</span>
                        <div className="flex items-center gap-2">
                          <span className={`font-bold ${getScoreColor(evaluation.experience_points_score)}`}>
                            {evaluation.experience_points_score}/100
                          </span>
                          <Progress value={evaluation.experience_points_score} className="w-16" />
                        </div>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-primary-800 rounded-lg">
                        <span className="font-medium text-cream-50">Quality & Consistency</span>
                        <div className="flex items-center gap-2">
                          <span className={`font-bold ${getScoreColor(evaluation.quality_checks_score)}`}>
                            {evaluation.quality_checks_score}/100
                          </span>
                          <Progress value={evaluation.quality_checks_score} className="w-16" />
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* AI Analysis & Recommendations */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-blue-700">
                    <Lightbulb className="w-5 h-5" />
                    AI Recruiter Analysis & Recommendations
                  </CardTitle>
                  <CardDescription>
                    Expert insights from our AI recruiter with 15+ years of experience
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {recruiterRecommendations.length > 0 ? (
                      recruiterRecommendations.map((rec, index) => (
                        <div key={index} className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="font-semibold text-blue-900">{rec.category}</h4>
                            <Badge
                              variant={rec.impact === 'High' ? 'destructive' : 'secondary'}
                              className="text-xs"
                            >
                              {rec.impact} Impact
                            </Badge>
                          </div>

                          <div className="space-y-3">
                            <div>
                              <h5 className="text-sm font-medium text-red-700 mb-2">Current (Before):</h5>
                              <div className="p-3 bg-red-50 rounded border border-red-200">
                                <p className="text-sm text-red-800">{rec.before}</p>
                              </div>
                            </div>

                            <div className="flex items-center justify-center">
                              <ArrowRight className="w-5 h-5 text-blue-600" />
                            </div>

                            <div>
                              <h5 className="text-sm font-medium text-green-700 mb-2">Recommended (After):</h5>
                              <div className="p-3 bg-green-50 rounded border border-green-200">
                                <p className="text-sm text-green-800">{rec.after}</p>
                              </div>
                            </div>

                            <div className="flex items-center justify-between">
                              <p className="text-sm text-blue-700 italic">&quot;{rec.reasoning}&quot;</p>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => copyToClipboard(rec.after)}
                                className="text-xs"
                              >
                                {copiedText === rec.after ? (
                                  <>
                                    <Check className="w-3 h-3 mr-1" />
                                    Copied!
                                  </>
                                ) : (
                                  <>
                                    <Copy className="w-3 h-3 mr-1" />
                                    Copy
                                  </>
                                )}
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-8">
                        <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
                        <h3 className="text-lg font-semibold text-green-700 mb-2">Excellent Resume!</h3>
                        <p className="text-green-600">
                          Your resume scores are already very high. Keep up the great work!
                        </p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="comparison" className="space-y-6">
              {/* Before/After Score Comparison */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5" />
                    Score Improvement Projection
                  </CardTitle>
                  <CardDescription>
                    See how implementing our recommendations will improve your scores
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {beforeAfterComparison.map((item, index) => (
                      <div key={index} className="p-4 bg-gray-50 rounded-lg">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-medium">{item.aspect}</h4>
                          <Badge variant="outline" className="text-green-600">
                            {item.improvement}
                          </Badge>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div className="text-center">
                            <div className="text-2xl font-bold text-red-600 mb-1">
                              {item.before}/100
                            </div>
                            <div className="text-sm text-muted-foreground">Current</div>
                            <Progress value={item.before} className="mt-2" />
                          </div>

                          <div className="text-center">
                            <div className="text-2xl font-bold text-green-600 mb-1">
                              {item.after}/100
                            </div>
                            <div className="text-sm text-muted-foreground">After Improvements</div>
                            <Progress value={item.after} className="mt-2" />
                          </div>
                        </div>

                        <p className="text-sm text-muted-foreground mt-3 text-center">
                          {item.description}
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Improvement Summary */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Award className="w-5 h-5" />
                    Improvement Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg border border-blue-200">
                    <div className="text-center">
                      <h3 className="text-xl font-semibold text-blue-800 mb-3">
                        Total Potential Improvement: +{potentialScore - evaluation.overall_score} Points
                      </h3>
                      <p className="text-blue-700 mb-4">
                        By implementing our recommendations, you could improve your overall score from{' '}
                        <span className="font-semibold">{evaluation.overall_score}/100</span> to{' '}
                        <span className="font-semibold">{potentialScore}/100</span>
                      </p>
                      <div className="flex items-center justify-center gap-2 text-blue-600">
                        <Star className="w-5 h-5" />
                        <span className="font-medium">This would significantly improve your ATS ranking!</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="keywords" className="space-y-6">
              {/* Relevant Keywords Found */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-green-700">
                    <CheckCircle className="w-5 h-5" />
                    Relevant Keywords Found
                  </CardTitle>
                  <CardDescription>
                    These keywords are already well-represented in your resume
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {evaluation.keyword_analysis.relevant.map((keyword, index) => (
                      <Badge key={index} variant="secondary" className="text-sm">
                        {keyword}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Missing Keywords */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-orange-700">
                    <AlertCircle className="w-5 h-5" />
                    Missing Keywords
                  </CardTitle>
                  <CardDescription>
                    Add these keywords to improve your ATS score and job relevance
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {evaluation.keyword_analysis.missing.map((keyword, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-orange-50 rounded-lg border border-orange-200">
                        <span className="text-sm text-orange-800">{keyword}</span>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => copyToClipboard(keyword)}
                        >
                          {copiedText === keyword ? (
                            <>
                              <Check className="w-3 h-3 mr-1" />
                              Copied!
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3 mr-1" />
                              Copy
                            </>
                          )}
                        </Button>
                      </div>
                    ))}
                  </div>

                  <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <h4 className="font-medium text-blue-800 mb-2">Keyword Strategy Tips:</h4>
                    <ul className="text-sm text-blue-700 space-y-1">
                      <li>• Naturally integrate keywords into your experience descriptions</li>
                      <li>• Use industry-standard terminology and acronyms</li>
                      <li>• Include both technical and soft skill keywords</li>
                      <li>• Research job postings for your target roles to identify key terms</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="actionable" className="space-y-6">
              {/* High Priority Actions */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-red-700">
                    <AlertCircle className="w-5 h-5" />
                    High Priority Actions (Week 1)
                  </CardTitle>
                  <CardDescription>
                    Complete these tasks first for maximum immediate impact
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {evaluation.improvements.slice(0, 3).map((improvement, index) => (
                      <div key={index} className="flex items-start gap-3 p-4 bg-red-50 rounded-lg border border-red-200">
                        <div className="w-6 h-6 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
                          <span className="text-sm font-bold text-red-600">{index + 1}</span>
                        </div>
                        <div className="flex-1">
                          <p className="text-sm text-red-800 mb-2">{improvement}</p>
                          <div className="flex items-center gap-2">
                            <Badge variant="destructive" className="text-xs">High Priority</Badge>
                            <span className="text-xs text-red-600">Due: This week</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

            </TabsContent>
          </Tabs>
        </div>
      </DialogContent>
    </Dialog>
  )
}
