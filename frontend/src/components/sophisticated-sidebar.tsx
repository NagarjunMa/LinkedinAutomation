"use client";

import React, { useState, createContext, useContext } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    Search,
    Briefcase,
    PanelLeft,
    LayoutGrid,
    Settings,
    LogOut,
    ChevronDown
} from 'lucide-react';
import { motion } from 'framer-motion';
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
    const isActive = to === '/dashboard' ? pathname === '/dashboard' : pathname.startsWith(to);

    return (
        <Link
            href={to}
            className={`
          flex items-center gap-4 py-3 px-4 transition-all duration-500 group relative rounded-md mx-2
          ${isActive ? 'text-app-text bg-app-text/5 font-extrabold shadow-sm' : 'text-app-text opacity-60 hover:opacity-100 hover:bg-app-text/5 font-bold'}
        `}
        >
            <span className={`shrink-0 transition-transform duration-500 group-hover:scale-110 ${isActive ? 'opacity-100' : 'opacity-70 group-hover:opacity-100'}`}>
                {icon}
            </span>
            {!isCollapsed && (
                <motion.span
                    initial={{ opacity: 0, x: -5 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="text-xs tracking-wider uppercase truncate"
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
                    <div className="w-1.5 h-1.5 bg-app-accent rounded-full" />
                </motion.div>
            )}
            {isCollapsed && isActive && (
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-app-accent rounded-r-full" />
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
            animate={{ width: isCollapsed ? 80 : 280 }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            className="fixed left-0 top-0 h-full border-r border-app-text/5 flex flex-col bg-app-bg z-50 overflow-hidden shadow-2xl shadow-black/5"
        >
            {/* Header */}
            <div className="p-6 flex items-center justify-between border-b border-app-text border-opacity-5 h-24 shrink-0 bg-app-bg bg-opacity-50 backdrop-blur-sm">
                <Link href="/dashboard" className="flex items-center gap-4 overflow-hidden">
                    <div className="shrink-0 w-10 h-10 border border-app-text border-opacity-20 flex items-center justify-center bg-app-card shadow-sm rounded-sm">
                        <LayoutGrid className="w-5 h-5 text-app-text" />
                    </div>
                    {!isCollapsed && (
                        <motion.h1
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-base font-extrabold tracking-tight text-app-text uppercase whitespace-nowrap"
                        >
                            PRISM <span className="font-serif italic lowercase font-medium text-app-accent">pro</span>
                        </motion.h1>
                    )}
                </Link>
                {!isCollapsed && (
                    <button
                        onClick={() => { toggle(); if (onClose) onClose(); }}
                        className="text-app-text opacity-40 hover:opacity-100 transition-colors p-2 hover:bg-app-text hover:bg-opacity-5 rounded-full"
                    >
                        <PanelLeft className="w-5 h-5" />
                    </button>
                )}
            </div>

            {/* Main Content */}
            <div className="flex-1 px-2 py-8 space-y-10 overflow-y-auto overflow-x-hidden custom-scrollbar">
                <div>
                    {!isCollapsed && (
                        <p className="px-6 mb-4 text-[10px] font-extrabold tracking-[0.2em] uppercase text-app-text opacity-40">Platform</p>
                    )}
                    <div className="space-y-1">
                        <NavItem to="/dashboard" label="Dashboard" icon={<LayoutGrid className="w-5 h-5" />} isCollapsed={isCollapsed} />
                        <NavItem to="/dashboard/jobs" label="Job Search" icon={<Search className="w-5 h-5" />} isCollapsed={isCollapsed} />
                        <NavItem to="/dashboard/applications" label="Applications" icon={<Briefcase className="w-5 h-5" />} isCollapsed={isCollapsed} />
                    </div>
                </div>

                <div>
                    {!isCollapsed && (
                        <p className="px-6 mb-4 text-[10px] font-extrabold tracking-[0.2em] uppercase text-app-text opacity-40">Account</p>
                    )}
                    <div className="space-y-1">
                        <NavItem to="/dashboard/profile" label="Profile Settings" icon={<Settings className="w-5 h-5" />} isCollapsed={isCollapsed} />
                        <NavItem to="/logout" label="Sign Out" icon={<LogOut className="w-5 h-5" />} isCollapsed={isCollapsed} />
                    </div>
                </div>
            </div>
            {/* Footer */}
            <div className="p-5 border-t border-app-text border-opacity-5 bg-app-card bg-opacity-30 shrink-0 backdrop-blur-md">
                <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-4'}`}>
                    <div className="w-12 h-12 border border-app-text border-opacity-10 flex items-center justify-center bg-app-bg text-sm font-bold shrink-0 rounded-full shadow-sm text-app-text">
                        {userName.charAt(0).toUpperCase()}
                    </div>
                    {!isCollapsed && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex-1 overflow-hidden"
                        >
                            <p className="text-xs font-extrabold uppercase tracking-tight truncate text-app-text">{userName}</p>
                            <p className="text-[10px] text-app-text opacity-50 italic truncate font-medium">Professional Account</p>
                        </motion.div>
                    )}
                    {!isCollapsed && (
                        <button onClick={toggle} className="text-app-text opacity-30 hover:opacity-100 transition-opacity">
                            <ChevronDown className="w-4 h-4" />
                        </button>
                    )}
                </div>
                {isCollapsed && (
                    <button
                        onClick={toggle}
                        className="mt-6 w-full flex justify-center text-app-text opacity-30 hover:opacity-100 transition-opacity"
                    >
                        <PanelLeft className="w-5 h-5" />
                    </button>
                )}
            </div>
        </motion.nav>
    );
}
