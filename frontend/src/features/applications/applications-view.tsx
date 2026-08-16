'use client';

import type { ReactNode } from 'react';
import {
  Briefcase,
  Calendar,
  CheckCircle,
  Clock,
  ExternalLink,
  MapPin,
  Plus,
  Search,
  Target,
  TrendingUp,
  Users,
  X,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import type { ApplicationStats, TrackedApplication } from './model';

interface ApplicationsViewProps {
  error: Error | null;
  extractor: ReactNode;
  filteredApplications: TrackedApplication[];
  isExtractorOpen: boolean;
  isLoading: boolean;
  loadingJobId: string | null;
  recentlyExtractedJob: TrackedApplication | null;
  searchTerm: string;
  stats: ApplicationStats;
  statusFilter: string;
  onDismissRecent: () => void;
  onOpenExtractor: () => void;
  onRetry: () => void;
  onSearchChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onViewJob: (application: TrackedApplication) => void;
}

const statusConfig = {
  applied: { label: 'Applied', icon: CheckCircle },
  interview_scheduled: { label: 'Interview Scheduled', icon: Clock },
  want_to_apply: { label: 'Want to Apply', icon: Target },
  not_interested: { label: 'Not Interested', icon: X },
};

export function ApplicationsView(props: ApplicationsViewProps) {
  const {
    error,
    extractor,
    filteredApplications,
    isExtractorOpen,
    isLoading,
    loadingJobId,
    recentlyExtractedJob,
    searchTerm,
    stats,
    statusFilter,
    onDismissRecent,
    onOpenExtractor,
    onRetry,
    onSearchChange,
    onStatusChange,
    onViewJob,
  } = props;

  return (
    <div className="min-h-screen space-y-8 bg-background px-4 py-8 font-sans text-foreground sm:px-6 lg:px-8">
      <header className="flex flex-col justify-between gap-6 border-b border-foreground/5 pb-6 sm:flex-row sm:items-end">
        <div>
          <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.3em] text-foreground/40">Workspace</p>
          <h1 className="font-serif-italic text-3xl tracking-tight text-foreground">Applications</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Track roles, status, resume fit, and interview follow-up from one quiet ledger.
          </p>
        </div>
        <Button onClick={onOpenExtractor} className="rounded-sm px-5 py-2 text-[10px] font-bold uppercase tracking-widest">
          <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
          Extract Job URL
        </Button>
      </header>

      {isExtractorOpen && extractor}

      {recentlyExtractedJob && (
        <RecentApplicationCard
          application={recentlyExtractedJob}
          onDismiss={onDismissRecent}
          onView={onViewJob}
        />
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-12" role="status">
          <span className="h-8 w-8 animate-spin rounded-full border-2 border-muted border-t-primary" />
          <span className="ml-3 font-medium text-muted-foreground">Loading applications...</span>
        </div>
      )}

      {error && !isLoading && (
        <div className="border border-destructive/20 bg-destructive/5 p-5">
          <p className="font-medium">Applications could not be loaded.</p>
          <p className="mt-1 text-sm text-muted-foreground">{error.message}</p>
          <Button className="mt-4" variant="outline" size="sm" onClick={onRetry}>Try again</Button>
        </div>
      )}

      {!isLoading && !error && (
        <>
          <StatsGrid stats={stats} />
          <ApplicationFilters
            searchTerm={searchTerm}
            statusFilter={statusFilter}
            onSearchChange={onSearchChange}
            onStatusChange={onStatusChange}
          />
          <ApplicationList
            applications={filteredApplications}
            hasFilters={Boolean(searchTerm) || statusFilter !== 'all'}
            loadingJobId={loadingJobId}
            onOpenExtractor={onOpenExtractor}
            onViewJob={onViewJob}
          />
        </>
      )}
    </div>
  );
}

function StatsGrid({ stats }: { stats: ApplicationStats }) {
  const entries = [
    ['Total', stats.total, 'Applications'],
    ['Active', stats.applied, 'Applied'],
    ['Interview', stats.interviews, 'Scheduled'],
    ['Score', `${stats.averageCompatibilityScore}%`, 'Avg Match'],
  ];
  return (
    <div className="grid grid-cols-2 border border-foreground/5 md:grid-cols-4">
      {entries.map(([label, value, caption]) => (
        <div key={label} className="border-b border-r border-foreground/5 bg-card/40 p-5 last:border-r-0 md:border-b-0">
          <p className="text-[9px] font-bold uppercase tracking-widest text-foreground/40">{label}</p>
          <p className="mt-3 font-mono text-3xl font-bold text-foreground">{value}</p>
          <p className="mt-1 text-[10px] font-bold uppercase tracking-widest text-foreground/50">{caption}</p>
        </div>
      ))}
    </div>
  );
}

