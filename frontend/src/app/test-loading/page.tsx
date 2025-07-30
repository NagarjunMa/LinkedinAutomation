"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { LoadingFillText, PageTransitionLoading } from "@/components/ui/loading-fill-text"

export default function TestLoadingPage() {
    const [showFullScreen, setShowFullScreen] = useState(false)

    const triggerFullScreenLoading = () => {
        setShowFullScreen(true)
        setTimeout(() => {
            setShowFullScreen(false)
        }, 4000) // Show for 4 seconds
    }

    return (
        <div className="min-h-screen bg-white p-8">
            <div className="max-w-4xl mx-auto space-y-12">
                <div className="text-center space-y-4">
                    <h1 className="text-4xl font-bold">Loading Animation Test</h1>
                    <p className="text-lg text-gray-600">
                        Test the loading animations with your custom color #4a5c6a
                    </p>
                </div>

                {/* Standalone Loading Text */}
                <div className="space-y-4">
                    <h2 className="text-2xl font-semibold">Standalone Loading Text</h2>
                    <div className="bg-gray-900 p-12 rounded-lg flex justify-center">
                        <LoadingFillText text="LOADING" />
                    </div>
                </div>

                {/* Different text examples */}
                <div className="space-y-4">
                    <h2 className="text-2xl font-semibold">Different Text Examples</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-gray-900 p-8 rounded-lg flex justify-center">
                            <LoadingFillText text="PLEASE WAIT" />
                        </div>
                        <div className="bg-gray-900 p-8 rounded-lg flex justify-center">
                            <LoadingFillText text="PROCESSING" />
                        </div>
                    </div>
                </div>

                {/* Full screen test */}
                <div className="space-y-4">
                    <h2 className="text-2xl font-semibold">Full Screen Loading Test</h2>
                    <div className="text-center">
                        <Button
                            onClick={triggerFullScreenLoading}
                            size="lg"
                            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3"
                        >
                            Trigger Full Screen Loading (4 seconds)
                        </Button>
                    </div>
                </div>

                {/* Color Reference */}
                <div className="space-y-4">
                    <h2 className="text-2xl font-semibold">Color Reference</h2>
                    <div className="bg-gray-100 p-6 rounded-lg">
                        <div className="flex items-center gap-4">
                            <div
                                className="w-20 h-20 rounded-lg border-2 border-gray-300"
                                style={{ backgroundColor: '#4a5c6a' }}
                            ></div>
                            <div>
                                <p className="font-mono text-lg font-bold">#4a5c6a</p>
                                <p className="text-gray-600">RGB(74, 92, 106)</p>
                                <p className="text-gray-600">Muted blue-gray</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Navigation */}
                <div className="text-center pt-8 border-t">
                    <Button
                        onClick={() => window.location.href = '/dashboard'}
                        variant="outline"
                    >
                        ← Back to Dashboard
                    </Button>
                </div>
            </div>

            {/* Full screen loading overlay */}
            {showFullScreen && <PageTransitionLoading />}
        </div>
    )
} 