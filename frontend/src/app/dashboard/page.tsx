"use client"

import { useState } from "react"
import Image from "next/image"
import { useDashboard } from "../contexts/dashboard-context"
import { Button } from "@/components/ui/button"
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import {
    Tabs,
    TabsContent,
    TabsList,
    TabsTrigger,
} from "@/components/ui/tabs"
import { CalendarDateRangePicker } from "@/components/date-range-picker"
import { MainNav } from "@/components/main-nav"
import { Overview } from "@/components/overview"
import { RecentSales } from "@/components/recent-sales"
import { ThemeSwitcher } from "@/components/theme-switcher"
import { UserNav } from "@/components/user-nav"
import { JobsTab } from "@/components/jobs-tab"
import { ProfileTab } from "@/components/profile-tab"
import JobURLExtractor from "@/components/job-url-extractor"
import { PageTransitionLoading } from "@/components/ui/loading-fill-text"
import { Logo } from "@/components/logo"
import Link from "next/link"
import { ExternalLink, Rocket, Briefcase } from "lucide-react"
import { Badge } from "@/components/ui/badge"

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

export default function DashboardPage() {
    const { stats, loading, error, refreshData } = useDashboard()
    const [activeTab, setActiveTab] = useState("overview")
    const [tabLoading, setTabLoading] = useState(false)

    const handleTabChange = (value: string) => {
        if (value !== activeTab) {
            setTabLoading(true)
            // Simulate loading delay for smooth transition
            setTimeout(() => {
                setActiveTab(value)
                setTabLoading(false)
            }, 1500) // Increased to 1.5 seconds to better show the loading effect
        }
    }

    if (error) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <p className="text-red-500 mb-4">Error: {error}</p>
                    <Button onClick={refreshData}>Retry</Button>
                </div>
            </div>
        )
    }

    return (
        <>
            {tabLoading && <PageTransitionLoading />}
            <div className="md:hidden">
                <Image
                    src="/examples/dashboard-light.png"
                    width={1280}
                    height={866}
                    alt="Dashboard"
                    className="block dark:hidden"
                />
                <Image
                    src="/examples/dashboard-dark.png"
                    width={1280}
                    height={866}
                    alt="Dashboard"
                    className="hidden dark:block"
                />
            </div>
            <div className="hidden flex-col md:flex">
                <div className="border-b">
                    <div className="flex h-16 items-center px-4">
                        <Link href="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
                            <Logo size={32} showText={false} />
                            <span className="text-xl font-bold text-foreground">JobFlow Pro</span>
                        </Link>
                        <MainNav className="mx-6" />
                        <div className="ml-auto flex items-center space-x-4">
                            <ThemeSwitcher />
                            <UserNav />
                        </div>
                    </div>
                </div>
                <div className="flex-1 space-y-4 p-8 pt-6">
                    <div className="flex items-center justify-between space-y-2">
                        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
                        <div className="flex items-center space-x-2">
                            <CalendarDateRangePicker />
                            <Button onClick={refreshData}>Refresh</Button>
                        </div>
                    </div>
                    <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-4">
                        <TabsList>
                            <TabsTrigger value="overview">Overview</TabsTrigger>
                            <TabsTrigger value="jobs">Jobs</TabsTrigger>
                            <TabsTrigger value="extract">Extract Job URL</TabsTrigger>
                            <TabsTrigger value="profile">AI Profile</TabsTrigger>
                        </TabsList>
                        <TabsContent value="overview" className="space-y-4">
                            {/* Startup Job Boards Section */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-lg font-semibold flex items-center gap-2">
                                        <Rocket className="h-5 w-5 text-orange-500" />
                                        Startup Job Boards
                                    </h3>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => window.open('/jobs', '_blank')}
                                    >
                                        View All
                                    </Button>
                                </div>
                                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                                    {STARTUP_JOB_BOARDS.slice(0, 4).map((board) => (
                                        <Card key={board.name} className="hover:shadow-md transition-shadow cursor-pointer">
                                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                                <CardTitle className="text-sm font-medium flex items-center gap-2">
                                                    <Rocket className="h-4 w-4 text-orange-500" />
                                                    {board.name}
                                                </CardTitle>
                                                <Button
                                                    size="sm"
                                                    variant="ghost"
                                                    onClick={() => window.open(board.url, '_blank')}
                                                    className="h-6 w-6 p-0"
                                                >
                                                    <ExternalLink className="h-3 w-3" />
                                                </Button>
                                            </CardHeader>
                                            <CardContent>
                                                <div className="text-xs text-muted-foreground mb-2">
                                                    {board.description}
                                                </div>
                                                {board.requiresAuth && (
                                                    <Badge variant="outline" className="text-xs">
                                                        Requires Account
                                                    </Badge>
                                                )}
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            </div>

                            {/* Job Extraction Statistics */}
                            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                                <Card>
                                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                        <CardTitle className="text-sm font-medium">
                                            Total Jobs Extracted
                                        </CardTitle>
                                        <svg
                                            xmlns="http://www.w3.org/2000/svg"
                                            viewBox="0 0 24 24"
                                            fill="none"
                                            stroke="currentColor"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth="2"
                                            className="h-4 w-4 text-muted-foreground"
                                        >
                                            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                                        </svg>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="text-2xl font-bold">
                                            {loading ? "..." : stats?.totalJobs || 0}
                                        </div>
                                        <p className="text-xs text-muted-foreground">
                                            From URLs & Extensions
                                        </p>
                                    </CardContent>
                                </Card>
                                <Card>
                                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                        <CardTitle className="text-sm font-medium">
                                            From URL Extraction
                                        </CardTitle>
                                        <svg
                                            xmlns="http://www.w3.org/2000/svg"
                                            viewBox="0 0 24 24"
                                            fill="none"
                                            stroke="currentColor"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth="2"
                                            className="h-4 w-4 text-muted-foreground"
                                        >
                                            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                                            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
                                        </svg>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="text-2xl font-bold text-blue-600">
                                            {loading ? "..." : Math.floor((stats?.totalJobs || 0) * 0.6)}
                                        </div>
                                        <p className="text-xs text-muted-foreground">
                                            Manual URL imports
                                        </p>
                                    </CardContent>
                                </Card>
                                <Card>
                                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                        <CardTitle className="text-sm font-medium">
                                            From Extension
                                        </CardTitle>
                                        <svg
                                            xmlns="http://www.w3.org/2000/svg"
                                            viewBox="0 0 24 24"
                                            fill="none"
                                            stroke="currentColor"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth="2"
                                            className="h-4 w-4 text-muted-foreground"
                                        >
                                            <rect width="20" height="14" x="2" y="5" rx="2" />
                                            <path d="M2 10h20" />
                                        </svg>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="text-2xl font-bold text-green-600">
                                            {loading ? "..." : Math.floor((stats?.totalJobs || 0) * 0.4)}
                                        </div>
                                        <p className="text-xs text-muted-foreground">
                                            Browser extension
                                        </p>
                                    </CardContent>
                                </Card>
                                <Card>
                                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                        <CardTitle className="text-sm font-medium">
                                            Applications
                                        </CardTitle>
                                        <svg
                                            xmlns="http://www.w3.org/2000/svg"
                                            viewBox="0 0 24 24"
                                            fill="none"
                                            stroke="currentColor"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth="2"
                                            className="h-4 w-4 text-muted-foreground"
                                        >
                                            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                                            <circle cx="9" cy="7" r="4" />
                                            <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
                                        </svg>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="text-2xl font-bold text-purple-600">
                                            {loading ? "..." : stats?.appliedJobs || 0}
                                        </div>
                                        <p className="text-xs text-muted-foreground">
                                            Jobs applied to
                                        </p>
                                    </CardContent>
                                </Card>
                            </div>

                            {/* Tech Stack Job Boards Section */}
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold flex items-center gap-2">
                                    <Briefcase className="h-5 w-5 text-blue-500" />
                                    Tech Stack Job Boards
                                </h3>
                                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                    {TECH_STACK_JOB_BOARDS.map((board) => (
                                        <Card key={board.name} className="hover:shadow-md transition-shadow cursor-pointer">
                                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                                <CardTitle className="text-sm font-medium flex items-center gap-2">
                                                    <Briefcase className="h-4 w-4 text-blue-500" />
                                                    {board.name}
                                                </CardTitle>
                                                <Button
                                                    size="sm"
                                                    variant="ghost"
                                                    onClick={() => window.open(board.url, '_blank')}
                                                    className="h-6 w-6 p-0"
                                                >
                                                    <ExternalLink className="h-3 w-3" />
                                                </Button>
                                            </CardHeader>
                                            <CardContent>
                                                <div className="text-xs text-muted-foreground mb-2">
                                                    {board.description}
                                                </div>
                                                {board.requiresAuth && (
                                                    <Badge variant="outline" className="text-xs">
                                                        Requires Account
                                                    </Badge>
                                                )}
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            </div>

                            {/* Quick Actions */}
                            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                                    <Link href="/resume-evaluation">
                                        <CardHeader className="pb-3">
                                            <CardTitle className="text-lg flex items-center gap-2">
                                                <svg
                                                    xmlns="http://www.w3.org/2000/svg"
                                                    viewBox="0 0 24 24"
                                                    fill="none"
                                                    stroke="currentColor"
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                    strokeWidth="2"
                                                    className="h-5 w-5 text-blue-600"
                                                >
                                                    <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                                                    <polyline points="14,2 14,8 20,8" />
                                                    <line x1="16" y1="13" x2="8" y2="13" />
                                                    <line x1="16" y1="17" x2="8" y2="17" />
                                                    <polyline points="10,9 9,9 8,9" />
                                                </svg>
                                                Resume Evaluation
                                            </CardTitle>
                                            <CardDescription>
                                                Review AI-powered resume analysis and get improvement recommendations
                                            </CardDescription>
                                        </CardHeader>
                                        <CardContent>
                                            <div className="text-sm text-muted-foreground">
                                                Get detailed ATS scoring, keyword analysis, and actionable feedback to improve your resume.
                                            </div>
                                        </CardContent>
                                    </Link>
                                </Card>

                                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                                    <Link href="/jobs">
                                        <CardHeader className="pb-3">
                                            <CardTitle className="text-lg flex items-center gap-2">
                                                <svg
                                                    xmlns="http://www.w3.org/2000/svg"
                                                    viewBox="0 0 24 24"
                                                    fill="none"
                                                    stroke="currentColor"
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                    strokeWidth="2"
                                                    className="h-5 w-5 text-green-600"
                                                >
                                                    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                                                    <circle cx="9" cy="7" r="4" />
                                                    <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
                                                </svg>
                                                Job Management
                                            </CardTitle>
                                            <CardDescription>
                                                Track your job applications and manage your career progress
                                            </CardDescription>
                                        </CardHeader>
                                        <CardContent>
                                            <div className="text-sm text-muted-foreground">
                                                Organize job applications, track status updates, and monitor your job search progress.
                                            </div>
                                        </CardContent>
                                    </Link>
                                </Card>

                                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                                    <Link href="/analytics">
                                        <CardHeader className="pb-3">
                                            <CardTitle className="text-lg flex items-center gap-2">
                                                <svg
                                                    xmlns="http://www.w3.org/2000/svg"
                                                    viewBox="0 0 24 24"
                                                    fill="none"
                                                    stroke="currentColor"
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                    strokeWidth="2"
                                                    className="h-5 w-5 text-purple-600"
                                                >
                                                    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                                                </svg>
                                                Analytics & Insights
                                            </CardTitle>
                                            <CardDescription>
                                                View detailed analytics and insights about your job search
                                            </CardDescription>
                                        </CardHeader>
                                        <CardContent>
                                            <div className="text-sm text-muted-foreground">
                                                Analyze your job search performance, track trends, and optimize your strategy.
                                            </div>
                                        </CardContent>
                                    </Link>
                                </Card>
                            </div>
                            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                                <Card className="col-span-4">
                                    <CardHeader>
                                        <CardTitle>Overview</CardTitle>
                                    </CardHeader>
                                    <CardContent className="pl-2">
                                        <Overview />
                                    </CardContent>
                                </Card>
                                <Card className="col-span-3">
                                    <CardHeader>
                                        <CardTitle>Recent Applications</CardTitle>
                                        <CardDescription>
                                            You applied to {stats?.appliedJobs || 0} jobs total.
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <RecentSales />
                                    </CardContent>
                                </Card>
                            </div>
                        </TabsContent>
                        <TabsContent value="jobs">
                            <JobsTab />
                        </TabsContent>
                        <TabsContent value="extract">
                            <div className="space-y-6">
                                <div>
                                    <h3 className="text-lg font-medium">Extract Job from URL</h3>
                                    <p className="text-sm text-muted-foreground">
                                        Paste any job URL to automatically extract job details and track your application.
                                    </p>
                                </div>
                                <JobURLExtractor
                                    userId="demo_user"
                                    onJobExtracted={() => {
                                        // Optionally refresh data or show success message
                                        refreshData()
                                    }}
                                />
                            </div>
                        </TabsContent>
                        <TabsContent value="profile">
                            <ProfileTab userId="demo_user" />
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
        </>
    )
} 