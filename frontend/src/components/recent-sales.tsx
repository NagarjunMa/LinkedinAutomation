"use client"

import { format } from "date-fns"
import {
    Avatar,
    AvatarFallback,
    AvatarImage,
} from "@/components/ui/avatar"
import { Skeleton } from "@/components/ui/skeleton"
import { useDashboard } from "@/app/contexts/dashboard-context"

function getCompanyInitials(company: string): string {
    return company
        .split(' ')
        .map(word => word[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
}

function ApplicationSkeleton() {
    return (
        <div className="flex items-center space-x-4">
            <Skeleton className="h-9 w-9 rounded-full" />
            <div className="space-y-2">
                <Skeleton className="h-4 w-[200px]" />
                <Skeleton className="h-4 w-[150px]" />
            </div>
            <Skeleton className="h-4 w-[100px] ml-auto" />
        </div>
    )
}

export function RecentSales() {
    const { recentApplications, loading } = useDashboard()

    if (loading) {
        return (
            <div className="space-y-8">
                {[...Array(5)].map((_, i) => (
                    <ApplicationSkeleton key={i} />
                ))}
            </div>
        )
    }

    return (
        <div className="space-y-8">
            {recentApplications.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                    No recent applications found
                </p>
            ) : (
                recentApplications.map((application) => (
                    <div key={application.id} className="flex items-center">
                        <Avatar className="h-9 w-9">
                            {application.companyLogo ? (
                                <AvatarImage src={application.companyLogo} alt={application.company} />
                            ) : null}
                            <AvatarFallback>{getCompanyInitials(application.company)}</AvatarFallback>
                        </Avatar>
                        <div className="ml-4 space-y-1">
                            <p className="text-sm font-medium leading-none">{application.title}</p>
                            <p className="text-sm text-muted-foreground">
                                {application.company}
                            </p>
                            <p className="text-xs text-muted-foreground">
                                {format(new Date(application.extracted_date), 'MMM dd, yyyy')}
                            </p>
                        </div>
                        <div className="ml-auto font-medium">{application.status || 'Applied'}</div>
                    </div>
                ))
            )}
        </div>
    )
} 