"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface JobExtractionDay {
  date: number
  jobsExtracted: number
  applicationsAdded: number
}

interface JobExtractionCalendarProps {
  className?: string
}

export function JobExtractionCalendar({ className }: JobExtractionCalendarProps) {
  const [currentDate, _setCurrentDate] = useState(new Date())
  const [extractionData, setExtractionData] = useState<JobExtractionDay[]>([])
  const [totalStats, setTotalStats] = useState({
    totalExtractions: 0,
    totalApplications: 0,
    activeDays: 0
  })

  // Fetch data from API
  useEffect(() => {
    const fetchCalendarData = async () => {
      try {
        const year = currentDate.getFullYear()
        const month = currentDate.getMonth() + 1 // JavaScript months are 0-indexed

        const response = await fetch(
          `/api/v1/stats/job-extraction-calendar?year=${year}&month=${month}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        )

        if (response.ok) {
          const result = await response.json()
          if (result.status === 'success') {
            const apiData = result.data.extraction_days.map((day: Record<string, unknown>) => ({
              date: day.date,
              jobsExtracted: day.jobs_extracted,
              applicationsAdded: day.applications_added
            }))

            setExtractionData(apiData)
            setTotalStats({
              totalExtractions: result.data.summary.total_extractions,
              totalApplications: result.data.summary.total_applications,
              activeDays: result.data.summary.active_days
            })
          }
        } else {
          // Fallback to empty state if API fails
          console.log('API failed, using empty state')
          setExtractionData([])
          setTotalStats({
            totalExtractions: 0,
            totalApplications: 0,
            activeDays: 0
          })
        }
      } catch (error) {
        console.log('Error fetching calendar data, using empty state:', error)
        setExtractionData([])
        setTotalStats({
          totalExtractions: 0,
          totalApplications: 0,
          activeDays: 0
        })
      }
    }

    fetchCalendarData()
  }, [currentDate])

  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ]

  const daysOfWeek = ["S", "M", "T", "W", "T", "F", "S"]

  const year = currentDate.getFullYear()
  const month = currentDate.getMonth()
  const today = new Date()
  const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month
  const todayDate = isCurrentMonth ? today.getDate() : null

  // Get first day of month and number of days
  const firstDayOfMonth = new Date(year, month, 1).getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const daysInPrevMonth = new Date(year, month, 0).getDate()

  // Create calendar grid
  const calendarDays = []

  // Previous month's trailing days
  for (let i = firstDayOfMonth - 1; i >= 0; i--) {
    calendarDays.push({
      date: daysInPrevMonth - i,
      isCurrentMonth: false,
      isPrevMonth: true
    })
  }

  // Current month's days
  for (let date = 1; date <= daysInMonth; date++) {
    const extractionDay = extractionData.find(d => d.date === date)
    calendarDays.push({
      date,
      isCurrentMonth: true,
      isPrevMonth: false,
      extractionData: extractionDay,
      isToday: date === todayDate
    })
  }

  // Next month's leading days
  const remainingCells = 42 - calendarDays.length
  for (let date = 1; date <= remainingCells; date++) {
    calendarDays.push({
      date,
      isCurrentMonth: false,
      isPrevMonth: false
    })
  }

  const getIntensityColor = (jobsExtracted: number) => {
    if (jobsExtracted >= 25) return "bg-orange-500"
    if (jobsExtracted >= 20) return "bg-orange-400"
    if (jobsExtracted >= 15) return "bg-orange-300"
    if (jobsExtracted >= 10) return "bg-orange-200"
    return "bg-orange-100"
  }

  return (
    <Card className={`bg-gray-900 border-gray-800 text-white ${className}`}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white text-lg font-medium">Overview</CardTitle>
          <div className="text-gray-400 text-sm">
            {monthNames[month]} {year}
          </div>
        </div>

        {/* Stats Row */}
        <div className="flex items-center justify-between pt-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-white">{totalStats.activeDays}</div>
            <div className="text-xs text-gray-400">Active Days</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-white">{totalStats.totalExtractions}</div>
            <div className="text-xs text-gray-400">Jobs Extracted</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-white">{totalStats.totalApplications}</div>
            <div className="text-xs text-gray-400">Applications</div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {/* Days of week header */}
        <div className="grid grid-cols-7 gap-1 mb-2">
          {daysOfWeek.map((day) => (
            <div key={day} className="text-center text-xs text-gray-500 font-medium py-2">
              {day}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
        <div className="grid grid-cols-7 gap-1">
          {calendarDays.map((day, index) => {
            const hasExtraction = day.extractionData
            const isToday = day.isToday

            return (
              <div
                key={index}
                className={`
                  relative w-8 h-8 flex items-center justify-center text-sm rounded-full
                  ${!day.isCurrentMonth ? 'text-gray-600' : 'text-gray-300'}
                  ${isToday && !hasExtraction ? 'border-2 border-orange-500' : ''}
                  ${hasExtraction ? `${getIntensityColor(hasExtraction.jobsExtracted)} text-gray-900 font-medium` : ''}
                  ${isToday && hasExtraction ? 'ring-2 ring-orange-500 ring-offset-2 ring-offset-gray-900' : ''}
                `}
                title={
                  hasExtraction
                    ? `${day.date}: ${hasExtraction.jobsExtracted} jobs extracted, ${hasExtraction.applicationsAdded} applications added`
                    : isToday
                    ? 'Today'
                    : `${day.date}`
                }
              >
                {day.date}
              </div>
            )
          })}
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-4 mt-4 pt-4 border-t border-gray-800">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full border-2 border-orange-500"></div>
            <span className="text-xs text-gray-400">Today</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-300"></div>
            <span className="text-xs text-gray-400">Activity</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}