import { Metadata } from "next"
import { DashboardProvider } from "../contexts/dashboard-context"

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
        <DashboardProvider>
            {children}
        </DashboardProvider>
    )
} 