'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loader2, ExternalLink, CheckCircle, AlertCircle, Copy, Globe, Zap } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ExtractedJob {
    job_id: number
    application_id?: number
    extracted_job: {
        title: string
        company: string
        location: string
        salary_range?: string
        job_type?: string
        experience_level?: string
        remote_policy?: string
        description: string
        requirements: string
        skills: string[]
        benefits?: string[]
        confidence: number
    }
    compatibility_score?: number
    extraction_confidence: number
    message: string
}

interface JobURLExtractorProps {
    userId: string
    onJobExtracted?: (job: ExtractedJob) => void
}

export default function JobURLExtractor({ userId, onJobExtracted }: JobURLExtractorProps) {
    const [url, setUrl] = useState('')
    const [extracting, setExtracting] = useState(false)
    const [extractedJobs, setExtractedJobs] = useState<ExtractedJob[]>([])
    const [error, setError] = useState('')
    const { toast } = useToast()

    const validateUrl = (urlString: string): boolean => {
        try {
            const url = new URL(urlString)
            return ['http:', 'https:'].includes(url.protocol)
        } catch {
            return false
        }
    }

    const extractJob = async () => {
        if (!url.trim()) {
            setError('Please enter a job URL')
            return
        }

        if (!validateUrl(url.trim())) {
            setError('Please enter a valid URL')
            return
        }

        setExtracting(true)
        setError('')

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/jobs/extract-from-url`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: url.trim(),
                    user_id: userId,
                    auto_apply: true,
                    application_notes: 'Extracted via AI job extraction tool'
                })
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Extraction failed')
            }

            const result: ExtractedJob = await response.json()

            // Add to extracted jobs list
            setExtractedJobs(prev => [result, ...prev])
            setUrl('') // Clear input

            // Call callback if provided
            if (onJobExtracted) {
                onJobExtracted(result)
            }

            // Show success toast
            toast({
                title: "Job extracted successfully!",
                description: `${result.extracted_job.title || 'Unknown Position'} at ${result.extracted_job.company || 'Unknown Company'}`,
            })

        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Extraction failed'
            setError(errorMessage)
            toast({
                title: "Extraction failed",
                description: errorMessage,
                variant: "destructive",
            })
        } finally {
            setExtracting(false)
        }
    }

    const handlePasteFromClipboard = async () => {
        try {
            const text = await navigator.clipboard.readText()
            if (validateUrl(text)) {
                setUrl(text)
                setError('')
            } else {
                setError('Clipboard does not contain a valid URL')
            }
        } catch (err) {
            setError('Failed to read from clipboard')
        }
    }

    const getConfidenceColor = (confidence: number): string => {
        if (confidence >= 0.8) return 'bg-green-500'
        if (confidence >= 0.6) return 'bg-yellow-500'
        return 'bg-red-500'
    }

    const getConfidenceText = (confidence: number): string => {
        if (confidence >= 0.8) return 'High'
        if (confidence >= 0.6) return 'Medium'
        return 'Low'
    }

    return (
        <div className="space-y-6">
            {/* URL Input Section */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Globe className="h-5 w-5" />
                        Extract Job from URL
                    </CardTitle>
                    <p className="text-sm text-muted-foreground">
                        Paste any job posting URL to automatically extract details and track your application
                    </p>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex gap-2">
                        <Input
                            placeholder="https://company.com/careers/job-posting..."
                            value={url}
                            onChange={(e) => {
                                setUrl(e.target.value)
                                setError('')
                            }}
                            className="flex-1"
                            onKeyPress={(e) => {
                                if (e.key === 'Enter' && !extracting) {
                                    extractJob()
                                }
                            }}
                        />
                        <Button
                            variant="outline"
                            onClick={handlePasteFromClipboard}
                            disabled={extracting}
                        >
                            <Copy className="h-4 w-4" />
                        </Button>
                    </div>

                    <div className="flex gap-2">
                        <Button
                            onClick={extractJob}
                            disabled={extracting || !url.trim()}
                            className="flex-1"
                        >
                            {extracting ? (
                                <>
                                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                    Extracting...
                                </>
                            ) : (
                                <>
                                    <ExternalLink className="h-4 w-4 mr-2" />
                                    Extract & Track Job
                                </>
                            )}
                        </Button>
                    </div>

                    {error && (
                        <div className="flex items-center gap-2 text-red-600 text-sm">
                            <AlertCircle className="h-4 w-4" />
                            {error}
                        </div>
                    )}

                    <div className="text-xs text-muted-foreground">
                        <p>✨ <strong>Powered by AI:</strong> Free Jina AI Reader + OpenAI GPT-4o-mini</p>
                        <p>🎯 <strong>Supports:</strong> Indeed, LinkedIn, Glassdoor, Stack Overflow Jobs, and most job sites</p>
                        <p>📊 <strong>Auto-scoring:</strong> Jobs are automatically scored against your profile</p>
                    </div>
                </CardContent>
            </Card>

            {/* Extracted Jobs Results */}
            {extractedJobs.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <CheckCircle className="h-5 w-5 text-green-600" />
                            Recently Extracted Jobs ({extractedJobs.length})
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {extractedJobs.map((result, index) => (
                            <div key={index} className="border rounded-lg p-4 space-y-3">
                                <div className="flex justify-between items-start">
                                    <div className="space-y-1">
                                        <h4 className="font-semibold text-lg">{result.extracted_job.title}</h4>
                                        <p className="text-muted-foreground">{result.extracted_job.company}</p>
                                        {result.extracted_job.location && (
                                            <p className="text-sm text-muted-foreground">{result.extracted_job.location}</p>
                                        )}
                                    </div>

                                    <div className="text-right space-y-2">
                                        {result.compatibility_score && (
                                            <Badge variant="secondary" className="text-sm">
                                                Match: {result.compatibility_score}%
                                            </Badge>
                                        )}
                                        <div className="flex items-center gap-2">
                                            <div className={`w-2 h-2 rounded-full ${getConfidenceColor(result.extraction_confidence)}`} />
                                            <span className="text-xs text-muted-foreground">
                                                {getConfidenceText(result.extraction_confidence)} confidence
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {result.extracted_job.salary_range && (
                                    <div className="flex items-center gap-2">
                                        <Badge variant="outline">{result.extracted_job.salary_range}</Badge>
                                        {result.extracted_job.job_type && (
                                            <Badge variant="outline">{result.extracted_job.job_type}</Badge>
                                        )}
                                        {result.extracted_job.remote_policy && (
                                            <Badge variant="outline">{result.extracted_job.remote_policy}</Badge>
                                        )}
                                    </div>
                                )}

                                {result.extracted_job.skills && result.extracted_job.skills.length > 0 && (
                                    <div className="space-y-1">
                                        <p className="text-sm font-medium">Required Skills:</p>
                                        <div className="flex flex-wrap gap-1">
                                            {result.extracted_job.skills.slice(0, 6).map((skill, skillIndex) => (
                                                <Badge key={skillIndex} variant="secondary" className="text-xs">
                                                    {skill}
                                                </Badge>
                                            ))}
                                            {result.extracted_job.skills.length > 6 && (
                                                <Badge variant="secondary" className="text-xs">
                                                    +{result.extracted_job.skills.length - 6} more
                                                </Badge>
                                            )}
                                        </div>
                                    </div>
                                )}

                                <div className="text-sm text-muted-foreground">
                                    {result.extracted_job.description && (
                                        <p className="line-clamp-2">{result.extracted_job.description}</p>
                                    )}
                                </div>

                                <div className="flex justify-between items-center pt-2 border-t">
                                    <div className="text-xs text-muted-foreground">
                                        {result.application_id ? (
                                            <>✅ Tracked as application #{result.application_id}</>
                                        ) : (
                                            <>📋 Job saved to database</>
                                        )}
                                    </div>

                                    <div className="flex gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => {
                                                // Navigate to job details or application tracking
                                                toast({
                                                    title: "Feature coming soon",
                                                    description: "Job details view will be available in the next update",
                                                })
                                            }}
                                        >
                                            View Details
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </CardContent>
                </Card>
            )}

            {/* Usage Tips */}
            {extractedJobs.length === 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-base">💡 How to use</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                            <div className="space-y-2">
                                <h4 className="font-medium">📋 Step-by-step:</h4>
                                <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
                                    <li>Copy a job posting URL</li>
                                    <li>Paste it in the input above</li>
                                    <li>Click "Extract & Track Job"</li>
                                    <li>Review the extracted details</li>
                                    <li>Check your dashboard for tracking</li>
                                </ol>
                            </div>

                            <div className="space-y-2">
                                <h4 className="font-medium">🎯 What happens next:</h4>
                                <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                                    <li>Job details are extracted via AI</li>
                                    <li>Compatibility score is calculated</li>
                                    <li>Application is automatically tracked</li>
                                    <li>You can manage it in your dashboard</li>
                                </ul>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Showcase Prompts - Show when no jobs extracted */}
            {extractedJobs.length === 0 && (
                <Card>
                <CardHeader>
                    <CardTitle className="text-base">🚀 Job URL Extractor Showcase</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        <Card className="p-4 border-dashed border-2 border-gray-300 hover:border-blue-400 transition-colors">
                            <div className="text-center space-y-2">
                                <Zap className="h-8 w-8 mx-auto text-blue-500" />
                                <h4 className="font-medium">AI-Powered Extraction</h4>
                                <p className="text-sm text-muted-foreground">
                                    Automatically extract job details using advanced AI technology
                                </p>
                            </div>
                        </Card>

                        <Card className="p-4 border-dashed border-2 border-gray-300 hover:border-green-400 transition-colors">
                            <div className="text-center space-y-2">
                                <CheckCircle className="h-8 w-8 mx-auto text-green-500" />
                                <h4 className="font-medium">Auto Application Tracking</h4>
                                <p className="text-sm text-muted-foreground">
                                    Automatically track your job applications with detailed metadata
                                </p>
                            </div>
                        </Card>

                        <Card className="p-4 border-dashed border-2 border-gray-300 hover:border-purple-400 transition-colors">
                            <div className="text-center space-y-2">
                                <Globe className="h-8 w-8 mx-auto text-purple-500" />
                                <h4 className="font-medium">Universal Compatibility</h4>
                                <p className="text-sm text-muted-foreground">
                                    Works with any job site - LinkedIn, Indeed, company careers pages, and more
                                </p>
                            </div>
                        </Card>
                    </div>

                    <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
                        <CardContent className="p-6">
                            <div className="space-y-4">
                                <div className="flex items-start gap-3">
                                    <div className="bg-blue-100 p-2 rounded-full">
                                        <Globe className="h-5 w-5 text-blue-600" />
                                    </div>
                                    <div>
                                        <h4 className="font-medium text-blue-900">How It Works</h4>
                                        <ol className="mt-2 space-y-1 text-sm text-blue-800 list-decimal list-inside">
                                            <li>Copy any job URL from LinkedIn, Indeed, company career pages, etc.</li>
                                            <li>Paste the URL into the input field above</li>
                                            <li>Our AI extracts job details, requirements, and company information</li>
                                            <li>The job is automatically added to your application tracker</li>
                                            <li>Get AI-powered compatibility scores based on your resume</li>
                                        </ol>
                                    </div>
                                </div>

                                <div className="flex items-start gap-3">
                                    <div className="bg-green-100 p-2 rounded-full">
                                        <CheckCircle className="h-5 w-5 text-green-600" />
                                    </div>
                                    <div>
                                        <h4 className="font-medium text-green-900">Supported Job Sites</h4>
                                        <div className="mt-2 flex flex-wrap gap-2">
                                            {[
                                                'LinkedIn', 'Indeed', 'Glassdoor', 'AngelList', 'Stack Overflow Jobs',
                                                'Company Career Pages', 'Greenhouse', 'Lever', 'Workday', 'And More!'
                                            ].map((site, index) => (
                                                <Badge key={index} variant="secondary" className="text-xs bg-green-100 text-green-800">
                                                    {site}
                                                </Badge>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </CardContent>
            </Card>
            )}
        </div>
    )
} 