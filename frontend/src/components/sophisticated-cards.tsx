"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"
import {
    TrendingUp,
    TrendingDown,
    ArrowUpRight,
    ArrowDownRight,
    ChevronDown
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useActivity } from "@/contexts/activity-context"
import { getDailyActivity } from "@/lib/activity-api"

interface OverviewCardProps {
    title: string
    period: string
    stats: {
        total: number
        applied: number
        interviews: number
    }
    activityData?: number[]  // Activity data for each day of the month
    userId?: string  // User ID for activity tracking
}

export function OverviewCard({ title, period, stats, activityData, userId }: OverviewCardProps) {
    return (
        <Card className="premium-card hover:scale-105 transition-all duration-300 group h-full flex flex-col min-w-[280px] max-w-[500px] w-full">
            <CardHeader className="pb-3 flex-shrink-0">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-cream-50 text-lg group-hover:text-accent-400 transition-colors">{title}</CardTitle>
                    <span className="text-sm text-cream-300 group-hover:text-cream-200 transition-colors">{period}</span>
                </div>
            </CardHeader>
            <CardContent className="space-y-4 flex-1 flex flex-col">
                <div className="grid grid-cols-3 gap-3">
                    <div className="text-center group-hover:scale-110 transition-transform duration-300">
                        <div className="text-xl font-bold text-cream-50 group-hover:text-accent-400 transition-colors">{stats.total}</div>
                        <div className="text-xs text-cream-300 group-hover:text-cream-200 transition-colors">Total Jobs</div>
                    </div>
                    <div className="text-center group-hover:scale-110 transition-transform duration-300">
                        <div className="text-xl font-bold text-gold-400">{stats.applied}</div>
                        <div className="text-xs text-cream-300 group-hover:text-cream-200 transition-colors">Applied</div>
                    </div>
                    <div className="text-center group-hover:scale-110 transition-transform duration-300">
                        <div className="text-xl font-bold text-accent-400">{stats.interviews}</div>
                        <div className="text-xs text-cream-300 group-hover:text-cream-200 transition-colors">Interviews</div>
                    </div>
                </div>

                {/* Activity Calendar Grid */}
                <div className="flex-1 flex items-center justify-center px-1 pb-1">
                    <ActivityCalendar activityData={activityData} userId={userId} />
                </div>
            </CardContent>
        </Card>
    )
}

interface BalanceCardProps {
    title: string
    balance: string
    change: string
    changeType: "increase" | "decrease"
    currency: string
}

export function BalanceCard({ title, balance, change, changeType, currency }: BalanceCardProps) {
    return (
        <Card className="premium-card hover:scale-105 transition-all duration-300 group min-w-[280px] max-w-[400px] w-full">
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-cream-50 text-lg group-hover:text-accent-400 transition-colors">{title}</CardTitle>
                    <div className="flex items-center space-x-2 group-hover:scale-110 transition-transform duration-300">
                        <span className="text-sm text-cream-300 group-hover:text-cream-200 transition-colors">{currency}</span>
                        <ChevronDown className="h-4 w-4 text-cream-300 group-hover:text-accent-400 transition-colors" />
                    </div>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="text-3xl font-bold text-cream-50 group-hover:text-accent-400 transition-colors">{balance}</div>
                <div className="flex items-center space-x-2">
                    {changeType === "increase" ? (
                        <ArrowUpRight className="h-4 w-4 text-green-400 group-hover:scale-110 transition-transform duration-300" />
                    ) : (
                        <ArrowDownRight className="h-4 w-4 text-red-400 group-hover:scale-110 transition-transform duration-300" />
                    )}
                    <span className={cn(
                        "text-sm font-medium",
                        changeType === "increase" ? "text-green-400" : "text-red-400"
                    )}>
                        {change}
                    </span>
                    <span className="text-sm text-cream-300 group-hover:text-cream-200 transition-colors">vs last month</span>
                </div>

                {/* Job Search Health */}
                <div className="mt-4 p-3 bg-primary-700 rounded-lg group-hover:bg-primary-600 transition-colors duration-300">
                    <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-accent-400 rounded-full animate-pulse group-hover:bg-accent-300"></div>
                        <span className="text-sm text-cream-200 group-hover:text-cream-50 transition-colors">Job Search Health</span>
                    </div>
                    <p className="text-xs text-cream-300 mt-1 group-hover:text-cream-200 transition-colors">is updating health status now...</p>
                </div>
            </CardContent>
        </Card>
    )
}

