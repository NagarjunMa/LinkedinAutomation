'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  User,
  MapPin,
  Mail,
  Briefcase,
  DollarSign,
  Edit3,
  Settings,
  ChevronRight,
  Code2,
  Terminal,
  ExternalLink,
  FileText,
  CheckCircle2,
  Plus,
  Trash2,
  AlertTriangle
} from 'lucide-react';
import { INITIAL_PROFILE_DATA } from './constants';
import { JobPreferences, ProfileData } from './types';
import { useAuth } from '@/contexts/auth-context';
import { profileApi } from '@/app/lib/api/profile';
import { resumeApi } from '@/app/lib/api/resume';
import { ResumeFile } from '@/app/lib/api/types';
import { useToast } from "@/components/ui/use-toast";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

// Typed for Framer Motion ease prop
const LeicaBezier: [number, number, number, number] = [0.22, 1, 0.36, 1];

export default function ProfilePage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [data, setData] = useState<ProfileData>(INITIAL_PROFILE_DATA);
  const [loading, setLoading] = useState(true);
  const [isEditingPrefs, setIsEditingPrefs] = useState(false);
  const [editedPrefs, setEditedPrefs] = useState<JobPreferences>(INITIAL_PROFILE_DATA.preferences);
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; resumeId: string | null; fileName: string }>({
    open: false,
    resumeId: null,
    fileName: ''
  });

  // Fetch Data
  const fetchData = useCallback(async () => {
    if (!user) return;
    try {
      setLoading(true);
      if (!user?.id) {
        setLoading(false);
        return;
      }

      const userId = user.id;

      // Parallel fetch
      const [userProfile, resumeData] = await Promise.all([
        profileApi.getProfile(userId),
        resumeApi.listResumes()
      ]);

      // Transform Data
      const transformedData: ProfileData = {
        user: {
          name: userProfile.full_name || 'User',
          email: userProfile.email || '',
          location: userProfile.location || 'Remote',
          title: userProfile.career_level || 'Professional'
        },
        stats: {
          applications: userProfile.total_applications || 0,
          experiences: userProfile.work_experiences?.length || 0
        },
        resumes: resumeData.resumes.map((r: ResumeFile) => ({
          id: r.id,
          fileName: r.filename,
          uploadDate: new Date(r.uploaded_at).toLocaleDateString(),
          score: r.evaluation_result?.overall_score || 0,
          isActive: r.is_primary || false
        })),
        preferences: {
          roles: userProfile.desired_roles || [],
          locations: userProfile.preferred_locations || [],
          salaryRange: userProfile.salary_range_min && userProfile.salary_range_max
            ? `$${(userProfile.salary_range_min / 1000).toFixed(0)}k - $${(userProfile.salary_range_max / 1000).toFixed(0)}k`
            : 'Not set'
        },
        referralBlueprint: userProfile.referral_template || 'No template defined.'
      };

      setData(transformedData);
      setEditedPrefs(transformedData.preferences);

    } catch (error) {
      console.error('Error fetching profile data:', error);
      toast({
        title: "Error",
        description: "Failed to load profile data",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  }, [user, toast]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSavePrefs = async () => {
    try {
      const userId = user?.id ? String(user.id) : 'current';

      // Parse salary range string back to numbers (Simple parsing logic)
      // Expected format: "$80k - $120k" or just numbers
      let minSalary = 0;
      let maxSalary = 0;

      const salaryMatch = editedPrefs.salaryRange.match(/(\d+)/g);
      if (salaryMatch && salaryMatch.length >= 2) {
        minSalary = parseInt(salaryMatch[0]) * 1000;
        maxSalary = parseInt(salaryMatch[1]) * 1000;
      }

      await profileApi.updateProfile(userId, {
        desired_roles: editedPrefs.roles,
        preferred_locations: editedPrefs.locations,
        salary_range_min: minSalary,
        salary_range_max: maxSalary
      });

      setData(prev => ({ ...prev, preferences: editedPrefs }));
      setIsEditingPrefs(false);
      toast({
        title: "Success",
        description: "Preferences updated successfully"
      });
    } catch (error) {
      console.error("Error updating preferences:", error);
      toast({
        title: "Error",
        description: "Failed to update preferences",
        variant: "destructive"
      });
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      await resumeApi.uploadResume(file);
      await fetchData(); // Refresh list
      toast({
        title: "Success",
        description: "Resume uploaded successfully!",
      });
    } catch (error) {
      console.error('Error uploading resume:', error);
      toast({
        title: "Error",
        description: "Failed to upload resume.",
        variant: "destructive",
      });
    }
  };

  const handleDeleteResume = (resumeId: string, fileName: string) => {
    setDeleteDialog({
      open: true,
      resumeId,
      fileName
    });
  };

  const confirmDeleteResume = async () => {
    if (!deleteDialog.resumeId) return;

    try {
      await resumeApi.deleteResume(deleteDialog.resumeId);
      setData(prev => ({
        ...prev,
        resumes: prev.resumes.filter(r => r.id !== deleteDialog.resumeId)
      }));
      toast({
        title: "Success",
        description: "Resume deleted successfully",
      });
    } catch (error) {
      console.error('Error deleting resume:', error);
      toast({
        title: "Error",
        description: "Failed to delete resume",
        variant: "destructive",
      });
    } finally {
      setDeleteDialog({ open: false, resumeId: null, fileName: '' });
    }
  };

  const cancelDeleteResume = () => {
    setDeleteDialog({ open: false, resumeId: null, fileName: '' });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse text-foreground/60 text-sm font-mono uppercase tracking-widest">Loading System Data...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-foreground selection:text-background relative overflow-hidden transition-colors duration-300">
      {/* Grain Overlay */}
      <div className="grain-overlay fixed inset-0 w-full h-full pointer-events-none z-50 opacity-[0.04] mix-blend-overlay" style={{ backgroundImage: 'url("https://grainy-gradients.vercel.app/noise.svg")' }}></div>

      <div className="max-w-5xl mx-auto px-6 py-12 md:py-24 relative z-10">
        {/* Utility Navigation */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: LeicaBezier }}
          className="flex justify-between items-center mb-16 border-b border-foreground/5 pb-4"
        >
          <div className="flex items-center gap-2 text-[10px] tracking-[0.2em] uppercase font-bold text-foreground/40">
            <span>JobFlow Pro</span>
            <ChevronRight size={10} strokeWidth={3} />
            <span className="text-foreground">Profile_v2.5</span>
          </div>
          <div className="flex gap-6">
            <button className="text-foreground/60 hover:text-foreground transition-colors">
              <Settings size={16} />
            </button>
          </div>
        </motion.div>

        {/* Identity Header */}
        <motion.header
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 1, ease: LeicaBezier, delay: 0.1 }}
          className="mb-20"
        >
          <h2 className="text-[10px] tracking-[0.4em] uppercase font-bold mb-3 text-foreground/60">Identity Profile</h2>
          <h1 className="text-6xl md:text-8xl font-serif-italic text-foreground tracking-tight">
            {data.user.name}
          </h1>
        </motion.header>

        {/* System Stats Section */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: LeicaBezier, delay: 0.3 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-12 mb-24 border-y border-foreground/5 py-10"
        >
          <StatItem label="Active Applications" value={data.stats.applications} />
          <StatItem label="Validated Resumes" value={data.resumes.length} />
          <StatItem label="Professional Nodes" value={data.stats.experiences} />
        </motion.section>

        {/* DNA Modules Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-24 mb-32">
          {/* Column 1: Personal Data */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: LeicaBezier, delay: 0.4 }}
          >
            <SectionLabel icon={<User size={14} />} label="Personal Specifications" />
            <div className="space-y-8 mt-8">
              <InfoRow label="Access Key" value={data.user.email} icon={<Mail size={14} />} />
              <InfoRow label="Primary Cluster" value={data.user.location} icon={<MapPin size={14} />} />
              <InfoRow label="Designation" value={data.user.title} icon={<Briefcase size={14} />} />
            </div>
          </motion.div>

          {/* Column 2: Job Preferences */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: LeicaBezier, delay: 0.5 }}
            className="relative"
          >
            <div className="flex justify-between items-center border-b border-foreground/5 pb-4">
              <SectionLabel icon={<Settings size={14} />} label="Preference Parameters" noBorder />
              {!isEditingPrefs && (
                <button
                  onClick={() => setIsEditingPrefs(true)}
                  className="text-foreground/40 hover:text-foreground transition-colors"
                >
                  <Edit3 size={14} />
                </button>
              )}
            </div>

            <AnimatePresence mode="wait">
              {!isEditingPrefs ? (
                <motion.div
                  key="prefs-view"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="space-y-8 mt-8"
                >
                  <InfoRow
                    label="Target Roles"
                    value={data.preferences.roles.join(' / ')}
                    icon={<Terminal size={14} />}
                  />
                  <InfoRow
                    label="Mobility Range"
                    value={data.preferences.locations.join(', ')}
                    icon={<MapPin size={14} />}
                  />
                  <InfoRow
                    label="Compensation Floor"
                    value={data.preferences.salaryRange}
                    icon={<DollarSign size={14} />}
                  />
                </motion.div>
              ) : (
                <motion.div
                  key="prefs-edit"
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  className="mt-8 bg-card/40 dark:bg-card/20 p-6 border border-foreground/5 rounded-sm backdrop-blur-sm"
                >
                  <div className="space-y-6">
                    <div>
                      <label className="text-[9px] uppercase tracking-widest font-bold text-foreground/40 mb-2 block">Roles (comma separated)</label>
                      <input
                        className="w-full bg-transparent border-b border-foreground/10 py-2 focus:border-foreground outline-none text-sm font-mono text-foreground"
                        value={editedPrefs.roles.join(', ')}
                        onChange={(e) => setEditedPrefs({ ...editedPrefs, roles: e.target.value.split(',').map(s => s.trim()) })}
                      />
                    </div>
                    <div>
                      <label className="text-[9px] uppercase tracking-widest font-bold text-foreground/40 mb-2 block">Locations (comma separated)</label>
                      <input
                        className="w-full bg-transparent border-b border-foreground/10 py-2 focus:border-foreground outline-none text-sm font-mono text-foreground"
                        value={editedPrefs.locations.join(', ')}
                        onChange={(e) => setEditedPrefs({ ...editedPrefs, locations: e.target.value.split(',').map(s => s.trim()) })}
                      />
                    </div>
                    <div>
                      <label className="text-[9px] uppercase tracking-widest font-bold text-foreground/40 mb-2 block">Salary Range (e.g. 100k - 120k)</label>
                      <input
                        className="w-full bg-transparent border-b border-foreground/10 py-2 focus:border-foreground outline-none text-sm font-mono text-foreground"
                        value={editedPrefs.salaryRange}
                        onChange={(e) => setEditedPrefs({ ...editedPrefs, salaryRange: e.target.value })}
                      />
                    </div>
                    <div className="flex gap-4 pt-4">
                      <button
                        onClick={handleSavePrefs}
                        className="bg-foreground text-background px-4 py-2 text-[10px] uppercase tracking-widest font-bold hover:bg-foreground/90 transition-colors"
                      >
                        Commit Changes
                      </button>
                      <button
                        onClick={() => setIsEditingPrefs(false)}
                        className="text-foreground/40 hover:text-foreground px-4 py-2 text-[10px] uppercase tracking-widest font-bold transition-colors"
                      >
                        Abort
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>

        {/* Resume Ledger Section */}
        <motion.section
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: LeicaBezier, delay: 0.6 }}
          className="mb-32"
        >
          <div className="flex justify-between items-end mb-8">
            <SectionLabel icon={<FileText size={14} />} label="Resume Revision Ledger" />
            <div className="relative">
              <input
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={handleFileUpload}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                id="resume-upload"
              />
              <button className="flex items-center gap-2 text-[10px] tracking-widest uppercase font-bold text-foreground/60 hover:text-foreground transition-colors">
                <Plus size={12} /> Upload Revision
              </button>
            </div>
          </div>

          <div className="border border-foreground/5 overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-foreground/5 bg-foreground/[0.02]">
                  <th className="py-4 px-6 text-[9px] uppercase tracking-widest font-bold text-foreground/40">Version ID</th>
                  <th className="py-4 px-6 text-[9px] uppercase tracking-widest font-bold text-foreground/40">Asset Name</th>
                  <th className="py-4 px-6 text-[9px] uppercase tracking-widest font-bold text-foreground/40">Timestamp</th>
                  <th className="py-4 px-6 text-[9px] uppercase tracking-widest font-bold text-foreground/40">AI Score</th>
                  <th className="py-4 px-6 text-[9px] uppercase tracking-widest font-bold text-foreground/40 text-right">Status</th>
                  <th className="py-4 px-6 text-[9px] uppercase tracking-widest font-bold text-foreground/40 w-12"></th>
                </tr>
              </thead>
              <tbody>
                {data.resumes.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-[10px] uppercase tracking-widest text-foreground/40">No resumes found</td>
                  </tr>
                ) : (
                  data.resumes.map((resume, idx) => (
                    <tr
                      key={resume.id}
                      className={`border-b border-foreground/5 hover:bg-card/40 dark:hover:bg-card/20 transition-colors group ${resume.isActive ? 'bg-card/20 dark:bg-card/10' : ''}`}
                    >
                      <td className="py-5 px-6 font-mono text-xs text-foreground/60">{resume.id.substring(0, 8)}</td>
                      <td className="py-5 px-6 text-sm font-medium text-foreground flex items-center gap-2">
                        {resume.fileName}
                        <ExternalLink size={10} className="opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer" />
                      </td>
                      <td className="py-5 px-6 font-mono text-xs text-foreground/40">{resume.uploadDate}</td>
                      <td className="py-5 px-6">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm font-bold">{resume.score.toFixed(1)}</span>
                          <div className="w-16 h-1 bg-foreground/5 rounded-full overflow-hidden hidden sm:block">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${resume.score}%` }}
                              transition={{ duration: 1, ease: LeicaBezier, delay: 0.8 + (idx * 0.1) }}
                              className="h-full bg-foreground/40"
                            />
                          </div>
                        </div>
                      </td>
                      <td className="py-5 px-6 text-right">
                        {resume.isActive ? (
                          <span className="inline-flex items-center gap-1 text-[9px] uppercase tracking-widest font-bold text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded-sm">
                            <CheckCircle2 size={10} /> Active
                          </span>
                        ) : (
                          <span className="text-[9px] uppercase tracking-widest font-bold text-foreground/30">
                            Archived
                          </span>
                        )}
                      </td>
                      <td className="py-5 px-6 text-right w-12">
                        <button
                          onClick={() => handleDeleteResume(resume.id, resume.fileName)}
                          className="text-foreground/20 hover:text-red-500 transition-colors p-2"
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </motion.section>

        {/* Referral Email Blueprint */}
        <motion.section
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: LeicaBezier, delay: 0.8 }}
          className="mb-32"
        >
          <div className="flex justify-between items-end mb-8">
            <SectionLabel icon={<Code2 size={14} />} label="Communication Blueprint [RE-01]" />
            <button className="flex items-center gap-2 text-[10px] tracking-widest uppercase font-bold text-foreground/40 hover:text-foreground transition-colors"
              onClick={() => {
                navigator.clipboard.writeText(data.referralBlueprint);
                toast({ title: "Copied", description: "Referral template copied to clipboard" });
              }}
            >
              Copy Syntax <ExternalLink size={10} />
            </button>
          </div>

          <div className="relative group">
            <div className="absolute -inset-0.5 bg-foreground/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-sm"></div>
            <div className="relative bg-card/40 dark:bg-card/20 border border-foreground/5 p-8 md:p-12 font-mono text-sm leading-relaxed text-foreground/80 shadow-sm backdrop-blur-sm">
              <div className="flex gap-4 mb-6 opacity-20">
                <div className="w-2 h-2 rounded-full bg-foreground"></div>
                <div className="w-2 h-2 rounded-full bg-foreground"></div>
                <div className="w-2 h-2 rounded-full bg-foreground"></div>
              </div>
              <pre className="whitespace-pre-wrap selection:bg-foreground/10 font-mono">
                {data.referralBlueprint}
              </pre>
            </div>
          </div>
        </motion.section>

        {/* Footer Branding */}
        <footer className="mt-32 pt-12 border-t border-foreground/5 flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-4">
            <div className="w-8 h-8 rounded-full border border-foreground flex items-center justify-center font-bold text-[10px]">JF</div>
            <p className="text-[10px] tracking-widest text-foreground/40 uppercase">System Integrity: Nominal</p>
          </div>
          <p className="text-[10px] tracking-widest text-foreground/30 uppercase">© 2026 JobFlow Command / Leica Theory Design</p>
        </footer>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialog.open} onOpenChange={(open) => !open && cancelDeleteResume()}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              Delete Resume
            </DialogTitle>
            <DialogDescription className="text-muted-foreground">
              Are you sure you want to delete <strong>{deleteDialog.fileName}</strong>? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="flex flex-col sm:flex-row gap-2">
            <Button
              variant="outline"
              onClick={cancelDeleteResume}
              className="w-full sm:w-auto"
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={confirmDeleteResume}
              className="w-full sm:w-auto"
            >
              Delete Resume
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

/* Sub-components */

const StatItem: React.FC<{ label: string, value: number }> = ({ label, value }) => (
  <div className="flex flex-col gap-2">
    <div className="font-mono text-5xl font-medium tracking-tighter text-foreground">
      {value.toString().padStart(2, '0')}
    </div>
    <div className="text-[9px] tracking-[0.3em] uppercase font-bold text-foreground/50">
      {label}
    </div>
  </div>
);

const SectionLabel: React.FC<{ icon: React.ReactNode, label: string, noBorder?: boolean }> = ({ icon, label, noBorder }) => (
  <div className={`flex items-center gap-3 text-foreground/60 ${!noBorder ? 'border-b border-foreground/5 pb-4' : ''}`}>
    {icon}
    <span className="text-[10px] tracking-[0.3em] uppercase font-bold">{label}</span>
  </div>
);

const InfoRow: React.FC<{ label: string, value: string, icon: React.ReactNode }> = ({ label, value, icon }) => (
  <div className="group">
    <div className="text-[9px] tracking-widest uppercase font-bold text-foreground/30 mb-1 flex items-center gap-2">
      {icon}
      {label}
    </div>
    <div className="text-lg md:text-xl font-light tracking-tight text-foreground group-hover:pl-2 transition-all duration-300">
      {value}
    </div>
  </div>
);