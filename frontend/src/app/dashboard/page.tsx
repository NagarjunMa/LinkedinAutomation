"use client"

import { useState, useEffect, useMemo } from "react"
import { useSearchParams } from "next/navigation"
import { useDashboard } from "@/app/contexts/dashboard-context"
import { useAuth } from "@/contexts/auth-context"
import {
    OverviewCard,
    QuickActionCard
} from "@/components/sophisticated-cards"
import { EmailStatsCard } from "@/components/email-stats-card"
import { ReferralAnalyticsCard } from "@/components/referral-analytics-card"
// Activity calendar is now integrated into OverviewCard
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
    BarChart3,
    Briefcase,
    TrendingUp,
    TrendingDown,
    Clock,
    CheckCircle,
    Link,
    Upload
} from "lucide-react"
import { ProfileSetupModal } from "@/components/profile-setup-modal"
import { ProfileCompletionBanner } from "@/components/profile-completion-banner"
import { cn } from "@/lib/utils"
import {
    StaggerContainer,
    StaggerItem
} from "@/components/animated-wrapper"
import { Area, AreaChart, CartesianGrid, XAxis } from "recharts"
import {
    ChartConfig,
    ChartContainer,
    ChartTooltip,
} from "@/components/ui/chart"

interface SuccessRateCardProps {
    rate: number;
    change: number;
}

interface TodayActivityCardProps {
    applications: number;
    profiles: number;
    messages: number;
}

function SuccessRateCard({ rate, change }: SuccessRateCardProps) {
    return (
        <Card className="premium-card hover:scale-105 transition-all duration-300 group">
            <CardHeader className="pb-2 px-4 pt-4">
                <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-400" />
                    <CardTitle className="text-cream-50 text-sm group-hover:text-accent-400 transition-colors">
                        Success Rate
                    </CardTitle>
                </div>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col justify-center items-center px-4 pb-4">
                <div className="text-3xl font-bold text-green-400 mb-2">{rate}%</div>
                <div className="text-xs text-cream-300 text-center">Response rate</div>
                <div className="text-xs text-cream-400 mt-1">↑ {change}% vs last month</div>
            </CardContent>
        </Card>
    );
}

function TodayActivityCard({ applications, profiles, messages }: TodayActivityCardProps) {
    return (
        <Card className="premium-card hover:scale-105 transition-all duration-300 group">
            <CardHeader className="pb-2 px-4 pt-4">
                <div className="flex items-center space-x-2">
                    <Clock className="h-4 w-4 text-blue-400" />
                    <CardTitle className="text-cream-50 text-sm group-hover:text-accent-400 transition-colors">
                        Today&rsquo;s Activity
                    </CardTitle>
                </div>
            </CardHeader>
            <CardContent className="px-4 pb-4 space-y-2">
                <div className="flex justify-between items-center">
                    <span className="text-xs text-cream-300">Applications</span>
                    <span className="text-cream-50 font-semibold text-sm">{applications}</span>
                </div>
                <div className="flex justify-between items-center">
                    <span className="text-xs text-cream-300">Profiles viewed</span>
                    <span className="text-cream-50 font-semibold text-sm">{profiles}</span>
                </div>
                <div className="flex justify-between items-center">
                    <span className="text-xs text-cream-300">Messages sent</span>
                    <span className="text-cream-50 font-semibold text-sm">{messages}</span>
                </div>
            </CardContent>
        </Card>
    );
}

// Chart configuration for Application Progress
const chartConfig = {
    applications: {
        label: "Applications",
        color: "rgb(249, 115, 22)", // Orange color to match theme
    },
} satisfies ChartConfig

// ProgressLineGraph component using Recharts
interface ProgressLineGraphProps {
    progressData?: { day: number; applications: number }[]
}

