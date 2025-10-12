import { useState, useEffect, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'

export interface JobSearchResult {
    id: number
    title: string
    company: string
    location: string | null
    description: string | null
    requirements: string | null
    job_type: string | null
    experience_level: string | null
    salary_range: string | null
    skills: string[] | null
    application_url: string | null
    source: string | null
    source_url: string | null
    is_active: boolean
    posted_date: string | null
    extracted_date: string
    applied: boolean
    applied_date: string | null
    application_status: string
    application_notes: string | null
    application_context: string | null
    compatibility_score: number | null
    ai_insights: string | null
}

interface UseJobSearchOptions {
    query: string
    enabled?: boolean
    limit?: number
}

export function useJobSearch({ query, enabled = true, limit = 20 }: UseJobSearchOptions) {
    const [debouncedQuery, setDebouncedQuery] = useState(query)

    // Debounce the search query
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedQuery(query)
        }, 300) // 300ms delay

        return () => clearTimeout(timer)
    }, [query])

    const searchJobs = useCallback(async (searchQuery: string): Promise<JobSearchResult[]> => {
        if (!searchQuery.trim()) return []

        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

        const response = await fetch(
            `${API_URL}/api/v1/search/?q=${encodeURIComponent(searchQuery)}&limit=${limit}`,
            {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            }
        )

        if (!response.ok) {
            throw new Error(`Search failed: ${response.statusText}`)
        }

        return response.json()
    }, [limit])

    const {
        data: searchResults = [],
        isLoading,
        error,
        refetch
    } = useQuery({
        queryKey: ['job-search', debouncedQuery],
        queryFn: () => searchJobs(debouncedQuery),
        enabled: enabled && debouncedQuery.trim().length > 0,
        staleTime: 30000, // 30 seconds
        retry: 2,
    })

    return {
        searchResults,
        isLoading,
        error,
        refetch,
        hasResults: searchResults.length > 0,
        query: debouncedQuery
    }
}

export function useSearchSuggestions(query: string) {
    const [suggestions, setSuggestions] = useState<string[]>([])
    const [isLoading, setIsLoading] = useState(false)

    useEffect(() => {
        const fetchSuggestions = async () => {
            if (query.trim().length < 2) {
                setSuggestions([])
                return
            }

            setIsLoading(true)
            try {
                const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
                const response = await fetch(
                    `${API_URL}/api/v1/search/suggestions?q=${encodeURIComponent(query)}&limit=10`,
                    {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    }
                )

                if (response.ok) {
                    const data = await response.json()
                    setSuggestions(data)
                }
            } catch (error) {
                console.error('Error fetching suggestions:', error)
            } finally {
                setIsLoading(false)
            }
        }

        const timer = setTimeout(fetchSuggestions, 200) // 200ms delay for suggestions
        return () => clearTimeout(timer)
    }, [query])

    return { suggestions, isLoading }
}
