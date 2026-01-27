"use client";

import React from 'react';
import { motion } from 'framer-motion';
import {
    BarChart3,
} from 'lucide-react';
import { useDashboard } from '@/app/contexts/dashboard-context';

// New Components
import { DashboardHeader } from '@/components/dashboard/header';
import { OverviewCalendar } from '@/components/dashboard/overview-calendar';
import { QuickActions } from '@/components/dashboard/quick-actions';
import { ChartAreaInteractive } from '@/components/dashboard/market-engagement-chart';
import { RecentApplications } from '@/components/dashboard/recent-applications';

export default function DashboardPage() {
    const { stats } = useDashboard();

    return (
        <div className="max-w-[1500px] mx-auto pb-24 px-4 md:px-8">
            <DashboardHeader />

            {/* Profiling State Alert */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-12 p-10 border border-[#3b3b3b]/10 bg-white/40 flex flex-col md:flex-row justify-between items-center gap-8 backdrop-blur-sm rounded-lg"
            >
                <div className="flex gap-6 items-start">
                    <div className="w-12 h-12 border border-[#3b3b3b]/10 flex items-center justify-center text-[#3b3b3b]/40 bg-white">
                        <BarChart3 className="w-5 h-5" />
                    </div>
                    <div className="space-y-2">
                        <h2 className="text-2xl font-light tracking-tight uppercase text-[#3b3b3b]">System Calibration <span className="font-serif-italic">Required</span></h2>
                        <p className="text-[11px] text-[#3b3b3b]/40 font-medium tracking-wide">66% DATA ACCURACY • Complete your professional profile to refine AI matching precision.</p>
                    </div>
                </div>
                <div className="flex gap-6">
                    <button className="px-8 py-3 bg-[#3b3b3b] text-white text-[10px] font-bold uppercase tracking-widest hover:bg-[#3b3b3b]/90 transition-all duration-700">Synchronize Identity</button>
                    <button className="px-8 py-3 border border-[#3b3b3b]/10 text-[#3b3b3b]/40 text-[10px] font-bold uppercase tracking-widest hover:text-[#3b3b3b] hover:border-[#3b3b3b]/30 transition-all duration-700">Ignore Warnings</button>
                </div>
            </motion.div>

            <div className="grid grid-cols-12 gap-10">
                {/* ROW 1: CALENDAR & QUICK ACTIONS */}
                <OverviewCalendar />
                <QuickActions />

                {/* ROW 2: INTERACTIVE CHART */}
                <ChartAreaInteractive />

                {/* ROW 3: RECENT JOBS */}
                <RecentApplications />
            </div>

            <footer className="mt-32 pt-16 border-t border-[#3b3b3b]/10 flex justify-between items-center">
                <p className="text-[10px] font-mono text-[#3b3b3b]/20 tracking-[0.5em] uppercase">SYSTEM CORE V2.4.9 — LEICA THEORY MINIMALISM</p>
                <p className="text-[10px] font-mono text-[#3b3b3b]/20 italic">PRECISION IS THE ONLY MEASURE.</p>
            </footer>
        </div>
    );
}