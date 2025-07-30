"use client"

import { useEffect, useState } from "react"

interface LoadingFillTextProps {
    text?: string
    className?: string
    duration?: number
}

export function LoadingFillText({
    text = "LOADING",
    className = "",
    duration = 2000
}: LoadingFillTextProps) {
    const [progress, setProgress] = useState(0)

    useEffect(() => {
        const interval = setInterval(() => {
            setProgress((prev) => {
                if (prev >= 100) {
                    return 0 // Reset for continuous animation
                }
                return prev + 1
            })
        }, duration / 100)

        return () => clearInterval(interval)
    }, [duration])

    return (
        <div className={`relative ${className}`}>
            {/* Background text */}
            <div
                className="text-5xl md:text-7xl font-black tracking-wider select-none"
                style={{
                    color: '#374151', // Darker gray for unfilled text
                    textShadow: '0 0 20px rgba(74, 92, 106, 0.3)'
                }}
            >
                {text}
            </div>

            {/* Animated filled text */}
            <div
                className="absolute inset-0 text-5xl md:text-7xl font-black tracking-wider select-none overflow-hidden"
                style={{
                    clipPath: `inset(0 ${100 - progress}% 0 0)`,
                    color: '#4a5c6a',
                    textShadow: '0 0 30px rgba(74, 92, 106, 0.8), 0 0 60px rgba(74, 92, 106, 0.4)',
                    transition: 'clip-path 0.1s ease-out'
                }}
            >
                {text}
            </div>
        </div>
    )
}

// Page transition loading component
export function PageTransitionLoading() {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm">
            <div className="text-center">
                <LoadingFillText text="LOADING" />
            </div>
        </div>
    )
}

// Custom CSS for animations
const styles = `
@keyframes progressBar {
  0% {
    transform: scaleX(0);
  }
  50% {
    transform: scaleX(0.8);
  }
  100% {
    transform: scaleX(1);
  }
}
`

// Inject styles
if (typeof document !== 'undefined') {
    const existingStyle = document.getElementById('loading-styles')
    if (!existingStyle) {
        const styleSheet = document.createElement("style")
        styleSheet.id = 'loading-styles'
        styleSheet.innerText = styles
        document.head.appendChild(styleSheet)
    }
} 