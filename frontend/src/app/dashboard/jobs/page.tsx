"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ExternalLink, Rocket, Briefcase } from "lucide-react"

// Startup Job Boards
const STARTUP_JOB_BOARDS = [
    {
        name: "Otta",
        description: "Find your people - Only relevant roles. Choose the right job, at the right company for you. Discover your top recommendations now.",
        url: "https://otta.com/",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Career Vault",
        description: "Land a remote job. Live anywhere. Join 50,000+ job seekers discovering the latest remote jobs with trusted companies worldwide.",
        url: "https://www.careervault.io/",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Startup Gallery",
        description: "Discover today's top startups - A handpicked gallery of 1,028+ outstanding early-stage companies, jobs and funding news. Curated daily.",
        url: "https://startups.gallery/",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Airtable Tech Jobs",
        description: "Tech industry portfolio job boards and talent networks - Comprehensive database of tech job opportunities across various platforms.",
        url: "https://www.airtable.com/universe/expFiABVAU83u1wKh/tech-industry-portfolio-job-boards-and-talent-networks",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Simplify Jobs",
        description: "Streamlined job application process - Apply to multiple jobs with one click. Simplify your job search and application process.",
        url: "https://simplify.jobs/",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Wellfound",
        description: "Startup jobs and opportunities - Connect with innovative startups and find your next role in the startup ecosystem.",
        url: "https://wellfound.com/jobs",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Built In",
        description: "Better Matches. Better Jobs. Happier You. Explore 106,859+ tech companies with personalized job recommendations and company insights.",
        url: "https://builtin.com/",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Tech Jobs for Good",
        description: "Tech jobs that make a difference - Find meaningful tech roles at companies focused on social impact, sustainability, and positive change.",
        url: "https://techjobsforgood.com/",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Startup Jobs",
        description: "Startup job board - Discover opportunities at innovative startups and early-stage companies across various industries.",
        url: "https://startup.jobs/",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Join Rise",
        description: "Rise in your career - Find opportunities at companies that value growth, learning, and career development for tech professionals.",
        url: "https://joinrise.co/",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Remotive",
        description: "Remote jobs and companies - The #1 remote work community. Find remote jobs, learn about remote work, and connect with remote companies.",
        url: "https://remotive.com/",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Stamplist",
        description: "List of Visa specific jobs - Find opportunities that sponsor visas and support international candidates in their job search.",
        url: "https://stamplist.com",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Welcome to the Jungle",
        description: "Startup job board - Discover opportunities at innovative startups and early-stage companies with a focus on company culture.",
        url: "https://welcometothejungle.com",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Hub",
        description: "Discover startup jobs - Find opportunities at innovative startups and early-stage companies across various sectors.",
        url: "https://hub.com",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Venture Loop",
        description: "Startup job opportunities - Connect with venture-backed startups and find roles at companies with strong growth potential.",
        url: "https://ventureloop.com",
        category: "startup",
        requiresAuth: false
    },
    {
        name: "Crunchboard",
        description: "Startup job board - Discover opportunities at innovative startups and early-stage companies in the tech ecosystem.",
        url: "https://crunchboard.com",
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

export default function JobsPage() {
    return (
        <div className="min-h-screen bg-primary-950">
            {/* Constrain content width for large monitors */}
            <div className="max-w-7xl mx-auto p-3 sm:p-4 lg:p-6 space-y-4 sm:space-y-6">
                <div className="text-center space-y-2">
                    <h1 className="text-2xl sm:text-3xl lg:text-4xl xl:text-4xl 2xl:text-4xl font-bold text-cream-50">Job Search Interface</h1>
                    <p className="text-cream-300 text-sm sm:text-base lg:text-lg xl:text-lg 2xl:text-lg">
                        Find your next opportunity across multiple job platforms
                    </p>
                </div>

                <div className="space-y-4 sm:space-y-6">
                    {/* Tech Stack Job Boards Section */}
                    <div className="space-y-4">
                        <h3 className="text-lg font-semibold flex items-center gap-2 text-cream-50">
                            <Briefcase className="h-5 w-5 text-accent-500" />
                            Tech Stack Job Boards
                        </h3>
                        <div className="grid gap-3 sm:gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-4">
                            {TECH_STACK_JOB_BOARDS.map((board) => (
                                <Card key={board.name} className="premium-card hover:scale-105 transition-all duration-300 cursor-pointer">
                                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                        <CardTitle className="text-sm font-medium text-cream-50 flex items-center gap-2">
                                            <Briefcase className="h-4 w-4 text-accent-500" />
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
                                        <div className="text-xs text-cream-300 mb-2">
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

                    {/* Startup Job Boards Section */}
                    <div className="space-y-4">
                        <h3 className="text-lg font-semibold flex items-center gap-2 text-cream-50">
                            <Rocket className="h-5 w-5 text-accent-500" />
                            Startup Job Boards
                        </h3>
                        <div className="grid gap-3 sm:gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-4">
                            {STARTUP_JOB_BOARDS.map((board) => (
                                <Card key={board.name} className="premium-card hover:scale-105 transition-all duration-300 cursor-pointer">
                                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                        <CardTitle className="text-sm font-medium text-cream-50 flex items-center gap-2">
                                            <Rocket className="h-4 w-4 text-accent-500" />
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
                                        <div className="text-xs text-cream-300 mb-2">
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
                </div>
            </div>
        </div>
    )
} 
