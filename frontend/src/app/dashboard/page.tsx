"use client"

import { useState, useEffect, useMemo } from "react"
import { useDashboard } from "@/app/contexts/dashboard-context"
import {
    OverviewCard,
    QuickActionCard,
    RecentJobsCard
} from "@/components/sophisticated-cards"
import { EmailStatsCard } from "@/components/email-stats-card"
// Removed separate calendar - now integrated into OverviewCard
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
    BarChart3,
    Briefcase,
    FileText,
    Mail,
    Search,
    Target,
    TrendingUp,
    TrendingDown,
    Users,
    Zap,
    Clock,
    CheckCircle,
    AlertCircle,
    Star,
    ArrowRight,
    Plus,
    Filter,
    Download,
    Send,
    ArrowUpRight,
    ChevronDown,
    Link,
    Upload
} from "lucide-react"
import { Overview } from "@/components/overview"
import { RecentSales } from "@/components/recent-sales"
import JobURLExtractor from "@/components/job-url-extractor"
import { cn } from "@/lib/utils"
import {
    FadeInUp,
    FadeIn,
    StaggerContainer,
    StaggerItem
} from "@/components/animated-wrapper"
import { Area, AreaChart, CartesianGrid, XAxis } from "recharts"
import {
    ChartConfig,
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
} from "@/components/ui/chart"

// Enhanced component props interfaces
interface SearchProgressCardProps {
    goal: number;
    current: number;
}

interface SuccessRateCardProps {
    rate: number;
    change: number;
}

interface TodayActivityCardProps {
    applications: number;
    profiles: number;
    messages: number;
}

