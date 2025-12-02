"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Building,
  MapPin,
  Calendar,
  DollarSign,
  Mail,
  ExternalLink,
  Star
} from "lucide-react"
import { ReferralRequestModal } from "./referral-request-modal"
import { cn } from "@/lib/utils"

interface JobCardWithReferralProps {
  job: {
    id: string
    title: string
    company: string
    location?: string
    salary?: string
    posted_date?: string
    description?: string
    application_status?: string
  }
  className?: string
}

export function JobCardWithReferral({ job, className }: JobCardWithReferralProps) {
  const [showReferralDialog, setShowReferralDialog] = useState(false)

  const getStatusBadgeVariant = (status?: string) => {
    switch (status?.toLowerCase()) {
      case 'applied':
        return 'bg-green-500/20 text-green-300 border-green-500/30'
      case 'interested':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/30'
      case 'maybe_later':
        return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30'
      case 'not_interested':
        return 'bg-gray-500/20 text-gray-300 border-gray-500/30'
      default:
        return 'bg-primary-700 text-cream-300 border-primary-500'
    }
  }

  return (
    <>
      <Card className={cn(
        "premium-card hover:scale-102 transition-all duration-300 group",
        className
      )}>
        <CardContent className="p-6">
          <div className="space-y-4">
            {/* Header */}
            <div className="flex items-start justify-between">
              <div className="flex-1 space-y-2">
                <h3 className="text-lg font-semibold text-cream-50 group-hover:text-accent-400 transition-colors line-clamp-2">
                  {job.title}
                </h3>
                <div className="flex items-center space-x-2 text-cream-300">
                  <Building className="h-4 w-4" />
                  <span>{job.company}</span>
                </div>
              </div>
              {job.application_status && (
                <Badge className={cn("text-xs", getStatusBadgeVariant(job.application_status))}>
                  {job.application_status.replace('_', ' ').toUpperCase()}
                </Badge>
              )}
            </div>

            {/* Job Details */}
            <div className="space-y-2">
              {job.location && (
                <div className="flex items-center space-x-2 text-sm text-cream-300">
                  <MapPin className="h-4 w-4" />
                  <span>{job.location}</span>
                </div>
              )}

              {job.salary && (
                <div className="flex items-center space-x-2 text-sm text-cream-300">
                  <DollarSign className="h-4 w-4" />
                  <span>{job.salary}</span>
                </div>
              )}

              {job.posted_date && (
                <div className="flex items-center space-x-2 text-sm text-cream-300">
                  <Calendar className="h-4 w-4" />
                  <span>Posted {new Date(job.posted_date).toLocaleDateString()}</span>
                </div>
              )}
            </div>

            {/* Description Preview */}
            {job.description && (
              <div className="text-sm text-cream-300 line-clamp-3">
                {job.description}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center gap-3 pt-2">
              <Button
                variant="default"
                size="sm"
                className="flex-1 bg-gradient-warm hover:bg-gradient-gold text-white"
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                View Job
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowReferralDialog(true)}
                className="border-accent-500/50 text-accent-400 hover:bg-accent-500/20 hover:border-accent-400"
              >
                <Mail className="h-4 w-4 mr-2" />
                Request Referral
              </Button>

              <Button
                variant="ghost"
                size="sm"
                className="text-cream-300 hover:text-cream-50 hover:bg-primary-700"
              >
                <Star className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Referral Request Modal */}
      <ReferralRequestModal
        job={{
          id: job.id,
          title: job.title,
          company: job.company,
          location: job.location || ''
        }}
        isOpen={showReferralDialog}
        onClose={() => setShowReferralDialog(false)}
      />
    </>
  )
}

// Example usage component showing how to integrate into job listings
export function JobListingWithReferrals({ jobs }: { jobs: Array<Record<string, unknown>> }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-cream-50">Job Opportunities</h2>
        <Badge className="bg-accent-500/20 text-accent-400 border-accent-500/30">
          {jobs.length} positions
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {jobs.map((job) => (
          <JobCardWithReferral
            key={job.id}
            job={job}
          />
        ))}
      </div>
    </div>
  )
}