"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { AlertTriangle, ArrowRight, CheckCircle, Target, Zap } from "lucide-react"
import { ResumeFile } from "@/app/lib/api/types"

interface EnhancedResumeAnalysisProps {
  resume: ResumeFile | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

const CATEGORY_LABELS = {
  content_quality: "Content Quality",
  role_fit: "Role Fit",
  evidence_strength: "Evidence Strength",
  recruiter_readability: "Recruiter Readability",
} as const

function getScoreColor(score: number) {
  if (score >= 80) return "text-green-600"
  if (score >= 60) return "text-yellow-600"
  return "text-red-600"
}

function getReadinessLabel(label?: string) {
  switch (label) {
    case "ready":
      return "Ready to apply"
    case "minor_edits":
      return "Apply after minor edits"
    case "needs_work":
      return "Needs work before applying"
    default:
      return "Evaluation complete"
  }
}

function getSeverityTone(severity: string) {
  if (severity === "critical") return "border-red-500/30 bg-red-500/10 text-red-700"
  if (severity === "warning") return "border-amber-500/30 bg-amber-500/10 text-amber-700"
  return "border-blue-500/30 bg-blue-500/10 text-blue-700"
}

export function EnhancedResumeAnalysis({ resume, open, onOpenChange }: EnhancedResumeAnalysisProps) {
  const [activeTab, setActiveTab] = useState("scores")

  if (!resume?.evaluation_result) return null

  const evaluation = resume.evaluation_result
  const breakdown = evaluation.score_breakdown ?? {
    content_quality: evaluation.content_quality_score,
    role_fit: evaluation.job_relevance_score,
    evidence_strength: evaluation.experience_points_score,
    recruiter_readability: evaluation.quality_checks_score,
  }
  const explanations = evaluation.score_explanation ?? []
  const topActions = evaluation.top_actions_before_applying ?? evaluation.improvements ?? []
  const parserConfidence = evaluation.parser_confidence ?? "medium"

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader className="pb-4">
          <DialogTitle className="text-2xl">Resume Readiness Analysis</DialogTitle>
          <DialogDescription>
            Evidence-backed scoring from the latest evaluation. No canned examples are shown here.
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="scores" className="flex items-center gap-2">
              <Target className="w-4 h-4" />
              Score Evidence
            </TabsTrigger>
            <TabsTrigger value="feedback" className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Before Applying
            </TabsTrigger>
          </TabsList>

          <TabsContent value="scores" className="space-y-6 pt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-4">
                    <div className="flex h-16 w-16 items-center justify-center rounded-full border text-2xl font-bold">
                      {evaluation.overall_score}
                    </div>
                    <div>
                      <p>Overall Resume Score</p>
                      <p className="text-sm font-normal text-muted-foreground">
                        {getReadinessLabel(evaluation.readiness_label)}
                      </p>
                    </div>
                  </div>
                  <Badge variant="outline">Parser confidence: {parserConfidence}</Badge>
                </CardTitle>
              </CardHeader>
              {evaluation.detailed_feedback && (
                <CardContent>
                  <p className="text-sm text-muted-foreground">{evaluation.detailed_feedback}</p>
                </CardContent>
              )}
            </Card>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {Object.entries(breakdown).map(([key, score]) => (
                <Card key={key}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between gap-3">
                      <CardTitle className="text-base">
                        {CATEGORY_LABELS[key as keyof typeof CATEGORY_LABELS] ?? key}
                      </CardTitle>
                      <span className={`text-xl font-bold ${getScoreColor(score)}`}>{score}/100</span>
                    </div>
                    <Progress value={score} />
                  </CardHeader>
                </Card>
              ))}
            </div>

            {explanations.length > 0 ? (
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                {explanations.map((item, index) => (
                  <Card key={`${item.category}-${index}`}>
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between gap-3 text-base">
                        {CATEGORY_LABELS[item.category] ?? item.category}
                        <span className={`font-bold ${getScoreColor(item.score)}`}>{item.score}/100</span>
                      </CardTitle>
                      <CardDescription>{item.reason}</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {item.evidence.length > 0 && (
                        <div>
                          <p className="mb-2 flex items-center gap-2 text-sm font-semibold">
                            <CheckCircle className="h-4 w-4 text-green-600" />
                            Evidence Used
                          </p>
                          <ul className="space-y-2">
                            {item.evidence.map((evidence, evidenceIndex) => (
                              <li key={evidenceIndex} className="text-sm text-muted-foreground">
                                {evidence}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <div className="rounded-md border bg-muted/30 p-3">
                        <p className="mb-1 flex items-center gap-2 text-sm font-semibold">
                          <ArrowRight className="h-4 w-4" />
                          Before Applying
                        </p>
                        <p className="text-sm text-muted-foreground">{item.before_applying_action}</p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="py-8 text-sm text-muted-foreground">
                  This evaluation was created before score explanations were available. Re-run evaluation to get category-level evidence.
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="feedback" className="space-y-6 pt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  Top Actions Before Applying
                </CardTitle>
              </CardHeader>
              <CardContent>
                {topActions.length > 0 ? (
                  <ol className="space-y-3">
                    {topActions.map((action, index) => (
                      <li key={index} className="flex gap-3 text-sm">
                        <span className="font-mono font-bold">{index + 1}.</span>
                        <span>{action}</span>
                      </li>
                    ))}
                  </ol>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No prioritized actions were returned for this evaluation.
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Bullet-Level Flags</CardTitle>
                <CardDescription>
                  These are the exact flags returned by the evaluator.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {evaluation.bullet_flags?.length ? (
                  <div className="space-y-3">
                    {evaluation.bullet_flags.map((flag, index) => (
                      <div key={`${flag.bullet_id}-${index}`} className={`rounded-md border p-3 text-sm ${getSeverityTone(flag.severity)}`}>
                        <div className="mb-1 flex flex-wrap items-center gap-2">
                          <Badge variant="outline">{flag.severity}</Badge>
                          <Badge variant="outline">{flag.category}</Badge>
                          <span className="font-mono text-xs opacity-70">{flag.bullet_id}</span>
                        </div>
                        <p>{flag.reason}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No bullet-level flags are available in this resume list view. Open the resume editor for line-level flags.
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
