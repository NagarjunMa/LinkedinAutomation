"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/components/ui/use-toast"
import { referralTemplatesAPI } from '@/app/lib/api/referral'
import {
    MessageSquare,
    Send,
    Copy,
    Trash2,
    Calendar,
    Building,
    User,
    Star,
    BarChart3,
    Eye,
    Clock,
    CheckCircle
} from "lucide-react"

interface FeedbackFormProps {
    templateId: string
    onSubmit: () => void
    onCancel: () => void
}

function FeedbackForm({ templateId, onSubmit, onCancel }: FeedbackFormProps) {
    const [feedback, setFeedback] = useState({
        got_response: false,
        response_type: "",
        response_quality_score: 3,
        user_satisfaction_score: 3,
        feedback_notes: ""
    })
    const [submitting, setSubmitting] = useState(false)
    const { toast } = useToast()

    const submitFeedback = async () => {
        try {
            setSubmitting(true)
            await referralTemplatesAPI.recordFeedback(templateId, feedback)
            toast({
                title: "Feedback Recorded",
                description: "Thank you for your feedback!",
            })
            onSubmit()
        } catch (error) {
            console.error('Error submitting feedback:', error)
            toast({
                title: "Error",
                description: "Failed to submit feedback.",
                variant: "destructive",
            })
        } finally {
            setSubmitting(false)
        }
    }

    return (
        <div className="space-y-4 p-6 bg-white dark:bg-[#1c1c1c] border border-[#3b3b3b]/10 dark:border-[#f0eff2]/10 rounded-2xl shadow-sm">
            <h4 className="text-[#3b3b3b] dark:text-[#f0eff2] font-bold uppercase tracking-wide text-sm">Provide Feedback</h4>

            <div className="space-y-4">
                <div className="flex items-center gap-4">
                    <label className="text-[#3b3b3b]/70 dark:text-[#f0eff2]/70 text-sm font-medium">Did you get a response?</label>
                    <div className="flex gap-2">
                        <Button
                            variant={feedback.got_response ? "default" : "outline"}
                            size="sm"
                            onClick={() => setFeedback({ ...feedback, got_response: true })}
                            className={feedback.got_response ? "bg-emerald-600 hover:bg-emerald-700 text-white" : "border-[#3b3b3b]/20 dark:border-[#f0eff2]/20 text-[#3b3b3b] dark:text-[#f0eff2]"}
                        >
                            Yes
                        </Button>
                        <Button
                            variant={!feedback.got_response ? "default" : "outline"}
                            size="sm"
                            onClick={() => setFeedback({ ...feedback, got_response: false })}
                            className={!feedback.got_response ? "bg-rose-600 hover:bg-rose-700 text-white" : "border-[#3b3b3b]/20 dark:border-[#f0eff2]/20 text-[#3b3b3b] dark:text-[#f0eff2]"}
                        >
                            No
                        </Button>
                    </div>
                </div>

                {feedback.got_response && (
                    <div className="space-y-2">
                        <label className="text-[#3b3b3b]/70 dark:text-[#f0eff2]/70 text-sm font-medium">Response Type</label>
                        <Input
                            placeholder="e.g., positive_reply, interview_scheduled, referred"
                            value={feedback.response_type}
                            onChange={(e) => setFeedback({ ...feedback, response_type: e.target.value })}
                            className="bg-[#f0eff2]/50 dark:bg-[#0a0a0a]/50 border-transparent focus:bg-white dark:focus:bg-[#1c1c1c] focus:border-[#3b3b3b]/10 dark:focus:border-[#f0eff2]/10 rounded-xl text-[#3b3b3b] dark:text-[#f0eff2]"
                        />
                    </div>
                )}

                <div className="space-y-2">
                    <label className="text-[#3b3b3b]/70 dark:text-[#f0eff2]/70 text-sm font-medium">Template Satisfaction (1-5)</label>
                    <Input
                        type="number"
                        min={1}
                        max={5}
                        value={feedback.user_satisfaction_score}
                        onChange={(e) => setFeedback({ ...feedback, user_satisfaction_score: parseInt(e.target.value) })}
                        className="bg-[#f0eff2]/50 dark:bg-[#0a0a0a]/50 border-transparent focus:bg-white dark:focus:bg-[#1c1c1c] focus:border-[#3b3b3b]/10 dark:focus:border-[#f0eff2]/10 rounded-xl text-[#3b3b3b] dark:text-[#f0eff2]"
                    />
                </div>

                <div className="space-y-2">
                    <label className="text-[#3b3b3b]/70 dark:text-[#f0eff2]/70 text-sm font-medium">Additional Notes</label>
                    <Textarea
                        placeholder="Any additional feedback..."
                        value={feedback.feedback_notes}
                        onChange={(e) => setFeedback({ ...feedback, feedback_notes: e.target.value })}
                        className="bg-[#f0eff2]/50 dark:bg-[#0a0a0a]/50 border-transparent focus:bg-white dark:focus:bg-[#1c1c1c] focus:border-[#3b3b3b]/10 dark:focus:border-[#f0eff2]/10 rounded-xl text-[#3b3b3b] dark:text-[#f0eff2]"
                        rows={3}
                    />
                </div>
            </div>

            <div className="flex gap-2 pt-2">
                <Button
                    onClick={submitFeedback}
                    disabled={submitting}
                    className="bg-[#3b3b3b] dark:bg-white hover:bg-black dark:hover:bg-[#e5e5e5] text-white dark:text-black px-6 rounded-xl font-bold text-xs uppercase tracking-widest"
                    size="sm"
                >
                    {submitting ? "Submitting..." : "Submit Feedback"}
                </Button>
                <Button
                    variant="ghost"
                    onClick={onCancel}
                    size="sm"
                    className="text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 hover:text-[#3b3b3b] dark:hover:text-[#f0eff2]"
                >
                    Cancel
                </Button>
            </div>
        </div>
    )
}

