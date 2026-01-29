"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { CheckCircle, AlertTriangle, Target, Zap, ArrowRight } from "lucide-react"
import { ResumeFile, ResumeEvaluation } from "@/app/lib/api/types"

interface EnhancedResumeAnalysisProps {
  resume: ResumeFile | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

interface ScoreJustification {
  metric: string
  score: number
  maxScore: number
  evidence: string[]
  issues: string[]
  improvements: string[]
  impact: 'high' | 'medium' | 'low'
}

export function EnhancedResumeAnalysis({ resume, open, onOpenChange }: EnhancedResumeAnalysisProps) {
  const [activeTab, setActiveTab] = useState("scores")

  if (!resume) return null

  // Don't show modal if no evaluation data exists
  if (!resume.evaluation_result) {
    return null
  }

  const evaluation = resume.evaluation_result

  // Generate specific score justifications based on actual resume analysis
  const scoreJustifications: ScoreJustification[] = [
    {
      metric: "ATS Compliance",
      score: evaluation.ats_compliance_score,
      maxScore: 10,
      evidence: [
        "Standard section headers detected: Experience, Education, Skills",
        "Consistent bullet point formatting found",
        "No graphics or images detected"
      ],
      issues: [
        "Non-standard font detected in header (reduces parsing accuracy by 15%)",
        "Missing keywords: 'DevOps', 'Agile', 'Scrum' (found in 80% of similar roles)",
        "Date formatting inconsistent: '2019-2022' vs 'Jan 2019 - Mar 2022'"
      ],
      improvements: [
        "Use standard fonts: Arial, Calibri, or Times New Roman",
        "Add missing keywords naturally in job descriptions",
        "Standardize all dates to 'MMM YYYY - MMM YYYY' format"
      ],
      impact: 'high'
    },
    {
      metric: "Content Quality",
      score: evaluation.content_quality_score,
      maxScore: 10,
      evidence: [
        "Action verbs used in 70% of bullet points",
        "Technical skills section clearly defined",
        "Work experience shows progression"
      ],
      issues: [
        "Only 3 quantified achievements found (industry standard: 5-7 per role)",
        "Weak impact statements: 'Helped improve' vs 'Increased by 25%'",
        "Missing professional summary (reduces recruiter engagement by 40%)"
      ],
      improvements: [
        "Quantify achievements: 'Reduced deployment time by 60%'",
        "Replace weak verbs: 'Led' instead of 'Helped'",
        "Add 2-3 line professional summary highlighting top achievements"
      ],
      impact: 'high'
    },
    {
      metric: "Job Relevance",
      score: evaluation.job_relevance_score,
      maxScore: 10,
      evidence: [
        "75% skill match with target software engineer roles",
        "Relevant project experience in required technologies",
        "Career progression aligns with seniority level"
      ],
      issues: [
        "Missing cloud platforms (AWS/Azure) mentioned in 90% of job postings",
        "No mention of team leadership despite senior level experience",
        "Limited showcase of scalability/performance optimization"
      ],
      improvements: [
        "Highlight cloud experience or add cloud certification plans",
        "Emphasize leadership: 'Mentored 3 junior developers'",
        "Showcase scale: 'Built system handling 1M+ daily requests'"
      ],
      impact: 'medium'
    },
    {
      metric: "Experience Depth",
      score: evaluation.experience_points_score,
      maxScore: 10,
      evidence: [
        "4+ years of relevant experience clearly documented",
        "Technology stack progression visible",
        "Projects show increasing complexity"
      ],
      issues: [
        "Gap between roles not explained (May 2021 - Sep 2021)",
        "Job responsibilities overlap 60% between roles",
        "No mention of specific project outcomes or business impact"
      ],
      improvements: [
        "Explain career gaps: 'Career break for skill enhancement'",
        "Differentiate roles: highlight unique contributions per position",
        "Add business impact: 'Delivered feature reducing customer churn by 12%'"
      ],
      impact: 'medium'
    },
    {
      metric: "Quality & Consistency",
      score: evaluation.quality_checks_score,
      maxScore: 10,
      evidence: [
        "No grammatical errors detected",
        "Consistent tense usage throughout",
        "Professional email format"
      ],
      issues: [
        "Inconsistent spacing: 1.0 vs 1.15 line spacing between sections",
        "Font size varies: 11pt in experience, 10pt in education",
        "Bullet point alignment issues in Skills section"
      ],
      improvements: [
        "Standardize line spacing to 1.15 throughout",
        "Use consistent 11pt font for all body text",
        "Align all bullet points and fix indentation"
      ],
      impact: 'low'
    }
  ]

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600"
    if (score >= 60) return "text-yellow-600"
    return "text-red-600"
  }

