"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { BentoCard } from './bento-card';
import { useDashboard } from '@/app/contexts/dashboard-context';

export const RecentApplications = () => {
    const { recentApplications } = useDashboard();

    const applications = recentApplications && recentApplications.length > 0 ? recentApplications.map(app => ({
        type: app.title || 'Unknown Role',
        company: app.company || 'Unknown Company',
        amount: 'TBD', // Backend doesn't provide this yet
        status: app.status || 'Applied',
        method: app.extracted_date ? 'AI Extraction' : 'Manual',
        date: app.appliedAt ? new Date(app.appliedAt).toLocaleDateString() : 'Recently'
    })) : [];

    return (
        <BentoCard title="Recent Applications (Top 10)" className="col-span-12 overflow-hidden" action={<span className="text-[10px] sm:text-xs text-app-text/60 font-bold uppercase cursor-pointer hover:text-app-text transition-colors">Filter</span>}>
            <div className="overflow-x-auto pb-4">
                <table className="w-full text-left border-collapse min-w-[800px] lg:min-w-full">
                    <thead>
                        <tr className="border-b border-app-text/10">
                            <th className="py-5 text-[10px] sm:text-xs font-extrabold uppercase tracking-widest text-app-text/50">Role Identification</th>
                            <th className="py-5 text-[10px] sm:text-xs font-extrabold uppercase tracking-widest text-app-text/50">Compensation</th>
                            <th className="py-5 text-[10px] sm:text-xs font-extrabold uppercase tracking-widest text-app-text/50 text-center">Status</th>
                            <th className="py-5 text-[10px] sm:text-xs font-extrabold uppercase tracking-widest text-app-text/50">Acquisition Method</th>
                        </tr>
                    </thead>
                    <tbody>
                        {applications.slice(0, 10).map((app, i) => (
                            <motion.tr
                                key={i}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: i * 0.05 }}
                                className="border-b border-app-text/5 hover:bg-app-text/5 transition-colors duration-500 group"
                            >
                                <td className="py-6 pr-4">
                                    <p className="text-sm sm:text-base font-bold text-app-text tracking-tight">{app.type}</p>
                                    <p className="text-xs text-app-text/60 italic font-medium mt-1">{app.company}</p>
                                </td>
                                <td className="py-6 text-xs sm:text-sm font-mono text-app-text/80 font-medium">
                                    {app.amount}
                                </td>
                                <td className="py-6 text-center">
                                    <span className={`text-[10px] sm:text-xs font-bold uppercase tracking-widest px-4 py-1.5 rounded-sm border transition-all duration-700 ${app.status === 'Applied' ? 'border-app-text/10 text-app-text/50' :
                                        app.status === 'Interview' ? 'border-app-text/40 text-app-text bg-app-text/5' :
                                            app.status === 'Success' ? 'border-green-500/40 text-green-600 bg-green-500/5' :
                                                'border-app-text/5 text-app-text/10 line-through'
                                        }`}>
                                        {app.status}
                                    </span>
                                </td>
                                <td className="py-6 pl-4">
                                    <p className="text-xs sm:text-sm font-semibold text-app-text/70">{app.method}</p>
                                    <p className="text-[10px] sm:text-xs text-app-text/40 font-mono italic mt-0.5">{app.date}</p>
                                </td>
                            </motion.tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <div className="mt-12 flex flex-col sm:flex-row gap-4 justify-between items-center text-[10px] sm:text-xs text-app-text/40 font-mono uppercase tracking-widest font-medium">
                <span>System Log: {Math.min(applications.length, 10)} / {recentApplications?.length || 15} records displayed</span>
                <div className="flex gap-8">
                    <button className="hover:text-app-text transition-all duration-700 disabled:opacity-30 font-bold" disabled>Previous Page</button>
                    <button className="hover:text-app-text transition-all duration-700 font-bold">Next Page</button>
                </div>
            </div>
        </BentoCard>
    );
};
