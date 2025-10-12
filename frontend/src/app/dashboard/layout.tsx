"use client"

import { usePathname } from "next/navigation"
import { DashboardProvider } from "../contexts/dashboard-context"
import { ProtectedRoute } from "@/components/protected-route"
import { SophisticatedLayout } from "@/components/sophisticated-layout"

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const pathname = usePathname()
    const isJobsPage = pathname === '/dashboard/jobs'

    return (
        <ProtectedRoute>
            <DashboardProvider>
                <SophisticatedLayout showHeader={!isJobsPage}>
                    {children}
                </SophisticatedLayout>
            </DashboardProvider>
        </ProtectedRoute>
    )
} 