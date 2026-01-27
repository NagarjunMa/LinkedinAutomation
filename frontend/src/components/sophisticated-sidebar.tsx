"use client";

import React, { useState, createContext, useContext } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    FileText,
    Search,
    Briefcase,
    Users,
    ChevronRight,
    PanelLeft,
    LayoutGrid,
    Settings,
    LogOut,
    ChevronDown
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from "@/contexts/auth-context";

// Sidebar State Management
const SidebarContext = createContext<{
    isCollapsed: boolean;
    toggle: () => void;
}>({ isCollapsed: false, toggle: () => { } });

export const SidebarProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const toggle = () => setIsCollapsed(!isCollapsed);
    return (
        <SidebarContext.Provider value={{ isCollapsed, toggle }}>
            {children}
        </SidebarContext.Provider>
    );
};

export const useSidebar = () => useContext(SidebarContext);

const NavItem: React.FC<{
    to: string;
    label: string;
    icon: React.ReactNode;
    isCollapsed: boolean;
}> = ({ to, label, icon, isCollapsed }) => {
    const pathname = usePathname();
    // Active if exact match or if it's a sub-route (e.g. /dashboard vs /dashboard/applications)
    // For root /dashboard, exact match is needed to avoid highlighting on sub-pages if desired, 
    // BUT usually dashboard home is overview.
    // Let's do simple inclusion check or exact check for root.
    const isActive = to === '/dashboard' ? pathname === '/dashboard' : pathname.startsWith(to);

    return (
        <Link
            href={to}
            className={`
          flex items-center gap-4 py-2 px-3 transition-all duration-500 group relative
          ${isActive ? 'text-[#3b3b3b] bg-[#3b3b3b]/5' : 'text-[#3b3b3b]/40 hover:text-[#3b3b3b]/70 hover:bg-[#3b3b3b]/5'}
        `}
        >
            <span className={`shrink-0 transition-transform duration-500 group-hover:scale-110 ${isActive ? 'opacity-100' : 'opacity-60 group-hover:opacity-100'}`}>
                {icon}
            </span>
            {!isCollapsed && (
                <motion.span
                    initial={{ opacity: 0, x: -5 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="text-[11px] font-bold tracking-widest uppercase truncate"
                >
                    {label}
                </motion.span>
            )}
            {isActive && !isCollapsed && (
                <motion.div
                    layoutId="active-nav-indicator"
                    className="ml-auto"
                    transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                >
                    <div className="w-1 h-1 bg-[#3b3b3b] rounded-full" />
                </motion.div>
            )}
            {isCollapsed && isActive && (
                <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-[#3b3b3b]" />
            )}
        </Link>
    );
};

export function SophisticatedSidebar({ onClose }: { onClose?: () => void }) {
    const { isCollapsed, toggle } = useSidebar();
    const { user } = useAuth();
    const userName = user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User';

    return (
        <motion.nav
            animate={{ width: isCollapsed ? 72 : 280 }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            className="fixed left-0 top-0 h-full border-r border-[#3b3b3b]/10 flex flex-col bg-[#f0eff2] z-50 overflow-hidden"
        >
            {/* Header */}
            <div className="p-6 flex items-center justify-between border-b border-[#3b3b3b]/5 h-20 shrink-0">
                <Link href="/dashboard" className="flex items-center gap-3 overflow-hidden">
                    <div className="shrink-0 w-8 h-8 border border-[#3b3b3b] flex items-center justify-center bg-white shadow-sm">
                        <LayoutGrid className="w-4 h-4 text-[#3b3b3b]" />
                    </div>
                    {!isCollapsed && (
                        <motion.h1
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-sm font-bold tracking-tighter text-[#3b3b3b] uppercase whitespace-nowrap"
                        >
                            JobFlow <span className="font-serif-italic lowercase">Pro</span>
                        </motion.h1>
                    )}
                </Link>
                {!isCollapsed && (
                    <button
                        onClick={() => { toggle(); if (onClose) onClose(); }}
                        className="text-[#3b3b3b]/30 hover:text-[#3b3b3b] transition-colors p-1"
                    >
                        <PanelLeft className="w-4 h-4" />
                    </button>
                )}
            </div>

            {/* Main Content */}
            <div className="flex-1 px-3 py-6 space-y-8 overflow-y-auto overflow-x-hidden">
                <div>
                    {!isCollapsed && (
                        <p className="px-4 mb-4 text-[9px] font-bold tracking-[0.3em] uppercase text-[#3b3b3b]/30">Platform</p>
                    )}
                    <div className="space-y-1">
                        <NavItem to="/dashboard" label="Dashboard" icon={<LayoutGrid className="w-4 h-4" />} isCollapsed={isCollapsed} />
                        <NavItem to="/dashboard/resume-evaluation" label="Resume Evaluator" icon={<FileText className="w-4 h-4" />} isCollapsed={isCollapsed} />
                        <NavItem to="/dashboard/jobs" label="Job Search" icon={<Search className="w-4 h-4" />} isCollapsed={isCollapsed} />
                        <NavItem to="/dashboard/applications" label="Applications" icon={<Briefcase className="w-4 h-4" />} isCollapsed={isCollapsed} />
                        <NavItem to="/dashboard/referrals" label="Referrals" icon={<Users className="w-4 h-4" />} isCollapsed={isCollapsed} />
                    </div>
                </div>

                <div>
                    {!isCollapsed && (
                        <p className="px-4 mb-4 text-[9px] font-bold tracking-[0.3em] uppercase text-[#3b3b3b]/30">Account</p>
                    )}
                    <div className="space-y-1">
                        <NavItem to="/dashboard/profile" label="Profile Settings" icon={<Settings className="w-4 h-4" />} isCollapsed={isCollapsed} />
                        <NavItem to="/logout" label="Sign Out" icon={<LogOut className="w-4 h-4" />} isCollapsed={isCollapsed} />
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-[#3b3b3b]/10 bg-white/30 shrink-0">
                <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'}`}>
                    <div className="w-10 h-10 border border-[#3b3b3b]/10 flex items-center justify-center bg-white text-[12px] font-bold shrink-0">
                        {userName.charAt(0).toUpperCase()}
                    </div>
                    {!isCollapsed && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex-1 overflow-hidden"
                        >
                            <p className="text-[10px] font-bold uppercase tracking-tighter truncate text-[#3b3b3b]">{userName}</p>
                            <p className="text-[9px] text-[#3b3b3b]/40 italic truncate">Professional Account</p>
                        </motion.div>
                    )}
                    {!isCollapsed && (
                        <button onClick={toggle} className="text-[#3b3b3b]/20 hover:text-[#3b3b3b] transition-colors">
                            <ChevronDown className="w-3 h-3" />
                        </button>
                    )}
                </div>
                {isCollapsed && (
                    <button
                        onClick={toggle}
                        className="mt-4 w-full flex justify-center text-[#3b3b3b]/20 hover:text-[#3b3b3b] transition-colors"
                    >
                        <PanelLeft className="w-4 h-4" />
                    </button>
                )}
            </div>
        </motion.nav>
    );
}
