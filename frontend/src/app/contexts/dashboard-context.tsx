"use client"

import React, { createContext, useContext, useCallback, useEffect, useState } from 'react'
import { JobStats, TimeRange } from '../types/stats'
import { fetchJobStats, fetchRecentApplications } from '../lib/api/jobs'
import { profileApi } from '../lib/api/profile'
import type { RecentApplication, UserProfile } from '../lib/api/types'
import { useAuth } from '../../contexts/auth-context'

interface DashboardContextType {
    stats: JobStats | null
    recentApplications: RecentApplication[]
    userProfile: UserProfile | null
    loading: boolean
    error: string | null
    timeRange: TimeRange
    refreshData: () => Promise<void>
    updateJobApplication: (jobId: string, applied: boolean) => void
    setTimeRange: (range: TimeRange) => void
    refreshAppliedJobs: () => void
    refreshAppliedJobsKey: number
}

const DashboardContext = createContext<DashboardContextType | undefined>(undefined)

export function DashboardProvider({ children }: { children: React.ReactNode }) {
    const { user } = useAuth()
    const [stats, setStats] = useState<JobStats | null>(null)
    const [recentApplications, setRecentApplications] = useState<RecentApplication[]>([])
    const [userProfile, setUserProfile] = useState<UserProfile | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [timeRange, setTimeRange] = useState<TimeRange>('last_30_days')
    const [refreshAppliedJobsKey, setRefreshAppliedJobsKey] = useState(0)

    const refreshData = useCallback(async () => {
        if (!user?.id) {
            setLoading(false)
            return
        }

        try {
            setError(null)
            setLoading(true)

            console.log('Fetching data progressively for time range:', timeRange, 'for user:', user.id)

            // Progressive loading - fetch critical data first, then secondary data

            // 1. Fetch stats first (most critical for dashboard)
            try {
                const statsData = await fetchJobStats(timeRange)
                console.log('Stats data received:', statsData)
                setStats(statsData)
            } catch (statsError) {
                console.warn('Stats fetch failed, continuing with other data:', statsError)
                setStats(null)
            }

            // 2. Fetch applications and profile in parallel (less critical)
            const secondaryPromises: [
                Promise<RecentApplication[]>,
                Promise<UserProfile | null>
            ] = [
                fetchRecentApplications().catch(error => {
                    console.warn('Applications fetch failed:', error)
                    return []
                }),
                profileApi.getProfile(user.id).catch(error => {
                    console.warn('Profile fetch failed:', error)
                    return null
                })
            ]

            const [applicationsData, profileData] = await Promise.all(secondaryPromises)

            console.log('Applications data received:', applicationsData)
            console.log('Profile data received:', profileData)

            setRecentApplications(applicationsData || [])
            setUserProfile(profileData)

        } catch (err) {
            console.error('Error during progressive data fetch:', err)
            setError(err instanceof Error ? err.message : 'Failed to fetch data')
        } finally {
            setLoading(false)
        }
    }, [timeRange, user?.id])

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

    const refreshAppliedJobs = useCallback(() => {
        setRefreshAppliedJobsKey(prev => prev + 1)
    }, [])

    useEffect(() => {
        refreshData()

        // Set up intelligent refresh - only when tab is active and user is engaged
        let interval: NodeJS.Timeout | null = null

        const startRefresh = () => {
            if (interval) clearInterval(interval)
            // Refresh every 5 minutes when active, instead of 30 seconds
            interval = setInterval(refreshData, 300000) // 5 minutes
        }

        const stopRefresh = () => {
            if (interval) {
                clearInterval(interval)
                interval = null
            }
        }

        // Only refresh when page is visible
        const handleVisibilityChange = () => {
            if (document.hidden) {
                stopRefresh()
            } else {
                refreshData() // Refresh immediately when tab becomes active
                startRefresh()
            }
        }

        // Start initial refresh cycle
        startRefresh()

        // Listen for visibility changes
        document.addEventListener('visibilitychange', handleVisibilityChange)

        return () => {
            stopRefresh()
            document.removeEventListener('visibilitychange', handleVisibilityChange)
        }
    }, [refreshData])

    return (
        <DashboardContext.Provider value={{
            stats,
            recentApplications,
            userProfile,
            loading,
            error,
            timeRange,
            refreshData,
            updateJobApplication,
            setTimeRange: handleTimeRangeChange,
            refreshAppliedJobs,
            refreshAppliedJobsKey
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
