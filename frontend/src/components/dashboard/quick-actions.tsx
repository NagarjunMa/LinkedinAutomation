"use client";

import React from 'react';
import { BentoCard } from './bento-card';
import {
    Link as LinkIcon,
    FileSearch,
    BarChart3
} from 'lucide-react';
import Link from 'next/link';

export const QuickActions = () => (
    <BentoCard title="Quick Actions" action={<span className="text-[10px] text-[#3b3b3b]/40 uppercase cursor-pointer hover:text-[#3b3b3b] transition-colors">Manage</span>} className="col-span-12 lg:col-span-4">
        <div className="space-y-4">
            {[
                { icon: <LinkIcon className="w-4 h-4" />, label: 'Job Intelligence', sub: 'Extract details from URL', shortcut: 'E', href: '/dashboard/applications' },
                { icon: <FileSearch className="w-4 h-4" />, label: 'Resume Review', sub: 'AI-powered matching', shortcut: 'R', href: '/dashboard/resume-evaluation' },
                { icon: <BarChart3 className="w-4 h-4" />, label: 'Performance', sub: 'Track systemic progress', shortcut: 'A', href: '/dashboard/analytics' },
            ].map((action, i) => (
                <Link
                    key={i}
                    href={action.href}
                    className="group border border-[#3b3b3b]/5 bg-white/20 p-5 flex items-center gap-4 hover:border-[#3b3b3b]/20 transition-all duration-700 cursor-pointer block"
                >
                    <div className="w-12 h-12 border border-[#3b3b3b]/10 flex items-center justify-center bg-white group-hover:bg-[#3b3b3b] group-hover:text-white transition-all duration-700 bg-white">
                        {action.icon}
                    </div>
                    <div className="flex-1">
                        <p className="text-[11px] font-bold uppercase tracking-tight text-[#3b3b3b]">{action.label}</p>
                        <p className="text-[10px] text-[#3b3b3b]/40 italic">{action.sub}</p>
                    </div>
                    <span className="text-[9px] font-mono text-[#3b3b3b]/20 px-2 border border-[#3b3b3b]/10">{action.shortcut}</span>
                </Link>
            ))}
        </div>
    </BentoCard>
);
