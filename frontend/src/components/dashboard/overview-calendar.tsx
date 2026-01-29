"use client";
import React from 'react';
import { motion } from 'framer-motion';
import { BentoCard } from './bento-card';
import { useDashboard } from '@/app/contexts/dashboard-context';

export const OverviewCalendar = () => {
    const { stats } = useDashboard();

    // Calculate days for the current month
    const currentDate = new Date();
    const daysInMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0).getDate();
    const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);
    const startDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1).getDay(); // 0 is Sunday

    // Map daily stats to date check
    const activityMap = new Map<number, number>();
    if (stats?.applicationsByDate) {
        stats.applicationsByDate.forEach(stat => {
            const date = new Date(stat.date);
            // Only map if same month/year
            if (date.getMonth() === currentDate.getMonth() && date.getFullYear() === currentDate.getFullYear()) {
                activityMap.set(date.getDate(), (stat.jobs_applied || 0) + (stat.jobs_extracted || 0));
            }
        });
    }

    const totalJobs = stats?.totalJobs || 0;
    const appliedJobs = stats?.appliedJobs || 0;
    const interviewCount = stats?.interviews || 0;
    // Calculate system efficiency based on response/success rate or just default to 0 if not available
    const systemEfficiency = stats?.successRate || 0;

    return (
        <BentoCard title="Overview Calendar" action={<span className="text-[10px] font-mono text-app-text/40 uppercase tracking-tighter">{currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}</span>} className="col-span-12 xl:col-span-8">
            <div className="flex flex-col xl:flex-row justify-between mb-8 items-start xl:items-end gap-6">
                <div className="flex gap-8 sm:gap-12 w-full sm:w-auto overflow-x-auto pb-2 sm:pb-0">
                    <div className="text-center min-w-fit">
                        <p className="text-4xl sm:text-5xl font-mono font-medium text-app-text">{totalJobs}</p>
                        <p className="text-[10px] sm:text-xs font-bold uppercase tracking-widest text-app-text/60 mt-1">Total Jobs</p>
                    </div>
                    <div className="text-center border-x border-app-text/10 px-8 sm:px-12 min-w-fit">
                        <p className="text-4xl sm:text-5xl font-mono font-medium text-app-text">{appliedJobs}</p>
                        <p className="text-[10px] sm:text-xs font-bold uppercase tracking-widest text-app-text/60 mt-1">Applied</p>
                    </div>
                    <div className="text-center min-w-fit">
                        <p className="text-4xl sm:text-5xl font-mono font-medium text-app-text/20">{interviewCount}</p>
                        <p className="text-[10px] sm:text-xs font-bold uppercase tracking-widest text-app-text/40 mt-1">Interviews</p>
                    </div>
                </div>
                <div className="w-full xl:w-auto">
                    <div className="w-full xl:w-32 h-1.5 bg-app-text/5 overflow-hidden rounded-full">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${Math.min(systemEfficiency, 100)}%` }}
                            transition={{ duration: 2, ease: [0.22, 1, 0.36, 1] }}
                            className="h-full bg-app-text"
                        />
                    </div>
                    <p className="text-[9px] sm:text-[10px] font-mono text-left xl:text-right mt-2 text-app-text/60 uppercase font-medium tracking-wider">System Efficiency: {systemEfficiency}%</p>
                </div>
            </div>

            <div className="grid grid-cols-7 gap-y-4 gap-x-2 text-center">
                {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map(d => (
                    <span key={d} className="text-[11px] sm:text-xs font-extrabold text-app-text/40">{d}</span>
                ))}
                {Array.from({ length: startDay }).map((_, i) => <span key={`empty-${i}`} />)}
                {days.map(day => {
                    const activity = activityMap.get(day) || 0;
                    const isToday = day === currentDate.getDate();

                    return (
                        <div key={day} className="flex items-center justify-center h-8 sm:h-10">
                            <span className={`text-[11px] sm:text-sm font-mono w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center rounded-sm cursor-default transition-all duration-700 ${isToday ? 'bg-app-text text-app-bg shadow-lg' :
                                    activity > 0 ? 'font-bold text-app-text bg-app-text/10' :
                                        'text-app-text/70 hover:bg-app-text/5 hover:font-bold'
                                }`}>
                                {day}
                            </span>
                        </div>
                    );
                })}
            </div>
        </BentoCard>
    );
};
