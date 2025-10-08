"use client"

import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { useEffect, useState } from "react"

export function ThemeToggle() {
    const { theme, setTheme } = useTheme()
    const [mounted, setMounted] = useState(false)
    const [isAnimating, setIsAnimating] = useState(false)

    // useEffect only runs on the client, so now we can safely show the UI
    useEffect(() => {
        setMounted(true)
    }, [])

    const toggleTheme = () => {
        setIsAnimating(true)
        setTheme(theme === "dark" ? "light" : "dark")

        // Reset animation state after animation completes
        setTimeout(() => {
            setIsAnimating(false)
        }, 300)
    }

    if (!mounted) {
        return (
            <Button
                variant="ghost"
                size="sm"
                className="h-9 w-9 p-0 text-muted-foreground hover:text-foreground hover:bg-accent transition-all duration-200"
            >
                <Sun className="h-4 w-4" />
            </Button>
        )
    }

    const isDark = theme === "dark"

    return (
        <Button
            variant="ghost"
            size="sm"
            onClick={toggleTheme}
            className={`h-9 w-9 p-0 text-muted-foreground hover:text-foreground hover:bg-accent transition-all duration-200 relative overflow-hidden ${isAnimating ? 'scale-95' : 'scale-100'
                }`}
        >
            <Sun
                className={`h-4 w-4 absolute transition-all duration-300 ${isDark
                        ? 'rotate-90 scale-0 opacity-0'
                        : 'rotate-0 scale-100 opacity-100'
                    }`}
            />
            <Moon
                className={`h-4 w-4 absolute transition-all duration-300 ${isDark
                        ? 'rotate-0 scale-100 opacity-100'
                        : '-rotate-90 scale-0 opacity-0'
                    }`}
            />
            <span className="sr-only">Toggle theme</span>
        </Button>
    )
}
