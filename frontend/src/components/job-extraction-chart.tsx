"use client"

import { motion, useInView } from "framer-motion"
import { useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp } from "lucide-react"

interface JobExtractionChartProps {
    data: Array<{
        date: string
        jobs: number
    }>
}

export function JobExtractionChart({ data }: JobExtractionChartProps) {
    const ref = useRef(null)
    const isInView = useInView(ref, { once: true, margin: "-100px" })
    const [hoveredPoint, setHoveredPoint] = useState<number | null>(null)

    // Calculate the maximum value for scaling
    const maxJobs = Math.max(...data.map(d => d.jobs))

    // Chart dimensions
    const width = 400
    const height = 160
    const paddingTop = 30
    const paddingBottom = 30
    const paddingLeft = 40
    const paddingRight = 40

    // Create smooth curve path using cubic bezier
    const createSmoothPath = () => {
        if (data.length === 0) return ""

        const stepX = (width - paddingLeft - paddingRight) / (data.length - 1)
        const chartHeight = height - paddingTop - paddingBottom
        // Use adjusted max value to prevent clipping
        const adjustedMaxJobs = Math.ceil(maxJobs * 1.1)
        const points = data.map((d, i) => ({
            x: paddingLeft + (i * stepX),
            y: paddingTop + (chartHeight - ((d.jobs / adjustedMaxJobs) * chartHeight))
        }))

        if (points.length < 2) return ""

        let path = `M ${points[0].x} ${points[0].y}`

        for (let i = 1; i < points.length; i++) {
            const prev = points[i - 1]
            const curr = points[i]

            // Create smooth curves using quadratic bezier
            const cpx = prev.x + (curr.x - prev.x) / 2
            const cpy = prev.y

            if (i === 1) {
                path += ` Q ${cpx} ${cpy} ${curr.x} ${curr.y}`
            } else {
                path += ` T ${curr.x} ${curr.y}`
            }
        }

        return path
    }

    // Create area path for gradient fill
    const createAreaPath = () => {
        if (data.length === 0) return ""

        const smoothPath = createSmoothPath()
        if (!smoothPath) return ""

        const lastPoint = {
            x: paddingLeft + ((data.length - 1) * (width - paddingLeft - paddingRight)) / (data.length - 1),
            y: height - paddingBottom
        }
        const firstPoint = { x: paddingLeft, y: height - paddingBottom }

        return `${smoothPath} L ${lastPoint.x} ${lastPoint.y} L ${firstPoint.x} ${firstPoint.y} Z`
    }

    // Get point coordinates
    const getPointCoordinates = (index: number) => {
        const stepX = (width - paddingLeft - paddingRight) / (data.length - 1)
        const chartHeight = height - paddingTop - paddingBottom
        const adjustedMaxJobs = Math.ceil(maxJobs * 1.1)
        return {
            x: paddingLeft + (index * stepX),
            y: paddingTop + (chartHeight - ((data[index].jobs / adjustedMaxJobs) * chartHeight))
        }
    }

    // Create Y-axis labels
    const createYAxisLabels = () => {
        const labels: any[] = []
        const numTicks = 4
        const chartHeight = height - paddingTop - paddingBottom
        // Add some buffer to prevent clipping of highest values
        const maxValue = Math.ceil(maxJobs * 1.1)

        for (let i = 0; i <= numTicks; i++) {
            const value = Math.round((maxValue / numTicks) * (numTicks - i))
            const y = paddingTop + (i * chartHeight) / numTicks

            labels.push(
                <text
                    key={i}
                    x={paddingLeft - 10}
                    y={y + 4}
                    textAnchor="end"
                    fill="#9CA3AF"
                    fontSize="10"
                    fontWeight="500"
                >
                    {value}
                </text>
            )
        }

        return labels
    }

    return (
        <Card className="premium-card hover:scale-105 transition-all duration-300 group h-full flex flex-col">
            <CardHeader className="pb-3 flex-shrink-0">
                <div className="flex items-center space-x-2">
                    <TrendingUp className="h-5 w-5 text-accent-500" />
                    <CardTitle className="text-cream-50 text-lg group-hover:text-accent-400 transition-colors">
                        Application Extraction
                    </CardTitle>
                </div>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col min-h-0 p-6">
                <div className="flex flex-col h-full space-y-3 min-h-0">
                    {/* Chart */}
                    <div className="flex-1 min-h-0 overflow-hidden" ref={ref}>
                        <svg width="100%" height="160" viewBox="0 0 400 160" className="w-full h-full">
                            <defs>
                                {/* Enhanced gradient for area fill */}
                                <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                    <stop offset="0%" stopColor="#f97316" stopOpacity="0.3" />
                                    <stop offset="50%" stopColor="#f97316" stopOpacity="0.15" />
                                    <stop offset="100%" stopColor="#f97316" stopOpacity="0.02" />
                                </linearGradient>

                                {/* Glow effect */}
                                <filter id="glow">
                                    <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                                    <feMerge>
                                        <feMergeNode in="coloredBlur" />
                                        <feMergeNode in="SourceGraphic" />
                                    </feMerge>
                                </filter>

                                {/* Drop shadow for dots */}
                                <filter id="dropshadow">
                                    <feDropShadow dx="0" dy="1" stdDeviation="2" floodColor="#000" floodOpacity="0.3" />
                                </filter>
                            </defs>

                            {/* Y-axis labels */}
                            <g>
                                {createYAxisLabels()}
                            </g>

                            {/* Area fill with enhanced gradient */}
                            <motion.path
                                d={createAreaPath()}
                                fill="url(#areaGradient)"
                                initial={{ opacity: 0, scaleY: 0 }}
                                animate={isInView ? { opacity: 1, scaleY: 1 } : { opacity: 0, scaleY: 0 }}
                                transition={{ duration: 1.2, delay: 0.3, ease: "easeOut" }}
                                style={{ transformOrigin: "bottom" }}
                            />

                            {/* Main line with enhanced animations */}
                            <motion.path
                                d={createSmoothPath()}
                                fill="none"
                                stroke="url(#lineGradient)"
                                strokeWidth="3"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                filter="url(#glow)"
                                initial={{ pathLength: 0, opacity: 0 }}
                                animate={isInView ? { pathLength: 1, opacity: 1 } : { pathLength: 0, opacity: 0 }}
                                transition={{ duration: 2, ease: "easeInOut", delay: 0.5 }}
                            />

                            {/* Enhanced gradient for line */}
                            <defs>
                                <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                    <stop offset="0%" stopColor="#f97316" />
                                    <stop offset="50%" stopColor="#fb923c" />
                                    <stop offset="100%" stopColor="#f97316" />
                                </linearGradient>
                            </defs>

                            {/* Animated data points with enhanced interactions */}
                            {data.map((point, index) => {
                                const coords = getPointCoordinates(index)
                                const isHovered = hoveredPoint === index

                                return (
                                    <g key={index}>
                                        {/* Hover circle background */}
                                        <motion.circle
                                            cx={coords.x}
                                            cy={coords.y}
                                            r={isHovered ? 12 : 0}
                                            fill="#f97316"
                                            opacity="0.1"
                                            initial={{ scale: 0 }}
                                            animate={{ scale: isHovered ? 1 : 0 }}
                                            transition={{ duration: 0.2 }}
                                        />

                                        {/* Main data point */}
                                        <motion.circle
                                            cx={coords.x}
                                            cy={coords.y}
                                            r={isHovered ? 6 : 4}
                                            fill="#f97316"
                                            stroke="#1f2937"
                                            strokeWidth={isHovered ? 3 : 2}
                                            filter="url(#dropshadow)"
                                            initial={{ scale: 0, opacity: 0 }}
                                            animate={isInView ? { scale: 1, opacity: 1 } : { scale: 0, opacity: 0 }}
                                            transition={{
                                                duration: 0.5,
                                                delay: 1.5 + index * 0.1,
                                                type: "spring",
                                                stiffness: 200,
                                                damping: 10
                                            }}
                                            whileHover={{
                                                scale: 1.4,
                                                transition: { duration: 0.2 }
                                            }}
                                            onHoverStart={() => setHoveredPoint(index)}
                                            onHoverEnd={() => setHoveredPoint(null)}
                                            className="cursor-pointer"
                                        />

                                        {/* Tooltip */}
                                        {isHovered && (
                                            <motion.g
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ duration: 0.2 }}
                                            >
                                                <rect
                                                    x={coords.x - 25}
                                                    y={coords.y - 35}
                                                    width="50"
                                                    height="20"
                                                    rx="4"
                                                    fill="#1f2937"
                                                    stroke="#f97316"
                                                    strokeWidth="1"
                                                />
                                                <text
                                                    x={coords.x}
                                                    y={coords.y - 22}
                                                    textAnchor="middle"
                                                    fill="#f97316"
                                                    fontSize="10"
                                                    fontWeight="bold"
                                                >
                                                    {point.jobs} jobs
                                                </text>
                                            </motion.g>
                                        )}
                                    </g>
                                )
                            })}
                        </svg>
                    </div>


                </div>
            </CardContent>
        </Card>
    )
}