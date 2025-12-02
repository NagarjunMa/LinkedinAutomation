"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import {
    CheckCircle,
    AlertCircle,
    Star,
    ChevronDown,
    ChevronRight,
    Target,
    FileText,
    Download,
    Calendar,
    Trash2,
    RefreshCw,
    Sparkles
} from "lucide-react"
import { ResumeFile, resumeApi } from "@/app/lib/api"
import { useToast } from "@/components/ui/use-toast"

interface ResumeListDropdownProps {
    resumes: ResumeFile[]
    onViewDetailedAnalysis: (resume: ResumeFile) => void
    onViewEnhancedAnalysis?: (resume: ResumeFile) => void
    onDownloadResume: (resumeId: string) => void
    onEvaluateResume: (resumeId: string) => void
    evaluatingResume: string | null
    onResumeDeleted?: () => void
}

export function ResumeListDropdown({
    resumes,
    onViewDetailedAnalysis,
    onViewEnhancedAnalysis,
    onDownloadResume,
    onEvaluateResume,
    evaluatingResume,
    onResumeDeleted
}: ResumeListDropdownProps) {
    const [expandedResume, setExpandedResume] = useState<string | null>(null)
    const [deleteConfirmResume, setDeleteConfirmResume] = useState<ResumeFile | null>(null)
    const [isDeleting, setIsDeleting] = useState(false)
    const { toast } = useToast()

    // Reset stuck evaluations on mount and every 30 seconds
    useEffect(() => {
        const resetStuckEvaluations = () => {
            const now = new Date()
            const stuckResumes = resumes.filter(resume => {
                if (resume.evaluation_status !== 'evaluating') return false
                const uploadedTime = new Date(resume.uploaded_at)
                const timeDiff = now.getTime() - uploadedTime.getTime()
                return timeDiff > 5 * 60 * 1000 // 5 minutes
            })

            if (stuckResumes.length > 0) {
                console.log(`Found ${stuckResumes.length} stuck evaluations, resetting...`)
                // The parent component should handle refreshing the data
                if (onResumeDeleted) {
                    onResumeDeleted()
                }
            }
        }

        // Run immediately
        resetStuckEvaluations()

        // Run every 30 seconds
        const interval = setInterval(resetStuckEvaluations, 30000)

        return () => clearInterval(interval)
    }, [resumes, onResumeDeleted])

    const _getScoreColor = (score: number) => {
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

    const toggleResume = (resumeId: string) => {
        setExpandedResume(expandedResume === resumeId ? null : resumeId)
    }

    const handleDeleteResume = async (resume: ResumeFile) => {
        setIsDeleting(true)
        try {
            await resumeApi.deleteResume(resume.id)
            toast({
                title: "Resume Deleted",
                description: `${resume.original_filename} has been deleted successfully.`,
            })
            if (onResumeDeleted) {
                onResumeDeleted()
            }
        } catch (error) {
            console.error('Failed to delete resume:', error)
            toast({
                title: "Delete Failed",
                description: "Failed to delete resume. Please try again.",
                variant: "destructive",
            })
        } finally {
            setIsDeleting(false)
            setDeleteConfirmResume(null)
        }
    }

    const confirmDeleteResume = (resume: ResumeFile) => {
        setDeleteConfirmResume(resume)
    }

    if (resumes.length === 0) {
        return (
            <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                    <FileText className="h-16 w-16 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No Resumes Found</h3>
                    <p className="text-muted-foreground text-center mb-4">
                        Upload your first resume to get started with AI-powered evaluation
                    </p>
                </CardContent>
            </Card>
        )
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-cream-50">Your Resumes</h2>
                <Badge variant="outline" className="text-sm border-accent-500/50 text-accent-300">
                    {resumes.length} {resumes.length === 1 ? 'Resume' : 'Resumes'}
                </Badge>
            </div>

            <div className="space-y-3">
                {resumes.map((resume) => (
                    <Card key={resume.id} className="premium-card overflow-hidden">
                        <Collapsible
                            open={expandedResume === resume.id}
                            onOpenChange={() => toggleResume(resume.id)}
                        >
                            <CollapsibleTrigger asChild>
                                <CardHeader className="cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            {resume.is_primary && (
                                                <Badge variant="default" className="bg-yellow-600">
                                                    <Star className="w-3 h-3 mr-1" />
                                                    Primary
                                                </Badge>
                                            )}
                                            <div className="flex-1">
                                                <CardTitle className="text-lg flex items-center gap-2">
                                                    {resume.filename}
                                                    {resume.is_primary && <Star className="w-4 h-4 text-yellow-600" />}
                                                </CardTitle>
                                                <CardDescription className="flex items-center gap-4 mt-1">
                                                    <span className="flex items-center gap-1">
                                                        <Calendar className="w-3 h-3" />
                                                        Uploaded {new Date(resume.uploaded_at).toLocaleDateString()}
                                                    </span>
                                                    <span className="flex items-center gap-1">
                                                        <FileText className="w-3 h-3" />
                                                        {(resume.file_size / 1024).toFixed(1)} KB
                                                    </span>
                                                </CardDescription>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <Badge variant={
                                                resume.evaluation_status === 'completed' ? 'default' :
                                                    resume.evaluation_status === 'evaluating' ? 'secondary' :
                                                        resume.evaluation_status === 'failed' ? 'destructive' : 'outline'
                                            }>
                                                {resume.evaluation_status === 'completed' && <CheckCircle className="w-3 h-3 mr-1" />}
                                                {resume.evaluation_status === 'evaluating' && <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-current mr-1"></div>}
                                                {resume.evaluation_status === 'failed' && <AlertCircle className="w-3 h-3 mr-1" />}
                                                {resume.evaluation_status.charAt(0).toUpperCase() + resume.evaluation_status.slice(1)}
                                            </Badge>

                                            {/* Action Buttons */}
                                            <div className="flex items-center gap-2">
                                                {/* Delete Button */}
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={(e) => {
                                                        e.stopPropagation()
                                                        confirmDeleteResume(resume)
                                                    }}
                                                    className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </Button>

                                                {/* Reset Stuck Evaluation Button */}
                                                {resume.evaluation_status === 'evaluating' && (
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={(e) => {
                                                            e.stopPropagation()
                                                            onEvaluateResume(resume.id)
                                                        }}
                                                        className="h-8 w-8 p-0 text-orange-600 hover:text-orange-700 hover:bg-orange-50 border-orange-200"
                                                        title="Reset stuck evaluation"
                                                    >
                                                        <RefreshCw className="w-4 h-4" />
                                                    </Button>
                                                )}

                                                {/* Expand/Collapse Button */}
                                                {expandedResume === resume.id ? (
                                                    <ChevronDown className="w-4 h-4 text-gray-500" />
                                                ) : (
                                                    <ChevronRight className="w-4 h-4 text-gray-500" />
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </CardHeader>
                            </CollapsibleTrigger>

                            <CollapsibleContent>
                                <CardContent className="pt-0">
                                    {resume.evaluation_status === 'completed' && resume.evaluation_result ? (
                                        <div className="space-y-6">
                                            {/* Success Message */}
                                            <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
                                                <div className="flex items-center gap-3">
                                                    <CheckCircle className="w-6 h-6 text-green-400" />
                                                    <div>
                                                        <h3 className="font-semibold text-green-300">Evaluation Complete! 🎉</h3>
                                                        <p className="text-sm text-green-200">
                                                            AI analysis completed with detailed scoring and recommendations
                                                        </p>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Score Overview */}
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                                <div className="text-center p-4 premium-card border-accent-500/30 rounded-lg">
                                                    <div className={`text-2xl font-bold mb-1 ${"text-accent-400"}`}>
                                                        {resume.evaluation_result.overall_score}/100
                                                    </div>
                                                    <div className="text-sm text-cream-300 mb-2">Overall Score</div>
                                                    <Progress value={resume.evaluation_result.overall_score} className="h-2" />
                                                </div>

                                                <div className="text-center p-4 premium-card border-accent-500/30 rounded-lg">
                                                    <div className={`text-2xl font-bold mb-1 ${"text-orange-400"}`}>
                                                        {resume.evaluation_result.ats_compliance_score}/100
                                                    </div>
                                                    <div className="text-sm text-cream-300 mb-2">ATS Compliance</div>
                                                    <Progress value={resume.evaluation_result.ats_compliance_score} className="h-2" />
                                                </div>

                                                <div className="text-center p-4 premium-card border-accent-500/30 rounded-lg">
                                                    <Badge
                                                        variant={getATSCompatibilityBadgeVariant(resume.evaluation_result.ats_compatibility)}
                                                        className="text-lg px-4 py-2 mb-2"
                                                    >
                                                        {resume.evaluation_result.ats_compatibility.charAt(0).toUpperCase() +
                                                            resume.evaluation_result.ats_compatibility.slice(1)}
                                                    </Badge>
                                                    <div className="text-sm text-cream-300">ATS Compatibility</div>
                                                </div>
                                            </div>

                                            {/* Quick Actions */}
                                            <div className="flex gap-2 flex-wrap">
                                                <Button
                                                    onClick={() => onViewDetailedAnalysis(resume)}
                                                    className="flex items-center gap-2"
                                                    size="sm"
                                                >
                                                    <Target className="w-4 h-4" />
                                                    View Analysis
                                                </Button>
                                                {onViewEnhancedAnalysis && (
                                                    <Button
                                                        onClick={() => onViewEnhancedAnalysis(resume)}
                                                        className="flex items-center gap-2 bg-gradient-warm hover:bg-gradient-gold"
                                                        size="sm"
                                                    >
                                                        <Sparkles className="w-4 h-4" />
                                                        Enhanced Analysis
                                                    </Button>
                                                )}
                                                <Button
                                                    variant="outline"
                                                    onClick={() => onDownloadResume(resume.id)}
                                                    className="flex items-center gap-2"
                                                    size="sm"
                                                >
                                                    <Download className="w-4 h-4" />
                                                    Download
                                                </Button>
                                            </div>
                                        </div>
                                    ) : resume.evaluation_status === 'evaluating' ? (
                                        <div className="text-center py-8">
                                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                                            <h3 className="text-lg font-semibold mb-2">AI Analyzing Your Resume</h3>
                                            <p className="text-muted-foreground">
                                                Our AI recruiter is carefully reviewing your resume. This may take a few minutes...
                                            </p>
                                        </div>
                                    ) : resume.evaluation_status === 'failed' ? (
                                        <div className="text-center py-8">
                                            <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-4" />
                                            <h3 className="text-lg font-semibold mb-2 text-red-700">Evaluation Failed</h3>
                                            <p className="text-muted-foreground mb-4">
                                                There was an error evaluating your resume. Please try again.
                                            </p>
                                            <Button
                                                variant="outline"
                                                onClick={() => onEvaluateResume(resume.id)}
                                                disabled={evaluatingResume === resume.id}
                                            >
                                                {evaluatingResume === resume.id ? (
                                                    <>
                                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                                                        Evaluating...
                                                    </>
                                                ) : (
                                                    'Retry Evaluation'
                                                )}
                                            </Button>
                                        </div>
                                    ) : (
                                        <div className="text-center py-8">
                                            <FileText className="h-8 w-8 text-blue-500 mx-auto mb-4" />
                                            <h3 className="text-lg font-semibold mb-2 text-blue-700">Ready for Evaluation</h3>
                                            <p className="text-muted-foreground mb-4">
                                                Your resume is ready to be analyzed by our AI recruiter.
                                            </p>
                                            <Button
                                                onClick={() => onEvaluateResume(resume.id)}
                                                disabled={evaluatingResume === resume.id}
                                            >
                                                {evaluatingResume === resume.id ? (
                                                    <>
                                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                                                        Evaluating...
                                                    </>
                                                ) : (
                                                    'Start Evaluation'
                                                )}
                                            </Button>
                                        </div>
                                    )}
                                </CardContent>
                            </CollapsibleContent>
                        </Collapsible>
                    </Card>
                ))}
            </div>

            {/* Delete Confirmation Dialog */}
            <Dialog open={!!deleteConfirmResume} onOpenChange={() => setDeleteConfirmResume(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <AlertCircle className="w-5 h-5 text-red-600" />
                            Delete Resume
                        </DialogTitle>
                        <DialogDescription>
                            Are you sure you want to delete &quot;{deleteConfirmResume?.original_filename}&quot;? This action cannot be undone.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setDeleteConfirmResume(null)}
                            disabled={isDeleting}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="destructive"
                            onClick={() => deleteConfirmResume && handleDeleteResume(deleteConfirmResume)}
                            disabled={isDeleting}
                        >
                            {isDeleting ? (
                                <>
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                                    Deleting...
                                </>
                            ) : (
                                <>
                                    <Trash2 className="w-4 h-4 mr-2" />
                                    Delete Resume
                                </>
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    )
}
