"use client"

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  ResumeEvaluationError,
  ResumeEvaluationErrorBanner,
  determineErrorType
} from './resume-evaluation-error'

// Demo component for testing error handling
export function ResumeEvaluationErrorDemo() {
  const [showTimeoutError, setShowTimeoutError] = useState(false)
  const [showServerError, setShowServerError] = useState(false)
  const [showNetworkError, setShowNetworkError] = useState(false)
  const [showBanner, setShowBanner] = useState(false)

  const handleRetry = () => {
    console.log('Retry evaluation clicked')
  }

  return (
    <div className="p-8 space-y-6">
      <h2 className="text-2xl font-bold">Resume Evaluation Error Handling Demo</h2>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Error Modals</h3>
        <div className="flex gap-2 flex-wrap">
          <Button onClick={() => setShowTimeoutError(true)} variant="outline">
            Show Timeout Error
          </Button>
          <Button onClick={() => setShowServerError(true)} variant="outline">
            Show Server Error
          </Button>
          <Button onClick={() => setShowNetworkError(true)} variant="outline">
            Show Network Error
          </Button>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Error Banner</h3>
        <Button onClick={() => setShowBanner(true)} variant="outline">
          Show Error Banner
        </Button>

        {showBanner && (
          <ResumeEvaluationErrorBanner
            errorType="server"
            onRetry={handleRetry}
            onDismiss={() => setShowBanner(false)}
            resumeFilename="my-resume.pdf"
          />
        )}
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Error Type Detection</h3>
        <div className="bg-muted p-4 rounded-lg">
          <div className="space-y-2 text-sm">
            <div><strong>Timeout:</strong> {determineErrorType("Request timeout")}</div>
            <div><strong>Network:</strong> {determineErrorType("Failed to fetch")}</div>
            <div><strong>Server:</strong> {determineErrorType("500 Internal Server Error")}</div>
            <div><strong>Unknown:</strong> {determineErrorType("Something went wrong")}</div>
          </div>
        </div>
      </div>

      {/* Error Modals */}
      <ResumeEvaluationError
        isOpen={showTimeoutError}
        onClose={() => setShowTimeoutError(false)}
        onRetry={handleRetry}
        errorType="timeout"
        errorMessage="Evaluation timed out after 5 minutes"
        resumeFilename="my-resume.pdf"
      />

      <ResumeEvaluationError
        isOpen={showServerError}
        onClose={() => setShowServerError(false)}
        onRetry={handleRetry}
        errorType="server"
        errorMessage="500 Internal Server Error"
        resumeFilename="my-resume.pdf"
      />

      <ResumeEvaluationError
        isOpen={showNetworkError}
        onClose={() => setShowNetworkError(false)}
        onRetry={handleRetry}
        errorType="network"
        errorMessage="Failed to fetch - Network unavailable"
        resumeFilename="my-resume.pdf"
      />
    </div>
  )
}