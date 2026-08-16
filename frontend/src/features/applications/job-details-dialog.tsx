'use client';

import { ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import type { JobDetails } from './model';

interface JobDetailsDialogProps {
  details?: JobDetails;
  error: Error | null;
  isLoading: boolean;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onRetry: () => void;
}

export function JobDetailsDialog({
  details,
  error,
  isLoading,
  open,
  onOpenChange,
  onRetry,
}: JobDetailsDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[80vh] max-w-4xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold">
            {details?.title || 'Job details'}
          </DialogTitle>
          <DialogDescription>
            {details ? `${details.company} · ${details.location}` : 'Application record'}
          </DialogDescription>
        </DialogHeader>

        {isLoading && (
          <div className="flex items-center justify-center py-12" role="status">
            <span className="h-6 w-6 animate-spin rounded-full border-2 border-muted border-t-foreground" />
            <span className="ml-3 text-sm text-muted-foreground">Loading job details...</span>
          </div>
        )}

        {error && !isLoading && (
          <div className="border border-destructive/20 bg-destructive/5 p-5">
            <p className="text-sm font-medium text-foreground">Job details could not be loaded.</p>
            <p className="mt-1 text-sm text-muted-foreground">{error.message}</p>
            <Button className="mt-4" variant="outline" size="sm" onClick={onRetry}>
              Try again
            </Button>
          </div>
        )}

        {details && !isLoading && !error && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Detail label="Job type" value={details.jobType} />
              <Detail label="Experience level" value={details.experienceLevel} />
              <Detail label="Salary range" value={details.salaryRange} fallback="Not disclosed" />
              <Detail
                label="Posted date"
                value={details.postedDate ? new Date(details.postedDate).toLocaleDateString() : undefined}
                fallback="Unknown"
              />
            </div>

            <TextSection title="Job description" value={details.description} />
            <TextSection title="Requirements" value={details.requirements} />

            {details.skills.length > 0 && (
              <section className="space-y-2">
                <h3 className="font-semibold text-foreground">Required skills</h3>
                <div className="flex flex-wrap gap-2">
                  {details.skills.map((skill) => (
                    <span key={skill} className="border border-border bg-muted px-2 py-1 text-xs">
                      {skill}
                    </span>
                  ))}
                </div>
              </section>
            )}

            <div className="flex gap-3 border-t border-border pt-4">
              <Button
                onClick={() => details.applicationUrl && window.open(details.applicationUrl, '_blank', 'noopener,noreferrer')}
                disabled={!details.applicationUrl}
              >
                <ExternalLink className="mr-2 h-4 w-4" aria-hidden="true" />
                {details.applicationUrl ? 'Open application' : 'Application URL missing'}
              </Button>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Close
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function Detail({ label, value, fallback = 'Not specified' }: {
  label: string;
  value?: string;
  fallback?: string;
}) {
  return (
    <div className="space-y-2">
      <h3 className="font-semibold text-foreground">{label}</h3>
      <p className="text-muted-foreground">{value || fallback}</p>
    </div>
  );
}

function TextSection({ title, value }: { title: string; value?: string }) {
  if (!value) return null;
  return (
    <section className="space-y-2">
      <h3 className="font-semibold text-foreground">{title}</h3>
      <div className="border border-border bg-muted p-4">
        <p className="whitespace-pre-wrap text-muted-foreground">{value}</p>
      </div>
    </section>
  );
}