export function ReferralTemplateManager() {
    const [templates, setTemplates] = useState<Array<Record<string, unknown>>>([])
    const [stats, setStats] = useState<Record<string, unknown> | null>(null)
    const [loading, setLoading] = useState(false)
    const [showFeedbackForm, setShowFeedbackForm] = useState<string | null>(null)
    const [expandedTemplate, setExpandedTemplate] = useState<string | null>(null)
    const { toast } = useToast()

    useEffect(() => {
        fetchData()
    }, [])

    const fetchData = async () => {
        try {
            setLoading(true)
            const [templatesData, statsData] = await Promise.all([
                referralTemplatesAPI.getTemplates(50),
                referralTemplatesAPI.getStats()
            ])
            setTemplates(templatesData as unknown as Array<Record<string, unknown>>)
            setStats(statsData as unknown as Record<string, unknown>)
        } catch (error) {
            console.error('Error fetching data:', error)
            toast({
                title: "Error",
                description: "Failed to load template data.",
                variant: "destructive",
            })
        } finally {
            setLoading(false)
        }
    }

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text)
        toast({
            title: "Copied!",
            description: "Content copied to clipboard.",
        })
    }

    const markAsSent = async (templateId: string) => {
        try {
            await referralTemplatesAPI.markSent(templateId)
            toast({
                title: "Marked as Sent",
                description: "Template has been marked as sent.",
            })
            fetchData() // Refresh data
        } catch (error) {
            console.error('Error marking as sent:', error)
            toast({
                title: "Error",
                description: "Failed to mark template as sent.",
                variant: "destructive",
            })
        }
    }

    const deleteTemplate = async (templateId: string) => {
        if (!confirm("Are you sure you want to delete this template?")) return

        try {
            await referralTemplatesAPI.deleteTemplate(templateId)
            toast({
                title: "Template Deleted",
                description: "Template has been removed.",
            })
            fetchData() // Refresh data
        } catch (error) {
            console.error('Error deleting template:', error)
            toast({
                title: "Error",
                description: "Failed to delete template.",
                variant: "destructive",
            })
        }
    }

    const getStatusBadge = (template: Record<string, unknown>) => {
        if (template.got_response) {
            return (
                <Badge className="bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-200 border-emerald-200 dark:border-emerald-800 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Responded
                </Badge>
            )
        } else if (template.was_sent) {
            return (
                <Badge className="bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-200 border-blue-200 dark:border-blue-800 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">
                    <Send className="h-3 w-3 mr-1" />
                    Sent
                </Badge>
            )
        } else {
            return (
                <Badge className="bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-200 border-amber-200 dark:border-amber-800 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">
                    <Clock className="h-3 w-3 mr-1" />
                    Draft
                </Badge>
            )
        }
    }

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#3b3b3b] dark:border-[#f0eff2]"></div>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Statistics Cards */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="bg-white dark:bg-[#1c1c1c] p-6 rounded-[24px] border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 shadow-sm">
                        <div className="flex items-center justify-between mb-2">
                            <div className="p-2 rounded-xl bg-[#3b3b3b]/5 dark:bg-[#f0eff2]/10 text-[#3b3b3b] dark:text-[#f0eff2]">
                                <MessageSquare className="h-5 w-5" />
                            </div>
                            <span className="text-[10px] font-black uppercase tracking-widest text-[#3b3b3b]/40 dark:text-[#f0eff2]/40">Total</span>
                        </div>
                        <div>
                            <p className="text-3xl font-black text-[#3b3b3b] dark:text-[#f0eff2] tracking-tighter">{stats.total_templates as number}</p>
                            <p className="text-xs font-bold uppercase tracking-widest text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 mt-1">Templates</p>
                        </div>
                    </div>

                    <div className="bg-white dark:bg-[#1c1c1c] p-6 rounded-[24px] border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 shadow-sm">
                        <div className="flex items-center justify-between mb-2">
                            <div className="p-2 rounded-xl bg-blue-500/10 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400">
                                <Send className="h-5 w-5" />
                            </div>
                            <span className="text-[10px] font-black uppercase tracking-widest text-[#3b3b3b]/40 dark:text-[#f0eff2]/40">Active</span>
                        </div>
                        <div>
                            <p className="text-3xl font-black text-[#3b3b3b] dark:text-[#f0eff2] tracking-tighter">{stats.sent_count as number}</p>
                            <p className="text-xs font-bold uppercase tracking-widest text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 mt-1">Sent Requests</p>
                        </div>
                    </div>

                    <div className="bg-white dark:bg-[#1c1c1c] p-6 rounded-[24px] border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 shadow-sm">
                        <div className="flex items-center justify-between mb-2">
                            <div className="p-2 rounded-xl bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">
                                <BarChart3 className="h-5 w-5" />
                            </div>
                            <span className="text-[10px] font-black uppercase tracking-widest text-[#3b3b3b]/40 dark:text-[#f0eff2]/40">Success</span>
                        </div>
                        <div>
                            <p className="text-3xl font-black text-[#3b3b3b] dark:text-[#f0eff2] tracking-tighter">{(stats.response_rate as number).toFixed(1)}%</p>
                            <p className="text-xs font-bold uppercase tracking-widest text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 mt-1">Response Rate</p>
                        </div>
                    </div>

                    <div className="bg-white dark:bg-[#1c1c1c] p-6 rounded-[24px] border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 shadow-sm">
                        <div className="flex items-center justify-between mb-2">
                            <div className="p-2 rounded-xl bg-amber-500/10 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400">
                                <Star className="h-5 w-5" />
                            </div>
                            <span className="text-[10px] font-black uppercase tracking-widest text-[#3b3b3b]/40 dark:text-[#f0eff2]/40">Quality</span>
                        </div>
                        <div>
                            <p className="text-3xl font-black text-[#3b3b3b] dark:text-[#f0eff2] tracking-tighter">{(stats.avg_effectiveness as number).toFixed(1)}</p>
                            <p className="text-xs font-bold uppercase tracking-widest text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 mt-1">Avg Effectiveness</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Templates List */}
            <Card className="bg-white dark:bg-[#1c1c1c] border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 rounded-[32px] shadow-sm overflow-hidden">
                <CardHeader className="border-b border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 p-8">
                    <CardTitle className="text-[#3b3b3b] dark:text-[#f0eff2] flex items-center gap-3 text-2xl font-black uppercase tracking-tight">
                        <MessageSquare className="h-6 w-6 text-[#3b3b3b]/40 dark:text-[#f0eff2]/40" />
                        Your Templates <span className="text-[#3b3b3b]/40 dark:text-[#f0eff2]/40 ml-2">({templates.length})</span>
                    </CardTitle>
                </CardHeader>
                <CardContent className="p-8">
                    {templates.length === 0 ? (
                        <div className="text-center py-16 bg-[#f0eff2]/30 dark:bg-[#0a0a0a]/30 rounded-3xl border border-dashed border-[#3b3b3b]/10 dark:border-[#f0eff2]/10">
                            <div className="w-16 h-16 rounded-full bg-[#3b3b3b]/5 dark:bg-[#f0eff2]/5 flex items-center justify-center mx-auto mb-4">
                                <MessageSquare className="h-8 w-8 text-[#3b3b3b]/40 dark:text-[#f0eff2]/40" />
                            </div>
                            <h3 className="text-lg font-black text-[#3b3b3b] dark:text-[#f0eff2] mb-2 uppercase tracking-tight">No templates created yet</h3>
                            <p className="text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 text-sm max-w-sm mx-auto">Generate your first referral template to get started</p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {templates.map((template) => (
                                <div
                                    key={template.id as string}
                                    className="border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 bg-[#f0eff2]/30 dark:bg-[#0a0a0a]/30 rounded-3xl p-6 transition-all hover:bg-white dark:hover:bg-[#1c1c1c] hover:shadow-lg hover:border-[#3b3b3b]/10 dark:hover:border-[#f0eff2]/20 group"
                                >
                                    <div className="flex flex-col md:flex-row items-start justify-between gap-4">
                                        <div className="space-y-2 flex-1">
                                            <div className="flex flex-wrap items-center gap-3">
                                                <h4 className="text-[#3b3b3b] dark:text-[#f0eff2] font-bold text-lg">{template.subject_line as string}</h4>
                                                {getStatusBadge(template)}
                                                <Badge className="bg-[#3b3b3b]/5 dark:bg-[#f0eff2]/5 text-[#3b3b3b] dark:text-[#f0eff2] border-[#3b3b3b]/10 dark:border-[#f0eff2]/10 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">
                                                    {template.template_style as string}
                                                </Badge>
                                            </div>
                                            <div className="flex flex-wrap items-center gap-4 text-xs font-medium text-[#3b3b3b]/60 dark:text-[#f0eff2]/60">
                                                {(template.contact_name as string) && (
                                                    <span className="flex items-center gap-1.5 bg-white dark:bg-[#1c1c1c] px-2 py-1 rounded-md border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10">
                                                        <User className="h-3.5 w-3.5" />
                                                        {template.contact_name as string}
                                                    </span>
                                                )}
                                                {(template.contact_company as string) && (
                                                    <span className="flex items-center gap-1.5 bg-white dark:bg-[#1c1c1c] px-2 py-1 rounded-md border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10">
                                                        <Building className="h-3.5 w-3.5" />
                                                        {template.contact_company as string}
                                                    </span>
                                                )}
                                                <span className="flex items-center gap-1.5">
                                                    <Calendar className="h-3.5 w-3.5" />
                                                    {formatDate(template.created_at as string)}
                                                </span>
                                                {(template.effectiveness_score as number) && (
                                                    <span className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400">
                                                        <Star className="h-3.5 w-3.5 fill-current" />
                                                        {((template.effectiveness_score as number) * 100).toFixed(0)}% Score
                                                    </span>
                                                )}
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-2">
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => setExpandedTemplate(
                                                    expandedTemplate === template.id ? null : template.id as string
                                                )}
                                                className="text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 hover:text-[#3b3b3b] dark:hover:text-[#f0eff2] hover:bg-[#3b3b3b]/5 dark:hover:bg-[#f0eff2]/10 h-9 w-9 p-0 rounded-xl"
                                                title="View Content"
                                            >
                                                <Eye className="h-4 w-4" />
                                            </Button>

                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => copyToClipboard(`Subject: ${template.subject_line as string}\n\n${(template.email_body as string) || 'Email body not available'}`)}
                                                className="text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 hover:text-[#3b3b3b] dark:hover:text-[#f0eff2] hover:bg-[#3b3b3b]/5 dark:hover:bg-[#f0eff2]/10 h-9 w-9 p-0 rounded-xl"
                                                title="Copy to Clipboard"
                                            >
                                                <Copy className="h-4 w-4" />
                                            </Button>

                                            {!template.was_sent && (
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => markAsSent(template.id as string)}
                                                    className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/30 h-9 w-9 p-0 rounded-xl"
                                                    title="Mark as Sent"
                                                >
                                                    <Send className="h-4 w-4" />
                                                </Button>
                                            )}

                                            {(template.was_sent as boolean) && !(template.got_response as boolean) && (
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => setShowFeedbackForm(
                                                        showFeedbackForm === template.id ? null : template.id as string
                                                    )}
                                                    className="text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 hover:bg-emerald-50 dark:hover:bg-emerald-900/30 h-9 w-9 p-0 rounded-xl"
                                                    title="Record Feedback"
                                                >
                                                    <Star className="h-4 w-4" />
                                                </Button>
                                            )}

                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => deleteTemplate(template.id as string)}
                                                className="text-[#3b3b3b]/40 dark:text-[#f0eff2]/40 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-900/30 h-9 w-9 p-0 rounded-xl"
                                                title="Delete Template"
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>

                                    {/* Expanded Template Content */}
                                    {expandedTemplate === template.id && (template.email_body as string) && (
                                        <div className="mt-6 p-6 bg-white dark:bg-[#1c1c1c] border border-[#3b3b3b]/10 dark:border-[#f0eff2]/10 rounded-2xl shadow-inner">
                                            <p className="text-xs font-black uppercase tracking-widest text-[#3b3b3b]/40 dark:text-[#f0eff2]/40 mb-3">Template Content</p>
                                            <pre className="text-[#3b3b3b] dark:text-[#f0eff2] text-sm whitespace-pre-wrap font-sans leading-relaxed">
                                                {template.email_body as string}
                                            </pre>
                                        </div>
                                    )}

                                    {/* Feedback Form */}
                                    {showFeedbackForm === template.id && (
                                        <div className="mt-6">
                                            <FeedbackForm
                                                templateId={template.id as string}
                                                onSubmit={() => {
                                                    setShowFeedbackForm(null)
                                                    fetchData()
                                                }}
                                                onCancel={() => setShowFeedbackForm(null)}
                                            />
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