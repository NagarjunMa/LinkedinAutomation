"use client"

import React, { createContext, useContext, useCallback, useEffect, useState } from 'react'
import { JobStats, TimeRange } from '../types/stats'
import { fetchJobStats, fetchRecentApplications, RecentApplication } from '../lib/api'

interface DashboardContextType {
    stats: JobStats | null
    recentApplications: RecentApplication[]
    loading: boolean
    error: string | null
    timeRange: TimeRange
    refreshData: () => Promise<void>
    updateJobApplication: (jobId: string, applied: boolean) => void
    setTimeRange: (range: TimeRange) => void
}

const DashboardContext = createContext<DashboardContextType | undefined>(undefined)

export function DashboardProvider({ children }: { children: React.ReactNode }) {
    const [stats, setStats] = useState<JobStats | null>(null)
    const [recentApplications, setRecentApplications] = useState<RecentApplication[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [timeRange, setTimeRange] = useState<TimeRange>('last_30_days')

    const refreshData = useCallback(async () => {
        try {
            setError(null)
            setLoading(true)

            console.log('Fetching data for time range:', timeRange)

            const [statsData, applicationsData] = await Promise.all([
                fetchJobStats(timeRange),
                fetchRecentApplications()
            ])

            console.log('Stats data received:', statsData)
            console.log('Applications data received:', applicationsData)

            setStats(statsData)
            setRecentApplications(applicationsData)
        } catch (err) {
            console.error('Error fetching dashboard data:', err)
            setError(err instanceof Error ? err.message : 'Failed to fetch data')
        } finally {
            setLoading(false)
        }
    }, [timeRange])

    const updateJobApplication = useCallback((jobId: string, applied: boolean) => {
        // Update stats optimistically
        setStats(prevStats => {
            if (!prevStats) return prevStats

            const change = applied ? 1 : -1
            return {
                ...prevStats,
                appliedJobs: Math.max(0, prevStats.appliedJobs + change),
                pendingJobs: Math.max(0, prevStats.pendingJobs - change)
            }
        })

        // If job was applied, refresh recent applications to show it
        if (applied) {
            setTimeout(() => {
                fetchRecentApplications().then(setRecentApplications).catch(console.error)
            }, 500) // Small delay to ensure backend is updated
        }
    }, [])

    const handleTimeRangeChange = useCallback((range: TimeRange) => {
        console.log('Time range changed to:', range)
        setTimeRange(range)
    }, [])

    useEffect(() => {
        refreshData()

        // Set up periodic refresh every 30 seconds
        const interval = setInterval(refreshData, 30000)

        return () => clearInterval(interval)
    }, [refreshData])

    return (
        <DashboardContext.Provider value={{
            stats,
            recentApplications,
            loading,
            error,
            timeRange,
            refreshData,
            updateJobApplication,
            setTimeRange: handleTimeRangeChange
        }}>
            {children}
        </DashboardContext.Provider>
    )
}

export function useDashboard() {
    const context = useContext(DashboardContext)
    if (context === undefined) {
        throw new Error('useDashboard must be used within a DashboardProvider')
    }
    return context
} 