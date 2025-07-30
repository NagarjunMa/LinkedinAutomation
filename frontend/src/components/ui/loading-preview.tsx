"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { LoadingFillText, PageTransitionLoading } from "./loading-fill-text"

export function LoadingPreview() {
    const [showLoading, setShowLoading] = useState(false)

    const triggerLoading = () => {
        setShowLoading(true)
        setTimeout(() => {
            setShowLoading(false)
        }, 3000) // Show for 3 seconds
    }

    return (
        <div className="p-8 space-y-6">
            <div className="text-center space-y-4">
                <h2 className="text-2xl font-bold">Loading Screen Preview</h2>
                <p className="text-gray-600">Click the button below to see the new loading screen with color #4a5c6a</p>

                <Button onClick={triggerLoading} className="bg-blue-600 hover:bg-blue-700">
                    Trigger Loading Screen
                </Button>
            </div>

            {/* Standalone loading text demo */}
            <div className="bg-gray-900 p-8 rounded-lg text-center">
                <h3 className="text-white mb-4">Loading Text Effect (Standalone)</h3>
                <LoadingFillText text="LOADING" />
            </div>

            {/* Color preview */}
            <div className="p-4 border rounded-lg">
                <h3 className="font-medium mb-3">Color Information:</h3>
                <div className="flex items-center gap-4">
                    <div
                        className="w-16 h-16 rounded border"
                        style={{ backgroundColor: '#4a5c6a' }}
                    ></div>
                    <div>
                        <p className="font-mono text-sm">Hex: #4a5c6a</p>
                        <p className="text-sm text-gray-600">RGB: 74, 92, 106</p>
                        <p className="text-sm text-gray-600">Muted blue-gray tone</p>
                    </div>
                </div>
            </div>

            {/* Full loading overlay */}
            {showLoading && <PageTransitionLoading />}
        </div>
    )
} 