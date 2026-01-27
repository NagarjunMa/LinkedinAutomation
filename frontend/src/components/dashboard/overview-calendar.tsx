"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { BentoCard } from './bento-card';

export const OverviewCalendar = () => {
    // Mock data for the calendar display
    const days = Array.from({ length: 31 }, (_, i) => i + 1);
    const startDay = 3; // Wednesday start for example month

    return (
        <BentoCard title="Overview Calendar" action={<span className="text-[10px] font-mono text-[#3b3b3b]/40 uppercase tracking-tighter">January 2026</span>} className="col-span-12 lg:col-span-8">
            <div className="flex justify-between mb-8 items-end">
                <div className="flex gap-12">
                    <div className="text-center">
                        <p className="text-3xl font-mono font-medium">528</p>
                        <p className="text-[10px] uppercase tracking-tighter text-[#3b3b3b]/40">Total Jobs</p>
                    </div>
                    <div className="text-center border-x border-[#3b3b3b]/10 px-12">
                        <p className="text-3xl font-mono font-medium text-[#3b3b3b]">22</p>
                        <p className="text-[10px] uppercase tracking-tighter text-[#3b3b3b]/40">Applied</p>
                    </div>
                    <div className="text-center">
                        <p className="text-3xl font-mono font-medium text-[#3b3b3b]/10">0</p>
                        <p className="text-[10px] uppercase tracking-tighter text-[#3b3b3b]/40">Interviews</p>
                    </div>
                </div>
                <div className="hidden md:block">
                    <div className="w-32 h-1 bg-[#3b3b3b]/5 overflow-hidden rounded-full">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: '66%' }}
                            transition={{ duration: 2, ease: [0.22, 1, 0.36, 1] }}
                            className="h-full bg-[#3b3b3b]/40"
                        />
                    </div>
                    <p className="text-[8px] font-mono text-right mt-1 text-[#3b3b3b]/40 uppercase">System Efficiency: 66%</p>
                </div>
            </div>

            <div className="grid grid-cols-7 gap-y-4 text-center">
                {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map(d => (
                    <span key={d} className="text-[10px] font-bold text-[#3b3b3b]/30">{d}</span>
                ))}
                {Array.from({ length: startDay }).map((_, i) => <span key={`empty-${i}`} />)}
                {days.map(day => (
                    <div key={day} className="flex items-center justify-center h-8">
                        <span className={`text-[11px] font-mono w-6 h-6 flex items-center justify-center rounded-sm cursor-default transition-all duration-700 ${day === 27 ? 'bg-[#3b3b3b] text-white' : 'text-[#3b3b3b]/60 hover:bg-[#3b3b3b]/5'}`}>
                            {day}
                        </span>
                    </div>
                ))}
            </div>
        </BentoCard>
    );
};
