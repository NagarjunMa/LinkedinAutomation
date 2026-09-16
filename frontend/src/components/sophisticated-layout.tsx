"use client";

import { useState } from "react"
import { SophisticatedSidebar, SidebarProvider, useSidebar } from "./sophisticated-sidebar"
import { SophisticatedHeader } from "./sophisticated-header"
import { AnimatePresence } from 'framer-motion';

interface SophisticatedLayoutProps {
    children: React.ReactNode
    notificationCount?: number
    showHeader?: boolean
}

// Inner component to consume the context
const LayoutContent = ({ children, notificationCount, showHeader }: SophisticatedLayoutProps) => {
    const { isCollapsed } = useSidebar();
    const [sidebarOpen, setSidebarOpen] = useState(false);

    return (
        <div className="min-h-screen bg-app-bg text-app-text transition-colors duration-300">
            {/* Sidebar (Desktop & Mobile) */}
            <div className="hidden lg:block">
                <SophisticatedSidebar />
            </div>

            {/* Mobile Sidebar Overlay */}
            {sidebarOpen && (
                <div className="fixed inset-0 z-50 lg:hidden">
                    <div
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300"
                        onClick={() => setSidebarOpen(false)}
                        aria-hidden="true"
                    />
                    <div className="relative flex-1 flex flex-col max-w-xs w-full bg-app-bg shadow-2xl animate-in slide-in-from-left duration-300 h-full">
                        <SophisticatedSidebar onClose={() => setSidebarOpen(false)} />
                    </div>
                </div>
            )}

            {/* Main Content Area */}
            {/* CSS keeps sidebar spacing desktop-only, including before hydration. */}
            <main
                className={`ml-0 min-w-0 flex-1 min-h-screen flex flex-col transition-[margin-left] [transition-duration:600ms] [transition-timing-function:cubic-bezier(0.22,1,0.36,1)] motion-reduce:transition-none ${isCollapsed ? 'lg:ml-20' : 'lg:ml-[280px]'}`}
            >
                {/* Header - if used, check if it needs integration with new design. 
                    The new dashboard has its own Header, so we might hide this global header on dashboard page 
                    or adapt it. The current prop showHeader controls this. 
                */}
                {showHeader && (
                    <SophisticatedHeader
                        notificationCount={notificationCount}
                        onMenuClick={() => setSidebarOpen(true)}
                    />
                )}

                <div className="p-8 md:p-12 overflow-y-auto w-full">
                    <AnimatePresence mode="wait">
                        {children}
                    </AnimatePresence>
                </div>
            </main>
        </div>
    );
};

export function SophisticatedLayout(props: SophisticatedLayoutProps) {
    return (
        <SidebarProvider>
            <LayoutContent {...props} />
        </SidebarProvider>
    )
}
