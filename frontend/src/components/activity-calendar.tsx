"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useActivity } from "@/contexts/activity-context"
import { getDailyActivity } from "@/lib/activity-api"
import {
    Calendar,
    Target,
    TrendingUp,
    Zap,
    Briefcase,
    Mail
} from "lucide-react"

interface ActivityData {
    date: string
    jobExtractions: number
    referralEmails: number
    totalTasks: number
}

interface ActivityCalendarProps {
    userId: string
    className?: string
}

// Generate color based on task count
const getActivityColor = (taskCount: number): string => {
    if (taskCount === 0) return "bg-gray-700 hover:bg-gray-600" // No activity
    if (taskCount >= 1 && taskCount < 5) return "bg-orange-200 hover:bg-orange-300" // Light orange
    if (taskCount >= 5 && taskCount < 10) return "bg-orange-400 hover:bg-orange-500" // Medium orange
    if (taskCount >= 10) return "bg-orange-600 hover:bg-orange-700" // Dark orange
    return "bg-gray-700 hover:bg-gray-600"
}

// Generate tooltip text
const getTooltipText = (data: ActivityData): string => {
    if (data.totalTasks === 0) return "No activity"

    const parts = []
    if (data.jobExtractions > 0) {
        parts.push(`${data.jobExtractions} job extraction${data.jobExtractions > 1 ? 's' : ''}`)
    }
    if (data.referralEmails > 0) {
        parts.push(`${data.referralEmails} referral email${data.referralEmails > 1 ? 's' : ''}`)
    }

    return `${data.totalTasks} task${data.totalTasks > 1 ? 's' : ''}: ${parts.join(', ')}`
}

