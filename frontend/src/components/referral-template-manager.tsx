"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/components/ui/use-toast"
import { referralTemplatesAPI } from '@/app/lib/api'
import {
    MessageSquare,
    Send,
    Copy,
    Trash2,
    Calendar,
    Building,
    User,
    Star,
    Plus,
    Filter,
    Download,
    BarChart3,
    Eye,
    Clock,
    CheckCircle,
    AlertCircle,
    Search
} from "lucide-react"
import { cn } from "@/lib/utils"

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
        <div className="space-y-4 p-4 bg-primary-950 border border-primary-700 rounded-lg">
            <h4 className="text-cream-50 font-medium">Provide Feedback</h4>

            <div className="space-y-3">
                <div className="flex items-center gap-4">
                    <label className="text-cream-200 text-sm">Did you get a response?</label>
                    <div className="flex gap-2">
                        <Button
                            variant={feedback.got_response ? "default" : "outline"}
                            size="sm"
                            onClick={() => setFeedback({...feedback, got_response: true})}
                            className={feedback.got_response ? "bg-green-600" : "border-primary-700"}
                        >
                            Yes
                        </Button>
                        <Button
                            variant={!feedback.got_response ? "default" : "outline"}
                            size="sm"
                            onClick={() => setFeedback({...feedback, got_response: false})}
                            className={!feedback.got_response ? "bg-red-600" : "border-primary-700"}
                        >
                            No
                        </Button>
                    </div>
                </div>

                {feedback.got_response && (
                    <div className="space-y-2">
                        <label className="text-cream-200 text-sm">Response Type</label>
                        <Input
                            placeholder="e.g., positive_reply, interview_scheduled, referred"
                            value={feedback.response_type}
                            onChange={(e) => setFeedback({...feedback, response_type: e.target.value})}
                            className="bg-primary-950 border-primary-700 text-cream-50"
                        />
                    </div>
                )}

                <div className="space-y-2">
                    <label className="text-cream-200 text-sm">Template Satisfaction (1-5)</label>
                    <Input
                        type="number"
                        min={1}
                        max={5}
                        value={feedback.user_satisfaction_score}
                        onChange={(e) => setFeedback({...feedback, user_satisfaction_score: parseInt(e.target.value)})}
                        className="bg-primary-950 border-primary-700 text-cream-50"
                    />
                </div>

                <div className="space-y-2">
                    <label className="text-cream-200 text-sm">Additional Notes</label>
                    <Textarea
                        placeholder="Any additional feedback..."
                        value={feedback.feedback_notes}
                        onChange={(e) => setFeedback({...feedback, feedback_notes: e.target.value})}
                        className="bg-primary-950 border-primary-700 text-cream-50"
                        rows={3}
                    />
                </div>
            </div>

            <div className="flex gap-2">
                <Button
                    onClick={submitFeedback}
                    disabled={submitting}
                    className="bg-accent-500 hover:bg-accent-600"
                    size="sm"
                >
                    {submitting ? "Submitting..." : "Submit Feedback"}
                </Button>
                <Button
                    variant="outline"
                    onClick={onCancel}
                    size="sm"
                    className="border-primary-700"
                >
                    Cancel
                </Button>
            </div>
        </div>
    )
}

