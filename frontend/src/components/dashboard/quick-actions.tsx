"use client";

import React from 'react';
import { BentoCard } from './bento-card';
import {
    Link as LinkIcon,
    FileSearch,
    Briefcase
} from 'lucide-react';
import Link from 'next/link';

export const QuickActions = () => (
    <BentoCard title="Quick Actions" action={<span className="text-[10px] sm:text-xs text-app-text/60 font-bold uppercase cursor-pointer hover:text-app-text transition-colors">Manage</span>} className="col-span-12 xl:col-span-4">
        <div className="space-y-4">
            {[
                { icon: <LinkIcon className="w-5 h-5" />, label: 'Job Intelligence', sub: 'Extract details from URL', shortcut: 'E', href: '/dashboard/applications' },
                { icon: <FileSearch className="w-5 h-5" />, label: 'Resume Review', sub: 'AI-powered matching', shortcut: 'R', href: '/dashboard/resume-evaluation' },
                { icon: <Briefcase className="w-5 h-5" />, label: 'Job Search', sub: 'Startup job portals', shortcut: 'J', href: '/dashboard/jobs' },
            ].map((action, i) => (
                <Link
                    key={i}
                    href={action.href}
                    className="group border border-app-text/5 bg-app-bg/40 hover:bg-app-bg p-4 sm:p-5 flex items-center gap-5 hover:border-app-text/20 transition-all duration-500 cursor-pointer block hover:shadow-sm"
                >
                    <div className="w-12 h-12 sm:w-14 sm:h-14 border border-app-text/10 flex items-center justify-center bg-app-surface group-hover:bg-app-text group-hover:text-app-bg transition-all duration-500 rounded-sm text-app-text">
                        {action.icon}
                    </div>
                    <div className="flex-1">
                        <p className="text-xs sm:text-sm font-extrabold uppercase tracking-tight text-app-text group-hover:translate-x-1 transition-transform duration-500">{action.label}</p>
                        <p className="text-[10px] sm:text-xs text-app-text/60 italic mt-0.5">{action.sub}</p>
                    </div>
                    <span className="text-[10px] font-mono text-app-text/40 font-bold px-2.5 py-1 border border-app-text/10 bg-app-surface/50 rounded-sm">{action.shortcut}</span>
                </Link>
            ))}
        </div>
    </BentoCard>
);
