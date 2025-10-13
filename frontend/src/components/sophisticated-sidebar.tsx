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
    TrendingUp,
    Users,
    Zap,
    ChevronRight,
    HelpCircle,
    Settings,
    X
} from "lucide-react"

const mainNavigation = [
    {
        name: "Dashboard",
        href: "/dashboard",
        icon: BarChart3,
        current: true,
    },
    {
        name: "Applications",
        href: "/dashboard/applications",
        icon: Briefcase,
        current: false,
    },
    {
        name: "Job Search",
        href: "/dashboard/jobs",
        icon: Search,
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
        name: "Analytics",
        href: "/dashboard/analytics",
        icon: TrendingUp,
        current: false,
    },
]


const supportNavigation = [
    {
        name: "Help Center",
        href: "/help",
        icon: HelpCircle,
    },
    {
        name: "Settings",
        href: "/settings",
        icon: Settings,
    },
]

interface SophisticatedSidebarProps {
    className?: string
    onClose?: () => void
}

export function SophisticatedSidebar({ className, onClose }: SophisticatedSidebarProps) {
    const [collapsed, setCollapsed] = useState(false)
    const pathname = usePathname()
    const { user, loading } = useAuth()

    // Get user display information
    const userName = user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User'
    const userEmail = user?.email || ''

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
                <div className="flex items-center gap-2">
                    {/* Mobile close button */}
                    {onClose && (
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={onClose}
                            className="h-8 w-8 p-0 text-cream-300 hover:text-cream-50 hover:bg-primary-800 transition-all duration-200 lg:hidden"
                        >
                            <X className="h-4 w-4" />
                        </Button>
                    )}
                    {/* Desktop collapse button */}
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setCollapsed(!collapsed)}
                        className="h-8 w-8 p-0 text-cream-300 hover:text-cream-50 hover:bg-primary-800 transition-all duration-200 hidden lg:flex"
                    >
                        <ChevronRight className={cn("h-4 w-4 transition-transform", collapsed && "rotate-180")} />
                    </Button>
                </div>
            </div>

            {/* Main Navigation */}
            <div className="flex-1 px-3 py-6">
                <div className="space-y-1">
                    <div className="px-3 mb-4">
                        <h3 className="text-xs font-semibold text-cream-400 uppercase tracking-wider">
                            {!collapsed && "MENU"}
                        </h3>
                    </div>
                    {mainNavigation.map((item) => {
                        const isActive = pathname === item.href
                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={cn(
                                    "group flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200",
                                    isActive
                                        ? "bg-gradient-warm/20 text-accent-400 border-r-2 border-accent-500 glow-orange"
                                        : "text-cream-300 hover:bg-primary-800 hover:text-cream-50"
                                )}
                            >
                                <item.icon
                                    className={cn(
                                        "mr-3 h-5 w-5 flex-shrink-0",
                                        isActive ? "text-accent-400" : "text-cream-300 group-hover:text-cream-50"
                                    )}
                                />
                                {!collapsed && (
                                    <span className="truncate">{item.name}</span>
                                )}
                                {isActive && !collapsed && (
                                    <ChevronRight className="ml-auto h-4 w-4 text-accent-400" />
                                )}
                            </Link>
                        )
                    })}
                </div>


                {/* Support Section */}
                <div className="mt-8">
                    <div className="px-3 mb-4">
                        <h3 className="text-xs font-semibold text-cream-400 uppercase tracking-wider">
                            {!collapsed && "SUPPORT"}
                        </h3>
                    </div>
                    <div className="space-y-1">
                        {supportNavigation.map((item) => (
                            <Link
                                key={item.name}
                                href={item.href}
                                className="group flex items-center px-3 py-2.5 text-sm font-medium text-cream-300 rounded-lg hover:bg-primary-800 hover:text-cream-50 transition-all duration-200"
                            >
                                <item.icon className="mr-3 h-5 w-5 flex-shrink-0 text-cream-300 group-hover:text-cream-50" />
                                {!collapsed && (
                                    <span className="truncate">{item.name}</span>
                                )}
                            </Link>
                        ))}
                    </div>
                </div>
            </div>


            {/* User Profile */}
            <div className="px-4 py-4 border-t border-primary-600">
                <div className="flex items-center">
                    <div className="w-8 h-8 bg-gradient-warm rounded-full flex items-center justify-center glow-orange">
                        <Users className="h-4 w-4 text-white" />
                    </div>
                    {!collapsed && (
                        <div className="ml-3">
                            {loading ? (
                                <div className="space-y-1">
                                    <div className="h-4 w-20 bg-primary-700 rounded animate-pulse"></div>
                                    <div className="h-3 w-24 bg-primary-700 rounded animate-pulse"></div>
                                </div>
                            ) : (
                                <>
                                    <p className="text-sm font-medium text-cream-50">{userName}</p>
                                    <p className="text-xs text-cream-300">{userEmail}</p>
                                </>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
