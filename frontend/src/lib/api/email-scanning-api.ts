import { apiClient } from './api-client'

export interface EmailScanSettings {
    email_scan_frequency: 'daily' | 'weekly' | 'bi-weekly' | 'monthly'
    email_scan_time: string
    email_scan_timezone: string
    email_tracking_enabled: boolean
}

export interface EmailScanStatus {
    last_full_scan: string | null
    last_urgent_scan: string | null
    next_scheduled_scan: string | null
    emails_processed_today: number
    urgent_emails_found_today: number
    status_updates_made_today: number
}

export interface EmailScanMetrics {
    emails_sent: number
    emails_processed: number
    status_updates_made: number
    urgent_emails_found: number
    weekly_change_percentage: number
    processing_status: 'idle' | 'processing' | 'error'
}

export interface EmailScanHistory {
    id: string
    scan_type: 'full' | 'urgent'
    emails_processed: number
    status_updates_made: number
    urgent_emails_found: number
    scan_started_at: string
    scan_completed_at: string | null
    errors: any[] | null
}

class EmailScanningApi {
    private baseUrl = '/api/v1/email-scanning'

    async getSettings(userId: string): Promise<EmailScanSettings & EmailScanStatus> {
        const response = await apiClient.get(`${this.baseUrl}/settings/${userId}`)
        return response
    }

    async updateSettings(userId: string, settings: Partial<EmailScanSettings>): Promise<void> {
        await apiClient.put(`${this.baseUrl}/settings`, {
            user_id: userId,
            ...settings
        })
    }

    async getScanStatus(userId: string): Promise<EmailScanStatus> {
        const response = await apiClient.get(`${this.baseUrl}/scan-status`)
        return response
    }

    async getPerformanceMetrics(userId: string, days: number = 7): Promise<EmailScanMetrics> {
        const response = await apiClient.get(`${this.baseUrl}/performance-metrics?days=${days}`)
        return response
    }

    async getScanHistory(userId: string, limit: number = 10): Promise<EmailScanHistory[]> {
        const response = await apiClient.get(`${this.baseUrl}/scan-history?limit=${limit}`)
        return response
    }

    async testEmailForwarding(userId: string): Promise<{ success: boolean; message: string }> {
        const response = await apiClient.post(`${this.baseUrl}/test-forwarding`)
        return response
    }

    async getSystemHealth(userId: string): Promise<{
        status: 'healthy' | 'warning' | 'error'
        last_scan: string | null
        next_scan: string | null
        errors: string[]
    }> {
        const response = await apiClient.get(`${this.baseUrl}/system-health`)
        return response
    }
}

export const emailScanningApi = new EmailScanningApi()
