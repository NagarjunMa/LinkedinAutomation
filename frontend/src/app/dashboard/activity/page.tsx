"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ActivityCalendar } from '@/components/ActivityCalendar'
import { useActivity } from '@/contexts/activity-context'
import { getDailyActivity } from '@/lib/activity-api'
import { useAuth } from '@/contexts/auth-context'
import {
  Calendar,
  TrendingUp,
  Target,
  Award,
  BarChart3,
  Clock,
  CheckCircle2,
  Zap,
  RefreshCw
} from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ActivityData {
  date: string
  jobsApplied: number
  urlsExtracted: number
  resumesEvaluated: number
  templatesGenerated: number
}

export default function ActivityPage() {
  const { user } = useAuth()
  const { stats, loading, error, refreshStats } = useActivity()
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [activities, setActivities] = useState<ActivityData[]>([])
  const [activitiesLoading, setActivitiesLoading] = useState(false)
  const [activitiesError, setActivitiesError] = useState<string | null>(null)

  // Load daily activities
  useEffect(() => {
    if (!user?.id) return

    const loadActivities = async () => {
      setActivitiesLoading(true)
      setActivitiesError(null)
      try {
        const response = await getDailyActivity(user.id)
        // Transform API response to match ActivityCalendar expected format
        const transformedActivities = response.daily_activity?.map((day: any) => ({
          date: day.date,
          jobsApplied: day.jobExtractions || 0,
          urlsExtracted: day.jobExtractions || 0, // Same as job applications for now
          resumesEvaluated: 0, // Not tracked separately yet
          templatesGenerated: day.referralEmails || 0
        })) || []
        setActivities(transformedActivities)
      } catch (err) {
        console.error('Error loading activities:', err)
        setActivitiesError('Failed to load activity data')
        setActivities([]) // Fallback to empty array
      } finally {
        setActivitiesLoading(false)
      }
    }

    loadActivities()
  }, [user?.id])

  // Manual refresh
  const handleRefresh = async () => {
    await refreshStats()
    if (user?.id) {
      setActivitiesLoading(true)
      try {
        const response = await getDailyActivity(user.id)
        const transformedActivities = response.daily_activity?.map((day: any) => ({
          date: day.date,
          jobsApplied: day.jobExtractions || 0,
          urlsExtracted: day.jobExtractions || 0, // Same as job applications for now
          resumesEvaluated: 0, // Not tracked separately yet
          templatesGenerated: day.referralEmails || 0
        })) || []
        setActivities(transformedActivities)
      } catch (err) {
        console.error('Error refreshing activities:', err)
      } finally {
        setActivitiesLoading(false)
      }
    }
  }

  const handleDateSelect = (date: string) => {
    setSelectedDate(date)
  }

  const getStreakColor = (streak: number): string => {
    if (streak === 0) return 'text-muted-foreground'
    if (streak < 3) return 'text-yellow-500'
    if (streak < 7) return 'text-orange-500'
    if (streak < 14) return 'text-red-500'
    return 'text-purple-500'
  }

  // Default values for when stats are loading or null
  const displayStats = stats || {
    currentStreak: 0,
    maxStreak: 0,
    totalTasks: 0,
    activeDays: 0,
    dailyActivity: []
  }

  // Calculate derived stats from API response
  const thisMonthApplications = displayStats.dailyActivity
    ?.filter((day: any) => {
      const dayDate = new Date(day.date)
      const now = new Date()
      return dayDate.getMonth() === now.getMonth() && dayDate.getFullYear() === now.getFullYear()
    })
    ?.reduce((sum: number, day: any) => sum + (day.jobExtractions || 0), 0) || 0

  const averagePerDay = displayStats.activeDays > 0 ? (displayStats.totalTasks / displayStats.activeDays).toFixed(1) : '0.0'

  // Find most active day (simplified)
  const mostActiveDay = 'Tuesday' // Could be calculated from dailyActivity data

  const getStreakBadge = (streak: number): { text: string, color: string } => {
    if (streak === 0) return { text: 'Start Today!', color: 'bg-muted text-muted-foreground border-border' }
    if (streak < 3) return { text: 'Getting Started', color: 'bg-yellow-500/20 text-yellow-600 border-yellow-500/30' }
    if (streak < 7) return { text: 'Building Momentum', color: 'bg-orange-500/20 text-orange-600 border-orange-500/30' }
    if (streak < 14) return { text: 'On Fire!', color: 'bg-red-500/20 text-red-600 border-red-500/30' }
    return { text: 'Legendary!', color: 'bg-purple-500/20 text-purple-600 border-purple-500/30' }
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
              <Calendar className="h-8 w-8 text-primary" />
              Activity Tracker
            </h1>
            <p className="text-muted-foreground">
              Track your job search consistency and build momentum
            </p>
            {(error || activitiesError) && (
              <p className="text-red-500 text-sm">
                {error || activitiesError}
              </p>
            )}
          </div>
          <Button
            onClick={handleRefresh}
            disabled={loading || activitiesLoading}
            variant="outline"
            size="sm"
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${(loading || activitiesLoading) ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="premium-card bg-card border-border">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-muted-foreground text-sm font-medium">Current Streak</p>
                  {loading ? (
                    <div className="h-9 bg-muted animate-pulse rounded mb-1"></div>
                  ) : (
                    <p className={`text-3xl font-bold ${getStreakColor(displayStats.currentStreak)}`}>
                      {displayStats.currentStreak}
                    </p>
                  )}
                  <p className="text-muted-foreground text-xs">
                    {displayStats.currentStreak === 1 ? 'day' : 'days'}
                  </p>
                </div>
                <div className="p-3 rounded-full bg-orange-500/20">
                  <Zap className="h-6 w-6 text-orange-500" />
                </div>
              </div>
              <div className="mt-3">
                {loading ? (
                  <div className="h-6 bg-muted animate-pulse rounded w-20"></div>
                ) : (
                  <Badge className={getStreakBadge(displayStats.currentStreak).color}>
                    {getStreakBadge(displayStats.currentStreak).text}
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="premium-card bg-card border-border">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-muted-foreground text-sm font-medium">Longest Streak</p>
                  {loading ? (
                    <div className="h-9 bg-muted animate-pulse rounded mb-1"></div>
                  ) : (
                    <p className="text-3xl font-bold text-purple-500">{displayStats.maxStreak}</p>
                  )}
                  <p className="text-muted-foreground text-xs">personal best</p>
                </div>
                <div className="p-3 rounded-full bg-purple-500/20">
                  <Award className="h-6 w-6 text-purple-500" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="premium-card bg-card border-border">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-muted-foreground text-sm font-medium">This Month</p>
                  {loading ? (
                    <div className="h-9 bg-muted animate-pulse rounded mb-1"></div>
                  ) : (
                    <p className="text-3xl font-bold text-green-500">{thisMonthApplications}</p>
                  )}
                  <p className="text-muted-foreground text-xs">applications</p>
                </div>
                <div className="p-3 rounded-full bg-green-500/20">
                  <Target className="h-6 w-6 text-green-500" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="premium-card bg-card border-border">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-muted-foreground text-sm font-medium">Daily Average</p>
                  {loading ? (
                    <div className="h-9 bg-muted animate-pulse rounded mb-1"></div>
                  ) : (
                    <p className="text-3xl font-bold text-blue-500">{averagePerDay}</p>
                  )}
                  <p className="text-muted-foreground text-xs">applications/day</p>
                </div>
                <div className="p-3 rounded-full bg-blue-500/20">
                  <BarChart3 className="h-6 w-6 text-blue-500" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Activity Calendar */}
          <div className="lg:col-span-2">
            <ActivityCalendar
              activities={activities}
              onDateSelect={handleDateSelect}
            />
          </div>

          {/* Insights Panel */}
          <div className="space-y-6">
            {/* Quick Insights */}
            <Card className="premium-card bg-card border-border">
              <CardHeader>
                <CardTitle className="text-foreground flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-primary" />
                  Insights
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg bg-muted/50 border border-border">
                  <div className="flex items-center gap-3 mb-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    <span className="text-foreground font-medium text-sm">Most Productive Day</span>
                  </div>
                  <p className="text-green-500 font-semibold">{mostActiveDay}</p>
                  <p className="text-muted-foreground text-xs mt-1">
                    You tend to apply to more jobs on {mostActiveDay}s
                  </p>
                </div>

                <div className="p-4 rounded-lg bg-muted/50 border border-border">
                  <div className="flex items-center gap-3 mb-2">
                    <Clock className="h-4 w-4 text-yellow-500" />
                    <span className="text-foreground font-medium text-sm">Consistency Score</span>
                  </div>
                  <p className="text-yellow-500 font-semibold">87%</p>
                  <p className="text-muted-foreground text-xs mt-1">
                    Great consistency! Keep it up
                  </p>
                </div>

                <div className="p-4 rounded-lg bg-muted/50 border border-border">
                  <div className="flex items-center gap-3 mb-2">
                    <Target className="h-4 w-4 text-blue-500" />
                    <span className="text-foreground font-medium text-sm">Weekly Goal</span>
                  </div>
                  <p className="text-blue-500 font-semibold">18/20 applications</p>
                  <p className="text-muted-foreground text-xs mt-1">
                    2 more to reach your weekly target
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Streak Motivation */}
            <Card className="premium-card bg-card border-border">
              <CardHeader>
                <CardTitle className="text-foreground flex items-center gap-2">
                  <Zap className="h-5 w-5 text-orange-500" />
                  Streak Motivation
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {displayStats.currentStreak > 0 ? (
                    <div className="text-center p-4 bg-gradient-to-br from-orange-500/10 to-red-500/10 border border-orange-500/20 rounded-lg">
                      <div className="text-2xl mb-2">🔥</div>
                      <p className="text-foreground font-semibold">
                        {displayStats.currentStreak} day streak!
                      </p>
                      <p className="text-muted-foreground text-sm mt-1">
                        Don&apos;t let the flame die out
                      </p>
                    </div>
                  ) : (
                    <div className="text-center p-4 bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-lg">
                      <div className="text-2xl mb-2">🚀</div>
                      <p className="text-foreground font-semibold">
                        Start your streak today!
                      </p>
                      <p className="text-muted-foreground text-sm mt-1">
                        Every journey begins with a single step
                      </p>
                    </div>
                  )}

                  <div className="space-y-2">
                    <p className="text-muted-foreground text-sm font-medium">Next Milestones:</p>
                    <div className="space-y-1">
                      {[7, 14, 30, 60].map(milestone => (
                        <div key={milestone} className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">{milestone} days</span>
                          <div className="flex-1 mx-3 bg-muted rounded-full h-1">
                            <div
                              className={`h-1 rounded-full transition-all ${displayStats.currentStreak >= milestone
                                  ? 'bg-green-500'
                                  : 'bg-muted-foreground/30'
                                }`}
                              style={{
                                width: `${Math.min(100, (displayStats.currentStreak / milestone) * 100)}%`
                              }}
                            />
                          </div>
                          {displayStats.currentStreak >= milestone ? (
                            <CheckCircle2 className="h-3 w-3 text-green-500" />
                          ) : (
                            <div className="h-3 w-3 rounded-full border border-muted-foreground/30" />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}