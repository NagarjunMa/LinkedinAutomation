"use client"

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Calendar, ChevronLeft, ChevronRight, Target, Fire } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ActivityData {
  date: string
  jobsApplied: number
  urlsExtracted: number
  resumesEvaluated: number
  templatesGenerated: number
}

interface ActivityCalendarProps {
  className?: string
  onDateSelect?: (date: string) => void
  activities?: ActivityData[]
}

export function ActivityCalendar({
  className,
  onDateSelect,
  activities = []
}: ActivityCalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [selectedDate, setSelectedDate] = useState<string | null>(null)

  // Get activity for a specific date
  const getActivityForDate = (date: Date): ActivityData | null => {
    const dateStr = date.toISOString().split('T')[0]
    return activities.find(activity => activity.date === dateStr) || null
  }

  // Calculate activity level for visual intensity
  const getActivityLevel = (activity: ActivityData | null): number => {
    if (!activity) return 0
    const total = activity.jobsApplied + activity.urlsExtracted + activity.resumesEvaluated + activity.templatesGenerated
    if (total === 0) return 0
    if (total <= 2) return 1
    if (total <= 5) return 2
    if (total <= 10) return 3
    return 4 // Very active
  }

  // Get activity color based on level
  const getActivityColor = (level: number): string => {
    switch (level) {
      case 0: return 'bg-primary-800 border-primary-700' // No activity
      case 1: return 'bg-green-900/30 border-green-700/50' // Light activity
      case 2: return 'bg-green-700/50 border-green-600' // Moderate activity
      case 3: return 'bg-green-500/70 border-green-400' // High activity
      case 4: return 'bg-green-400 border-green-300' // Very high activity
      default: return 'bg-primary-800 border-primary-700'
    }
  }

  // Calculate current streak
  const getCurrentStreak = (): number => {
    let streak = 0
    const today = new Date()

    for (let i = 0; i < 30; i++) {
      const checkDate = new Date(today)
      checkDate.setDate(today.getDate() - i)
      const activity = getActivityForDate(checkDate)

      if (activity && (activity.jobsApplied > 0 || activity.urlsExtracted > 0)) {
        streak++
      } else {
        break
      }
    }

    return streak
  }

  // Generate calendar grid
  const generateCalendar = () => {
    const year = currentDate.getFullYear()
    const month = currentDate.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const startDate = new Date(firstDay)
    startDate.setDate(startDate.getDate() - firstDay.getDay()) // Start from Sunday

    const weeks = []
    let currentWeek = []

    for (let i = 0; i < 42; i++) { // 6 weeks max
      const date = new Date(startDate)
      date.setDate(startDate.getDate() + i)

      if (date > lastDay && currentWeek.length > 0) break

      currentWeek.push(date)

      if (currentWeek.length === 7) {
        weeks.push(currentWeek)
        currentWeek = []
      }
    }

    return weeks
  }

  const navigateMonth = (direction: 'prev' | 'next') => {
    setCurrentDate(prev => {
      const newDate = new Date(prev)
      if (direction === 'prev') {
        newDate.setMonth(prev.getMonth() - 1)
      } else {
        newDate.setMonth(prev.getMonth() + 1)
      }
      return newDate
    })
  }

  const handleDateClick = (date: Date) => {
    const dateStr = date.toISOString().split('T')[0]
    setSelectedDate(dateStr)
    onDateSelect?.(dateStr)
  }

  const formatMonthYear = (date: Date) => {
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
  }

  const isToday = (date: Date) => {
    const today = new Date()
    return date.toDateString() === today.toDateString()
  }

  const isCurrentMonth = (date: Date) => {
    return date.getMonth() === currentDate.getMonth()
  }

  const currentStreak = getCurrentStreak()
  const totalThisMonth = activities
    .filter(activity => {
      const activityDate = new Date(activity.date)
      return activityDate.getMonth() === currentDate.getMonth() &&
             activityDate.getFullYear() === currentDate.getFullYear()
    })
    .reduce((total, activity) => total + activity.jobsApplied, 0)

  return (
    <Card className={cn("premium-card", className)}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-cream-50 flex items-center gap-2">
            <Calendar className="h-5 w-5 text-accent-400" />
            Activity Calendar
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigateMonth('prev')}
              className="border-primary-600 text-cream-300 hover:bg-primary-700"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-cream-50 font-medium px-4">
              {formatMonthYear(currentDate)}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigateMonth('next')}
              className="border-primary-600 text-cream-300 hover:bg-primary-700"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Stats Row */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Fire className="h-4 w-4 text-orange-400" />
            <span className="text-sm text-cream-300">
              Current Streak: <span className="text-orange-400 font-semibold">{currentStreak} days</span>
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-green-400" />
            <span className="text-sm text-cream-300">
              This Month: <span className="text-green-400 font-semibold">{totalThisMonth} applications</span>
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-6">
        {/* Calendar Grid */}
        <div className="space-y-2">
          {/* Day Headers */}
          <div className="grid grid-cols-7 gap-1 mb-4">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="text-center text-sm font-medium text-cream-400 py-2">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar Days */}
          {generateCalendar().map((week, weekIndex) => (
            <div key={weekIndex} className="grid grid-cols-7 gap-1">
              {week.map((date, dayIndex) => {
                const activity = getActivityForDate(date)
                const activityLevel = getActivityLevel(activity)
                const dateStr = date.toISOString().split('T')[0]
                const isSelected = selectedDate === dateStr

                return (
                  <button
                    key={dayIndex}
                    onClick={() => handleDateClick(date)}
                    className={cn(
                      "relative h-12 w-full rounded-lg border text-sm font-medium transition-all hover:scale-105",
                      getActivityColor(activityLevel),
                      isCurrentMonth(date) ? "text-cream-50" : "text-cream-500 opacity-50",
                      isToday(date) && "ring-2 ring-accent-400",
                      isSelected && "ring-2 ring-blue-400",
                      "hover:brightness-110"
                    )}
                  >
                    <span className="relative z-10">{date.getDate()}</span>

                    {/* Activity indicators */}
                    {activity && activityLevel > 0 && (
                      <div className="absolute inset-x-0 bottom-1 flex justify-center">
                        <div className="flex gap-0.5">
                          {activity.jobsApplied > 0 && (
                            <div className="w-1 h-1 bg-blue-400 rounded-full"></div>
                          )}
                          {activity.urlsExtracted > 0 && (
                            <div className="w-1 h-1 bg-purple-400 rounded-full"></div>
                          )}
                          {activity.resumesEvaluated > 0 && (
                            <div className="w-1 h-1 bg-yellow-400 rounded-full"></div>
                          )}
                          {activity.templatesGenerated > 0 && (
                            <div className="w-1 h-1 bg-pink-400 rounded-full"></div>
                          )}
                        </div>
                      </div>
                    )}
                  </button>
                )
              })}
            </div>
          ))}
        </div>

        {/* Activity Legend */}
        <div className="mt-6 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-cream-400">Activity Level</span>
            <div className="flex items-center gap-1">
              <span className="text-xs text-cream-500">Less</span>
              {[0, 1, 2, 3, 4].map(level => (
                <div
                  key={level}
                  className={cn("w-3 h-3 rounded border", getActivityColor(level))}
                />
              ))}
              <span className="text-xs text-cream-500">More</span>
            </div>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
              <span className="text-cream-400">Job Applications</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
              <span className="text-cream-400">URLs Extracted</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
              <span className="text-cream-400">Resume Evaluations</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-pink-400 rounded-full"></div>
              <span className="text-cream-400">Referral Templates</span>
            </div>
          </div>
        </div>

        {/* Selected Date Details */}
        {selectedDate && (() => {
          const selectedActivity = activities.find(a => a.date === selectedDate)
          const selectedDateObj = new Date(selectedDate)

          return (
            <div className="mt-6 p-4 rounded-lg bg-primary-800/50 border border-primary-600">
              <h4 className="text-cream-50 font-medium mb-3">
                {selectedDateObj.toLocaleDateString('en-US', {
                  weekday: 'long',
                  month: 'long',
                  day: 'numeric'
                })}
              </h4>

              {selectedActivity ? (
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-400">{selectedActivity.jobsApplied}</div>
                    <div className="text-xs text-cream-400">Applications</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-400">{selectedActivity.urlsExtracted}</div>
                    <div className="text-xs text-cream-400">URLs Extracted</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-400">{selectedActivity.resumesEvaluated}</div>
                    <div className="text-xs text-cream-400">Evaluations</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-pink-400">{selectedActivity.templatesGenerated}</div>
                    <div className="text-xs text-cream-400">Templates</div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-4">
                  <div className="text-cream-400 text-sm">No activity recorded for this date</div>
                  <div className="text-cream-500 text-xs mt-1">Start applying to jobs to track your progress!</div>
                </div>
              )}
            </div>
          )
        })()}
      </CardContent>
    </Card>
  )
}

export default ActivityCalendar