function ProgressLineGraph({ progressData }: ProgressLineGraphProps) {
    // Generate sample data if none provided (last 7 days)
    const defaultData = Array.from({ length: 7 }, (_, i) => ({
        day: i + 1,
        date: new Date(Date.now() - (6 - i) * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        applications: Math.floor(Math.random() * 50) + 10 // Random between 10-60
    }))

    const data = progressData?.map((item, i) => ({
        ...item,
        date: new Date(Date.now() - (progressData.length - 1 - i) * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    })) || defaultData

    const maxApplications = Math.max(...data.map(d => d.applications))

    return (
        <div className="w-full h-full">
            {/* Progress indicator */}
            <div className="flex items-center justify-between mb-4">
                <div className="text-sm text-cream-400">Last {data.length} days</div>
                <div className="text-sm text-cream-300">
                    Peak: {maxApplications} applications
                </div>
            </div>

            {/* Recharts Area Chart */}
            <ChartContainer config={chartConfig} className="h-[200px] w-full">
                <AreaChart data={data}>
                    <defs>
                        <linearGradient id="fillApplications" x1="0" y1="0" x2="0" y2="1">
                            <stop
                                offset="5%"
                                stopColor="rgb(249, 115, 22)"
                                stopOpacity={0.8}
                            />
                            <stop
                                offset="95%"
                                stopColor="rgb(249, 115, 22)"
                                stopOpacity={0.1}
                            />
                        </linearGradient>
                    </defs>
                    <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.1)" />
                    <XAxis
                        dataKey="date"
                        tickLine={false}
                        axisLine={false}
                        tickMargin={8}
                        tick={{ fill: "rgb(203, 213, 225)", fontSize: 12 }}
                    />
                    <ChartTooltip
                        className="bg-primary-800 border border-primary-600 text-cream-50"
                    />
                    <Area
                        dataKey="applications"
                        type="natural"
                        fill="url(#fillApplications)"
                        stroke="rgb(249, 115, 22)"
                        strokeWidth={2}
                    />
                </AreaChart>
            </ChartContainer>
        </div>
    )
}

function ApplicationTrendChart() {
    const [timeRange, setTimeRange] = useState('7days');

    // Generate sample data based on time range - same format as ProgressCard
    const progressData = useMemo(() => {
        const days = timeRange === '7days' ? 7 : timeRange === '10days' ? 10 : 30;
        return Array.from({ length: days }, (_, i) => ({
            day: i + 1,
            applications: Math.floor(Math.random() * 80) + 20 // Random between 20-100 applications per day
        }));
    }, [timeRange]);

    // Calculate trend for header
    const firstHalf = progressData.slice(0, Math.ceil(progressData.length / 2));
    const secondHalf = progressData.slice(Math.ceil(progressData.length / 2));
    const firstAvg = firstHalf.reduce((sum, d) => sum + d.applications, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((sum, d) => sum + d.applications, 0) / secondHalf.length;
    const isIncreasing = secondAvg > firstAvg;

    return (
        <Card className="premium-card">
            <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <CardTitle className="text-cream-50 text-lg">Application Progress</CardTitle>
                        <div className={cn(
                            "flex items-center gap-1 text-xs font-medium",
                            isIncreasing ? "text-green-400" : "text-red-400"
                        )}>
                            {isIncreasing ? (
                                <TrendingUp className="h-4 w-4" />
                            ) : (
                                <TrendingDown className="h-4 w-4" />
                            )}
                            {isIncreasing ? "Trending up" : "Trending down"}
                        </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {(['7days', '10days', '30days'] as const).map((range) => (
                            <button
                                key={range}
                                onClick={() => setTimeRange(range)}
                                className={`px-2 sm:px-3 py-1 rounded-md text-xs sm:text-sm transition-colors ${timeRange === range
                                    ? 'bg-gradient-warm text-white'
                                    : 'text-cream-300 hover:text-cream-100 hover:bg-primary-700'
                                    }`}
                            >
                                {range === '7days' ? '7 Days' : range === '10days' ? '10 Days' : '30 Days'}
                            </button>
                        ))}
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <div className="h-48 sm:h-64 w-full">
                    <ProgressLineGraph progressData={progressData} />
                </div>
            </CardContent>
        </Card>
    );
}

function RecentApplicationsTable() {
    const { recentApplications } = useDashboard();

    // Show empty state or loading if no data
    if (!recentApplications || recentApplications.length === 0) {
        return (
            <Card className="bg-gradient-to-br from-primary-900/50 to-primary-800/30 border-primary-700/50">
                <CardHeader>
                    <CardTitle className="text-lg font-semibold text-cream-50">
                        Recent Applications
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-center py-8">
                        <Briefcase className="mx-auto h-12 w-12 text-primary-400 mb-4" />
                        <h3 className="text-lg font-medium text-cream-200 mb-2">No Applications Yet</h3>
                        <p className="text-cream-400 mb-4">Start applying to jobs to see them here</p>
                        <Button variant="outline" size="sm">
                            Extract Job URL
                        </Button>
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Map recentApplications to the format expected by the component
    const applications = recentApplications.map(app => ({
        id: app.id,
        jobTitle: app.title || 'Unknown Position',
        companyName: app.company || 'Unknown Company',
        location: 'Remote',
        jobType: 'Full-time' as const,
        skillsPreferred: [],
        salary: 'TBD',
        status: app.status || 'Applied',
        appliedDate: app.appliedAt || 'Recently',
        method: app.extracted_date ? 'AI Extraction' : 'Manual'
    }));

    const getStatusBadge = (status: string) => {
        const styles = {
            'Applied': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
            'Waiting': 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
            'Success': 'bg-green-500/20 text-green-400 border-green-500/30',
            'Due': 'bg-red-500/20 text-red-400 border-red-500/30',
            'Disabled': 'bg-gray-500/20 text-gray-400 border-gray-500/30'
        };

        return (
            <span className={`px-2 py-1 text-xs font-medium rounded border ${styles[status as keyof typeof styles]}`}>
                {status}
            </span>
        );
    };

    return (
        <Card className="premium-card">
            <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-cream-50 text-lg">Recent Applications</CardTitle>
                    <Button variant="ghost" size="sm" className="text-accent-500 hover:text-accent-400">
                        Filter
                    </Button>
                </div>
            </CardHeader>
            <CardContent className="p-0">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-primary-700 border-b border-primary-600">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-cream-200 uppercase tracking-wider">Type</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-cream-200 uppercase tracking-wider">Amount</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-cream-200 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-cream-200 uppercase tracking-wider">Method</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-primary-600">
                            {applications.map((app) => (
                                <tr key={app.id} className="hover:bg-primary-700 cursor-pointer transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-cream-50">{app.jobTitle}</div>
                                        <div className="text-xs text-cream-300">{app.companyName}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-cream-50">{app.salary}</div>
                                        <div className="text-xs text-cream-300">{app.location}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        {getStatusBadge(app.status)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm text-cream-200">{app.method}</div>
                                        <div className="text-xs text-cream-400">{app.appliedDate}</div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <div className="px-6 py-4 border-t border-primary-600 flex items-center justify-between">
                    <div className="text-sm text-cream-300">
                        Showing 1-3 of 15 applications
                    </div>
                    <div className="flex gap-2">
                        <Button variant="ghost" size="sm" className="text-cream-300 hover:text-cream-100">
                            Previous
                        </Button>
                        <Button variant="ghost" size="sm" className="text-cream-300 hover:text-cream-100">
                            Next
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

// Overview data will be taken from dashboard context

// Activity data will be taken from backend when available

// Progress data will be generated from real application data

// Recent jobs will be taken from dashboard context

// Application extraction data will be fetched from the backend

const quickActions = [
    {
        label: "Job Intelligence",
        description: "Extract job details from any URL",
        shortcut: "E",
        icon: Link,
        onClick: () => window.location.href = "/dashboard/applications"
    },
    {
        label: "Resume Review",
        description: "AI-powered resume analysis",
        shortcut: "R",
        icon: Upload,
        onClick: () => window.location.href = "/dashboard/resume-evaluation"
    },
    {
        label: "Performance Dashboard",
        description: "Track your progress",
        shortcut: "A",
        icon: BarChart3,
        onClick: () => window.location.href = "/dashboard/analytics"
    }
]

export default function DashboardPage() {
    const { user } = useAuth()
    const { stats, error, refreshData } = useDashboard()
    const searchParams = useSearchParams()
    const [showProfileSetup, setShowProfileSetup] = useState(false)
    const [profileSetupChecked, setProfileSetupChecked] = useState(false)

    // Check for profile setup requirement
    useEffect(() => {
        if (!user || profileSetupChecked) return

        const setupParam = searchParams.get('setup')

        if (setupParam === 'true') {
            // User needs profile setup
            setShowProfileSetup(true)
            setProfileSetupChecked(true)
        } else if (setupParam === 'check') {
            // Check if user has a profile in backend
            const checkProfile = async () => {
                try {
                    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/user-profiles/${user.id}`)
                    if (response.status === 404) {
                        setShowProfileSetup(true)
                    }
                } catch (error) {
                    console.error('Error checking profile:', error)
                    // On error, assume profile setup is needed
                    setShowProfileSetup(true)
                } finally {
                    setProfileSetupChecked(true)
                }
            }
            checkProfile()
        } else {
            setProfileSetupChecked(true)
        }
    }, [user, searchParams, profileSetupChecked])

    if (error) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-primary-950">
                <div className="text-center">
                    <p className="text-red-400 mb-4">Error: {error}</p>
                    <Button onClick={refreshData} className="bg-orange-500 hover:bg-orange-600">
                        Retry
                    </Button>
                </div>
            </div>
        )
    }

    const handleProfileSetupComplete = async () => {
        setShowProfileSetup(false)
        // Refresh dashboard data instead of full page reload
        await refreshData()
        // Also trigger a profile data refresh event to update profile completion banner
        window.dispatchEvent(new CustomEvent('profileUpdated'))
    }

    return (
        <div className="min-h-screen bg-primary-950">
            {/* Profile Setup Modal */}
            <ProfileSetupModal
                isOpen={showProfileSetup}
                onClose={() => setShowProfileSetup(false)}
                onComplete={handleProfileSetupComplete}
            />

            {/* Main Dashboard Container following handwritten design */}
            <div className="w-full px-4 sm:px-6 py-4 sm:py-6">
                <StaggerContainer>
                    <div className="space-y-4 sm:space-y-6">
                        {/* Profile Completion Banner */}
                        <ProfileCompletionBanner />

                        {/* Top Section - 4 cards as per handwritten design */}
                        <StaggerItem>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
                                {/* Overview Calendar Card - moved to first position */}
                                <OverviewCard
                                    title="Overview Calendar"
                                    period={`${new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}`}
                                    stats={stats ? {
                                        total: stats.totalJobs || 0,
                                        applied: stats.appliedJobs || 0,
                                        interviews: stats.interviews || 0
                                    } : { total: 0, applied: 0, interviews: 0 }}
                                    activityData={[]} // Real activity data will be implemented later
                                    userId={user?.id}
                                />

                                {/* Referral Analytics Card */}
                                <ReferralAnalyticsCard
                                    title="📧 Referral Assistant"
                                    showActions={true}
                                />

                                {/* Quick Action Card */}
                                <QuickActionCard
                                    title="Quick Action"
                                    actions={quickActions}
                                />

                                {/* Email Processing Card */}
                                <EmailStatsCard
                                    title="Email Processing"
                                    emailsSent={24}
                                    emailsProcessed={18}
                                    change="+15%"
                                    changeType="increase"
                                />
                            </div>
                        </StaggerItem>

                        {/* Line Graph Section - Full width as per sketch */}
                        <StaggerItem>
                            <ApplicationTrendChart />
                        </StaggerItem>

                        {/* Bottom Section - Success Rate and Today's Activity as per sketch */}
                        <StaggerItem>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
                                {/* Success Rate Card */}
                                <SuccessRateCard
                                    rate={stats?.successRate || 0}
                                    change={stats?.successRateChange || 0}
                                />

                                {/* Today's Activity Card */}
                                <TodayActivityCard
                                    applications={stats?.todayApplications || 0}
                                    profiles={stats?.todayProfiles || 0}
                                    messages={stats?.todayMessages || 0}
                                />
                            </div>
                        </StaggerItem>

                        {/* Recent applications */}
                        <StaggerItem>
                            <RecentApplicationsTable />
                        </StaggerItem>


                    </div>
                </StaggerContainer>
            </div>
        </div>
    )
} 