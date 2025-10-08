"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Area,
  AreaChart
} from "recharts"
import { TrendingUp, TrendingDown, Users, Briefcase, Target } from "lucide-react"

const jobStatusData = [
  { name: "Applied", value: 45, color: "#3B82F6" },
  { name: "Interview", value: 12, color: "#F59E0B" },
  { name: "Offer", value: 3, color: "#10B981" },
  { name: "Rejected", value: 8, color: "#EF4444" },
]

const monthlyApplications = [
  { month: "Jan", applications: 12, interviews: 3, offers: 1 },
  { month: "Feb", applications: 18, interviews: 5, offers: 2 },
  { month: "Mar", applications: 25, interviews: 8, offers: 1 },
  { month: "Apr", applications: 22, interviews: 6, offers: 3 },
  { month: "May", applications: 30, interviews: 10, offers: 2 },
  { month: "Jun", applications: 28, interviews: 9, offers: 4 },
]

const skillMatchData = [
  { skill: "React", match: 95, demand: 88 },
  { skill: "TypeScript", match: 92, demand: 85 },
  { skill: "Node.js", match: 88, demand: 82 },
  { skill: "Python", match: 85, demand: 90 },
  { skill: "AWS", match: 78, demand: 75 },
  { skill: "Docker", match: 82, demand: 80 },
]

const weeklyActivity = [
  { day: "Mon", applications: 4, emails: 12, calls: 2 },
  { day: "Tue", applications: 6, emails: 8, calls: 1 },
  { day: "Wed", applications: 3, emails: 15, calls: 3 },
  { day: "Thu", applications: 8, emails: 10, calls: 2 },
  { day: "Fri", applications: 5, emails: 6, calls: 1 },
  { day: "Sat", applications: 2, emails: 4, calls: 0 },
  { day: "Sun", applications: 1, emails: 3, calls: 0 },
]

export function JobStatusChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Target className="h-5 w-5 text-orange-500" />
          <span>Application Status</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={jobStatusData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
              >
                {jobStatusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="grid grid-cols-2 gap-4 mt-4">
          {jobStatusData.map((item) => (
            <div key={item.name} className="flex items-center space-x-2">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: item.color }}
              />
              <span className="text-sm text-gray-600">{item.name}</span>
              <Badge variant="secondary" className="ml-auto">{item.value}</Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export function MonthlyTrendsChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <TrendingUp className="h-5 w-5 text-orange-500" />
          <span>Monthly Trends</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={monthlyApplications}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="applications"
                stackId="1"
                stroke="#3B82F6"
                fill="#3B82F6"
                fillOpacity={0.6}
              />
              <Area
                type="monotone"
                dataKey="interviews"
                stackId="1"
                stroke="#F59E0B"
                fill="#F59E0B"
                fillOpacity={0.6}
              />
              <Area
                type="monotone"
                dataKey="offers"
                stackId="1"
                stroke="#10B981"
                fill="#10B981"
                fillOpacity={0.6}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

export function SkillMatchChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Users className="h-5 w-5 text-orange-500" />
          <span>Skill Match Analysis</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={skillMatchData} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 100]} />
              <YAxis dataKey="skill" type="category" width={80} />
              <Tooltip />
              <Bar dataKey="match" fill="#3B82F6" name="Your Match %" />
              <Bar dataKey="demand" fill="#F59E0B" name="Market Demand %" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center justify-center space-x-6 mt-4">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded" />
            <span className="text-sm text-gray-600">Your Match</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-yellow-500 rounded" />
            <span className="text-sm text-gray-600">Market Demand</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function WeeklyActivityChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Briefcase className="h-5 w-5 text-orange-500" />
          <span>Weekly Activity</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={weeklyActivity}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="applications"
                stroke="#3B82F6"
                strokeWidth={2}
                name="Applications"
              />
              <Line
                type="monotone"
                dataKey="emails"
                stroke="#10B981"
                strokeWidth={2}
                name="Emails"
              />
              <Line
                type="monotone"
                dataKey="calls"
                stroke="#F59E0B"
                strokeWidth={2}
                name="Calls"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

export function QuickStats() {
  const stats = [
    {
      title: "Response Rate",
      value: "68%",
      change: "+12%",
      changeType: "increase" as const,
      icon: TrendingUp,
      color: "text-green-600"
    },
    {
      title: "Interview Rate",
      value: "24%",
      change: "+5%",
      changeType: "increase" as const,
      icon: Users,
      color: "text-blue-600"
    },
    {
      title: "Offer Rate",
      value: "8%",
      change: "-2%",
      changeType: "decrease" as const,
      icon: Target,
      color: "text-orange-600"
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {stats.map((stat) => (
        <Card key={stat.title} className="hover:shadow-md transition-shadow">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                <div className="flex items-center mt-1">
                  {stat.changeType === "increase" ? (
                    <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
                  )}
                  <span className={`text-sm font-medium ${stat.color}`}>
                    {stat.change}
                  </span>
                  <span className="text-sm text-gray-500 ml-1">vs last month</span>
                </div>
              </div>
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                stat.color === "text-green-600" ? "bg-green-100" :
                stat.color === "text-blue-600" ? "bg-blue-100" :
                "bg-orange-100"
              }`}>
                <stat.icon className={`h-5 w-5 ${stat.color}`} />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
