"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { BentoCard } from './bento-card';
import { useDashboard } from '@/app/contexts/dashboard-context';

export const RecentApplications = () => {
    const { recentApplications } = useDashboard();

    // Transform existing backend data or use mock if empty
    const applications = recentApplications && recentApplications.length > 0 ? recentApplications.map(app => ({
        type: app.title || 'Unknown Role',
        company: app.company || 'Unknown Company',
        amount: 'TBD', // Backend doesn't provide this yet
        status: app.status || 'Applied',
        method: app.extracted_date ? 'AI Extraction' : 'Manual',
        date: app.appliedAt ? new Date(app.appliedAt).toLocaleDateString() : 'Recently'
    })) : [
        { type: 'Software Engineer, Backend', company: 'Betterment', amount: 'TBD', status: 'Applied', method: 'AI Extraction', date: '2025-11-30' },
        { type: 'Staff Developer, Core Platform', company: 'Stripe', amount: '$240k', status: 'Interview', method: 'Manual Entry', date: '2025-11-28' },
        { type: 'Job from linkedin.com', company: 'Unknown Company', amount: 'TBD', status: 'Applied', method: 'AI Extraction', date: '2025-11-26' },
    ];

    return (
        <BentoCard title="Recent Applications (Top 10)" className="col-span-12 overflow-hidden" action={<span className="text-[10px] text-[#3b3b3b]/40 uppercase cursor-pointer hover:text-[#3b3b3b] transition-colors">Filter</span>}>
            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="border-b border-[#3b3b3b]/10">
                            <th className="py-4 text-[9px] font-bold uppercase tracking-widest text-[#3b3b3b]/40">Role Identification</th>
                            <th className="py-4 text-[9px] font-bold uppercase tracking-widest text-[#3b3b3b]/40">Compensation</th>
                            <th className="py-4 text-[9px] font-bold uppercase tracking-widest text-[#3b3b3b]/40 text-center">Status</th>
                            <th className="py-4 text-[9px] font-bold uppercase tracking-widest text-[#3b3b3b]/40">Acquisition Method</th>
                        </tr>
                    </thead>
                    <tbody>
                        {applications.slice(0, 10).map((app, i) => (
                            <motion.tr
                                key={i}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: i * 0.05 }}
                                className="border-b border-[#3b3b3b]/5 hover:bg-[#3b3b3b]/5 transition-colors duration-500 group"
                            >
                                <td className="py-6 pr-4">
                                    <p className="text-[12px] font-bold text-[#3b3b3b] tracking-tight">{app.type}</p>
                                    <p className="text-[10px] text-[#3b3b3b]/40 italic font-light">{app.company}</p>
                                </td>
                                <td className="py-6 text-[10px] font-mono text-[#3b3b3b]/60">
                                    {app.amount}
                                </td>
                                <td className="py-6 text-center">
                                    <span className={`text-[9px] font-bold uppercase tracking-widest px-4 py-1.5 rounded-sm border transition-all duration-700 ${app.status === 'Applied' ? 'border-[#3b3b3b]/10 text-[#3b3b3b]/30' :
                                            app.status === 'Interview' ? 'border-[#3b3b3b]/40 text-[#3b3b3b] bg-[#3b3b3b]/5' :
                                                app.status === 'Success' ? 'border-green-500/40 text-green-600 bg-green-500/5' :
                                                    'border-[#3b3b3b]/5 text-[#3b3b3b]/10 line-through'
                                        }`}>
                                        {app.status}
                                    </span>
                                </td>
                                <td className="py-6 pl-4">
                                    <p className="text-[11px] font-medium text-[#3b3b3b]/60">{app.method}</p>
                                    <p className="text-[9px] text-[#3b3b3b]/20 font-mono italic">{app.date}</p>
                                </td>
                            </motion.tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <div className="mt-12 flex justify-between items-center text-[10px] text-[#3b3b3b]/30 font-mono uppercase tracking-widest">
                <span>System Log: {Math.min(applications.length, 10)} / {recentApplications?.length || 15} records displayed</span>
                <div className="flex gap-8">
                    <button className="hover:text-[#3b3b3b] transition-all duration-700 disabled:opacity-10" disabled>Previous Page</button>
                    <button className="hover:text-[#3b3b3b] transition-all duration-700">Next Page</button>
                </div>
            </div>
        </BentoCard>
    );
};
