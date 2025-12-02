"use client"

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { useAuth } from './auth-context'
import {
    trackJobExtraction,
    trackReferralEmail,
    getActivityStats,
    ActivityStats,
    JobExtractionActivityInput,
    ReferralEmailActivityInput
} from '@/lib/activity-api'

interface ActivityContextType {
    stats: ActivityStats | null
    loading: boolean
    error: string | null
    trackJobExtractionActivity: (jobData: JobExtractionActivityInput) => Promise<void>
    trackReferralEmailActivity: (referralData: ReferralEmailActivityInput) => Promise<void>
    refreshStats: () => Promise<void>
}

const ActivityContext = createContext<ActivityContextType | undefined>(undefined)

export function ActivityProvider({ children }: { children: ReactNode }) {
    const { user } = useAuth()
    const [stats, setStats] = useState<ActivityStats | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Load activity stats
    const loadStats = useCallback(async () => {
        if (!user?.id) {
            setStats(null)
            return
        }

        setLoading(true)
        setError(null)

        try {
            const activityStats = await getActivityStats(user.id)
            setStats(activityStats)
        } catch (err) {
            console.error('Error loading activity stats:', err)
            setError('Failed to load activity statistics')
        } finally {
            setLoading(false)
        }
    }, [user?.id])

    // Track job extraction activity
    const trackJobExtractionActivity = async (jobData: JobExtractionActivityInput) => {
        if (!user?.id) return

        try {
            await trackJobExtraction(user.id, jobData)
            // Refresh stats after tracking
            await loadStats()
        } catch (err) {
            console.error('Error tracking job extraction:', err)
            setError('Failed to track job extraction activity')
        }
    }

    // Track referral email activity
    const trackReferralEmailActivity = async (referralData: ReferralEmailActivityInput) => {
        if (!user?.id) return

        try {
            await trackReferralEmail(user.id, referralData)
            // Refresh stats after tracking
            await loadStats()
        } catch (err) {
            console.error('Error tracking referral email:', err)
            setError('Failed to track referral email activity')
        }
    }

    // Refresh stats manually
    const refreshStats = async () => {
        await loadStats()
    }

    // Load stats when user changes
    useEffect(() => {
        loadStats()
    }, [loadStats])

    const value: ActivityContextType = {
        stats,
        loading,
        error,
        trackJobExtractionActivity,
        trackReferralEmailActivity,
        refreshStats
    }

    return (
        <ActivityContext.Provider value={value}>
            {children}
        </ActivityContext.Provider>
    )
}

export function useActivity() {
    const context = useContext(ActivityContext)
    if (context === undefined) {
        throw new Error('useActivity must be used within an ActivityProvider')
    }
    return context
}
