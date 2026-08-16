'use client';

import { useMemo, useState } from 'react';
import JobURLExtractor from '@/components/job-url-extractor';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/auth-context';
import { ApplicationsView } from './applications-view';
import { JobDetailsDialog } from './job-details-dialog';
import {
  createExtractedApplication,
  filterApplications,
  summarizeApplications,
  type ExtractedJobPayload,
  type TrackedApplication,
} from './model';
import { useApplicationDetails, useApplications } from './use-applications';

export function ApplicationsPageClient() {
  const { user } = useAuth();
  const { toast } = useToast();
  const applicationsQuery = useApplications();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isExtractorOpen, setExtractorOpen] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [recentlyExtractedJob, setRecentlyExtractedJob] = useState<TrackedApplication | null>(null);
  const detailsQuery = useApplicationDetails(selectedJobId);
  const applications = applicationsQuery.data || [];

  const filteredApplications = useMemo(
    () => filterApplications(applications, searchTerm, statusFilter),
    [applications, searchTerm, statusFilter],
  );
  const stats = useMemo(() => summarizeApplications(applications), [applications]);

  const handleJobExtracted = async (payload: ExtractedJobPayload) => {
    const application = createExtractedApplication(payload);
    setRecentlyExtractedJob(application);
    toast({
      title: 'Job extracted successfully',
      description: `${application.title} at ${application.company}`,
    });
    await applicationsQuery.refetch();
    setExtractorOpen(false);
  };

  const extractor = (
    <Card className="rounded-sm border-foreground/10 bg-card shadow-none">
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="text-base">Extract job from URL</CardTitle>
        <Button variant="ghost" size="sm" onClick={() => setExtractorOpen(false)}>Close</Button>
      </CardHeader>
      <CardContent>
        {user?.id
          ? <JobURLExtractor userId={user.id} onJobExtracted={handleJobExtracted} />
          : <p className="text-sm text-muted-foreground">Sign in again to extract a job.</p>}
      </CardContent>
    </Card>
  );

  return (
    <>
      <ApplicationsView
        error={applicationsQuery.error}
        extractor={extractor}
        filteredApplications={filteredApplications}
        isExtractorOpen={isExtractorOpen}
        isLoading={applicationsQuery.isLoading}
        loadingJobId={detailsQuery.isFetching ? selectedJobId : null}
        recentlyExtractedJob={recentlyExtractedJob}
        searchTerm={searchTerm}
        stats={stats}
        statusFilter={statusFilter}
        onDismissRecent={() => setRecentlyExtractedJob(null)}
        onOpenExtractor={() => setExtractorOpen(true)}
        onRetry={() => applicationsQuery.refetch()}
        onSearchChange={setSearchTerm}
        onStatusChange={setStatusFilter}
        onViewJob={(application) => setSelectedJobId(application.id)}
      />
      <JobDetailsDialog
        details={detailsQuery.data}
        error={detailsQuery.error}
        isLoading={detailsQuery.isFetching}
        open={selectedJobId !== null}
        onOpenChange={(open) => !open && setSelectedJobId(null)}
        onRetry={() => detailsQuery.refetch()}
      />
    </>
  );
}
