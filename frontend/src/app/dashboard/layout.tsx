"use client"

import { usePathname } from "next/navigation"
import { DashboardProvider } from "../contexts/dashboard-context"
import { ActivityProvider } from "@/contexts/activity-context"
import { ProtectedRoute } from "@/components/protected-route"
import { SophisticatedLayout } from "@/components/sophisticated-layout"
import ErrorBoundary, { ComponentErrorFallback } from "@/components/error-boundary"

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const pathname = usePathname()

    return (
        <ProtectedRoute>
            <ErrorBoundary fallback={ComponentErrorFallback}>
                <DashboardProvider>
                    <ActivityProvider>
                        <ErrorBoundary fallback={ComponentErrorFallback}>
                            <SophisticatedLayout showHeader={true}>
                                <ErrorBoundary
                                    fallback={ComponentErrorFallback}
                                    resetKeys={[pathname]}
                                >
                                    {children}
                                </ErrorBoundary>
                            </SophisticatedLayout>
                        </ErrorBoundary>
                    </ActivityProvider>
                </DashboardProvider>
            </ErrorBoundary>
        </ProtectedRoute>
    )
} 