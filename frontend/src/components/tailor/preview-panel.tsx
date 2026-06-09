"use client";

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import { useExportPdf } from '@/hooks/use-export-pdf';
import { APIError } from '@/app/lib/api/config';

const TEMPLATE_OPTIONS = [
  { id: 'us-swe', label: 'USA — Software Engineer' },
  { id: 'us-ds', label: 'USA — Data Scientist' },
  { id: 'us-pm', label: 'USA — Product Manager' },
  { id: 'in-swe', label: 'India — Software Engineer' },
  { id: 'in-ds', label: 'India — Data Scientist' },
  { id: 'in-pm', label: 'India — Product Manager' },
];

interface PreviewPanelProps {
  versionId: string;
  previewHtml: string;
  suggestedTemplate: string;
  filenameHint: string;
  warning?: string;
}

export function PreviewPanel({
  versionId,
  previewHtml,
  suggestedTemplate,
  filenameHint,
  warning,
}: PreviewPanelProps) {
  const [template, setTemplate] = useState(suggestedTemplate);
  const [filename, setFilename] = useState(filenameHint);
  const exportMut = useExportPdf();
  const { toast } = useToast();

  // Re-sync when a new Apply result lands
  useEffect(() => {
    setTemplate(suggestedTemplate);
    setFilename(filenameHint);
  }, [versionId, suggestedTemplate, filenameHint]);

  const onDownload = async () => {
    try {
      await exportMut.mutateAsync({
        resume_version_id: versionId,
        template_id: template,
        filename,
      });
      toast({ title: 'Downloaded', description: filename });
    } catch (err: unknown) {
      const isApiError = err instanceof APIError;
      const status = isApiError ? err.status : undefined;
      const message = err instanceof Error ? err.message : 'Export failed';

      if (status === 402 || message.toLowerCase().includes('credit')) {
        toast({
          title: 'Need more credits',
          description: 'Credits refresh monthly during the freemium launch.',
          variant: 'destructive',
        });
      } else {
        toast({ title: 'Export failed', description: message, variant: 'destructive' });
      }
    }
  };

  return (
    <aside className="sticky top-24 h-[calc(100vh-8rem)] flex flex-col gap-4">
      <div className="flex-1 overflow-hidden border border-border rounded-md bg-card">
        {previewHtml ? (
          <iframe
            srcDoc={previewHtml}
            sandbox="allow-same-origin"
            className="w-full h-full"
            title="Resume preview"
          />
        ) : (
          <div className="h-full flex items-center justify-center text-sm text-muted-foreground p-6 text-center">
            {warning ?? 'Apply changes to see preview'}
          </div>
        )}
      </div>

      <div className="space-y-3">
        <div>
          <label className="text-xs uppercase tracking-wider text-muted-foreground">
            Template
          </label>
          <Select value={template} onValueChange={setTemplate}>
            <SelectTrigger className="w-full mt-1">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TEMPLATE_OPTIONS.map((opt) => (
                <SelectItem key={opt.id} value={opt.id}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div>
          <label className="text-xs uppercase tracking-wider text-muted-foreground">
            Filename
          </label>
          <Input
            value={filename}
            onChange={(e) => setFilename(e.target.value)}
            placeholder="firstname-lastname-company.pdf"
            className="mt-1"
          />
        </div>

        <Button
          onClick={onDownload}
          disabled={exportMut.isPending}
          className="w-full"
        >
          {exportMut.isPending ? 'Generating PDF…' : 'Download PDF'}
        </Button>
      </div>
    </aside>
  );
}
