// Activity tracking API service
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface ActivityRecord {
    id: string
    user_id: string
    activity_type: 'job_extraction' | 'referral_email'
    created_at: string
    metadata?: {
        job_title?: string
        company?: string
        referral_contact?: string
    }
}

export interface ActivityStats {
    totalTasks: number
    activeDays: number
    maxStreak: number
    currentStreak: number
    dailyActivity: {
        date: string
        jobExtractions: number
        referralEmails: number
        totalTasks: number
    }[]
}

// Track a new activity
export const trackActivity = async (
    userId: string,
    activityType: 'job_extraction' | 'referral_email',
    metadata?: any
): Promise<ActivityRecord> => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/activity/track`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                activity_type: activityType,
                metadata
            })
        })

        if (!response.ok) {
            throw new Error('Failed to track activity')
        }

        return await response.json()
    } catch (error) {
        console.error('Error tracking activity:', error)
        throw error
    }
}

// Get activity statistics for a user
export const getActivityStats = async (userId: string): Promise<ActivityStats> => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/activity/stats/${userId}`)

        if (!response.ok) {
            throw new Error('Failed to fetch activity stats')
        }

        return await response.json()
    } catch (error) {
        console.error('Error fetching activity stats:', error)
        throw error
    }
}

// Get daily activity data for calendar
export const getDailyActivity = async (userId: string, startDate?: string, endDate?: string) => {
    try {
        const params = new URLSearchParams()
        if (startDate) params.append('start_date', startDate)
        if (endDate) params.append('end_date', endDate)

        const response = await fetch(`${API_BASE_URL}/api/v1/activity/daily/${userId}?${params}`)

        if (!response.ok) {
            throw new Error('Failed to fetch daily activity')
        }

        return await response.json()
    } catch (error) {
        console.error('Error fetching daily activity:', error)
        throw error
    }
}

// Track job extraction activity
export const trackJobExtraction = async (userId: string, jobData: any) => {
    return trackActivity(userId, 'job_extraction', {
        job_title: jobData.title,
        company: jobData.company,
        source: jobData.source
    })
}

// Track referral email activity
export const trackReferralEmail = async (userId: string, referralData: any) => {
    return trackActivity(userId, 'referral_email', {
        referral_contact: referralData.contact,
        company: referralData.company,
        position: referralData.position
    })
}
