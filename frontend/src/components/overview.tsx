"use client"

import React from "react"
import type { ChartDataItem } from "@/app/types/job"
import { Area, AreaChart, CartesianGrid, XAxis } from "recharts"
import { useDashboard } from "@/app/contexts/dashboard-context"
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import {
    ChartConfig,
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
} from "@/components/ui/chart"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { format, parseISO, isValid } from "date-fns"

const chartConfig = {
    jobs: {
        label: "Jobs",
    },
    jobs_extracted: {
        label: "Jobs Extracted",
        color: "hsl(var(--primary))",
    },
    jobs_applied: {
        label: "Jobs Applied",
        color: "hsl(var(--secondary))",
    },
} satisfies ChartConfig

export function Overview() {
    const { stats, loading, error, timeRange, setTimeRange } = useDashboard()

    if (loading) return (
        <Card>
            <CardContent className="flex items-center justify-center h-[350px]">
                Loading...
            </CardContent>
        </Card>
    )

    if (error) return (
        <Card>
            <CardContent className="flex items-center justify-center h-[350px] flex-col gap-2">
                <p className="text-red-500">Error: {error}</p>
                <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
                    Retry
                </Button>
            </CardContent>
        </Card>
    )

    if (!stats) return (
        <Card>
            <CardContent className="flex items-center justify-center h-[350px]">
                No data available
            </CardContent>
        </Card>
    )

    // Create chart data with proper error handling
    const chartData = stats.applicationsByDate?.map(item => {
        try {
            const date = parseISO(item.date)
            if (!isValid(date)) {
                console.warn('Invalid date:', item.date)
                return null
            }
            return {
                date: item.date,
                jobs_extracted: item.jobs_extracted || 0,
                jobs_applied: item.jobs_applied || 0
            }
        } catch (err) {
            console.warn('Error processing date:', item.date, err)
            return null
        }
    }).filter(Boolean) || []

    const getTimeRangeLabel = (range: string) => {
        switch (range) {
            case 'last_7_days': return 'Last 7 days'
            case 'last_30_days': return 'Last 30 days'
            case 'last_3_months': return 'Last 3 months'
            default: return 'Last 30 days'
        }
    }

    const getTimeRangeDescription = (range: string) => {
        switch (range) {
            case 'last_7_days': return 'Jobs extracted and applied in the past week'
            case 'last_30_days': return 'Jobs extracted and applied in the past month'
            case 'last_3_months': return 'Jobs extracted and applied in the past 3 months'
            default: return 'Jobs extracted and applied in the past month'
        }
    }

    if (chartData.length === 0) {
        return (
            <Card className="@container/card">
                <CardHeader>
                    <CardTitle>Job Activity</CardTitle>
                    <CardDescription>
                        {getTimeRangeDescription(timeRange)}
                    </CardDescription>
                    <div className="flex gap-2">
                        <Select value={timeRange} onValueChange={setTimeRange}>
                            <SelectTrigger
                                className="flex w-40"
                                aria-label="Select a value"
                            >
                                <SelectValue placeholder="Last 30 days" />
                            </SelectTrigger>
                            <SelectContent className="rounded-xl">
                                <SelectItem value="last_3_months" className="rounded-lg">
                                    Last 3 months
                                </SelectItem>
                                <SelectItem value="last_30_days" className="rounded-lg">
                                    Last 30 days
                                </SelectItem>
                                <SelectItem value="last_7_days" className="rounded-lg">
                                    Last 7 days
                                </SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </CardHeader>
                <CardContent className="flex items-center justify-center h-[350px]">
                    <p className="text-muted-foreground">No job activity data available for this time period</p>
                </CardContent>
            </Card>
        )
    }

    // Calculate the reference date (latest date in data) for filtering
    const latestDate = new Date(Math.max(...chartData.map(item => new Date(item?.date || '').getTime())))

    // Filter data based on time range
    const filteredData = chartData.filter((item) => {
        if (!item) return false
        const date = new Date(item.date)
        let daysToSubtract = 30
        if (timeRange === "last_3_months") {
            daysToSubtract = 90
        } else if (timeRange === "last_7_days") {
            daysToSubtract = 7
        }
        const startDate = new Date(latestDate)
        startDate.setDate(startDate.getDate() - daysToSubtract)
        return date >= startDate
    }).sort((a, b) => new Date(a?.date || '').getTime() - new Date(b?.date || '').getTime())

    return (
        <Card className="@container/card">
            <CardHeader>
                <CardTitle>Job Activity</CardTitle>
                <CardDescription>
                    <span className="hidden @[540px]/card:block">
                        {getTimeRangeDescription(timeRange)}
                    </span>
                    <span className="@[540px]/card:hidden">{getTimeRangeLabel(timeRange)}</span>
                </CardDescription>
                <div className="flex gap-2">
                    <div className="hidden @[767px]/card:flex gap-2">
                        <Button
                            variant={timeRange === 'last_3_months' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setTimeRange('last_3_months')}
                        >
                            Last 3 months
                        </Button>
                        <Button
                            variant={timeRange === 'last_30_days' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setTimeRange('last_30_days')}
                        >
                            Last 30 days
                        </Button>
                        <Button
                            variant={timeRange === 'last_7_days' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setTimeRange('last_7_days')}
                        >
                            Last 7 days
                        </Button>
                    </div>
                    <Select value={timeRange} onValueChange={setTimeRange}>
                        <SelectTrigger
                            className="flex w-40 @[767px]/card:hidden"
                            aria-label="Select a value"
                        >
                            <SelectValue placeholder="Last 30 days" />
                        </SelectTrigger>
                        <SelectContent className="rounded-xl">
                            <SelectItem value="last_3_months" className="rounded-lg">
                                Last 3 months
                            </SelectItem>
                            <SelectItem value="last_30_days" className="rounded-lg">
                                Last 30 days
                            </SelectItem>
                            <SelectItem value="last_7_days" className="rounded-lg">
                                Last 7 days
                            </SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </CardHeader>
            <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
                <ChartContainer
                    config={chartConfig}
                    className="aspect-auto h-[250px] w-full"
                >
                    <AreaChart data={filteredData}>
                        <defs>
                            <linearGradient id="fillExtracted" x1="0" y1="0" x2="0" y2="1">
                                <stop
                                    offset="5%"
                                    stopColor="var(--color-jobs_extracted)"
                                    stopOpacity={0.8}
                                />
                                <stop
                                    offset="95%"
                                    stopColor="var(--color-jobs_extracted)"
                                    stopOpacity={0.1}
                                />
                            </linearGradient>
                            <linearGradient id="fillApplied" x1="0" y1="0" x2="0" y2="1">
                                <stop
                                    offset="5%"
                                    stopColor="var(--color-jobs_applied)"
                                    stopOpacity={0.8}
                                />
                                <stop
                                    offset="95%"
                                    stopColor="var(--color-jobs_applied)"
                                    stopOpacity={0.1}
                                />
                            </linearGradient>
                        </defs>
                        <CartesianGrid vertical={false} />
                        <XAxis
                            dataKey="date"
                            tickLine={false}
                            axisLine={false}
                            tickMargin={8}
                            minTickGap={32}
                            tickFormatter={(value) => {
                                const date = new Date(value)
                                return date.toLocaleDateString("en-US", {
                                    month: "short",
                                    day: "numeric",
                                })
                            }}
                        />
                        <ChartTooltip
                            labelFormatter={(value) => {
                                return new Date(value).toLocaleDateString("en-US", {
                                    month: "short",
                                    day: "numeric",
                                    year: "numeric",
                                })
                            }}
                        />
                        <Area
                            dataKey="jobs_applied"
                            type="natural"
                            fill="url(#fillApplied)"
                            stroke="var(--color-jobs_applied)"
                            stackId="a"
                        />
                        <Area
                            dataKey="jobs_extracted"
                            type="natural"
                            fill="url(#fillExtracted)"
                            stroke="var(--color-jobs_extracted)"
                            stackId="a"
                        />
                    </AreaChart>
                </ChartContainer>
            </CardContent>
        </Card>
    )
} 