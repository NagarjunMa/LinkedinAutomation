"use client"

import React, { useState, useRef, useEffect } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { MapPin, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { searchLocations } from "@/lib/location-data"

interface LocationAutoCompleteProps {
    value: string
    onChange: (value: string) => void
    placeholder?: string
    id?: string
    className?: string
}

export function LocationAutoComplete({
    value,
    onChange,
    placeholder = "Search for a location...",
    id,
    className
}: LocationAutoCompleteProps) {
    const [suggestions, setSuggestions] = useState<string[]>([])
    const [showSuggestions, setShowSuggestions] = useState(false)
    const [highlightedIndex, setHighlightedIndex] = useState(-1)
    const containerRef = useRef<HTMLDivElement>(null)
    const inputRef = useRef<HTMLInputElement>(null)

    // Update suggestions when value changes
    useEffect(() => {
        if (value.trim()) {
            const results = searchLocations(value, 8)
            setSuggestions(results)
            setShowSuggestions(results.length > 0)
            setHighlightedIndex(-1)
        } else {
            setSuggestions([])
            setShowSuggestions(false)
        }
    }, [value])

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = e.target.value
        onChange(newValue)
    }

    const handleInputFocus = () => {
        if (value.trim() && suggestions.length > 0) {
            setShowSuggestions(true)
        }
    }

    const handleInputBlur = () => {
        // Delay hiding suggestions to allow for clicks
        setTimeout(() => {
            setShowSuggestions(false)
            setHighlightedIndex(-1)
        }, 200)
    }

    const handleSuggestionClick = (suggestion: string) => {
        onChange(suggestion)
        setShowSuggestions(false)
        setHighlightedIndex(-1)
        inputRef.current?.focus()
    }

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (!showSuggestions || suggestions.length === 0) return

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault()
                setHighlightedIndex(prev =>
                    prev < suggestions.length - 1 ? prev + 1 : prev
                )
                break
            case 'ArrowUp':
                e.preventDefault()
                setHighlightedIndex(prev => prev > 0 ? prev - 1 : -1)
                break
            case 'Enter':
                e.preventDefault()
                if (highlightedIndex >= 0) {
                    handleSuggestionClick(suggestions[highlightedIndex])
                }
                break
            case 'Escape':
                setShowSuggestions(false)
                setHighlightedIndex(-1)
                inputRef.current?.blur()
                break
        }
    }

    const clearInput = () => {
        onChange("")
        setShowSuggestions(false)
        setHighlightedIndex(-1)
        inputRef.current?.focus()
    }

    return (
        <div ref={containerRef} className={cn("relative", className)}>
            <div className="relative">
                <MapPin className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                    ref={inputRef}
                    id={id}
                    value={value}
                    onChange={handleInputChange}
                    onFocus={handleInputFocus}
                    onBlur={handleInputBlur}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder}
                    className="pl-10 pr-10"
                    autoComplete="off"
                />
                {value && (
                    <button
                        type="button"
                        onClick={clearInput}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    >
                        <X className="h-4 w-4" />
                    </button>
                )}
            </div>

            {/* Inline Suggestions */}
            {showSuggestions && suggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 z-50 mt-1 bg-background border border-border rounded-md shadow-lg max-h-60 overflow-y-auto">
                    {suggestions.map((suggestion, index) => (
                        <div
                            key={suggestion}
                            className={cn(
                                "px-4 py-2 cursor-pointer flex items-center gap-2 text-sm transition-colors",
                                index === highlightedIndex
                                    ? "bg-accent text-accent-foreground"
                                    : "hover:bg-muted"
                            )}
                            onClick={() => handleSuggestionClick(suggestion)}
                            onMouseEnter={() => setHighlightedIndex(index)}
                        >
                            <MapPin className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                            <span className="truncate">{suggestion}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