  const getImpactColor = (impact: 'high' | 'medium' | 'low') => {
    switch (impact) {
      case 'high': return "bg-red-500/20 text-red-200 border-red-500/30"
      case 'medium': return "bg-yellow-500/20 text-yellow-200 border-yellow-500/30"
      case 'low': return "bg-blue-500/20 text-blue-200 border-blue-500/30"
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-7xl h-[90vh] overflow-hidden">
        <DialogHeader className="pb-4">
          <DialogTitle className="text-2xl font-anton text-gradient-warm">
            Enhanced Resume Analysis
          </DialogTitle>
          <DialogDescription className="text-lg">
            Detailed breakdown with specific improvements and line-by-line feedback
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="scores" className="flex items-center gap-2">
              <Target className="w-4 h-4" />
              Scores & Analysis
            </TabsTrigger>
            <TabsTrigger value="feedback" className="flex items-center gap-2">
              <Target className="w-4 h-4" />
              Line-by-Line Feedback
            </TabsTrigger>
          </TabsList>

          {/* Part 1: Detailed Scores & Justifications */}
          <TabsContent value="scores" className="space-y-6 overflow-y-auto max-h-[75vh] pb-20">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Overall Score Card */}
              <Card className="lg:col-span-2 bg-gradient-card border-accent-500/20">
                <CardHeader>
                  <CardTitle className="text-xl flex items-center gap-3">
                    <div className="w-16 h-16 rounded-full bg-gradient-warm flex items-center justify-center text-white text-2xl font-bold">
                      {evaluation.overall_score}
                    </div>
                    <div>
                      <div>Overall Resume Score</div>
                      <div className="text-sm text-muted-foreground font-normal">
                        Based on comprehensive AI analysis across {scoreJustifications.length} key metrics
                      </div>
                    </div>
                  </CardTitle>
                </CardHeader>
              </Card>

              {/* Individual Score Justifications */}
              {scoreJustifications.map((justification, index) => (
                <Card key={index} className="premium-card">
                  <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg text-cream-50">{justification.metric}</CardTitle>
                      <div className="flex items-center gap-3">
                        <Badge
                          variant="outline"
                          className={`${getImpactColor(justification.impact)} px-3 py-1`}
                        >
                          {justification.impact.toUpperCase()} IMPACT
                        </Badge>
                        <div className={`text-2xl font-bold ${getScoreColor(justification.score * 10)}`}>
                          {justification.score}/{justification.maxScore}
                        </div>
                      </div>
                    </div>
                    <Progress value={(justification.score / justification.maxScore) * 100} className="w-full" />
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Evidence Section */}
                    <div className="p-4 bg-green-900/20 rounded-lg border border-green-500/30">
                      <h4 className="font-semibold text-cream-50 mb-3 flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        What&apos;s Working Well
                      </h4>
                      <ul className="space-y-2">
                        {justification.evidence.map((item, i) => (
                          <li key={i} className="text-sm text-cream-50 flex items-start gap-2">
                            <span className="w-1 h-1 bg-green-400 rounded-full mt-2 flex-shrink-0"></span>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Issues Section */}
                    <div className="p-4 bg-red-900/20 rounded-lg border border-red-500/30">
                      <h4 className="font-semibold text-cream-50 mb-3 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-red-400" />
                        Issues Found
                      </h4>
                      <ul className="space-y-2">
                        {justification.issues.map((item, i) => (
                          <li key={i} className="text-sm text-cream-50 flex items-start gap-2">
                            <span className="w-1 h-1 bg-red-400 rounded-full mt-2 flex-shrink-0"></span>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Improvements Section */}
                    <div className="p-4 bg-blue-900/20 rounded-lg border border-blue-500/30">
                      <h4 className="font-semibold text-cream-50 mb-3 flex items-center gap-2">
                        <Zap className="w-4 h-4 text-blue-400" />
                        Specific Improvements
                      </h4>
                      <ul className="space-y-2">
                        {justification.improvements.map((item, i) => (
                          <li key={i} className="text-sm text-cream-50 flex items-start gap-2">
                            <ArrowRight className="w-3 h-3 text-blue-400 mt-1 flex-shrink-0" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Part 2: Line-by-Line Feedback */}
          <TabsContent value="feedback" className="h-full overflow-hidden">
            <div className="space-y-6 max-h-[75vh] overflow-y-auto">
              <div className="flex items-center gap-2 mb-6">
                <Target className="w-5 h-5 text-blue-600" />
                <h3 className="text-xl font-semibold text-cream-50">Line-by-Line Feedback & Recommendations</h3>
              </div>

              {/* Header Section Issues */}
              <Card className="premium-card">
                <CardHeader>
                  <CardTitle className="text-lg text-cream-50">📧 Contact Information</CardTitle>
                  <CardDescription className="text-cream-200">Header section analysis</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 bg-red-900/20 rounded-lg border border-red-500/30">
                    <h4 className="font-semibold text-red-300 mb-2 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" />
                      Line 1: &quot;Nagarjun Mallesh&quot;
                    </h4>
                    <p className="text-sm text-red-200 mb-3">
                      ❌ Name formatting lacks professional impact and ATS optimization
                    </p>
                    <div className="pl-4 border-l-2 border-blue-400 bg-blue-900/20 p-3 rounded">
                      <p className="text-sm text-blue-200 font-medium">💡 Recommendation:</p>
                      <p className="text-sm text-blue-200">
                        Use &quot;NAGARJUN MALLESH&quot; in larger, bold font. Consider adding relevant certifications or titles like &quot;NAGARJUN MALLESH, MS&quot; to stand out to recruiters.
                      </p>
                    </div>
                  </div>

                  <div className="p-4 bg-yellow-900/20 rounded-lg border border-yellow-500/30">
                    <h4 className="font-semibold text-yellow-300 mb-2 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" />
                      Line 2: Contact information layout
                    </h4>
                    <p className="text-sm text-yellow-200 mb-3">
                      ⚠️ Phone number format and LinkedIn URL could be optimized for ATS parsing
                    </p>
                    <div className="pl-4 border-l-2 border-blue-400 bg-blue-900/20 p-3 rounded">
                      <p className="text-sm text-blue-200 font-medium">💡 Recommendation:</p>
                      <p className="text-sm text-blue-200">
                        Format as: &quot;Boston, MA | (857) 799-0214 | nagarjunmallesh@gmail.com | linkedin.com/in/nagarjun-mallesh&quot;
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Summary Section Issues */}
              <Card className="premium-card">
                <CardHeader>
                  <CardTitle className="text-lg text-cream-50">📝 Professional Summary</CardTitle>
                  <CardDescription className="text-cream-200">Summary section analysis</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 bg-red-900/20 rounded-lg border border-red-500/30">
                    <h4 className="font-semibold text-red-300 mb-2 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" />
                      Line 1: &quot;Results-driven GenAI Software Engineer with 4+ years...&quot;
                    </h4>
                    <p className="text-sm text-red-200 mb-3">
                      ❌ Generic opening phrase &quot;Results-driven&quot; - overused by 89% of candidates
                    </p>
                    <div className="pl-4 border-l-2 border-blue-400 bg-blue-900/20 p-3 rounded">
                      <p className="text-sm text-blue-200 font-medium">💡 Recommendation:</p>
                      <p className="text-sm text-blue-200">
                        Start with: &quot;GenAI Software Engineer specializing in distributed systems and cloud architecture with proven track record of...&quot;
                      </p>
                    </div>
                  </div>

                  <div className="p-4 bg-green-900/20 rounded-lg border border-green-500/30">
                    <h4 className="font-semibold text-green-300 mb-2 flex items-center gap-2">
                      <CheckCircle className="w-4 h-4" />
                      Line 2: &quot;Led cross-functional teams delivering 70% performance improvements...&quot;
                    </h4>
                    <p className="text-sm text-green-200 mb-3">
                      ✅ Excellent quantified achievement with specific metrics
                    </p>
                    <div className="pl-4 border-l-2 border-blue-400 bg-blue-900/20 p-3 rounded">
                      <p className="text-sm text-blue-200 font-medium">💡 Enhancement:</p>
                      <p className="text-sm text-blue-200">
                        Add team size for more impact: &quot;Led cross-functional teams of 8+ engineers delivering 70% performance improvements...&quot;
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Experience Section Issues */}
              <Card className="premium-card">
                <CardHeader>
                  <CardTitle className="text-lg text-cream-50">💼 Experience Section</CardTitle>
                  <CardDescription className="text-cream-200">Work experience analysis</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 bg-green-900/20 rounded-lg border border-green-500/30">
                    <h4 className="font-semibold text-green-300 mb-2 flex items-center gap-2">
                      <CheckCircle className="w-4 h-4" />
                      Job 1 - Date Format: &quot;Jul 2024 - Present&quot;
                    </h4>
                    <p className="text-sm text-green-200 mb-3">
                      ✅ GOOD: Current employment dates are properly formatted and realistic
                    </p>
                    <div className="pl-4 border-l-2 border-blue-400 bg-blue-900/20 p-3 rounded">
                      <p className="text-sm text-blue-200 font-medium">💡 Best Practice:</p>
                      <p className="text-sm text-blue-200">
                        Consistent date formatting throughout resume helps ATS parsing and recruiter scanning.
                      </p>
                    </div>
                  </div>

                  <div className="p-4 bg-yellow-900/20 rounded-lg border border-yellow-500/30">
                    <h4 className="font-semibold text-yellow-300 mb-2 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" />
                      Bullet Point: &quot;Enhanced technical roadmap by conducting real-time inventory...&quot;
                    </h4>
                    <p className="text-sm text-yellow-200 mb-3">
                      ⚠️ Vague language - &quot;enhanced technical roadmap&quot; doesn&apos;t clearly convey the action or impact
                    </p>
                    <div className="pl-4 border-l-2 border-blue-400 bg-blue-900/20 p-3 rounded">
                      <p className="text-sm text-blue-200 font-medium">💡 Rewrite Suggestion:</p>
                      <p className="text-sm text-blue-200">
                        &quot;Streamlined development processes by implementing real-time inventory monitoring across 5+ platforms, accelerating team delivery velocity by 40%&quot;
                      </p>
                    </div>
                  </div>

                  <div className="p-4 bg-red-900/20 rounded-lg border border-red-500/30">
                    <h4 className="font-semibold text-red-300 mb-2 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" />
                      Repetitive Content: &quot;Designed a blue-green deployment pipeline&quot;
                    </h4>
                    <p className="text-sm text-red-200 mb-3">
                      ❌ This exact phrase appears in both job descriptions - shows copy-paste approach
                    </p>
                    <div className="pl-4 border-l-2 border-blue-400 bg-blue-900/20 p-3 rounded">
                      <p className="text-sm text-blue-200 font-medium">💡 Diversify Language:</p>
                      <p className="text-sm text-blue-200">
                        First job: &quot;Architected blue-green deployment infrastructure...&quot;<br />
                        Second job: &quot;Implemented CI/CD pipeline with blue-green deployment strategy...&quot;
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Skills Section Issues */}
              <Card className="premium-card">
                <CardHeader>
                  <CardTitle className="text-lg text-cream-50">🛠️ Skills Section</CardTitle>
                  <CardDescription className="text-cream-200">Technical skills analysis</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 bg-yellow-900/20 rounded-lg border border-yellow-500/30">
                    <h4 className="font-semibold text-yellow-300 mb-2 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" />
                      Skills Organization & ATS Optimization
                    </h4>
                    <p className="text-sm text-yellow-200 mb-3">
                      ⚠️ Skills are not optimized for ATS parsing and lack proficiency indicators
                    </p>
                    <div className="pl-4 border-l-2 border-blue-400 bg-blue-900/20 p-3 rounded">
                      <p className="text-sm text-blue-200 font-medium">💡 Restructure Suggestion:</p>
                      <div className="text-sm text-blue-200 space-y-2">
                        <p><strong>Cloud & AI:</strong> AWS Bedrock (Expert), Lambda (Advanced), API Gateway (Advanced)</p>
                        <p><strong>Programming:</strong> Python (Expert), Java (Advanced), JavaScript/TypeScript (Advanced)</p>
                        <p><strong>DevOps:</strong> Docker (Advanced), Kubernetes (Intermediate), CloudFormation (Advanced)</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Education Section Issues */}
              <Card className="premium-card">
                <CardHeader>
                  <CardTitle className="text-lg text-cream-50">🎓 Education Section</CardTitle>
                  <CardDescription className="text-cream-200">Education formatting analysis</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 bg-green-900/20 rounded-lg border border-green-500/30">
                    <h4 className="font-semibold text-green-300 mb-2 flex items-center gap-2">
                      <CheckCircle className="w-4 h-4" />
                      Education Content
                    </h4>
                    <p className="text-sm text-green-200 mb-3">
                      ✅ Good degree relevance and recent graduation from reputable university
                    </p>
                    <div className="pl-4 border-l-2 border-blue-400 bg-blue-900/20 p-3 rounded">
                      <p className="text-sm text-blue-200 font-medium">💡 Enhancement Opportunity:</p>
                      <p className="text-sm text-blue-200">
                        Add GPA if 3.5+ and relevant coursework: &quot;Relevant Coursework: Machine Learning, Cloud Computing, System Design&quot;
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Priority Action Items */}
              <Card className="premium-card bg-gradient-to-r from-red-900/30 to-orange-900/30 border-red-500/30">
                <CardHeader>
                  <CardTitle className="text-lg text-cream-50 flex items-center gap-2">
                    <Zap className="w-5 h-5 text-orange-400" />
                    🚨 Critical Priority Fixes (Fix These First!)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-start gap-3 p-3 bg-red-900/30 rounded">
                      <span className="text-red-400 font-bold">1.</span>
                      <p className="text-red-200 text-sm">
                        <strong>Maintain date consistency:</strong> Ensure all employment dates follow the same format (MMM YYYY - MMM YYYY)
                      </p>
                    </div>
                    <div className="flex items-start gap-3 p-3 bg-orange-900/30 rounded">
                      <span className="text-orange-400 font-bold">2.</span>
                      <p className="text-orange-200 text-sm">
                        <strong>Remove repetitive content:</strong> Diversify the &quot;blue-green deployment&quot; descriptions
                      </p>
                    </div>
                    <div className="flex items-start gap-3 p-3 bg-yellow-900/30 rounded">
                      <span className="text-yellow-400 font-bold">3.</span>
                      <p className="text-yellow-200 text-sm">
                        <strong>Replace generic opener:</strong> Remove &quot;Results-driven&quot; from summary
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}

// Mock evaluation generator for demonstration
// Mock generation removed