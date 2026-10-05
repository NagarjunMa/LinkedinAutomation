"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  CheckCircle,
  AlertCircle,
  Star
} from "lucide-react"
import { cn } from "@/lib/utils"

interface StatCardProps {
  title: string
  value: string | number
  change?: number
  changeType?: "increase" | "decrease"
  icon: React.ElementType
  color?: string
  description?: string
}

export function StatCard({
  title,
  value,
  change,
  changeType = "increase",
  icon: Icon,
  color = "blue",
  description
}: StatCardProps) {
  const colorClasses = {
    blue: "bg-blue-500",
    green: "bg-green-500",
    purple: "bg-purple-500",
    orange: "bg-orange-500",
    red: "bg-red-500",
    yellow: "bg-yellow-500",
  }

  return (
    <Card className="hover:shadow-lg hover:scale-105 transition-all duration-300 border-0 shadow-sm group">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-cream-300 mb-1 group-hover:text-cream-200 transition-colors">{title}</p>
            <p className="text-2xl font-bold text-cream-50 group-hover:text-accent-400 transition-colors">{value}</p>
            {change !== undefined && (
              <div className="flex items-center mt-2">
                {changeType === "increase" ? (
                  <ArrowUpRight className="h-4 w-4 text-green-500 mr-1" />
                ) : (
                  <ArrowDownRight className="h-4 w-4 text-red-500 mr-1" />
                )}
                <span className={cn(
                  "text-sm font-medium",
                  changeType === "increase" ? "text-green-600" : "text-red-600"
                )}>
                  {change}%
                </span>
                <span className="text-sm text-cream-400 ml-1">vs last month</span>
              </div>
            )}
            {description && (
              <p className="text-xs text-cream-400 mt-1 group-hover:text-cream-300 transition-colors">{description}</p>
            )}
          </div>
          <div className={cn(
            "w-12 h-12 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300",
            colorClasses[color as keyof typeof colorClasses]
          )}>
            <Icon className="h-6 w-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

interface ProgressCardProps {
  title: string
  progress: number
  total: number
  color?: string
  icon: React.ElementType
}

export function ProgressCard({ title, progress, total, color = "blue", icon: Icon }: ProgressCardProps) {
  const percentage = Math.round((progress / total) * 100)

  const colorClasses = {
    blue: "bg-blue-500",
    green: "bg-green-500",
    purple: "bg-purple-500",
    orange: "bg-orange-500",
  }

  return (
    <Card className="hover:shadow-lg hover:scale-105 transition-all duration-300 border-0 shadow-sm group">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={cn(
              "w-10 h-10 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300",
              colorClasses[color as keyof typeof colorClasses]
            )}>
              <Icon className="h-5 w-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 group-hover:text-orange-600 transition-colors">{title}</h3>
              <p className="text-sm text-gray-500 group-hover:text-gray-600 transition-colors">{progress} of {total} completed</p>
            </div>
          </div>
          <Badge variant="secondary" className="text-sm font-medium group-hover:bg-orange-100 group-hover:text-orange-800 transition-colors">
            {percentage}%
          </Badge>
        </div>
        <Progress value={percentage} className="h-2" />
      </CardContent>
    </Card>
  )
}

interface ActivityCardProps {
  title: string
  activities: Array<{
    id: string
    title: string
    description: string
    time: string
    type: "success" | "warning" | "info"
    icon: React.ElementType
  }>
}

export function ActivityCard({ title, activities }: ActivityCardProps) {
  const typeClasses = {
    success: "text-green-500 bg-green-50",
    warning: "text-yellow-500 bg-yellow-50",
    info: "text-blue-500 bg-blue-50",
  }

  const iconClasses = {
    success: CheckCircle,
    warning: AlertCircle,
    info: Clock,
  }

  return (
    <Card className="hover:shadow-lg transition-all duration-200 border-0 shadow-sm">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-semibold text-gray-900">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {activities.map((activity) => {
          const IconComponent = iconClasses[activity.type]
          return (
            <div key={activity.id} className="flex items-start space-x-3">
              <div className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                typeClasses[activity.type]
              )}>
                <IconComponent className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                <p className="text-sm text-gray-500">{activity.description}</p>
                <p className="text-xs text-gray-400 mt-1">{activity.time}</p>
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}

interface JobCardProps {
  job: {
    id: string
    title: string
    company: string
    location: string
    salary?: string
    status: "applied" | "interview" | "offer" | "rejected"
    matchScore: number
    appliedDate: string
    tags: string[]
  }
}

export function JobCard({ job }: JobCardProps) {
  const statusClasses = {
    applied: "bg-blue-100 text-blue-800",
    interview: "bg-yellow-100 text-yellow-800",
    offer: "bg-green-100 text-green-800",
    rejected: "bg-red-100 text-red-800",
  }

  const statusLabels = {
    applied: "Applied",
    interview: "Interview",
    offer: "Offer",
    rejected: "Rejected",
  }

  return (
    <Card className="hover:shadow-lg transition-all duration-200 border-0 shadow-sm group">
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 group-hover:text-orange-600 transition-colors">
              {job.title}
            </h3>
            <p className="text-sm text-gray-600">{job.company}</p>
            <p className="text-sm text-gray-500">{job.location}</p>
          </div>
          <div className="flex items-center space-x-2">
            <Badge className={statusClasses[job.status]}>
              {statusLabels[job.status]}
            </Badge>
            <div className="flex items-center space-x-1">
              <Star className="h-4 w-4 text-yellow-400" />
              <span className="text-sm font-medium text-gray-900">{job.matchScore}%</span>
            </div>
          </div>
        </div>

        {job.salary && (
          <p className="text-sm text-gray-600 mb-3">{job.salary}</p>
        )}

        <div className="flex items-center justify-between">
          <div className="flex flex-wrap gap-1">
            {job.tags.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
            {job.tags.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{job.tags.length - 3}
              </Badge>
            )}
          </div>
          <span className="text-xs text-gray-500">{job.appliedDate}</span>
        </div>
      </CardContent>
    </Card>
  )
}
