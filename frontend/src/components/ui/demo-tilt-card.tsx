"use client"

import { useRef, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Building, Calendar, Brain } from "lucide-react"

// Custom hook for tilt effect (same as in applied-jobs-list.tsx)
function useTiltEffect() {
    const ref = useRef<HTMLDivElement>(null)

    useEffect(() => {
        const element = ref.current
        if (!element) return

        const handleMouseMove = (e: MouseEvent) => {
            const rect = element.getBoundingClientRect()
            const x = e.clientX - rect.left
            const y = e.clientY - rect.top
            const centerX = rect.width / 2
            const centerY = rect.height / 2
            const rotateX = (y - centerY) / 10
            const rotateY = (centerX - x) / 10

            element.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`
        }

        const handleMouseLeave = () => {
            element.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)'
        }

        element.addEventListener('mousemove', handleMouseMove)
        element.addEventListener('mouseleave', handleMouseLeave)

        return () => {
            element.removeEventListener('mousemove', handleMouseMove)
            element.removeEventListener('mouseleave', handleMouseLeave)
        }
    }, [])

    return ref
}

export function DemoTiltCard() {
    const tiltRef = useTiltEffect()

    return (
        <div
            ref={tiltRef}
            className="w-[400px] transition-transform duration-300 ease-out"
            style={{ transformStyle: 'preserve-3d' }}
        >
            <Card className="h-full border border-gray-200 shadow-sm hover:shadow-lg transition-shadow duration-300">
                <CardContent className="p-6">
                    <div className="space-y-4">
                        {/* Header with Role and Company */}
                        <div className="space-y-2">
                            <h3 className="font-semibold text-lg leading-tight text-gray-900">
                                Software Engineer
                            </h3>
                            <div className="flex items-center gap-2 text-gray-600">
                                <Building className="h-4 w-4" />
                                <span className="font-medium">Demo Company</span>
                            </div>
                        </div>

                        {/* Salary and Location */}
                        <div className="flex items-center justify-between">
                            <div className="space-y-1">
                                <div className="text-sm font-medium text-green-700">
                                    $120,000 - $180,000
                                </div>
                                <div className="text-sm text-gray-500">
                                    📍 San Francisco, CA
                                </div>
                            </div>
                            <div className="text-right space-y-1">
                                <Badge className="bg-blue-100 text-blue-800 border-blue-200" variant="outline">
                                    Applied
                                </Badge>
                            </div>
                        </div>

                        {/* Applied Date and AI Score */}
                        <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                            <div className="flex items-center gap-2 text-sm text-gray-500">
                                <Calendar className="h-4 w-4" />
                                <span>Applied Jul 25, 2025</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <Brain className="h-4 w-4 text-purple-500" />
                                <span className="text-sm font-medium text-purple-700">
                                    AI: 95%
                                </span>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
} 