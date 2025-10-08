"use client"

import { useState, useEffect } from "react"
import { useDashboard } from "../contexts/dashboard-context"
import { SophisticatedLayout } from "@/components/sophisticated-layout"
import {
    OverviewCard,
    QuickActionCard,
    RecentJobsCard
} from "@/components/sophisticated-cards"
import { EmailStatsCard } from "@/components/email-stats-card"
import { JobExtractionChart } from "@/components/job-extraction-chart"
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
    ChevronDown
} from "lucide-react"
import { Overview } from "@/components/overview"
import { RecentSales } from "@/components/recent-sales"
import JobURLExtractor from "@/components/job-url-extractor"
import {
    FadeInUp,
    FadeIn,
    StaggerContainer,
    StaggerItem
} from "@/components/animated-wrapper"

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
        shortcut: "E",
        icon: Target,
        onClick: () => window.location.href = "/dashboard"
    },
    {
        label: "Upload Resume",
        shortcut: "R",
        icon: FileText,
        onClick: () => window.location.href = "/dashboard/resume-evaluation"
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
        <SophisticatedLayout
            notificationCount={2}
        >
            <StaggerContainer>
                {/* Main Dashboard Grid */}
                <StaggerItem>
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                        {/* Overview Card */}
                        <div className="h-80">
                            <OverviewCard
                                title="Overview"
                                period="This Week"
                                stats={overviewData}
                            />
                        </div>

                        {/* Email Stats Card */}
                        <div className="h-80">
                            <EmailStatsCard
                                title="Email Processing"
                                emailsSent={24}
                                emailsProcessed={18}
                                change="+15%"
                                changeType="increase"
                            />
                        </div>

                        {/* Quick Action Card */}
                        <div className="h-80">
                            <QuickActionCard
                                title="Quick Action"
                                actions={quickActions}
                            />
                        </div>
                    </div>
                </StaggerItem>

                {/* Application Extraction Chart and Recent Applications */}
                <StaggerItem>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                        {/* Application Extraction Chart */}
                        <div className="h-80">
                            <JobExtractionChart data={applicationStats} />
                        </div>

                        {/* Recent Applications Card */}
                        <div className="h-80">
                            <RecentJobsCard
                                title="Recent Applications"
                                jobs={recentJobs}
                            />
                        </div>
                    </div>
                </StaggerItem>

                {/* Additional Dashboard Content */}
                <StaggerItem>
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                        {/* Job Search Progress */}
                        <div className="h-60">
                            <Card className="premium-card hover:scale-105 transition-all duration-300 group h-full flex flex-col">
                                <CardHeader className="pb-3 flex-shrink-0">
                                    <div className="flex items-center space-x-2">
                                        <Target className="h-5 w-5 text-accent-500" />
                                        <CardTitle className="text-cream-50 text-lg group-hover:text-accent-400 transition-colors">
                                            Search Progress
                                        </CardTitle>
                                    </div>
                                </CardHeader>
                                <CardContent className="flex-1 flex flex-col space-y-4">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-cream-300">Weekly Goal</span>
                                        <span className="text-accent-400 font-semibold">15/20 applications</span>
                                    </div>
                                    <div className="w-full bg-primary-700 rounded-full h-2">
                                        <div className="bg-gradient-warm h-2 rounded-full" style={{ width: '75%' }}></div>
                                    </div>
                                    <div className="text-xs text-cream-400">75% of weekly goal completed</div>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Success Rate */}
                        <div className="h-60">
                            <Card className="premium-card hover:scale-105 transition-all duration-300 group h-full flex flex-col">
                                <CardHeader className="pb-3 flex-shrink-0">
                                    <div className="flex items-center space-x-2">
                                        <CheckCircle className="h-5 w-5 text-green-400" />
                                        <CardTitle className="text-cream-50 text-lg group-hover:text-accent-400 transition-colors">
                                            Success Rate
                                        </CardTitle>
                                    </div>
                                </CardHeader>
                                <CardContent className="flex-1 flex flex-col justify-center items-center">
                                    <div className="text-4xl font-bold text-green-400 mb-2">67%</div>
                                    <div className="text-sm text-cream-300 text-center">Response rate this month</div>
                                    <div className="text-xs text-cream-400 mt-2">↑ 12% from last month</div>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Activity Summary */}
                        <div className="h-60">
                            <Card className="premium-card hover:scale-105 transition-all duration-300 group h-full flex flex-col">
                                <CardHeader className="pb-3 flex-shrink-0">
                                    <div className="flex items-center space-x-2">
                                        <Clock className="h-5 w-5 text-blue-400" />
                                        <CardTitle className="text-cream-50 text-lg group-hover:text-accent-400 transition-colors">
                                            Today's Activity
                                        </CardTitle>
                                    </div>
                                </CardHeader>
                                <CardContent className="flex-1 flex flex-col space-y-3">
                                    <div className="flex justify-between items-center">
                                        <span className="text-sm text-cream-300">Applications sent</span>
                                        <span className="text-cream-50 font-semibold">3</span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-sm text-cream-300">Profiles viewed</span>
                                        <span className="text-cream-50 font-semibold">12</span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-sm text-cream-300">Messages sent</span>
                                        <span className="text-cream-50 font-semibold">5</span>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    </div>
                </StaggerItem>

            </StaggerContainer>
        </SophisticatedLayout>
    )
} 