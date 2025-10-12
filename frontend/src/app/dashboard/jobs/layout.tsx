import { Metadata } from "next"

export const metadata: Metadata = {
    title: "Jobs - Dashboard",
    description: "Job Search and Discovery",
}

export default function JobsLayout({
    children,
}: {
    children: React.ReactNode
}) {
    // This layout only provides metadata
    // The actual layout is handled by the parent dashboard layout
    return <>{children}</>
}