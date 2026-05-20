"use client";

import React from 'react';
import { motion } from 'framer-motion';
import {
    BarChart3,
} from 'lucide-react';
import { useDashboard } from '@/app/contexts/dashboard-context';

// New Components

import { OverviewCalendar } from '@/components/dashboard/overview-calendar';
import { QuickActions } from '@/components/dashboard/quick-actions';
import { ChartAreaInteractive } from '@/components/dashboard/market-engagement-chart';
import { RecentApplications } from '@/components/dashboard/recent-applications';
import { PremiumButton } from '@/components/ui/premium-button';

import { useRouter } from 'next/navigation';

export default function DashboardPage() {
    const { stats: _stats, userProfile, loading } = useDashboard();
    const router = useRouter();
    const [isWarningIgnored, setIsWarningIgnored] = React.useState(false);

    // Calculate if calibration is needed based on "missing personal information"
    const needsCalibration = React.useMemo(() => {
        if (!userProfile) return false;

        // Essential fields check per user requirement
        const hasEducation = (userProfile.education_history?.length ?? 0) > 0 || (userProfile.degrees?.length ?? 0) > 0;
        const hasExperience = (userProfile.work_experiences?.length ?? 0) > 0 || (userProfile.job_titles?.length ?? 0) > 0;
        const hasProjectInfo = !!userProfile.professional_summary; // Assuming summary covers "project information" or general context

        // If any essential section is missing
        return !hasEducation || !hasExperience || !hasProjectInfo;
    }, [userProfile]);

    const handleSynchronize = () => {
        router.push('/dashboard/profile');
    };

    const handleIgnore = () => {
        setIsWarningIgnored(true);
    };

    // Calculate completion percentage for display
    const completionPercentage = userProfile?.profile_completion || 66; // Fallback to 66 purely for visual consistency if not loaded

    return (
        <div className="min-h-screen bg-app-bg text-app-text max-w-[1500px] mx-auto pb-24 px-4 md:px-8 transition-colors duration-300">


            {/* Profiling State Alert */}
            {needsCalibration && !isWarningIgnored && !loading && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                    className="mb-8 md:mb-12 p-6 md:p-10 border border-app-text/10 bg-app-card/40 flex flex-col xl:flex-row justify-between items-start xl:items-center gap-8 backdrop-blur-sm rounded-lg overflow-hidden"
                >
                    <div className="flex flex-col sm:flex-row gap-6 items-start max-w-full">
                        <div className="w-14 h-14 border border-app-text/10 flex-shrink-0 flex items-center justify-center text-app-text/40 bg-app-bg shadow-sm">
                            <BarChart3 className="w-6 h-6" />
                        </div>
                        <div className="space-y-3">
                            <h2 className="text-2xl sm:text-3xl font-normal tracking-tight uppercase text-app-text break-words">System Calibration <span className="font-serif-italic font-medium block sm:inline text-app-accent">Required</span></h2>
                            <p className="text-xs sm:text-sm text-app-text/60 font-medium tracking-wide max-w-2xl">{completionPercentage}% DATA ACCURACY • Complete your professional profile to refine AI matching precision.</p>
                        </div>
                    </div>
                    <div className="flex flex-col sm:flex-row gap-4 w-full xl:w-auto">
                        <PremiumButton onClick={handleSynchronize} className="w-full sm:w-auto text-[10px] sm:text-xs">
                            Synchronize Identity
                        </PremiumButton>
                        <PremiumButton onClick={handleIgnore} className="w-full sm:w-auto text-[10px] sm:text-xs bg-transparent border-app-text/20 shadow-none hover:shadow-lg">
                            Ignore Warnings
                        </PremiumButton>
                    </div>
                </motion.div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-10">
                {/* ROW 1: CALENDAR & QUICK ACTIONS */}
                <OverviewCalendar />
                <QuickActions />

                {/* ROW 2: INTERACTIVE CHART */}
                <ChartAreaInteractive />

                {/* ROW 3: RECENT JOBS */}
                <RecentApplications />
            </div>

            <footer className="mt-32 pt-16 border-t border-app-text/10 flex flex-col sm:flex-row gap-4 justify-between items-center text-center sm:text-left">
                <p className="text-xs font-mono text-app-text/40 tracking-[0.2em] uppercase font-medium">SYSTEM CORE V2.4.9 — LEICA THEORY MINIMALISM</p>
                <p className="text-xs font-mono text-app-text/40 italic">PRECISION IS THE ONLY MEASURE.</p>
            </footer>
        </div>
    );
}