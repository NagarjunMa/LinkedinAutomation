"use client";

import React from "react";
import Link from "next/link";
import {
  ArrowRight,
  Briefcase,
  Calendar,
  Download,
  Eye,
  FileText,
  Search,
  Sparkles,
} from "lucide-react";

import { tailoredResumesApi } from "@/app/lib/api/tailored-resumes";
import type {
  ExperienceEntry,
  TailoredResumeDetail,
  TailoredResumeListItem,
} from "@/app/lib/api/types-v2";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useToast } from "@/components/ui/use-toast";

interface TailoredResumeLibraryProps {
  title?: string;
  description?: string;
  mode?: "page" | "embedded";
}

function formatDate(value: string | null) {
  if (!value) return "--";
  return new Date(value).toLocaleDateString();
}

function buildFilename(item: TailoredResumeListItem) {
  const company = item.company_name || "tailored-resume";
  const role = item.target_role_title || item.role_category || "resume";
  return `${company}-${role}`.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") + ".pdf";
}

function ResumeSnapshot({ detail }: { detail: TailoredResumeDetail }) {
  const resume = detail.resume_json;
  const experience = resume.experience.slice(0, 4);

  return (
    <div className="space-y-5">
      <div>
        <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-foreground/40">Candidate</p>
        <h3 className="mt-1 text-xl font-semibold text-foreground">{resume.contact.name}</h3>
        <p className="text-xs text-foreground/50">{[resume.contact.email, resume.contact.phone].filter(Boolean).join(" · ")}</p>
      </div>

      {resume.summary && (
        <div>
          <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-foreground/40">Summary</p>
          <p className="mt-2 text-sm leading-relaxed text-foreground/75">{resume.summary}</p>
        </div>
      )}

      <div>
        <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-foreground/40">Experience Snapshot</p>
        <div className="mt-3 space-y-4">
          {experience.map((entry: ExperienceEntry) => (
            <div key={`${entry.company}-${entry.role}`} className="border border-foreground/10 p-4">
              <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-sm font-bold text-foreground">{entry.role}</p>
                  <p className="text-xs text-foreground/55">{entry.company}</p>
                </div>
                <p className="text-xs font-mono text-foreground/45">{entry.dates || "--"}</p>
              </div>
              <ul className="mt-3 space-y-2">
                {entry.bullets.slice(0, 3).map((bullet) => (
                  <li key={bullet.id} className="text-xs leading-relaxed text-foreground/70">
                    {bullet.text}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function TailoredResumeLibrary({
  title = "Tailored Resume Library",
  description = "Review every company-specific resume saved from the JD tailoring workflow.",
  mode = "embedded",
}: TailoredResumeLibraryProps) {
  const { toast } = useToast();
  const [items, setItems] = React.useState<TailoredResumeListItem[]>([]);
  const [search, setSearch] = React.useState("");
  const [loading, setLoading] = React.useState(true);
  const [loadingId, setLoadingId] = React.useState<string | null>(null);
  const [selected, setSelected] = React.useState<TailoredResumeDetail | null>(null);
  const [dialogOpen, setDialogOpen] = React.useState(false);

  const loadItems = React.useCallback(async () => {
    try {
      setLoading(true);
      setItems(await tailoredResumesApi.list());
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load tailored resumes";
      toast({ title: "Library unavailable", description: message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  React.useEffect(() => {
    void loadItems();
  }, [loadItems]);

  const filteredItems = React.useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return items;
    return items.filter((item) =>
      [
        item.company_name,
        item.target_role_title,
        item.role_category,
        item.source_filename,
      ].some((value) => value?.toLowerCase().includes(query))
    );
  }, [items, search]);

  const handleOpen = async (versionId: string) => {
    try {
      setLoadingId(versionId);
      setSelected(await tailoredResumesApi.get(versionId));
      setDialogOpen(true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load tailored resume";
      toast({ title: "Review failed", description: message, variant: "destructive" });
    } finally {
      setLoadingId(null);
    }
  };

  const handleDownload = async (item: TailoredResumeListItem) => {
    try {
      setLoadingId(item.version_id);
      const filename = buildFilename(item);
      const blob = await tailoredResumesApi.downloadPdf(item.version_id, {
        template_id: item.template_id || undefined,
        filename,
      });
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      URL.revokeObjectURL(objectUrl);
      toast({ title: "Downloaded", description: "1 credit used for PDF generation." });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Download failed";
      toast({ title: "Download failed", description: message, variant: "destructive" });
    } finally {
      setLoadingId(null);
    }
  };

  const containerClass =
    mode === "page"
      ? "max-w-[1400px] mx-auto px-4 md:px-8 pb-24"
      : "w-full";

  return (
    <section className={containerClass}>
      <div className="mb-8 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="mb-3 text-[10px] font-extrabold uppercase tracking-[0.2em] text-app-text/40">
            Prism Pro Saved Work
          </p>
          <h1 className={mode === "page" ? "text-4xl md:text-5xl font-serif-italic text-app-text" : "text-2xl font-semibold text-foreground"}>
            {title}
          </h1>
          <p className="mt-3 max-w-2xl text-sm font-medium leading-relaxed text-app-text/60">
            {description}
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative w-full sm:w-80">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-app-text/30" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search company, role, or file"
              className="w-full border border-app-text/10 bg-transparent py-3 pl-10 pr-3 text-xs font-mono outline-none transition-colors focus:border-app-text/40"
            />
          </div>
          <Link
            href="/dashboard/resume/tailor"
            className="inline-flex items-center justify-center gap-2 border border-app-text/20 px-4 py-3 text-[10px] font-bold uppercase tracking-widest text-app-text transition-colors hover:bg-app-text hover:text-app-bg"
          >
            Tailor New <ArrowRight size={13} />
          </Link>
        </div>
      </div>

      <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="border border-app-text/10 bg-app-card/30 p-5">
          <div className="mb-4 flex h-10 w-10 items-center justify-center border border-app-text/10 bg-app-bg">
            <FileText size={18} />
          </div>
          <p className="text-3xl font-mono font-bold">{items.length}</p>
          <p className="mt-1 text-[10px] font-bold uppercase tracking-widest text-app-text/40">Saved tailored resumes</p>
        </div>
        <div className="border border-app-text/10 bg-app-card/30 p-5">
          <div className="mb-4 flex h-10 w-10 items-center justify-center border border-app-text/10 bg-app-bg">
            <Briefcase size={18} />
          </div>
          <p className="text-3xl font-mono font-bold">
            {new Set(items.map((item) => item.company_name).filter(Boolean)).size}
          </p>
          <p className="mt-1 text-[10px] font-bold uppercase tracking-widest text-app-text/40">Companies prepared</p>
        </div>
        <div className="border border-app-text/10 bg-app-card/30 p-5">
          <div className="mb-4 flex h-10 w-10 items-center justify-center border border-app-text/10 bg-app-bg">
            <Sparkles size={18} />
          </div>
          <p className="text-3xl font-mono font-bold">
            {items.reduce((sum, item) => sum + item.accepted_change_count, 0)}
          </p>
          <p className="mt-1 text-[10px] font-bold uppercase tracking-widest text-app-text/40">Accepted JD changes</p>
        </div>
      </div>

      <div className="overflow-x-auto border border-app-text/10 bg-app-card/20">
        <table className="w-full min-w-[860px] border-collapse text-left">
          <thead>
            <tr className="border-b border-app-text/10 bg-app-text/[0.02]">
              <th className="px-6 py-4 text-[9px] font-bold uppercase tracking-widest text-app-text/40">Company</th>
              <th className="px-6 py-4 text-[9px] font-bold uppercase tracking-widest text-app-text/40">Role</th>
              <th className="px-6 py-4 text-[9px] font-bold uppercase tracking-widest text-app-text/40">Match</th>
              <th className="px-6 py-4 text-[9px] font-bold uppercase tracking-widest text-app-text/40">Changes</th>
              <th className="px-6 py-4 text-[9px] font-bold uppercase tracking-widest text-app-text/40">Saved</th>
              <th className="px-6 py-4 text-right text-[9px] font-bold uppercase tracking-widest text-app-text/40">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-[10px] font-bold uppercase tracking-widest text-app-text/40">
                  Loading tailored resumes
                </td>
              </tr>
            ) : filteredItems.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-16 text-center">
                  <div className="mx-auto max-w-md">
                    <FileText className="mx-auto mb-4 h-10 w-10 text-app-text/25" />
                    <p className="text-sm font-bold text-app-text">No tailored resumes saved</p>
                    <p className="mt-2 text-xs leading-relaxed text-app-text/50">
                      Tailor a resume to a job description and apply selected pointers to save a company-specific version here.
                    </p>
                    <Link
                      href="/dashboard/resume/tailor"
                      className="mt-5 inline-flex items-center gap-2 border border-app-text/20 px-4 py-2 text-[10px] font-bold uppercase tracking-widest text-app-text hover:bg-app-text hover:text-app-bg"
                    >
                      Start Tailoring <ArrowRight size={12} />
                    </Link>
                  </div>
                </td>
              </tr>
            ) : (
              filteredItems.map((item) => (
                <tr key={item.version_id} className="border-b border-app-text/5 transition-colors hover:bg-app-card/40">
                  <td className="px-6 py-5">
                    <p className="text-sm font-semibold text-app-text">{item.company_name || "Unknown company"}</p>
                    <p className="mt-1 text-[10px] uppercase tracking-widest text-app-text/35">{item.source_filename}</p>
                  </td>
                  <td className="px-6 py-5">
                    <p className="text-sm text-app-text">{item.target_role_title || item.role_category || "Target role"}</p>
                    <p className="mt-1 text-[10px] uppercase tracking-widest text-app-text/35">
                      {[item.seniority, item.country_hint, item.template_id].filter(Boolean).join(" · ") || "Template pending"}
                    </p>
                  </td>
                  <td className="px-6 py-5 font-mono text-sm font-bold text-app-text">{item.match_score ?? "--"}</td>
                  <td className="px-6 py-5 font-mono text-xs text-app-text/60">{item.accepted_change_count}</td>
                  <td className="px-6 py-5">
                    <div className="flex items-center gap-2 text-xs font-mono text-app-text/45">
                      <Calendar size={13} />
                      {formatDate(item.accepted_at || item.created_at)}
                    </div>
                  </td>
                  <td className="px-6 py-5">
                    <div className="flex justify-end gap-2">
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => handleOpen(item.version_id)}
                        disabled={loadingId === item.version_id}
                        aria-label="Review tailored resume"
                      >
                        <Eye size={15} />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDownload(item)}
                        disabled={loadingId === item.version_id}
                        aria-label="Download tailored resume"
                      >
                        <Download size={15} />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-h-[88vh] overflow-y-auto sm:max-w-5xl">
          <DialogHeader>
            <DialogTitle>{selected?.company_name || "Tailored Resume"}</DialogTitle>
            <DialogDescription>
              {selected?.target_role_title || selected?.role_category || "Role details unavailable"}
            </DialogDescription>
          </DialogHeader>

          {selected && (
            <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
              <div className="space-y-5">
                <div className="grid grid-cols-2 gap-3 text-xs md:grid-cols-4">
                  <div className="border border-foreground/10 p-3">
                    <p className="mb-1 uppercase tracking-widest text-foreground/40">Match</p>
                    <p className="font-mono font-bold">{selected.match_score ?? "--"}</p>
                  </div>
                  <div className="border border-foreground/10 p-3">
                    <p className="mb-1 uppercase tracking-widest text-foreground/40">Changes</p>
                    <p className="font-mono font-bold">{selected.accepted_change_count}</p>
                  </div>
                  <div className="border border-foreground/10 p-3">
                    <p className="mb-1 uppercase tracking-widest text-foreground/40">Seniority</p>
                    <p className="font-mono font-bold">{selected.seniority || "--"}</p>
                  </div>
                  <div className="border border-foreground/10 p-3">
                    <p className="mb-1 uppercase tracking-widest text-foreground/40">Template</p>
                    <p className="font-mono font-bold">{selected.template_id || "--"}</p>
                  </div>
                </div>
                <ResumeSnapshot detail={selected} />
              </div>

              <div className="space-y-5">
                <div>
                  <h3 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-foreground/50">Accepted Changes</h3>
                  <pre className="max-h-56 overflow-auto rounded-sm border border-foreground/10 bg-foreground/[0.02] p-4 text-xs">
                    {JSON.stringify(selected.accepted_changes, null, 2)}
                  </pre>
                </div>
                <div>
                  <h3 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-foreground/50">Source JD</h3>
                  <p className="max-h-56 overflow-auto whitespace-pre-wrap rounded-sm border border-foreground/10 bg-foreground/[0.02] p-4 text-xs leading-relaxed">
                    {selected.source_jd_text || "No source JD stored."}
                  </p>
                </div>
                <div>
                  <h3 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-foreground/50">Resume JSON</h3>
                  <pre className="max-h-64 overflow-auto rounded-sm border border-foreground/10 bg-foreground/[0.02] p-4 text-xs">
                    {JSON.stringify(selected.resume_json, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </section>
  );
}