export function ReferralTemplateManager() {
    const [templates, setTemplates] = useState<any[]>([])
    const [stats, setStats] = useState<any>(null)
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
            setTemplates(templatesData)
            setStats(statsData)
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

    const getStatusBadge = (template: any) => {
        if (template.got_response) {
            return (
                <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Responded
                </Badge>
            )
        } else if (template.was_sent) {
            return (
                <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                    <Send className="h-3 w-3 mr-1" />
                    Sent
                </Badge>
            )
        } else {
            return (
                <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30">
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
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-500"></div>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Statistics Cards */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <Card className="bg-primary-900/50 border-primary-800">
                        <CardContent className="pt-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-cream-300">Total Templates</p>
                                    <p className="text-2xl font-bold text-cream-50">{stats.total_templates}</p>
                                </div>
                                <MessageSquare className="h-8 w-8 text-accent-400" />
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="bg-primary-900/50 border-primary-800">
                        <CardContent className="pt-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-cream-300">Sent</p>
                                    <p className="text-2xl font-bold text-cream-50">{stats.sent_count}</p>
                                </div>
                                <Send className="h-8 w-8 text-blue-400" />
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="bg-primary-900/50 border-primary-800">
                        <CardContent className="pt-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-cream-300">Response Rate</p>
                                    <p className="text-2xl font-bold text-cream-50">{stats.response_rate.toFixed(1)}%</p>
                                </div>
                                <BarChart3 className="h-8 w-8 text-green-400" />
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="bg-primary-900/50 border-primary-800">
                        <CardContent className="pt-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-cream-300">Avg Effectiveness</p>
                                    <p className="text-2xl font-bold text-cream-50">{stats.avg_effectiveness.toFixed(1)}</p>
                                </div>
                                <Star className="h-8 w-8 text-yellow-400" />
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Templates List */}
            <Card className="bg-primary-900/50 border-primary-800">
                <CardHeader>
                    <CardTitle className="text-cream-50 flex items-center gap-2">
                        <MessageSquare className="h-5 w-5 text-accent-400" />
                        Your Templates ({templates.length})
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {templates.length === 0 ? (
                        <div className="text-center py-8">
                            <MessageSquare className="h-12 w-12 text-cream-400 mx-auto mb-4" />
                            <p className="text-cream-300">No templates created yet</p>
                            <p className="text-cream-400 text-sm">Generate your first referral template to get started</p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {templates.map((template) => (
                                <div
                                    key={template.id}
                                    className="border border-primary-700 rounded-lg p-4 space-y-3"
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="space-y-1">
                                            <div className="flex items-center gap-3">
                                                <h4 className="text-cream-50 font-medium">{template.subject_line}</h4>
                                                {getStatusBadge(template)}
                                                <Badge className="bg-gray-500/20 text-gray-400 border-gray-500/30">
                                                    {template.template_style}
                                                </Badge>
                                            </div>
                                            <div className="flex items-center gap-4 text-sm text-cream-400">
                                                {template.contact_name && (
                                                    <span className="flex items-center gap-1">
                                                        <User className="h-4 w-4" />
                                                        {template.contact_name}
                                                    </span>
                                                )}
                                                {template.contact_company && (
                                                    <span className="flex items-center gap-1">
                                                        <Building className="h-4 w-4" />
                                                        {template.contact_company}
                                                    </span>
                                                )}
                                                <span className="flex items-center gap-1">
                                                    <Calendar className="h-4 w-4" />
                                                    {formatDate(template.created_at)}
                                                </span>
                                                {template.effectiveness_score && (
                                                    <span className="flex items-center gap-1">
                                                        <Star className="h-4 w-4" />
                                                        {(template.effectiveness_score * 100).toFixed(0)}%
                                                    </span>
                                                )}
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-2">
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => setExpandedTemplate(
                                                    expandedTemplate === template.id ? null : template.id
                                                )}
                                                className="text-cream-400 hover:text-cream-200"
                                            >
                                                <Eye className="h-4 w-4" />
                                            </Button>

                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => copyToClipboard(`Subject: ${template.subject_line}\n\n${template.email_body || 'Email body not available'}`)}
                                                className="text-cream-400 hover:text-cream-200"
                                            >
                                                <Copy className="h-4 w-4" />
                                            </Button>

                                            {!template.was_sent && (
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => markAsSent(template.id)}
                                                    className="text-blue-400 hover:text-blue-300"
                                                >
                                                    <Send className="h-4 w-4" />
                                                </Button>
                                            )}

                                            {template.was_sent && !template.got_response && (
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => setShowFeedbackForm(
                                                        showFeedbackForm === template.id ? null : template.id
                                                    )}
                                                    className="text-green-400 hover:text-green-300"
                                                >
                                                    <Star className="h-4 w-4" />
                                                </Button>
                                            )}

                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => deleteTemplate(template.id)}
                                                className="text-red-400 hover:text-red-300"
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>

                                    {/* Expanded Template Content */}
                                    {expandedTemplate === template.id && template.email_body && (
                                        <div className="mt-3 p-3 bg-primary-950 border border-primary-700 rounded-lg">
                                            <pre className="text-cream-50 text-sm whitespace-pre-wrap font-sans">
                                                {template.email_body}
                                            </pre>
                                        </div>
                                    )}

                                    {/* Feedback Form */}
                                    {showFeedbackForm === template.id && (
                                        <FeedbackForm
                                            templateId={template.id}
                                            onSubmit={() => {
                                                setShowFeedbackForm(null)
                                                fetchData()
                                            }}
                                            onCancel={() => setShowFeedbackForm(null)}
                                        />
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