export function ActivityCalendar({ userId, className = "" }: ActivityCalendarProps) {
    const { stats, loading } = useActivity()
    const [activityData, setActivityData] = useState<ActivityData[]>([])
    const [calendarLoading, setCalendarLoading] = useState(true)

    // Generate calendar data for the past year
    const generateCalendarData = () => {
        const today = new Date()
        const oneYearAgo = new Date(today)
        oneYearAgo.setFullYear(today.getFullYear() - 1)

        const data: ActivityData[] = []
        const current = new Date(oneYearAgo)

        while (current <= today) {
            data.push({
                date: current.toISOString().split('T')[0],
                jobExtractions: 0,
                referralEmails: 0,
                totalTasks: 0
            })
            current.setDate(current.getDate() + 1)
        }

        return data
    }

    // Mock data for demonstration - replace with actual API calls
    const generateMockData = (baseData: ActivityData[]): ActivityData[] => {
        return baseData.map(day => {
            // Simulate some activity patterns
            const random = Math.random()
            let jobExtractions = 0
            let referralEmails = 0

            if (random > 0.7) { // 30% chance of activity
                jobExtractions = Math.floor(Math.random() * 8) + 1
                referralEmails = Math.floor(Math.random() * 3)
            }

            return {
                ...day,
                jobExtractions,
                referralEmails,
                totalTasks: jobExtractions + referralEmails
            }
        })
    }

    // Calculate statistics
    const calculateStats = (data: ActivityData[]) => {
        const totalTasks = data.reduce((sum, day) => sum + day.totalTasks, 0)
        const activeDays = data.filter(day => day.totalTasks > 0).length

        // Calculate streaks
        let maxStreak = 0
        let currentStreak = 0
        let tempStreak = 0

        data.forEach(day => {
            if (day.totalTasks > 0) {
                tempStreak++
                currentStreak = tempStreak
                maxStreak = Math.max(maxStreak, tempStreak)
            } else {
                tempStreak = 0
            }
        })

        return {
            totalTasks,
            activeDays,
            maxStreak,
            currentStreak: tempStreak > 0 ? currentStreak : 0
        }
    }

    useEffect(() => {
        const loadActivityData = async () => {
            setCalendarLoading(true)
            try {
                // Get date range for past year
                const today = new Date()
                const oneYearAgo = new Date(today)
                oneYearAgo.setFullYear(today.getFullYear() - 1)

                // Fetch daily activity data
                const dailyData = await getDailyActivity(
                    userId,
                    oneYearAgo.toISOString().split('T')[0],
                    today.toISOString().split('T')[0]
                )

                // Transform API data to our format
                const transformedData = dailyData.map((day: any) => ({
                    date: day.date,
                    jobExtractions: day.job_extractions || 0,
                    referralEmails: day.referral_emails || 0,
                    totalTasks: (day.job_extractions || 0) + (day.referral_emails || 0)
                }))

                setActivityData(transformedData)

            } catch (error) {
                console.error('Error loading activity data:', error)
                // Fallback to mock data if API fails
                const baseData = generateCalendarData()
                const mockData = generateMockData(baseData)
                setActivityData(mockData)
            } finally {
                setCalendarLoading(false)
            }
        }

        loadActivityData()
    }, [userId])

    // Group data by months for display
    const groupByMonths = (data: ActivityData[]) => {
        const months: { [key: string]: ActivityData[] } = {}

        data.forEach(day => {
            const date = new Date(day.date)
            const monthKey = `${date.getFullYear()}-${date.getMonth()}`

            if (!months[monthKey]) {
                months[monthKey] = []
            }
            months[monthKey].push(day)
        })

        return months
    }

    const months = groupByMonths(activityData)
    const monthNames = [
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ]

    if (loading || calendarLoading) {
        return (
            <Card className={className}>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-cream-50">
                        <Calendar className="w-5 h-5" />
                        Activity Calendar
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center py-12">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
                    </div>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card className={className}>
            <CardHeader>
                <CardTitle className="flex items-center gap-2 text-cream-50">
                    <Calendar className="w-5 h-5" />
                    Activity Calendar
                </CardTitle>
                <p className="text-cream-300 text-sm">
                    Track your job search consistency over the past year
                </p>
            </CardHeader>
            <CardContent>
                {/* Statistics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="text-center">
                        <div className="text-2xl font-bold text-cream-50">{stats?.totalTasks || 0}</div>
                        <div className="text-sm text-cream-300">Total Tasks</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold text-cream-50">{stats?.activeDays || 0}</div>
                        <div className="text-sm text-cream-300">Active Days</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold text-cream-50">{stats?.maxStreak || 0}</div>
                        <div className="text-sm text-cream-300">Max Streak</div>
                    </div>
                    <div className="text-center">
                        <div className="text-2xl font-bold text-orange-400">{stats?.currentStreak || 0}</div>
                        <div className="text-sm text-cream-300">Current Streak</div>
                    </div>
                </div>

                {/* Calendar Grid */}
                <div className="space-y-4">
                    {Object.entries(months).map(([monthKey, days]) => {
                        const date = new Date(days[0].date)
                        const monthName = monthNames[date.getMonth()]
                        const year = date.getFullYear()

                        return (
                            <div key={monthKey} className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <h4 className="text-sm font-medium text-cream-300">
                                        {monthName} {year}
                                    </h4>
                                    <div className="flex items-center gap-2 text-xs text-cream-400">
                                        <div className="flex items-center gap-1">
                                            <div className="w-3 h-3 bg-gray-700 rounded"></div>
                                            <span>No activity</span>
                                        </div>
                                        <div className="flex items-center gap-1">
                                            <div className="w-3 h-3 bg-orange-200 rounded"></div>
                                            <span>1-4 tasks</span>
                                        </div>
                                        <div className="flex items-center gap-1">
                                            <div className="w-3 h-3 bg-orange-400 rounded"></div>
                                            <span>5-9 tasks</span>
                                        </div>
                                        <div className="flex items-center gap-1">
                                            <div className="w-3 h-3 bg-orange-600 rounded"></div>
                                            <span>10+ tasks</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-7 gap-1">
                                    {days.map((day, index) => {
                                        const dayDate = new Date(day.date)
                                        const dayOfWeek = dayDate.getDay()

                                        return (
                                            <div
                                                key={day.date}
                                                className={`
                                                    w-3 h-3 rounded-sm cursor-pointer transition-all duration-200
                                                    ${getActivityColor(day.totalTasks)}
                                                    ${dayOfWeek === 0 || dayOfWeek === 6 ? 'opacity-60' : ''}
                                                `}
                                                title={`${dayDate.toLocaleDateString()}: ${getTooltipText(day)}`}
                                            />
                                        )
                                    })}
                                </div>
                            </div>
                        )
                    })}
                </div>

                {/* Legend */}
                <div className="mt-6 pt-4 border-t border-primary-700">
                    <div className="flex items-center justify-center gap-6 text-xs text-cream-400">
                        <div className="flex items-center gap-2">
                            <Briefcase className="w-4 h-4" />
                            <span>Job Extractions</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <Mail className="w-4 h-4" />
                            <span>Referral Emails</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <Zap className="w-4 h-4" />
                            <span>Total Tasks</span>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
