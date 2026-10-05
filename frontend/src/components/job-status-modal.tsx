"use client"

import React, { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  CheckCircle,
  Clock,
  XCircle,
  Target,
  Calendar as CalendarIcon2
} from 'lucide-react'
import { format } from 'date-fns'
import { cn } from '@/lib/utils'

export interface JobAnalysis {
  id: string
  title: string
  company: string
  location: string
  description: string
  source: string
  sourceUrl: string
  extractedDate: string
  compatibilityScore?: number
  aiInsights?: string
}

export interface StatusUpdate {
  status: 'applied' | 'want_to_apply' | 'maybe_later' | 'not_interested'
  date?: Date
  notes?: string
  context?: string
}

interface JobStatusModalProps {
  isOpen: boolean
  onClose: () => void
  job: JobAnalysis | null
  onStatusUpdate: (statusUpdate: StatusUpdate) => void
}

const statusOptions = [
  {
    id: 'applied' as const,
    label: 'Applied',
    description: 'Mark as applied with date',
    icon: CheckCircle,
    color: 'bg-green-500',
    textColor: 'text-green-700 dark:text-green-300',
    borderColor: 'border-green-200 dark:border-green-700',
    bgColor: 'bg-green-50 dark:bg-green-950'
  },
  {
    id: 'want_to_apply' as const,
    label: 'Want to Apply',
    description: 'Add to application todo list',
    icon: Target,
    color: 'bg-blue-500',
    textColor: 'text-blue-700 dark:text-blue-300',
    borderColor: 'border-blue-200 dark:border-blue-700',
    bgColor: 'bg-blue-50 dark:bg-blue-950'
  },
  {
    id: 'maybe_later' as const,
    label: 'Maybe Later',
    description: 'Schedule for future review',
    icon: Clock,
    color: 'bg-yellow-500',
    textColor: 'text-yellow-700 dark:text-yellow-300',
    borderColor: 'border-yellow-200 dark:border-yellow-700',
    bgColor: 'bg-yellow-50 dark:bg-yellow-950'
  },
  {
    id: 'not_interested' as const,
    label: 'Not Interested',
    description: 'Improve AI matching',
    icon: XCircle,
    color: 'bg-red-500',
    textColor: 'text-red-700 dark:text-red-300',
    borderColor: 'border-red-200 dark:border-red-700',
    bgColor: 'bg-red-50 dark:bg-red-950'
  }
]

export function JobStatusModal({ isOpen, onClose, job, onStatusUpdate }: JobStatusModalProps) {
  const [selectedStatus, setSelectedStatus] = useState<StatusUpdate['status'] | null>(null)
  const [applicationDate, setApplicationDate] = useState<Date | undefined>(undefined)
  const [notes, setNotes] = useState('')
  const [context, setContext] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleStatusSelect = (status: StatusUpdate['status']) => {
    setSelectedStatus(status)

    // Auto-fill context based on status
    if (status === 'applied') {
      setContext('Job application submitted successfully')
    } else if (status === 'want_to_apply') {
      setContext('Added to application todo list')
    } else if (status === 'maybe_later') {
      setContext('Scheduled for future review')
    } else if (status === 'not_interested') {
      setContext('Not a good fit for current goals')
    }
  }

  const handleSubmit = async () => {
    if (!selectedStatus || !job) return

    setIsSubmitting(true)

    try {
      const statusUpdate: StatusUpdate = {
        status: selectedStatus,
        notes: notes.trim() || undefined,
        context: context.trim() || undefined
      }

      // Add date for applied status
      if (selectedStatus === 'applied') {
        statusUpdate.date = applicationDate || new Date()
      }

      await onStatusUpdate(statusUpdate)

      // Reset form and close modal
      resetForm()
      onClose()
    } catch (error) {
      console.error('Failed to update status:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const resetForm = () => {
    setSelectedStatus(null)
    setApplicationDate(undefined)
    setNotes('')
    setContext('')
  }

  const handleClose = () => {
    resetForm()
    onClose()
  }

  if (!job) return null

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-gray-900 dark:text-white">
            Job Analysis Complete
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Job Summary Card */}
          <Card className="border-2 border-gray-100 dark:border-gray-700">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <CardTitle className="text-xl text-gray-900 dark:text-white">{job.title}</CardTitle>
                  <CardDescription className="text-lg text-gray-600 dark:text-gray-300">
                    {job.company} • {job.location}
                  </CardDescription>
                </div>
                <Badge variant="secondary" className="text-sm">
                  {job.source}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {job.compatibilityScore && (
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                    <span className="text-sm text-gray-600 dark:text-gray-300">
                      AI Compatibility Score: <strong>{job.compatibilityScore}%</strong>
                    </span>
                  </div>
                )}
                {job.aiInsights && (
                  <div className="text-sm text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                    <strong>AI Insights:</strong> {job.aiInsights}
                  </div>
                )}
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Extracted on {format(new Date(job.extractedDate), 'MMM dd, yyyy')}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Status Selection */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              What would you like to do with this job?
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {statusOptions.map((option) => {
                const Icon = option.icon
                const isSelected = selectedStatus === option.id

                return (
                  <button
                    key={option.id}
                    onClick={() => handleStatusSelect(option.id)}
                    className={cn(
                      "p-4 rounded-lg border-2 transition-all duration-200 hover:shadow-md",
                      "text-left focus:outline-hidden focus:ring-2 focus:ring-offset-2",
                      isSelected
                        ? `${option.borderColor} ${option.bgColor} ring-2 ring-offset-2 ring-blue-500`
                        : "border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500"
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <div className={cn(
                        "p-2 rounded-lg",
                        option.color,
                        "text-white"
                      )}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1">
                        <h4 className={cn(
                          "font-semibold text-lg mb-1",
                          isSelected ? option.textColor : "text-gray-900 dark:text-white"
                        )}>
                          {option.label}
                        </h4>
                        <p className="text-sm text-gray-600 dark:text-gray-300">
                          {option.description}
                        </p>
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Additional Context Collection */}
          {selectedStatus && (
            <div className="space-y-4 animate-in slide-in-from-bottom-2 duration-300">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Additional Details
              </h3>

              {/* Date Picker for Applied Status */}
              {selectedStatus === 'applied' && (
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    When did you apply?
                  </label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className={cn(
                          "w-full justify-start text-left font-normal",
                          !applicationDate && "text-muted-foreground"
                        )}
                      >
                        <CalendarIcon2 className="mr-2 h-4 w-4" />
                        {applicationDate ? format(applicationDate, "PPP") : "Pick a date"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        selected={applicationDate}
                        onSelect={setApplicationDate}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>
              )}

              {/* Notes Input */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Notes (optional)
                </label>
                <Textarea
                  placeholder="Add any notes about this job or application..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="min-h-[80px]"
                />
              </div>

              {/* Context Input */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Context (optional)
                </label>
                <Textarea
                  placeholder="Why this status? Help improve AI matching..."
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                  className="min-h-[80px]"
                />
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={isSubmitting}
            >
              Cancel
            </Button>

            {selectedStatus && (
              <Button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="min-w-[120px]"
              >
                {isSubmitting ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Updating...
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4" />
                    Update Status
                  </div>
                )}
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
