"use client";

import React from 'react';
import {
    Search,
    Bell,
    Settings,
    Sun,
    LayoutGrid,
    ChevronDown
} from 'lucide-react';
import { useAuth } from '@/contexts/auth-context';

export const DashboardHeader = () => {
    const { user } = useAuth();

    return (
        <header className="flex items-center justify-between mb-12 bg-white/50 border border-[#3b3b3b]/10 p-5 backdrop-blur-md">
            <div className="flex items-center gap-8 px-4">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 border border-[#3b3b3b]/10 flex items-center justify-center bg-white">
                        <LayoutGrid className="w-5 h-5 text-[#3b3b3b]" />
                    </div>
                    <h1 className="text-xl font-light tracking-tight text-[#3b3b3b]">JobFlow <span className="font-serif-italic">Pro</span></h1>
                </div>
                <div className="h-8 w-px bg-[#3b3b3b]/10" />
                <div className="relative group hidden md:block">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#3b3b3b]/20" />
                    <input
                        type="text"
                        placeholder="Search jobs, companies... (⌘F)"
                        className="bg-[#f0eff2]/50 border border-[#3b3b3b]/5 pl-12 pr-6 py-2.5 text-[11px] w-80 focus:outline-none focus:border-[#3b3b3b]/20 transition-all duration-700 font-light"
                    />
                </div>
            </div>
            <div className="flex items-center gap-8 px-4">
                <div className="flex gap-6 items-center">
                    <div className="relative cursor-pointer group">
                        <Bell className="w-4 h-4 text-[#3b3b3b]/40 group-hover:text-[#3b3b3b] transition-colors" />
                        <span className="absolute -top-1.5 -right-1.5 w-3.5 h-3.5 bg-[#3b3b3b] text-white text-[7px] flex items-center justify-center font-bold">2</span>
                    </div>
                    <Settings className="w-4 h-4 text-[#3b3b3b]/40 hover:text-[#3b3b3b] transition-colors cursor-pointer" />
                    <Sun className="w-4 h-4 text-[#3b3b3b]/40 hover:text-[#3b3b3b] transition-colors cursor-pointer" />
                </div>
                <div className="h-8 w-px bg-[#3b3b3b]/10" />
                <div className="flex items-center gap-4 cursor-pointer group">
                    <div className="text-right hidden sm:block">
                        <p className="text-[11px] font-bold uppercase tracking-tighter text-[#3b3b3b]">{user?.email?.split('@')[0] || 'User'}</p>
                        <p className="text-[9px] text-[#3b3b3b]/40 italic">Professional Account</p>
                    </div>
                    <div className="w-10 h-10 bg-white border border-[#3b3b3b]/10 flex items-center justify-center text-[12px] font-bold group-hover:bg-[#3b3b3b] group-hover:text-white transition-all duration-700">
                        {user?.email?.[0].toUpperCase() || 'U'}
                    </div>
                    <ChevronDown className="w-3 h-3 text-[#3b3b3b]/20" />
                </div>
            </div>
        </header>
    );
};
