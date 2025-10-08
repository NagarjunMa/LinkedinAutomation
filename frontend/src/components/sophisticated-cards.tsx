"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"
import {
    TrendingUp,
    TrendingDown,
    Users,
    Briefcase,
    Target,
    Mail,
    FileText,
    BarChart3,
    ArrowUpRight,
    ArrowDownRight,
    Clock,
    CheckCircle,
    AlertCircle,
    Star,
    Calendar,
    DollarSign,
    Building,
    MapPin,
    ExternalLink,
    ChevronDown
} from "lucide-react"
import { cn } from "@/lib/utils"

interface OverviewCardProps {
    title: string
    period: string
    stats: {
        total: number
        applied: number
        interviews: number
    }
}

export function OverviewCard({ title, period, stats }: OverviewCardProps) {
    return (
        <Card className="premium-card hover:scale-105 transition-all duration-300 group h-full flex flex-col">
            <CardHeader className="pb-3 flex-shrink-0">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-cream-50 text-lg group-hover:text-accent-400 transition-colors">{title}</CardTitle>
                    <span className="text-sm text-cream-300 group-hover:text-cream-200 transition-colors">{period}</span>
                </div>
            </CardHeader>
            <CardContent className="space-y-4 flex-1 flex flex-col">
                <div className="grid grid-cols-3 gap-4">
                    <div className="text-center group-hover:scale-110 transition-transform duration-300">
                        <div className="text-2xl font-bold text-cream-50 group-hover:text-accent-400 transition-colors">{stats.total}</div>
                        <div className="text-xs text-cream-300 group-hover:text-cream-200 transition-colors">Total Jobs</div>
                    </div>
                    <div className="text-center group-hover:scale-110 transition-transform duration-300">
                        <div className="text-2xl font-bold text-gold-400">{stats.applied}</div>
                        <div className="text-xs text-cream-300 group-hover:text-cream-200 transition-colors">Applied</div>
                    </div>
                    <div className="text-center group-hover:scale-110 transition-transform duration-300">
                        <div className="text-2xl font-bold text-accent-400">{stats.interviews}</div>
                        <div className="text-xs text-cream-300 group-hover:text-cream-200 transition-colors">Interviews</div>
                    </div>
                </div>

                {/* Compact Calendar Grid */}
                <div className="mt-4">
                    <div className="text-sm text-cream-300 mb-2 group-hover:text-cream-200 transition-colors">This Week</div>
                    <div className="grid grid-cols-7 gap-1 max-w-48">
                        {Array.from({ length: 7 }, (_, i) => (
                            <div
                                key={i}
                                className={cn(
                                    "w-5 h-5 rounded text-xs flex items-center justify-center cursor-pointer transition-all duration-200 hover:scale-110",
                                    i === 0 || i === 4
                                        ? "bg-gradient-warm text-white shadow-glow-orange"
                                        : "bg-primary-700 text-cream-300 hover:bg-primary-600 hover:text-cream-50"
                                )}
                            >
                                {i + 1}
                            </div>
                        ))}
                    </div>
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
        <Card className="premium-card hover:scale-105 transition-all duration-300 group">
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
        shortcut: string
        icon: React.ElementType
        onClick: () => void
    }>
}

export function QuickActionCard({ title, actions }: QuickActionCardProps) {
    return (
        <Card className="premium-card transition-all duration-300 h-full flex flex-col">
            <CardHeader className="pb-3 flex-shrink-0">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-cream-50 text-lg">{title}</CardTitle>
                    <Button variant="ghost" size="sm" className="text-cream-300 hover:text-cream-50">
                        Manage
                    </Button>
                </div>
            </CardHeader>
            <CardContent className="space-y-3 flex-1 flex flex-col">
                {actions.map((action, index) => (
                    <Button
                        key={index}
                        onClick={action.onClick}
                        className="w-full justify-between bg-primary-700 hover:bg-primary-600 text-cream-50 border-primary-500 hover:border-accent-500 transition-all duration-200"
                    >
                        <div className="flex items-center space-x-3">
                            <action.icon className="h-4 w-4" />
                            <span>{action.label}</span>
                        </div>
                        <kbd className="px-2 py-1 text-xs bg-primary-600 text-cream-200 rounded">
                            {action.shortcut}
                        </kbd>
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
        <Card className="premium-card transition-all duration-300">
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
        <Card className="premium-card transition-all duration-300 h-full group flex flex-col">
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
        <Card className="bg-gradient-card border-accent-500/20 hover:bg-gradient-warm/10 transition-all duration-300 glow-orange">
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
