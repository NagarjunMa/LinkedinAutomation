"use client"

import { usePathname } from "next/navigation"
import { DashboardProvider } from "../contexts/dashboard-context"
import { ProtectedRoute } from "@/components/protected-route"
import { SophisticatedLayout } from "@/components/sophisticated-layout"
import ErrorBoundary, { ComponentErrorFallback } from "@/components/error-boundary"
import { AuthProvider } from "@/contexts/auth-context"

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const pathname = usePathname()

    return (
        <AuthProvider>
            <ProtectedRoute>
                <ErrorBoundary fallback={ComponentErrorFallback}>
                    <DashboardProvider>
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
                    </DashboardProvider>
                </ErrorBoundary>
            </ProtectedRoute>
        </AuthProvider>
    )
}
