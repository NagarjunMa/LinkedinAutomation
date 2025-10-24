"use client"

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Search,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react'
import { JobStatusModal, JobAnalysis, StatusUpdate } from './job-status-modal'
import { useJobStatusModal } from '@/hooks/use-job-status-modal'
import { updateJobApplicationStatus } from '@/app/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { useActivity } from '@/contexts/activity-context'

interface JobURLExtractorProps {
  userId: string
  onJobExtracted?: (job: any) => void
}

export default function JobURLExtractor({ userId, onJobExtracted }: JobURLExtractorProps) {
  const [url, setUrl] = useState('')
  const [isExtracting, setIsExtracting] = useState(false)
  const [extractedJob, setExtractedJob] = useState<JobAnalysis | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()
  const { trackJobExtractionActivity } = useActivity()

  const {
    isModalOpen,
    currentJob,
    openModal,
    closeModal,
    handleStatusUpdate
  } = useJobStatusModal(async (jobId, statusUpdate) => {
    try {
      // Call the backend API to update job status
      await updateJobApplicationStatus(jobId, statusUpdate)

      // Update local state if needed
      if (extractedJob && extractedJob.id === jobId) {
        setExtractedJob(prev => prev ? { ...prev, status: statusUpdate.status } : null)
      }

      // Show success toast
      toast({
        title: "Status Updated",
        description: `Job status updated to ${statusUpdate.status.replace('_', ' ')}`,
      })

      // Call the callback to refresh data
      if (onJobExtracted) {
        onJobExtracted({ id: jobId, status: statusUpdate.status })
      }
    } catch (error) {
      console.error('Failed to update job status:', error)
      toast({
        title: "Error",
        description: "Failed to update job status",
        variant: "destructive",
      })
      throw error // Re-throw to let the modal handle the error
    }
  })

  const handleExtractJob = async () => {
    if (!url.trim()) return

    setIsExtracting(true)
    setError(null)

    try {
      // Call the backend job extraction API
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      console.log('Making API call to:', `${API_BASE_URL}/api/v1/jobs/extract-from-url`);
      console.log('Request payload:', { url: url.trim(), user_id: userId });

      const response = await fetch(`${API_BASE_URL}/api/v1/jobs/extract-from-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url.trim(),
          user_id: userId
        })
      })

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorData = await response.json()
        console.error('API error response:', errorData);
        throw new Error(errorData.detail || `HTTP ${response.status}: Failed to extract job`)
      }

      const result = await response.json()
      console.log('API success response:', result);

      if (result.success) {
        const jobData = result.extracted_job

        // Transform the API response to match our JobAnalysis interface
        const job: JobAnalysis = {
          id: result.job_id?.toString() || 'unknown',
          title: jobData.title,
          company: jobData.company,
          location: jobData.location,
          description: jobData.description,
          source: jobData.source || 'url_extraction',
          sourceUrl: jobData.application_url || jobData.original_url || url,
          extractedDate: jobData.extracted_at || new Date().toISOString(),
          compatibilityScore: result.compatibility_score,
          aiInsights: jobData.ai_insights
        }

        setExtractedJob(job)

        // Automatically open the status modal after successful extraction
        openModal(job)

        // Show success toast
        toast({
          title: "Job Extracted Successfully!",
          description: `${job.title} at ${job.company}`,
        })

        // Track activity for successful job extraction
        try {
          await trackJobExtractionActivity({
            title: job.title,
            company: job.company,
            source: job.source
          })
        } catch (error) {
          console.error('Failed to track job extraction activity:', error)
        }

        // Call the callback with complete extraction result
        if (onJobExtracted) {
          onJobExtracted({
            ...job,
            ...result, // Include full API response
            extracted_job: result.extracted_job // Include the raw extracted data
          })
        }
      } else {
        setError(result.message || 'Failed to extract job')
      }
    } catch (error: any) {
      console.error('Job extraction failed:', error)
      setError(error.message || 'Failed to extract job from URL')

      toast({
        title: "Extraction Failed",
        description: error.message || 'Failed to extract job from URL',
        variant: "destructive",
      })
    } finally {
      setIsExtracting(false)
    }
  }

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUrl(e.target.value)
    // Clear error when user starts typing
    if (error) setError(null)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && url.trim() && !isExtracting) {
      handleExtractJob()
    }
  }

  return (
    <div className="space-y-6">
      {/* URL Input Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5" />
            Extract Job from URL
          </CardTitle>
          <CardDescription>
            Paste a job URL from LinkedIn, Indeed, or other job boards to extract job details
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="job-url">Job URL</Label>
            <div className="flex gap-2">
              <Input
                id="job-url"
                type="url"
                placeholder="https://linkedin.com/jobs/view/123..."
                value={url}
                onChange={handleUrlChange}
                onKeyPress={handleKeyPress}
                className="flex-1"
                disabled={isExtracting}
              />
              <Button
                onClick={handleExtractJob}
                disabled={!url.trim() || isExtracting}
                className="min-w-[120px]"
              >
                {isExtracting ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Extracting...
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Search className="w-4 h-4" />
                    Extract
                  </div>
                )}
              </Button>
            </div>
          </div>

          {/* Sample URLs */}
          <div className="space-y-2">
            <Label className="text-sm text-cream-300">Try these sample URLs:</Label>
            <div className="flex flex-wrap gap-2">
              {[
                'https://linkedin.com/jobs/view/senior-software-engineer',
                'https://indeed.com/viewjob?jk=abc123',
                'https://glassdoor.com/job-listing/full-stack-developer'
              ].map((sampleUrl) => (
                <Button
                  key={sampleUrl}
                  variant="outline"
                  size="sm"
                  onClick={() => setUrl(sampleUrl)}
                  className="text-xs"
                  disabled={isExtracting}
                >
                  {sampleUrl.includes('linkedin') ? 'LinkedIn' :
                    sampleUrl.includes('indeed') ? 'Indeed' : 'Glassdoor'}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Extraction Progress */}
      {isExtracting && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                <div>
                  <h3 className="font-medium text-blue-800">Extracting Job Details...</h3>
                  <p className="text-blue-600 text-sm">This may take 10-30 seconds</p>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center text-sm text-blue-700">
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Fetching job page content
                </div>
                <div className="flex items-center text-sm text-blue-700">
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Analyzing with AI to extract job details
                </div>
                <div className="flex items-center text-sm text-blue-600">
                  <div className="w-4 h-4 mr-2" />
                  Saving to database and calculating compatibility
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-700">
              <AlertCircle className="w-5 h-5" />
              <span className="font-medium">Extraction Failed</span>
            </div>
            <p className="text-red-600 mt-1">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Extracted Job Display */}
      {extractedJob && (
        <Card className="border-2 border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-800">
              <CheckCircle className="w-5 h-5" />
              Job Extracted Successfully!
            </CardTitle>
            <CardDescription className="text-green-700">
              Review the job details and assign an application status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <h3 className="text-xl font-semibold text-cream-50">
                    {extractedJob.title}
                  </h3>
                  <p className="text-lg text-cream-200">
                    {extractedJob.company} • {extractedJob.location}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="text-sm">
                    {extractedJob.source}
                  </Badge>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openModal(extractedJob)}
                  >
                    Manage Status
                  </Button>
                </div>
              </div>

              {extractedJob.compatibilityScore && (
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-sm text-cream-300">
                    AI Compatibility Score: <strong>{extractedJob.compatibilityScore}%</strong>
                  </span>
                </div>
              )}

              {extractedJob.aiInsights && (
                <div className="text-sm text-cream-300 bg-primary-800 p-3 rounded-lg border border-primary-600">
                  <strong>AI Insights:</strong> {extractedJob.aiInsights}
                </div>
              )}

              <div className="text-sm text-cream-400">
                <strong>Extracted:</strong> {new Date(extractedJob.extractedDate).toLocaleDateString()}
              </div>

              <div className="pt-2">
                <Button
                  onClick={() => openModal(extractedJob)}
                  className="w-full"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Assign Application Status
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Job Status Modal */}
      <JobStatusModal
        isOpen={isModalOpen}
        onClose={closeModal}
        job={currentJob}
        onStatusUpdate={handleStatusUpdate}
      />

      {/* Instructions */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-800">How It Works</CardTitle>
        </CardHeader>
        <CardContent className="text-blue-700 space-y-2">
          <p>1. <strong>Paste URL:</strong> Copy a job posting URL from any job board</p>
          <p>2. <strong>Extract Details:</strong> AI analyzes the job and extracts key information</p>
          <p>3. <strong>Review Analysis:</strong> See compatibility score and AI insights</p>
          <p>4. <strong>Assign Status:</strong> Choose from 4 status options with one click</p>
          <p>5. <strong>Track Progress:</strong> Monitor your job application pipeline</p>
        </CardContent>
      </Card>
    </div>
  )
} 