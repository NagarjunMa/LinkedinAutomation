"use client"

import { useState } from "react"
import { SophisticatedSidebar } from "./sophisticated-sidebar"
import { SophisticatedHeader } from "./sophisticated-header"

interface SophisticatedLayoutProps {
    children: React.ReactNode
    notificationCount?: number
}

export function SophisticatedLayout({
    children,
    notificationCount = 2
}: SophisticatedLayoutProps) {
    const [sidebarOpen, setSidebarOpen] = useState(false)

    return (
        <div className="h-screen flex bg-primary-950 overflow-hidden">
            {/* Sidebar */}
            <div className="hidden md:flex md:flex-shrink-0">
                <SophisticatedSidebar />
            </div>

            {/* Mobile sidebar overlay */}
            {sidebarOpen && (
                <div className="fixed inset-0 z-40 md:hidden">
                    <div className="fixed inset-0 bg-primary-900/75" onClick={() => setSidebarOpen(false)} />
                    <div className="relative flex-1 flex flex-col max-w-xs w-full bg-primary-900">
                        <SophisticatedSidebar />
                    </div>
                </div>
            )}

            {/* Main content */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Header */}
                <SophisticatedHeader
                    notificationCount={notificationCount}
                />

                {/* Page content */}
                <main className="flex-1 overflow-y-auto bg-primary-950">
                    <div className="p-6 min-h-full">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    )
}
