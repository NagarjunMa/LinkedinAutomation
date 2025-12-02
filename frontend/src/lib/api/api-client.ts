// Basic API client for making HTTP requests
import { createClient } from '@/lib/supabase'

class ApiClient {
    private baseUrl: string

    constructor() {
        this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    }

    private async getAuthHeaders() {
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }

        if (typeof window !== 'undefined') {
            try {
                const supabase = createClient()
                const { data: { session } } = await supabase.auth.getSession()

                if (session?.access_token) {
                    headers['Authorization'] = `Bearer ${session.access_token}`
                }
            } catch (error) {
                console.warn('Failed to get Supabase session for API client:', error)
            }
        }

        return headers
    }

    async get<T>(url: string): Promise<T> {
        const headers = await this.getAuthHeaders()
        const response = await fetch(`${this.baseUrl}${url}`, {
            method: 'GET',
            headers,
        })

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        return response.json() as Promise<T>
    }

    async post<T>(url: string, data?: Record<string, unknown>): Promise<T> {
        const headers = await this.getAuthHeaders()
        const response = await fetch(`${this.baseUrl}${url}`, {
            method: 'POST',
            headers,
            body: data ? JSON.stringify(data) : undefined,
        })

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        return response.json() as Promise<T>
    }

    async put<T>(url: string, data?: Record<string, unknown>): Promise<T> {
        const headers = await this.getAuthHeaders()
        const response = await fetch(`${this.baseUrl}${url}`, {
            method: 'PUT',
            headers,
            body: data ? JSON.stringify(data) : undefined,
        })

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        return response.json() as Promise<T>
    }

    async delete<T>(url: string): Promise<T> {
        const headers = await this.getAuthHeaders()
        const response = await fetch(`${this.baseUrl}${url}`, {
            method: 'DELETE',
            headers,
        })

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        return response.json() as Promise<T>
    }
}

export const apiClient = new ApiClient()