interface QuickActionCardProps {
    title: string
    actions: Array<{
        label: string
        description?: string
        shortcut: string
        icon: React.ElementType
        onClick: () => void
    }>
}

export function QuickActionCard({ title, actions }: QuickActionCardProps) {
    return (
        <Card className="premium-card transition-all duration-300 h-full flex flex-col w-full">
            <CardHeader className="pb-2 flex-shrink-0 px-4 pt-4">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-cream-50 text-base">{title}</CardTitle>
                    <Button variant="ghost" size="sm" className="text-cream-300 hover:text-cream-50 text-xs px-2 py-1">
                        Manage
                    </Button>
                </div>
            </CardHeader>
            <CardContent className="space-y-2 flex-1 flex flex-col px-4 pb-4">
                {actions.map((action, index) => (
                    <Button
                        key={index}
                        onClick={action.onClick}
                        className="w-full h-auto p-3 bg-primary-700 hover:bg-primary-600 text-cream-50 border-primary-500 hover:border-accent-500 transition-all duration-200 group"
                    >
                        <div className="flex items-center justify-between w-full">
                            <div className="flex items-center space-x-2.5">
                                <action.icon className="h-4 w-4 group-hover:text-accent-400 transition-colors flex-shrink-0" />
                                <div className="text-left min-w-0 flex-1">
                                    <div className="font-medium text-sm">{action.label}</div>
                                    {action.description && (
                                        <div className="text-xs text-cream-300 group-hover:text-cream-200 mt-0.5 truncate">
                                            {action.description}
                                        </div>
                                    )}
                                </div>
                            </div>
                            <kbd className="px-1.5 py-0.5 text-xs bg-primary-600 text-cream-200 rounded group-hover:bg-primary-500 transition-colors flex-shrink-0 ml-2">
                                {action.shortcut}
                            </kbd>
                        </div>
                    </Button>
                ))}
            </CardContent>
        </Card>
    )
}

interface GoalsCardProps {
    title: string
    goals: Array<{
        name: string
        amount: string
        timeframe: string
        progress: number
    }>
}

export function GoalsCard({ title, goals }: GoalsCardProps) {
    return (
        <Card className="premium-card transition-all duration-300 min-w-[280px] max-w-[400px] w-full">
            <CardHeader className="pb-3">
                <CardTitle className="text-cream-50 text-lg">{title}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {goals.map((goal, index) => (
                    <div key={index} className="space-y-2">
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-cream-50">{goal.name}</span>
                            <span className="text-sm text-cream-300">{goal.timeframe}</span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-lg font-bold text-accent-400">{goal.amount}</span>
                            <span className="text-xs text-cream-300">Achieved in {goal.timeframe}</span>
                        </div>
                        <Progress value={goal.progress} className="h-1" />
                    </div>
                ))}
            </CardContent>
        </Card>
    )
}

interface RecentJobsCardProps {
    title: string
    jobs: Array<{
        id: string
        company: string
        position: string
        amount: string
        status: "success" | "waiting" | "due" | "disabled"
        method: string
        date: string
    }>
}

