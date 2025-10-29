"use client"

import { useState } from "react"
import { SophisticatedSidebar } from "./sophisticated-sidebar"
import { SophisticatedHeader } from "./sophisticated-header"

interface SophisticatedLayoutProps {
    children: React.ReactNode
    notificationCount?: number
    showHeader?: boolean
}

export function SophisticatedLayout({
    children,
    notificationCount = 2,
    showHeader = true
}: SophisticatedLayoutProps) {
    const [sidebarOpen, setSidebarOpen] = useState(false)

    return (
        <div className="h-screen flex bg-primary-950 overflow-hidden">
            {/* Desktop Sidebar */}
            <div className="hidden lg:flex lg:flex-shrink-0">
                <SophisticatedSidebar />
            </div>

            {/* Mobile sidebar overlay */}
            {sidebarOpen && (
                <div className="fixed inset-0 z-50 lg:hidden">
                    <div
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300"
                        onClick={() => setSidebarOpen(false)}
                        aria-hidden="true"
                    />
                    <div className="relative flex-1 flex flex-col max-w-xs w-full bg-primary-900 shadow-2xl animate-in slide-in-from-left duration-300">
                        <SophisticatedSidebar onClose={() => setSidebarOpen(false)} />
                    </div>
                </div>
            )}

            {/* Main content */}
            <div className="flex-1 flex flex-col overflow-hidden min-w-0">
                {/* Header */}
                {showHeader && (
                    <SophisticatedHeader
                        notificationCount={notificationCount}
                        onMenuClick={() => setSidebarOpen(true)}
                    />
                )}

                {/* Page content */}
                <main className="flex-1 overflow-y-auto bg-primary-950">
                    <div className="min-h-full">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    )
}
