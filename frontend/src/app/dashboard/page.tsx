"use client";

import React from 'react';
import { motion } from 'framer-motion';
import {
    Wand2,
    Coins,
    Briefcase,
    LibraryBig,
    ArrowRight,
    BarChart3,
    Upload,
    Zap,
} from 'lucide-react';
import { useDashboard } from '@/app/contexts/dashboard-context';
import { PremiumButton } from '@/components/ui/premium-button';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

const LeicaBezier: [number, number, number, number] = [0.22, 1, 0.36, 1];

const primaryActions = [
    {
        icon: <Upload className="w-6 h-6" />,
        title: 'Polish a Resume',
        description: 'Review content feedback and document checks, then consider bullet-point rewrites supported by your experience.',
        href: '/dashboard/resume',
        shortcut: 'R',
        cta: 'Open Resume Lab',
    },
    {
        icon: <Wand2 className="w-6 h-6" />,
        title: 'Tailor to a JD',
        description: 'Compare a job description with your resume. Review gaps and accept only changes supported by your actual experience.',
        href: '/dashboard/resume/tailor',
        shortcut: 'T',
        cta: 'Start Tailoring',
    },
    {
        icon: <LibraryBig className="w-6 h-6" />,
        title: 'Resume Library',
        description: 'Review saved company-specific resumes, source JDs, accepted changes, and export the version you used.',
        href: '/dashboard/library',
        shortcut: 'L',
        cta: 'Review Saved Work',
    },
    {
        icon: <Coins className="w-6 h-6" />,
        title: 'View Credits',
        description: 'Check your remaining evaluation credits and export quota. Each AI evaluation costs one credit.',
        href: '/dashboard/credits',
        shortcut: 'C',
        cta: 'Manage Credits',
    },
    {
        icon: <Briefcase className="w-6 h-6" />,
        title: 'Applications',
        description: 'Track the roles you have applied to. Link each application to the resume version you submitted.',
        href: '/dashboard/applications',
        shortcut: 'A',
        cta: 'View Pipeline',
    },
];