function ApplicationFilters({ searchTerm, statusFilter, onSearchChange, onStatusChange }: {
  searchTerm: string;
  statusFilter: string;
  onSearchChange: (value: string) => void;
  onStatusChange: (value: string) => void;
}) {
  return (
    <div className="flex flex-col gap-4 border border-foreground/10 bg-card p-5 sm:flex-row sm:gap-6">
      <div className="flex-1">
        <Label htmlFor="application-search" className="mb-2 block text-[10px] font-bold uppercase tracking-widest text-foreground/50">
          Search applications
        </Label>
        <div className="relative">
          <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
          <Input
            id="application-search"
            value={searchTerm}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Search by job title or company..."
            className="h-11 rounded-sm border-foreground/10 bg-background pl-11 text-sm"
          />
        </div>
      </div>
      <div className="sm:w-64">
        <Label htmlFor="application-status" className="mb-2 block text-[10px] font-bold uppercase tracking-widest text-foreground/50">
          Filter by status
        </Label>
        <select
          id="application-status"
          value={statusFilter}
          onChange={(event) => onStatusChange(event.target.value)}
          className="h-11 w-full rounded-sm border border-foreground/10 bg-background px-4 text-sm text-foreground"
        >
          <option value="all">All statuses</option>
          <option value="applied">Applied</option>
          <option value="interview_scheduled">Interview scheduled</option>
          <option value="want_to_apply">Want to apply</option>
          <option value="not_interested">Not interested</option>
        </select>
      </div>
    </div>
  );
}

function ApplicationList({ applications, hasFilters, loadingJobId, onOpenExtractor, onViewJob }: {
  applications: TrackedApplication[];
  hasFilters: boolean;
  loadingJobId: string | null;
  onOpenExtractor: () => void;
  onViewJob: (application: TrackedApplication) => void;
}) {
  if (applications.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center border border-foreground/5 bg-card/30 px-6 py-14">
        <Briefcase className="mb-4 h-12 w-12 text-muted-foreground" aria-hidden="true" />
        <h2 className="mb-2 text-base font-semibold">No applications found</h2>
        <p className="mb-5 text-center text-sm text-muted-foreground">
          {hasFilters ? 'Try adjusting your search or filter criteria.' : 'Start by extracting a job from a URL.'}
        </p>
        {!hasFilters && <Button variant="outline" onClick={onOpenExtractor}><Plus className="mr-2 h-4 w-4" />Extract Job URL</Button>}
      </div>
    );
  }

  return (
    <div className="border border-foreground/5">
      {applications.map((application) => (
        <article key={application.id} className="border-b border-foreground/5 bg-card/30 p-5 last:border-b-0 hover:bg-card/60">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <div className="mb-2 flex flex-wrap items-center gap-3">
                <h2 className="text-base font-semibold">{application.title}</h2>
                <StatusBadge status={application.status} />
              </div>
              <div className="mb-3 flex flex-wrap gap-x-4 gap-y-2 text-sm text-muted-foreground">
                <Meta icon={Users} text={application.company} />
                <Meta icon={MapPin} text={application.location} />
                <Meta icon={TrendingUp} text={application.salary} />
              </div>
              <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-muted-foreground">
                <Meta icon={Calendar} text={application.appliedDate ? `Applied ${new Date(application.appliedDate).toLocaleDateString()}` : statusConfig[application.status as keyof typeof statusConfig]?.label || 'Status unknown'} />
                <Meta icon={ExternalLink} text={application.source} />
                {application.compatibilityScore > 0 && <Meta icon={TrendingUp} text={`${application.compatibilityScore}% match`} />}
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={() => onViewJob(application)} disabled={Boolean(loadingJobId)}>
              <ExternalLink className="mr-1 h-4 w-4" aria-hidden="true" />
              {loadingJobId === application.id ? 'Loading...' : 'View'}
            </Button>
          </div>
        </article>
      ))}
    </div>
  );
}

function RecentApplicationCard({ application, onDismiss, onView }: {
  application: TrackedApplication;
  onDismiss: () => void;
  onView: (application: TrackedApplication) => void;
}) {
  return (
    <Card className="rounded-sm border-foreground/10 bg-card shadow-none">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm uppercase tracking-widest">Recently extracted job</CardTitle>
          <Button variant="ghost" size="icon" onClick={onDismiss} aria-label="Dismiss extracted job"><X className="h-4 w-4" /></Button>
        </div>
        <CardDescription>Job successfully extracted from URL</CardDescription>
      </CardHeader>
      <CardContent className="flex items-end justify-between gap-4">
        <div><h2 className="font-semibold">{application.title}</h2><p className="text-sm text-muted-foreground">{application.company} · {application.location}</p></div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => onView(application)}>View details</Button>
          {application.sourceUrl && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(application.sourceUrl, '_blank', 'noopener,noreferrer')}
            >
              <ExternalLink className="mr-1 h-4 w-4" aria-hidden="true" />
              Open job
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config = statusConfig[status as keyof typeof statusConfig];
  const Icon = config?.icon || CheckCircle;
  return <Badge variant="outline"><Icon className="mr-1 h-3 w-3" />{config?.label || status || 'Unknown'}</Badge>;
}

function Meta({ icon: Icon, text }: { icon: typeof Users; text: string }) {
  return <span className="flex items-center gap-1"><Icon className="h-4 w-4" aria-hidden="true" />{text}</span>;
}