// Compact metric card components
function SearchProgressCard({ goal, current }: SearchProgressCardProps) {
    const percentage = Math.round((current / goal) * 100);

    return (
        <Card className="premium-card hover:scale-105 transition-all duration-300 group">
            <CardHeader className="pb-2 px-4 pt-4">
                <div className="flex items-center space-x-2">
                    <Target className="h-4 w-4 text-accent-500" />
                    <CardTitle className="text-cream-50 text-sm group-hover:text-accent-400 transition-colors">
                        Search Progress
                    </CardTitle>
                </div>
            </CardHeader>
            <CardContent className="px-4 pb-4 space-y-3">
                <div className="flex justify-between text-xs">
                    <span className="text-cream-300">Weekly Goal</span>
                    <span className="text-accent-400 font-semibold">{current}/{goal}</span>
                </div>
                <div className="w-full bg-primary-700 rounded-full h-2">
                    <div
                        className="bg-gradient-warm h-2 rounded-full transition-all duration-500"
                        style={{ width: `${percentage}%` }}
                    />
                </div>
                <div className="text-xs text-cream-400 text-center">{percentage}% completed</div>
            </CardContent>
        </Card>
    );
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
                        Today's Activity
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
                        cursor={false}
                        content={
                            <ChartTooltipContent
                                labelFormatter={(value) => `${value}`}
                                formatter={(value, name) => [
                                    `${value} applications`,
                                    name === "applications" ? "Applications" : name
                                ]}
                                indicator="dot"
                                className="bg-primary-800 border-primary-600 text-cream-50"
                            />
                        }
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
                    <div className="flex gap-2">
                        {(['7days', '10days', '30days'] as const).map((range) => (
                            <button
                                key={range}
                                onClick={() => setTimeRange(range)}
                                className={`px-3 py-1 rounded-md text-sm transition-colors ${
                                    timeRange === range
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
                <div className="h-64 w-full">
                    <ProgressLineGraph progressData={progressData} />
                </div>
            </CardContent>
        </Card>
    );
}

function RecentApplicationsTable() {
    // Sample data for the table
    const applications = [
        {
            id: '1',
            jobTitle: 'Senior Frontend Developer',
            companyName: 'TechCorp Inc.',
            location: 'San Francisco, CA',
            jobType: 'Full-time' as const,
            skillsPreferred: ['React', 'TypeScript', 'Node.js'],
            salary: '$120,000 - $150,000',
            status: 'Waiting' as const,
            appliedDate: '2 days ago',
            method: 'LinkedIn' as const
        },
        {
            id: '2',
            jobTitle: 'Full Stack Engineer',
            companyName: 'StartupXYZ',
            location: 'Remote',
            jobType: 'Full-time' as const,
            skillsPreferred: ['Python', 'Django', 'PostgreSQL'],
            salary: '$100,000 - $130,000',
            status: 'Success' as const,
            appliedDate: '3 days ago',
            method: 'Company Site' as const
        },
        {
            id: '3',
            jobTitle: 'Software Engineer',
            companyName: 'BigTech Co.',
            location: 'Seattle, WA',
            jobType: 'Full-time' as const,
            skillsPreferred: ['Java', 'Spring', 'AWS'],
            salary: '$110,000 - $140,000',
            status: 'Due' as const,
            appliedDate: '5 days ago',
            method: 'Indeed' as const
        }
    ];

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

// Startup Job Boards
const STARTUP_JOB_BOARDS = [
    {
        name: "Otta",
        description: "Find your people - Only relevant roles. Choose the right job, at the right company for you.",
        url: "https://otta.com/",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Career Vault",
        description: "Land a remote job. Live anywhere. Join 50,000+ job seekers discovering remote jobs.",
        url: "https://www.careervault.io/",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Startup Gallery",
        description: "Discover today's top startups - A handpicked gallery of 1,028+ outstanding companies.",
        url: "https://startups.gallery/",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Built In",
        description: "Better Matches. Better Jobs. Explore 106,859+ tech companies with personalized recommendations.",
        url: "https://builtin.com/",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Wellfound",
        description: "Startup jobs and opportunities - Connect with innovative startups in the ecosystem.",
        url: "https://wellfound.com/jobs",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Remotive",
        description: "Remote jobs and companies - The #1 remote work community for tech professionals.",
        url: "https://remotive.com/",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Tech Jobs for Good",
        description: "Tech jobs that make a difference - Find meaningful roles focused on social impact.",
        url: "https://techjobsforgood.com/",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Simplify Jobs",
        description: "Streamlined job application process - Apply to multiple jobs with one click.",
        url: "https://simplify.jobs/",
        category: "startup",
        requiresAuth: false
    }
]

// Tech Stack Job Boards
const TECH_STACK_JOB_BOARDS = [
    {
        name: "TechStackLeads",
        description: "Super fast job search engine. No sign in required.",
        url: "https://techstackleads.com",
        category: "techstack",
        requiresAuth: false
    },
    {
        name: "Theirstack",
        description: "Create an account and search jobs based on your skills.",
        url: "https://app.theirstack.com/home",
        category: "techstack",
        requiresAuth: true
    },
    {
        name: "Stackjobs",
        description: "Sign in and apply for jobs based on your tech stack.",
        url: "https://stackjobs.dev",
        category: "techstack",
        requiresAuth: true
    }
]

// Sample data for sophisticated dashboard
const overviewData = {
    total: 40,
    applied: 24,
    interviews: 16
}

// Activity data for current month (0 = no activity, higher numbers = more activity)
// This simulates LeetCode-style consistency tracking
const activityData = (() => {
    const today = new Date()
    const daysInMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate()
    const data = new Array(daysInMonth).fill(0)

    // Simulate some activity on random days (like user login/usage)
    const activeDays = [1, 5, 9, 10, 15, 18, 22, 25] // Days with activity
    activeDays.forEach(day => {
        if (day <= daysInMonth) {
            data[day - 1] = Math.floor(Math.random() * 5) + 1 // 1-5 activities per day
        }
    })

    // Mark today as active if not already
    const todayDate = today.getDate()
    if (todayDate <= daysInMonth) {
        data[todayDate - 1] = Math.max(data[todayDate - 1], 2)
    }

    return data
})()

// Progress data for application tracking over the last 7 days
// This shows user's application progress with relative scaling
const progressData = Array.from({ length: 7 }, (_, i) => ({
    day: i + 1,
    applications: Math.floor(Math.random() * 80) + 20 // Random between 20-100 applications per day
}))

const recentJobs = [
    {
        id: "1",
        company: "TechCorp Inc.",
        position: "Senior Frontend Developer",
        amount: "$120,000 - $150,000",
        status: "waiting" as const,
        method: "LinkedIn Application",
        date: "Applied Aug 24, 2024"
    },
    {
        id: "2",
        company: "StartupXYZ",
        position: "Full Stack Engineer",
        amount: "$100,000 - $130,000",
        status: "success" as const,
        method: "Company Website",
        date: "Applied Aug 18, 2024"
    },
    {
        id: "3",
        company: "BigTech Co.",
        position: "Software Engineer",
        amount: "$110,000 - $140,000",
        status: "due" as const,
        method: "Indeed Application",
        date: "Applied Aug 8, 2024"
    },
    {
        id: "4",
        company: "Innovation Labs",
        position: "DevOps Engineer",
        amount: "$95,000 - $125,000",
        status: "disabled" as const,
        method: "AngelList",
        date: "Applied Aug 2, 2024"
    }
]

// Sample data for application extraction chart - random values for demo
const applicationExtractionData = [
    { date: "2024-10-01", jobs: 12 },
    { date: "2024-10-02", jobs: 8 },
    { date: "2024-10-03", jobs: 15 },
    { date: "2024-10-04", jobs: 6 },
    { date: "2024-10-05", jobs: 18 },
    { date: "2024-10-06", jobs: 10 },
    { date: "2024-10-07", jobs: 14 }
]

const quickActions = [
    {
        label: "Extract Job URL",
        description: "Extract job details from any URL",
        shortcut: "E",
        icon: Link,
        onClick: () => window.location.href = "/dashboard"
    },
    {
        label: "Upload Resume",
        description: "AI-powered resume analysis",
        shortcut: "R",
        icon: Upload,
        onClick: () => window.location.href = "/dashboard/resume-evaluation"
    },
    {
        label: "View Analytics",
        description: "Track your progress",
        shortcut: "A",
        icon: BarChart3,
        onClick: () => window.location.href = "/dashboard/analytics"
    }
]

export default function DashboardPage() {
    const { stats, loading, error, refreshData } = useDashboard()
    const [applicationStats, setApplicationStats] = useState(applicationExtractionData)
    const [dashboardSummary, setDashboardSummary] = useState(null)
    const [loadingStats, setLoadingStats] = useState(false)

    // Fetch application extraction stats from backend
    useEffect(() => {
        const fetchApplicationStats = async () => {
            setLoadingStats(true)
            try {
                const response = await fetch('/api/v1/stats/application-extraction-stats', {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                    }
                })

                if (response.ok) {
                    const result = await response.json()
                    if (result.status === 'success') {
                        setApplicationStats(result.data)
                    }
                } else {
                    console.log('Using fallback data for application stats')
                }
            } catch (error) {
                console.log('Error fetching application stats, using fallback data:', error)
            } finally {
                setLoadingStats(false)
            }
        }

        fetchApplicationStats()
    }, [])

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

    return (
        <div className="min-h-screen bg-primary-950">
            {/* Main Dashboard Container following handwritten design */}
            <div className="w-full px-6 py-6">
                <StaggerContainer>
                    <div className="space-y-6">

                        {/* Top Section - 4 cards as per handwritten design */}
                        <StaggerItem>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                {/* Overview Calendar Card - moved to first position */}
                                <OverviewCard
                                    title="Overview Calendar"
                                    period={`${new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}`}
                                    stats={overviewData}
                                    activityData={activityData}
                                />

                                {/* Top Bar - placeholder for future development */}
                                <Card className="premium-card">
                                    <CardHeader className="pb-3">
                                        <CardTitle className="text-cream-50 text-lg">Top Bar</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="text-center text-cream-400 py-8">
                                            <div className="text-sm">Keep it blank</div>
                                            <div className="text-xs mt-1">We will build it later</div>
                                        </div>
                                    </CardContent>
                                </Card>

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
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {/* Success Rate Card */}
                                <SuccessRateCard rate={67} change={12} />

                                {/* Today's Activity Card */}
                                <TodayActivityCard applications={3} profiles={12} messages={5} />
                            </div>
                        </StaggerItem>

                        {/* Sidebar Section - as noted in handwritten design */}
                        <StaggerItem>
                            <Card className="premium-card">
                                <CardHeader className="pb-3">
                                    <CardTitle className="text-cream-50 text-lg">Sidebar</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-center text-cream-400 py-8">
                                        <div className="text-sm">From data development</div>
                                        <div className="text-xs mt-1">Future implementation</div>
                                    </div>
                                </CardContent>
                            </Card>
                        </StaggerItem>

                    </div>
                </StaggerContainer>
            </div>
        </div>
    )
} 