export default function DashboardPage() {
    const { userProfile, loading } = useDashboard();
    const router = useRouter();
    const [isWarningIgnored, setIsWarningIgnored] = React.useState(false);

    const userName = userProfile?.full_name
        ? userProfile.full_name.split(' ')[0]
        : null;

    const needsCalibration = React.useMemo(() => {
        if (!userProfile) return false;
        const hasEducation = (userProfile.education_history?.length ?? 0) > 0 || (userProfile.degrees?.length ?? 0) > 0;
        const hasExperience = (userProfile.work_experiences?.length ?? 0) > 0 || (userProfile.job_titles?.length ?? 0) > 0;
        const hasProjectInfo = !!userProfile.professional_summary;
        return !hasEducation || !hasExperience || !hasProjectInfo;
    }, [userProfile]);

    const completionPercentage = userProfile?.profile_completion || 66;

    return (
        <div className="min-h-screen bg-app-bg text-app-text max-w-[1400px] mx-auto pb-24 px-4 md:px-8 transition-colors duration-300">

            {/* Profile Calibration Alert */}
            {needsCalibration && !isWarningIgnored && !loading && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                    className="mb-8 md:mb-12 p-6 md:p-10 border border-app-text/10 bg-app-card/40 flex flex-col xl:flex-row justify-between items-start xl:items-center gap-8 backdrop-blur-sm rounded-lg overflow-hidden"
                >
                    <div className="flex flex-col sm:flex-row gap-6 items-start max-w-full">
                        <div className="w-14 h-14 border border-app-text/10 shrink-0 flex items-center justify-center text-app-text/40 bg-app-bg shadow-sm">
                            <BarChart3 className="w-6 h-6" />
                        </div>
                        <div className="space-y-3">
                            <h2 className="text-2xl sm:text-3xl font-normal tracking-tight uppercase text-app-text break-words">
                                Profile Incomplete{' '}
                                <span className="font-serif-italic font-medium block sm:inline text-app-accent">
                                    Action Required
                                </span>
                            </h2>
                            <p className="text-xs sm:text-sm text-app-text/60 font-medium tracking-wide max-w-2xl">
                                {completionPercentage}% complete — Add your experience, education, and a short professional summary so the AI can generate accurate resume rewrites.
                            </p>
                        </div>
                    </div>
                    <div className="flex flex-col sm:flex-row gap-4 w-full xl:w-auto">
                        <PremiumButton onClick={() => router.push('/dashboard/profile')} className="w-full sm:w-auto text-[10px] sm:text-xs">
                            Complete Profile
                        </PremiumButton>
                        <PremiumButton onClick={() => setIsWarningIgnored(true)} className="w-full sm:w-auto text-[10px] sm:text-xs bg-transparent border-app-text/20 shadow-none hover:shadow-lg">
                            Dismiss
                        </PremiumButton>
                    </div>
                </motion.div>
            )}

            {/* Welcome Header */}
            <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, ease: LeicaBezier }}
                className="mb-12 md:mb-16"
            >
                <p className="text-[10px] font-extrabold tracking-[0.2em] uppercase text-app-text/40 mb-3">
                    Prism Pro — Resume Intelligence
                </p>
                <h1 className="text-4xl md:text-5xl font-serif-italic text-app-text tracking-tight">
                    {userName ? `Welcome back, ${userName}.` : 'Welcome back.'}
                </h1>
                <p className="mt-4 text-sm text-app-text/60 font-medium max-w-xl">
                    Your resume workspace. Review content suggestions separately from document checks; neither predicts a hiring outcome.
                </p>
            </motion.div>

            {/* Primary Action Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-6 md:gap-8 mb-20">
                {primaryActions.map((action, i) => (
                    <motion.div
                        key={action.href}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, ease: LeicaBezier, delay: i * 0.08 }}
                    >
                        <Link
                            href={action.href}
                            className="group flex flex-col h-full border border-app-text/5 bg-app-card/40 hover:bg-app-card hover:border-app-text/20 p-6 md:p-8 transition-all duration-500 rounded-sm hover:shadow-lg block"
                        >
                            {/* Icon + shortcut row */}
                            <div className="flex items-start justify-between mb-6">
                                <div className="w-12 h-12 border border-app-text/10 flex items-center justify-center bg-app-bg group-hover:bg-app-text group-hover:text-app-bg transition-all duration-500 rounded-sm text-app-text">
                                    {action.icon}
                                </div>
                                <span className="text-[10px] font-mono text-app-text/30 font-bold px-2 py-1 border border-app-text/10 bg-app-surface/50 rounded-sm">
                                    {action.shortcut}
                                </span>
                            </div>

                            {/* Title + description */}
                            <div className="flex-1">
                                <h3 className="text-sm font-extrabold uppercase tracking-tight text-app-text mb-2 group-hover:translate-x-1 transition-transform duration-500">
                                    {action.title}
                                </h3>
                                <p className="text-xs text-app-text/60 font-medium leading-relaxed">
                                    {action.description}
                                </p>
                            </div>

                            {/* CTA row */}
                            <div className="mt-6 flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-app-text/40 group-hover:text-app-text transition-colors duration-500">
                                <span>{action.cta}</span>
                                <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform duration-500" />
                            </div>
                        </Link>
                    </motion.div>
                ))}
            </div>

            {/* Quick-start hint */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.8, ease: LeicaBezier, delay: 0.5 }}
                className="border border-app-text/5 bg-app-card/20 p-6 md:p-8 flex flex-col md:flex-row items-start md:items-center gap-6 rounded-sm"
            >
                <div className="w-10 h-10 border border-app-text/10 flex items-center justify-center bg-app-bg text-app-text/40 shrink-0 rounded-sm">
                    <Zap className="w-5 h-5" />
                </div>
                <div className="flex-1">
                    <p className="text-xs font-extrabold uppercase tracking-widest text-app-text mb-1">
                        New here? Start with Resume Polish.
                    </p>
                    <p className="text-xs text-app-text/50 font-medium leading-relaxed">
                        Upload your current resume, review its content and document findings, then use Tailor to compare it with a target job description.
                    </p>
                </div>
                <Link
                    href="/dashboard/resume"
                    className="shrink-0 inline-flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider border border-app-text/20 px-4 py-2 hover:bg-app-text hover:text-app-bg transition-all duration-500 rounded-sm text-app-text"
                >
                    Get Started <ArrowRight className="w-3 h-3" />
                </Link>
            </motion.div>

            <footer className="mt-32 pt-16 border-t border-app-text/10 flex flex-col sm:flex-row gap-4 justify-between items-center text-center sm:text-left">
                <p className="text-xs font-mono text-app-text/40 tracking-[0.2em] uppercase font-medium">Prism Pro — Recruiter-Grade Resume Intelligence</p>
                <p className="text-xs font-mono text-app-text/40 italic">Every bullet point earned.</p>
            </footer>
        </div>
    );
}