export function RecentJobsCard({ title, jobs }: RecentJobsCardProps) {
    const statusConfig = {
        success: { color: "text-green-400", bg: "bg-green-400/20" },
        waiting: { color: "text-gold-400", bg: "bg-gold-400/20" },
        due: { color: "text-red-400", bg: "bg-red-400/20" },
        disabled: { color: "text-cream-400", bg: "bg-cream-400/20" },
    }

    return (
        <Card className="premium-card transition-all duration-300 h-full group flex flex-col min-w-[320px] max-w-[500px] w-full">
            <CardHeader className="pb-3 px-6 flex-shrink-0">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-cream-50 text-lg group-hover:text-accent-400 transition-colors">{title}</CardTitle>
                    <Button variant="ghost" size="sm" className="text-cream-300 hover:text-cream-50 text-sm">
                        Filter
                    </Button>
                </div>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col min-h-0 p-0">
                <div className="flex flex-col h-full">
                    {/* Header */}
                    <div className="px-6 py-3 border-b border-primary-600 flex-shrink-0">
                        <div className="grid grid-cols-4 gap-3 text-xs font-medium text-cream-300 uppercase tracking-wider">
                            <div className="min-w-0">TYPE</div>
                            <div className="min-w-0">AMOUNT</div>
                            <div className="min-w-0">STATUS</div>
                            <div className="min-w-0">METHOD</div>
                        </div>
                    </div>

                    {/* Jobs List - Scrollable */}
                    <div className="flex-1 overflow-y-auto min-h-0">
                        <div className="px-6 py-2">
                            {jobs.slice(0, 4).map((job) => {
                                const status = statusConfig[job.status]
                                return (
                                    <div key={job.id} className="grid grid-cols-4 gap-3 items-center py-2 border-b border-primary-600 last:border-0 hover:bg-primary-700/30 rounded transition-colors">
                                        <div className="min-w-0">
                                            <div className="text-sm font-medium text-cream-50 group-hover:text-accent-400 transition-colors truncate">{job.company}</div>
                                            <div className="text-xs text-cream-300 truncate">{job.position}</div>
                                            <div className="text-xs text-cream-400 truncate">{job.date}</div>
                                        </div>
                                        <div className="text-sm text-cream-50 truncate min-w-0">{job.amount}</div>
                                        <div className="min-w-0">
                                            <Badge className={`${status.bg} ${status.color} border-0 text-xs whitespace-nowrap`}>
                                                {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                                            </Badge>
                                        </div>
                                        <div className="text-xs text-cream-400 truncate min-w-0">{job.method}</div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

interface ProVersionCardProps {
    title: string
    description: string
    price: string
    period: string
}

export function ProVersionCard({ title, description, price, period }: ProVersionCardProps) {
    return (
        <Card className="bg-gradient-card border-accent-500/20 hover:bg-gradient-warm/10 transition-all duration-300 glow-orange min-w-[280px] max-w-[400px] w-full">
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-cream-50 text-lg">{title}</CardTitle>
                    <Button variant="ghost" size="sm" className="text-accent-400 hover:text-accent-300">
                        Details
                    </Button>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                <p className="text-sm text-cream-200">{description}</p>
                <div className="space-y-2">
                    <div className="text-2xl font-bold text-cream-50">{price}</div>
                    <div className="text-sm text-cream-300">{period}</div>
                </div>
                <Button className="w-full bg-gradient-warm hover:bg-gradient-gold text-white glow-orange hover:glow-gold transition-all duration-300">
                    Learn More
                </Button>
            </CardContent>
        </Card>
    )
}

interface ActivityCalendarProps {
    activityData?: number[]
    userId?: string
}

function ActivityCalendar({ activityData, userId }: ActivityCalendarProps) {
    const { stats: _stats } = useActivity()
    const [realActivityData, setRealActivityData] = useState<{ [key: string]: number }>({})
    const [_loading, setLoading] = useState(false)

    const today = new Date()
    const currentMonth = today.getMonth()
    const currentYear = today.getFullYear()
    const currentDate = today.getDate()

    // Load real activity data
    useEffect(() => {
        const loadActivityData = async () => {
            if (!userId) return

            setLoading(true)
            try {
                // Get current month's activity data
                const startOfMonth = new Date(currentYear, currentMonth, 1)
                const endOfMonth = new Date(currentYear, currentMonth + 1, 0)

                const dailyData = await getDailyActivity(
                    userId,
                    startOfMonth.toISOString().split('T')[0],
                    endOfMonth.toISOString().split('T')[0]
                )

                // Transform to date -> totalTasks mapping
                const activityMap: { [key: string]: number } = {}
                dailyData.forEach((day: Record<string, unknown>) => {
                    const totalTasks = (day.job_extractions as number || 0) + (day.referral_emails as number || 0)
                    activityMap[day.date as string] = totalTasks
                })

                setRealActivityData(activityMap)
            } catch (error) {
                console.error('Error loading activity data:', error)
            } finally {
                setLoading(false)
            }
        }

        loadActivityData()
    }, [userId, currentMonth, currentYear])

    // Get first day of month and number of days
    const firstDayOfMonth = new Date(currentYear, currentMonth, 1).getDay()
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate()

    // Create calendar grid - show 5 weeks (35 days max)
    const calendarDays: any[] = []
    const maxDaysToShow = 35

    // Previous month's trailing days
    for (let i = firstDayOfMonth - 1; i >= 0; i--) {
        calendarDays.push({
            date: new Date(currentYear, currentMonth, 0).getDate() - i,
            isCurrentMonth: false,
            isToday: false,
            activity: 0
        })
    }

    // Current month's days
    for (let date = 1; date <= daysInMonth; date++) {
        const isToday = date === currentDate
        const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(date).padStart(2, '0')}`
        const activity = realActivityData[dateStr] || activityData?.[date - 1] || 0

        calendarDays.push({
            date,
            isCurrentMonth: true,
            isToday,
            activity
        })
    }

    // Only show up to maxDaysToShow for compact display
    const displayDays = calendarDays.slice(0, maxDaysToShow)

    const getActivityColor = (activity: number, isToday: boolean, isCurrentMonth: boolean) => {
        if (!isCurrentMonth) {
            return "bg-primary-800/30 text-cream-500"
        }

        if (isToday) {
            if (activity > 0) {
                return "bg-orange-500 text-white ring-2 ring-orange-400"
            } else {
                return "bg-primary-600 text-cream-300 ring-2 ring-orange-500"
            }
        }

        if (activity === 0) {
            return "bg-primary-700 text-cream-400 hover:bg-primary-600"
        } else if (activity >= 10) {
            return "bg-orange-600 text-white hover:bg-orange-700" // Dark orange for 10+ tasks
        } else if (activity >= 5) {
            return "bg-orange-400 text-white hover:bg-orange-500" // Medium orange for 5-9 tasks
        } else if (activity >= 1) {
            return "bg-orange-200 text-gray-900 hover:bg-orange-300" // Light orange for 1-4 tasks
        }

        return "bg-primary-700 text-cream-400"
    }

    const daysOfWeek = ["S", "M", "T", "W", "T", "F", "S"]

    return (
        <div className="w-full max-w-none">
            {/* Days of week header */}
            <div className="grid grid-cols-7 gap-1 mb-2">
                {daysOfWeek.map((day) => (
                    <div key={day} className="text-center text-xs text-cream-400 font-medium">
                        {day}
                    </div>
                ))}
            </div>

            {/* Calendar grid */}
            <div className="grid grid-cols-7 gap-1">
                {displayDays.map((day, index) => (
                    <div
                        key={index}
                        className={cn(
                            "w-7 h-7 text-xs flex items-center justify-center rounded cursor-pointer transition-all duration-200 hover:scale-110",
                            getActivityColor(day.activity, day.isToday, day.isCurrentMonth)
                        )}
                        title={
                            day.isCurrentMonth
                                ? day.isToday
                                    ? `Today - ${day.activity} activities`
                                    : `${day.date} - ${day.activity} activities`
                                : `${day.date}`
                        }
                    >
                        {day.date}
                    </div>
                ))}
            </div>
        </div>
    )
}

interface ProgressCardProps {
    title: string
    progressData?: { day: number; applications: number }[]
}

export function ProgressCard({ title, progressData }: ProgressCardProps) {
    // Calculate trend for header
    const defaultData = Array.from({ length: 7 }, (_, i) => ({
        day: i + 1,
        applications: Math.floor(Math.random() * 50) + 10
    }))
    const data = progressData || defaultData
    const firstHalf = data.slice(0, Math.ceil(data.length / 2))
    const secondHalf = data.slice(Math.ceil(data.length / 2))
    const firstAvg = firstHalf.reduce((sum, d) => sum + d.applications, 0) / firstHalf.length
    const secondAvg = secondHalf.reduce((sum, d) => sum + d.applications, 0) / secondHalf.length
    const isIncreasing = secondAvg > firstAvg

    return (
        <Card className="premium-card hover:scale-105 transition-all duration-300 group h-full flex flex-col min-w-[300px] max-w-[550px] w-full">
            <CardHeader className="pb-2 flex-shrink-0">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-cream-50 text-lg group-hover:text-accent-400 transition-colors">{title}</CardTitle>
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
            </CardHeader>
            <CardContent className="flex-1 flex flex-col px-4 pb-3 min-h-0 overflow-hidden">
                <ProgressLineGraph progressData={progressData} />
            </CardContent>
        </Card>
    )
}

interface ProgressLineGraphProps {
    progressData?: { day: number; applications: number }[]
}

function ProgressLineGraph({ progressData }: ProgressLineGraphProps) {
    // Generate sample data if none provided (last 7 days)
    const defaultData = Array.from({ length: 7 }, (_, i) => ({
        day: i + 1,
        applications: Math.floor(Math.random() * 50) + 10 // Random between 10-60
    }))

    const data = progressData || defaultData
    const maxApplications = Math.max(...data.map(d => d.applications))
    const minApplications = Math.min(...data.map(d => d.applications))

    // Calculate trend
    const firstHalf = data.slice(0, Math.ceil(data.length / 2))
    const secondHalf = data.slice(Math.ceil(data.length / 2))
    const firstAvg = firstHalf.reduce((sum, d) => sum + d.applications, 0) / firstHalf.length
    const secondAvg = secondHalf.reduce((sum, d) => sum + d.applications, 0) / secondHalf.length
    const _isIncreasing = secondAvg > firstAvg

    // SVG dimensions - responsive for card fit
    const width = 400
    const height = 160
    const padding = 20

    // Calculate points for the line
    const points = data.map((d, i) => {
        const x = padding + (i * (width - 2 * padding)) / (data.length - 1)
        const y = height - padding - ((d.applications - minApplications) / (maxApplications - minApplications)) * (height - 2 * padding)
        return { x, y, applications: d.applications, day: d.day }
    })

    // Create path string for the line
    const pathData = points.reduce((path, point, i) => {
        return path + (i === 0 ? `M ${point.x} ${point.y}` : ` L ${point.x} ${point.y}`)
    }, "")

    return (
        <div className="w-full">
            {/* Progress indicator */}
            <div className="flex items-center justify-between mb-1">
                <div className="text-xs text-cream-400">Last {data.length} days</div>
            </div>

            {/* SVG Line Graph */}
            <div className="relative w-full flex-1 min-h-0 overflow-hidden">
                <svg
                    viewBox={`0 0 ${width} ${height}`}
                    className="w-full h-full max-h-full"
                    preserveAspectRatio="xMidYMid meet"
                >
                    {/* Grid lines */}
                    <defs>
                        <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
                            <path d="M 30 0 L 0 0 0 30" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="0.5" />
                        </pattern>
                    </defs>
                    <rect width="100%" height="100%" fill="url(#grid)" />

                    {/* Area under the curve */}
                    <defs>
                        <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stopColor="rgb(249, 115, 22)" stopOpacity={0.3} />
                            <stop offset="100%" stopColor="rgb(249, 115, 22)" stopOpacity={0.05} />
                        </linearGradient>
                    </defs>
                    <path
                        d={`${pathData} L ${points[points.length - 1].x} ${height - padding} L ${points[0].x} ${height - padding} Z`}
                        fill="url(#gradient)"
                    />

                    {/* Main line */}
                    <path
                        d={pathData}
                        fill="none"
                        stroke="rgb(249, 115, 22)"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />

                    {/* Data points */}
                    {points.map((point, i) => (
                        <g key={i}>
                            <circle
                                cx={point.x}
                                cy={point.y}
                                r="3"
                                fill="rgb(249, 115, 22)"
                                stroke="rgb(255, 255, 255)"
                                strokeWidth="1.5"
                                className="hover:r-4 transition-all cursor-pointer"
                            />
                            <title>{`Day ${point.day}: ${point.applications} applications`}</title>
                        </g>
                    ))}

                    {/* Y-axis labels */}
                    <text x="12" y={padding + 5} className="text-xs fill-cream-400" textAnchor="start">
                        {maxApplications}
                    </text>
                    <text x="12" y={height - padding + 5} className="text-xs fill-cream-400" textAnchor="start">
                        {minApplications}
                    </text>
                </svg>
            </div>

        </div>
    )
}
