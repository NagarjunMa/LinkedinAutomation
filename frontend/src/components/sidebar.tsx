"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useAuth } from "@/contexts/auth-context"
import { Logo } from "@/components/logo"
import {
  BarChart3,
  Briefcase,
  FileText,
  Mail,
  Search,
  Settings,
  Target,
  TrendingUp,
  Users,
  Zap,
  ChevronLeft,
  ChevronRight,
  Home,
  Calendar,
  Bell,
  User
} from "lucide-react"

const navigation = [
  {
    name: "Overview",
    href: "/dashboard",
    icon: Home,
    current: true,
  },
  {
    name: "Jobs",
    href: "/dashboard/jobs",
    icon: Briefcase,
    current: false,
  },
  {
    name: "Analytics",
    href: "/dashboard/analytics",
    icon: BarChart3,
    current: false,
  },
  {
    name: "Resume Manager",
    href: "/dashboard/resume-evaluation",
    icon: FileText,
    current: false,
  },
  {
    name: "Email Agent",
    href: "/dashboard/email-agent",
    icon: Mail,
    current: false,
  },
  {
    name: "Job Search",
    href: "/dashboard/jobs",
    icon: Search,
    current: false,
  },
]

const quickActions = [
  {
    name: "Extract Job",
    href: "/dashboard/jobs",
    icon: Target,
    color: "bg-blue-500",
  },
  {
    name: "Upload Resume",
    href: "/dashboard/resume-evaluation",
    icon: FileText,
    color: "bg-green-500",
  },
  {
    name: "AI Matching",
    href: "/dashboard/analytics",
    icon: Zap,
    color: "bg-purple-500",
  },
]

interface SidebarProps {
  className?: string
}

export function Sidebar({ className }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false)
  const pathname = usePathname()
  const { user, loading } = useAuth()

  return (
    <div className={cn(
      "flex h-full flex-col bg-primary-900 border-r border-primary-600 transition-all duration-300",
      collapsed ? "w-16" : "w-64",
      className
    )}>
      {/* Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-primary-600">
        {!collapsed && (
          <div className="flex items-center space-x-2">
            <Logo size={32} showText={false} />
            <span className="text-lg font-semibold text-cream-50">JobFlow Pro</span>
          </div>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCollapsed(!collapsed)}
          className="h-8 w-8 p-0"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors duration-200",
                isActive
                  ? "bg-orange-50 text-orange-700 border-r-2 border-orange-500"
                  : "text-cream-200 hover:bg-primary-800 hover:text-cream-50"
              )}
            >
              <item.icon
                className={cn(
                  "mr-3 h-5 w-5 flex-shrink-0",
                  isActive ? "text-accent-500" : "text-cream-300 group-hover:text-accent-400"
                )}
              />
              {!collapsed && (
                <span className="truncate">{item.name}</span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* Quick Actions */}
      {!collapsed && (
        <div className="px-3 py-4 border-t border-primary-600">
          <h3 className="px-3 text-xs font-semibold text-cream-400 uppercase tracking-wider mb-3">
            Quick Actions
          </h3>
          <div className="space-y-1">
            {quickActions.map((action) => (
              <Link
                key={action.name}
                href={action.href}
                className="group flex items-center px-3 py-2 text-sm font-medium text-cream-200 rounded-lg hover:bg-primary-800 hover:text-cream-50 transition-colors duration-200"
              >
                <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center mr-3", action.color)}>
                  <action.icon className="h-4 w-4 text-white" />
                </div>
                <span className="truncate">{action.name}</span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* User Profile */}
      <div className="px-3 py-4 border-t border-primary-600">
        <div className="flex items-center">
          {user?.user_metadata?.avatar_url ? (
            <img
              src={user.user_metadata.avatar_url}
              alt="Profile"
              className="w-8 h-8 rounded-full object-cover"
            />
          ) : (
            <div className="w-8 h-8 bg-primary-700 rounded-full flex items-center justify-center">
              <User className="h-4 w-4 text-cream-300" />
            </div>
          )}
          {!collapsed && (
            <div className="ml-3">
              <p className="text-sm font-medium text-cream-50">
                {loading ? "Loading..." : user?.user_metadata?.full_name || user?.email?.split('@')[0] || "User"}
              </p>
              <p className="text-xs text-cream-300">
                {loading ? "..." : user?.email || "No email"}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
