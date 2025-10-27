"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Mail,
  TrendingUp,
  TrendingDown,
  Activity,
  AlertCircle,
  RefreshCw,
  ExternalLink,
  Users,
  Send,
  MessageCircle
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useState, useEffect } from "react"
import { referralAPI, ReferralAnalytics, isReferralAPIError } from "@/lib/referral-api"
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts'

interface ReferralAnalyticsCardProps {
  title?: string
  className?: string
  showActions?: boolean
}

export function ReferralAnalyticsCard({
  title = "📧 Referral Outreach",
  className,
  showActions = true
}: ReferralAnalyticsCardProps) {
  const [analyticsData, setAnalyticsData] = useState<ReferralAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const fetchAnalytics = async () => {
    try {
      setError(null)
      const data = await referralAPI.getAnalytics()
      setAnalyticsData(data)
    } catch (err) {
      if (isReferralAPIError(err)) {
        setError(err.message)
      } else {
        setError("Failed to load referral analytics")
      }
    } finally {
      setLoading(false)
      setIsRefreshing(false)
    }
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await fetchAnalytics()
  }

  useEffect(() => {
    fetchAnalytics()
  }, [])

  if (loading) {
    return <ReferralAnalyticsCardSkeleton title={title} className={className} />
  }

  if (error) {
    return <ErrorCard title={title} className={className} error={error} onRefresh={handleRefresh} />
  }

  if (!analyticsData) {
    return <ErrorCard title={title} className={className} error="No data available" onRefresh={handleRefresh} />
  }

  // Determine trend direction
  const getTrendDirection = () => {
    if (analyticsData.trend_data.length < 2) return 'stable'

    const recent = analyticsData.trend_data.slice(-7).reduce((sum, day) => sum + day.count, 0)
    const previous = analyticsData.trend_data.slice(-14, -7).reduce((sum, day) => sum + day.count, 0)

    if (recent > previous * 1.2) return 'up'
    if (recent < previous * 0.8) return 'down'
    return 'stable'
  }

  const trendDirection = getTrendDirection()

  const getTrendIcon = () => {
    switch (trendDirection) {
      case 'up': return TrendingUp
      case 'down': return TrendingDown
      default: return Activity
    }
  }

  const getTrendColor = () => {
    switch (trendDirection) {
      case 'up': return 'text-green-400'
      case 'down': return 'text-red-400'
      default: return 'text-cream-300'
    }
  }

  const TrendIcon = getTrendIcon()

  return (
    <Card className={cn(
      "premium-card hover:scale-105 transition-all duration-300 group max-h-[400px] flex flex-col",
      className
    )}>
      <CardHeader className="pb-4 flex-shrink-0">
        <div className="flex items-center justify-between mb-2">
          <CardTitle className="text-cream-50 text-lg group-hover:text-accent-400 transition-colors">
            {title}
          </CardTitle>
          {showActions && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="text-cream-300 hover:text-cream-50 text-xs px-2 py-1 h-6"
            >
              {isRefreshing ? (
                <RefreshCw className="h-3 w-3 animate-spin" />
              ) : (
                "Refresh"
              )}
            </Button>
          )}
        </div>

        {/* Trend Summary */}
        <div className="flex items-center gap-3 mt-2">
          <div className="flex items-center space-x-1">
            <TrendIcon className={cn("h-4 w-4", getTrendColor())} />
            <span className={cn("font-medium capitalize text-sm", getTrendColor())}>
              {trendDirection} trend
            </span>
          </div>
          <Badge className="bg-primary-700 text-cream-300 border-primary-500 text-xs">
            {Math.round(analyticsData.response_rate)}% response rate
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col space-y-4 min-h-0">
        {/* Key Metrics */}
        <div className="grid grid-cols-3 gap-3 pt-2">
          <div className="text-center p-3 rounded-lg bg-primary-800/30 hover:bg-primary-800/50 transition-colors">
            <div className="text-2xl font-bold text-accent-400 mb-1">{analyticsData.this_week}</div>
            <div className="text-xs text-cream-300 font-medium">This Week</div>
          </div>
          <div className="text-center p-3 rounded-lg bg-primary-800/30 hover:bg-primary-800/50 transition-colors">
            <div className="text-2xl font-bold text-cream-50 mb-1">{analyticsData.total_sent}</div>
            <div className="text-xs text-cream-300 font-medium">Total Sent</div>
          </div>
          <div className="text-center p-3 rounded-lg bg-primary-800/30 hover:bg-primary-800/50 transition-colors">
            <div className="text-2xl font-bold text-green-400 mb-1">{analyticsData.response_rate}%</div>
            <div className="text-xs text-cream-300 font-medium">Response Rate</div>
          </div>
        </div>

        {/* Mini Trend Chart */}
        {analyticsData.trend_data.length > 0 && (
          <div className="h-16">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={analyticsData.trend_data}>
                <defs>
                  <linearGradient id="referralGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="rgb(249, 115, 22)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="rgb(249, 115, 22)" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" hide />
                <YAxis hide />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgb(51, 65, 85)',
                    border: '1px solid rgb(100, 116, 139)',
                    borderRadius: '8px',
                    color: 'rgb(248, 250, 252)'
                  }}
                  labelFormatter={(date) => `Date: ${date}`}
                  formatter={(value: number) => [value, 'Referrals Sent']}
                />
                <Area
                  type="monotone"
                  dataKey="count"
                  stroke="rgb(249, 115, 22)"
                  strokeWidth={2}
                  fill="url(#referralGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Action Button */}
        {showActions && (
          <div className="mt-4 pt-4 border-t border-primary-700/50">
            <Button
              className="w-full bg-primary-700 hover:bg-primary-600 text-cream-50 border-primary-500 hover:border-accent-500 transition-all duration-200 group/btn"
              onClick={() => {
                // Navigate to referrals page or open referral form
                window.location.href = '/dashboard/referrals'
              }}
            >
              <div className="flex items-center justify-center space-x-2">
                <Send className="h-4 w-4 group-hover/btn:text-accent-400 transition-colors" />
                <span>Manage Referrals</span>
                <ExternalLink className="h-3 w-3 group-hover/btn:text-accent-400 transition-colors" />
              </div>
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function ReferralAnalyticsCardSkeleton({ title, className }: { title: string; className?: string }) {
  return (
    <Card className={cn(
      "premium-card max-h-[400px] flex flex-col",
      className
    )}>
      <CardHeader className="pb-3 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Mail className="h-5 w-5 text-accent-400" />
            <CardTitle className="text-cream-50 text-lg">{title}</CardTitle>
          </div>
          <Skeleton className="h-6 w-16 bg-primary-700" />
        </div>
        <div className="flex items-center justify-between">
          <Skeleton className="h-4 w-24 bg-primary-700" />
          <Skeleton className="h-4 w-20 bg-primary-700" />
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col space-y-4">
        <div className="grid grid-cols-3 gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="text-center space-y-1">
              <Skeleton className="h-8 w-8 mx-auto bg-primary-700" />
              <Skeleton className="h-3 w-12 mx-auto bg-primary-700" />
            </div>
          ))}
        </div>

        <Skeleton className="h-16 w-full bg-primary-700" />
        <Skeleton className="h-10 w-full bg-primary-700" />
      </CardContent>
    </Card>
  )
}

function ErrorCard({
  title,
  className,
  error,
  onRefresh
}: {
  title: string;
  className?: string;
  error: string;
  onRefresh: () => void
}) {
  return (
    <Card className={cn(
      "premium-card max-h-[400px] flex flex-col",
      className
    )}>
      <CardHeader className="pb-3 flex-shrink-0">
        <div className="flex items-center space-x-2">
          <Mail className="h-5 w-5 text-accent-400" />
          <CardTitle className="text-cream-50 text-lg">{title}</CardTitle>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col items-center justify-center space-y-4">
        <Alert className="border-red-500/20 bg-red-500/10">
          <AlertCircle className="h-4 w-4 text-red-400" />
          <AlertDescription className="text-cream-200">
            {error}
          </AlertDescription>
        </Alert>

        <div className="text-center space-y-2">
          <div className="text-6xl">📧</div>
          <p className="text-sm text-cream-300">
            Unable to load referral data. Please try again.
          </p>
        </div>

        <Button
          onClick={onRefresh}
          className="bg-red-500 hover:bg-red-400 text-white"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </CardContent>
    </Card>
  )
}