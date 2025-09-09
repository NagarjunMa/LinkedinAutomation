import { Metadata } from "next"
import { DashboardProvider } from "../contexts/dashboard-context"
import { ProtectedRoute } from "@/components/protected-route"

export const metadata: Metadata = {
    title: "Dashboard",
    description: "LinkedIn Job Search Dashboard",
}

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <ProtectedRoute>
            <DashboardProvider>
                {children}
            </DashboardProvider>
        </ProtectedRoute>
    )
} 