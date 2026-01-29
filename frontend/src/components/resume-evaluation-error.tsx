"use client"

import React from 'react'
import {
  AlertCircle,
  RefreshCw,
  Mail,
  X
} from 'lucide-react'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui/alert'
import { Button } from '@/components/ui/button'

interface ResumeEvaluationErrorProps {
  isOpen: boolean
  onClose: () => void
  onRetry: () => void
  errorType?: 'timeout' | 'server' | 'network' | 'unknown'
  errorMessage?: string
  resumeFilename?: string
}

// Error type configurations with specific user guidance
const ERROR_CONFIGS = {
  timeout: {
    title: 'Evaluation Timeout',
    description: 'The resume analysis took longer than expected and timed out.',
    guidance: 'This usually happens during high server load. Please try again in a few minutes.',
    iconColor: 'text-amber-500',
    retryRecommended: true,
  },
  server: {
    title: 'Server Error',
    description: 'Our AI evaluation service encountered an internal error.',
    guidance: 'Our team has been automatically notified. Please try again, or contact support if the issue persists.',
    iconColor: 'text-red-500',
    retryRecommended: true,
  },
  network: {
    title: 'Connection Error',
    description: 'Unable to connect to our evaluation service.',
    guidance: 'Please check your internet connection and try again.',
    iconColor: 'text-orange-500',
    retryRecommended: true,
  },
  unknown: {
    title: 'Evaluation Failed',
    description: 'An unexpected error occurred during resume analysis.',
    guidance: 'Please try uploading your resume again. If the problem continues, our support team can help.',
    iconColor: 'text-red-500',
    retryRecommended: true,
  },
} as const

export function ResumeEvaluationError({
  isOpen,
  onClose,
  onRetry,
  errorType = 'unknown',
  errorMessage,
  resumeFilename
}: ResumeEvaluationErrorProps) {
  const config = ERROR_CONFIGS[errorType]

  return (
    <AlertDialog open={isOpen} onOpenChange={onClose}>
      <AlertDialogContent className="max-w-md">
        <AlertDialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <AlertCircle className={`w-6 h-6 ${config.iconColor}`} />
            <AlertDialogTitle className="text-lg font-black text-foreground">
              {config.title}
            </AlertDialogTitle>
          </div>

          {resumeFilename && (
            <div className="text-xs text-muted-foreground font-medium">
              File: {resumeFilename}
            </div>
          )}
        </AlertDialogHeader>

        <div className="space-y-4">
          <AlertDialogDescription className="text-sm text-muted-foreground leading-relaxed">
            {config.description}
          </AlertDialogDescription>

          {/* User Guidance */}
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle className="text-sm font-bold">What to do next</AlertTitle>
            <AlertDescription className="text-sm mt-2">
              {config.guidance}
            </AlertDescription>
          </Alert>

          {/* Technical Error Details (if provided) */}
          {errorMessage && (
            <div className="p-3 bg-muted/50 rounded-lg border">
              <div className="text-xs font-bold text-muted-foreground uppercase tracking-wide mb-1">
                Technical Details
              </div>
              <div className="text-xs text-muted-foreground font-mono">
                {errorMessage}
              </div>
            </div>
          )}
        </div>

        <AlertDialogFooter className="flex-col sm:flex-row gap-2">
          {/* Contact Support */}
          <Button
            variant="outline"
            size="sm"
            className="w-full sm:w-auto"
            onClick={() => window.open('mailto:support@jobflowpro.com?subject=Resume Evaluation Error&body=Error details: ' + encodeURIComponent(errorMessage || config.description))}
          >
            <Mail className="w-4 h-4 mr-2" />
            Contact Support
          </Button>

          <div className="flex gap-2 w-full sm:w-auto">
            <AlertDialogCancel className="flex-1 sm:flex-none">
              Close
            </AlertDialogCancel>

            {config.retryRecommended && (
              <AlertDialogAction
                onClick={(e) => {
                  e.preventDefault()
                  onRetry()
                  onClose()
                }}
                className="flex-1 sm:flex-none"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Try Again
              </AlertDialogAction>
            )}
          </div>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

interface ResumeEvaluationErrorBannerProps {
  errorType?: 'timeout' | 'server' | 'network' | 'unknown'
  onRetry: () => void
  onDismiss?: () => void
  resumeFilename?: string
}

export function ResumeEvaluationErrorBanner({
  errorType = 'unknown',
  onRetry,
  onDismiss,
  resumeFilename
}: ResumeEvaluationErrorBannerProps) {
  const config = ERROR_CONFIGS[errorType]

  return (
    <Alert variant="destructive" className="mb-6">
      <AlertCircle className="h-4 w-4" />
      <div className="flex-1">
        <AlertTitle className="font-black text-sm mb-1">
          Resume Evaluation Failed
        </AlertTitle>
        <AlertDescription className="text-sm mb-3">
          {config.description} {config.guidance}
        </AlertDescription>

        {resumeFilename && (
          <div className="text-xs opacity-75 mb-3">
            File: {resumeFilename}
          </div>
        )}

        <div className="flex items-center gap-2">
          {config.retryRecommended && (
            <Button
              size="sm"
              variant="outline"
              onClick={onRetry}
              className="h-8 text-xs"
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              Retry Evaluation
            </Button>
          )}

          <Button
            size="sm"
            variant="outline"
            onClick={() => window.open('mailto:support@jobflowpro.com?subject=Resume Evaluation Error')}
            className="h-8 text-xs"
          >
            <Mail className="w-3 h-3 mr-1" />
            Contact Support
          </Button>
        </div>
      </div>

      {onDismiss && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onDismiss}
          className="p-1 h-auto min-h-0 ml-2"
        >
          <X className="h-3 w-3" />
        </Button>
      )}
    </Alert>
  )
}

// Helper function to determine error type from error message
export function determineErrorType(error: string | Error | null): 'timeout' | 'server' | 'network' | 'unknown' {
  if (!error) return 'unknown'

  const errorMessage = typeof error === 'string' ? error : error.message
  const lowerMessage = errorMessage.toLowerCase()

  if (lowerMessage.includes('timeout') || lowerMessage.includes('time out')) {
    return 'timeout'
  }

  if (lowerMessage.includes('network') || lowerMessage.includes('fetch') || lowerMessage.includes('connection')) {
    return 'network'
  }

  if (lowerMessage.includes('500') || lowerMessage.includes('server') || lowerMessage.includes('internal')) {
    return 'server'
  }

  return 'unknown'
}