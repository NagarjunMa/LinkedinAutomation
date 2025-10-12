"use client"

import { useState, useEffect, useRef } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
    Search,
    X,
    Clock,
    TrendingUp,
    Building2,
    MapPin,
    Briefcase
} from "lucide-react"
import { useJobSearch, useSearchSuggestions } from "@/hooks/use-job-search"
import { JobSearchResults } from "@/components/job-search-results"
import { cn } from "@/lib/utils"

interface JobSearchModalProps {
    isOpen: boolean
    onClose: () => void
    initialQuery?: string
}

export function JobSearchModal({ isOpen, onClose, initialQuery = "" }: JobSearchModalProps) {
    const [searchQuery, setSearchQuery] = useState(initialQuery)
    const [showSuggestions, setShowSuggestions] = useState(false)
    const [recentSearches, setRecentSearches] = useState<string[]>([])
    const inputRef = useRef<HTMLInputElement>(null)

    const { searchResults, isLoading, hasResults } = useJobSearch({
        query: searchQuery,
        enabled: isOpen
    })

    const { suggestions, isLoading: suggestionsLoading } = useSearchSuggestions(
        showSuggestions ? searchQuery : ""
    )

    // Load recent searches from localStorage
    useEffect(() => {
        const saved = localStorage.getItem('job-search-history')
        if (saved) {
            try {
                setRecentSearches(JSON.parse(saved))
            } catch (error) {
                console.error('Error loading search history:', error)
            }
        }
    }, [])

    // Save search to history
    const saveToHistory = (query: string) => {
        if (!query.trim()) return

        const newHistory = [query, ...recentSearches.filter(item => item !== query)].slice(0, 10)
        setRecentSearches(newHistory)
        localStorage.setItem('job-search-history', JSON.stringify(newHistory))
    }

    // Handle search
    const handleSearch = (query: string) => {
        setSearchQuery(query)
        setShowSuggestions(false)
        if (query.trim()) {
            saveToHistory(query)
        }
    }

    // Handle suggestion click
    const handleSuggestionClick = (suggestion: string) => {
        handleSearch(suggestion)
    }

    // Handle recent search click
    const handleRecentClick = (query: string) => {
        handleSearch(query)
    }

    // Clear search
    const clearSearch = () => {
        setSearchQuery("")
        setShowSuggestions(false)
        inputRef.current?.focus()
    }

    // Clear recent searches
    const clearRecentSearches = () => {
        setRecentSearches([])
        localStorage.removeItem('job-search-history')
    }

    // Focus input when modal opens
    useEffect(() => {
        if (isOpen && inputRef.current) {
            inputRef.current.focus()
        }
    }, [isOpen])

    // Close modal on escape
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isOpen) {
                onClose()
            }
        }

        document.addEventListener('keydown', handleEscape)
        return () => document.removeEventListener('keydown', handleEscape)
    }, [isOpen, onClose])

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-4xl max-h-[80vh] p-0">
                <DialogHeader className="p-6 pb-4 border-b">
                    <DialogTitle className="flex items-center space-x-2">
                        <Search className="h-5 w-5" />
                        <span>Search Jobs</span>
                    </DialogTitle>
                </DialogHeader>

                <div className="flex flex-col h-full">
                    {/* Search Input */}
                    <div className="p-6 pb-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                            <Input
                                ref={inputRef}
                                placeholder="Search by company, job title, location, or skills..."
                                value={searchQuery}
                                onChange={(e) => {
                                    setSearchQuery(e.target.value)
                                    setShowSuggestions(e.target.value.length > 0)
                                }}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                        handleSearch(searchQuery)
                                    }
                                }}
                                className="pl-10 pr-10 h-12 text-lg"
                            />
                            {searchQuery && (
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={clearSearch}
                                    className="absolute right-2 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0"
                                >
                                    <X className="h-4 w-4" />
                                </Button>
                            )}
                        </div>

                        {/* Suggestions Dropdown */}
                        {showSuggestions && (suggestions.length > 0 || recentSearches.length > 0) && (
                            <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto">
                                {/* Recent Searches */}
                                {recentSearches.length > 0 && searchQuery.length === 0 && (
                                    <div className="p-2">
                                        <div className="flex items-center justify-between px-2 py-1">
                                            <span className="text-xs font-medium text-gray-500">Recent searches</span>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={clearRecentSearches}
                                                className="h-6 px-2 text-xs"
                                            >
                                                Clear
                                            </Button>
                                        </div>
                                        {recentSearches.map((query, index) => (
                                            <button
                                                key={index}
                                                onClick={() => handleRecentClick(query)}
                                                className="w-full text-left px-2 py-2 hover:bg-gray-100 rounded text-sm flex items-center space-x-2"
                                            >
                                                <Clock className="h-4 w-4 text-gray-400" />
                                                <span>{query}</span>
                                            </button>
                                        ))}
                                    </div>
                                )}

                                {/* Search Suggestions */}
                                {suggestions.length > 0 && (
                                    <div className="p-2">
                                        <div className="px-2 py-1">
                                            <span className="text-xs font-medium text-gray-500">Suggestions</span>
                                        </div>
                                        {suggestions.map((suggestion, index) => (
                                            <button
                                                key={index}
                                                onClick={() => handleSuggestionClick(suggestion)}
                                                className="w-full text-left px-2 py-2 hover:bg-gray-100 rounded text-sm flex items-center space-x-2"
                                            >
                                                <TrendingUp className="h-4 w-4 text-gray-400" />
                                                <span>{suggestion}</span>
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Search Results */}
                    <div className="flex-1 overflow-y-auto px-6 pb-6">
                        {searchQuery.trim() ? (
                            <JobSearchResults
                                results={searchResults}
                                isLoading={isLoading}
                                query={searchQuery}
                                onJobClick={(job) => {
                                    console.log('Job clicked:', job)
                                    // You can add navigation logic here
                                }}
                            />
                        ) : (
                            <div className="space-y-6">
                                {/* Quick Search Categories */}
                                <div>
                                    <h3 className="text-lg font-semibold mb-4">Quick Search</h3>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                        {[
                                            { icon: Building2, label: "Companies", query: "tech companies" },
                                            { icon: MapPin, label: "Locations", query: "remote jobs" },
                                            { icon: Briefcase, label: "Job Types", query: "full-time" },
                                            { icon: TrendingUp, label: "Trending", query: "software engineer" }
                                        ].map(({ icon: Icon, label, query }) => (
                                            <Button
                                                key={label}
                                                variant="outline"
                                                onClick={() => handleSearch(query)}
                                                className="h-20 flex flex-col items-center space-y-2"
                                            >
                                                <Icon className="h-6 w-6" />
                                                <span className="text-sm">{label}</span>
                                            </Button>
                                        ))}
                                    </div>
                                </div>

                                {/* Recent Searches */}
                                {recentSearches.length > 0 && (
                                    <div>
                                        <h3 className="text-lg font-semibold mb-4">Recent Searches</h3>
                                        <div className="flex flex-wrap gap-2">
                                            {recentSearches.map((query, index) => (
                                                <Badge
                                                    key={index}
                                                    variant="secondary"
                                                    className="cursor-pointer hover:bg-gray-200"
                                                    onClick={() => handleRecentClick(query)}
                                                >
                                                    {query}
                                                </Badge>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    )
}
