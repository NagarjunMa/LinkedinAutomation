"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
    Search,
    Bell,
    Settings,
    User,
    ChevronDown,
    Menu
} from "lucide-react"
import { Input } from "@/components/ui/input"
import { useAuth } from "@/contexts/auth-context"
import { ThemeToggle } from "@/components/theme-toggle"
import { Logo } from "@/components/logo"
import { JobSearchModal } from "@/components/job-search-modal"

interface SophisticatedHeaderProps {
    notificationCount?: number
    onMenuClick?: () => void
}

export function SophisticatedHeader({
    notificationCount = 2,
    onMenuClick
}: SophisticatedHeaderProps) {
    const [searchQuery, setSearchQuery] = useState("")
    const [isSearchModalOpen, setIsSearchModalOpen] = useState(false)
    const { user, loading, signOutUser } = useAuth()
    const router = useRouter()

    const userName = user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User'
    const userEmail = user?.email || ''

    const handleProfileClick = () => {
        router.push('/dashboard/profile')
    }

    const handleSettingsClick = () => {
        router.push('/dashboard/settings')
    }

    // Keyboard shortcut for search (Cmd+F)
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'f') {
                e.preventDefault()
                setIsSearchModalOpen(true)
            }
        }

        document.addEventListener('keydown', handleKeyDown)
        return () => document.removeEventListener('keydown', handleKeyDown)
    }, [])

    return (
        <div className="bg-primary-900 border-b border-primary-600">
            {/* Main Header */}
            <div className="px-3 sm:px-4 lg:px-6 py-3 sm:py-4">
                <div className="flex items-center justify-between">
                    {/* Left side - Mobile menu + Logo */}
                    <div className="flex items-center space-x-3 sm:space-x-4">
                        {/* Mobile menu button */}
                        {onMenuClick && (
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={onMenuClick}
                                className="h-10 w-10 p-0 text-cream-50 hover:text-accent-400 hover:bg-primary-800/80 transition-all duration-200 lg:hidden border border-primary-600/50 hover:border-accent-500/50 backdrop-blur-sm"
                                aria-label="Open navigation menu"
                            >
                                <Menu className="h-6 w-6" />
                            </Button>
                        )}

                        {/* Logo and Title */}
                        <Link href="/dashboard" className="flex items-center space-x-2 sm:space-x-3 hover:opacity-80 transition-opacity">
                            <Logo size={32} showText={false} />
                            <div className="hidden sm:block">
                                <h1 className="text-lg sm:text-xl font-semibold text-cream-50">JobFlow Pro</h1>
                                <p className="text-xs sm:text-sm text-cream-300">Job Search Assistant</p>
                            </div>
                        </Link>
                    </div>

                    {/* Right side - Search and User actions */}
                    <div className="flex items-center space-x-2 sm:space-x-4 lg:space-x-6">
                        {/* Search Bar - Hidden on mobile */}
                        <div className="hidden md:block relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-cream-300" />
                            <Input
                                placeholder="Search jobs, companies..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onFocus={() => setIsSearchModalOpen(true)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' || e.key === ' ') {
                                        setIsSearchModalOpen(true)
                                    }
                                }}
                                className="pl-10 pr-4 py-2 w-60 lg:w-80 bg-primary-800 border-primary-600 text-cream-50 placeholder-cream-300 focus:border-accent-500 focus:ring-accent-500 transition-all duration-200 cursor-pointer"
                                readOnly
                            />
                            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                                <kbd className="px-1.5 py-0.5 text-xs font-semibold text-cream-300 bg-primary-700 border border-primary-500 rounded">
                                    ⌘F
                                </kbd>
                            </div>
                        </div>

                        {/* Mobile search button */}
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setIsSearchModalOpen(true)}
                            className="h-8 w-8 p-0 text-cream-300 hover:text-cream-50 hover:bg-primary-800 transition-all duration-200 md:hidden"
                        >
                            <Search className="h-4 w-4" />
                        </Button>

                        {/* Notifications */}
                        <div className="relative">
                            <Button variant="ghost" size="sm" className="relative p-2 text-cream-300 hover:text-cream-50 hover:bg-primary-800 transition-all duration-200">
                                <Bell className="h-4 w-4 sm:h-5 sm:w-5" />
                                {notificationCount > 0 && (
                                    <Badge className="absolute -top-1 -right-1 h-4 w-4 sm:h-5 sm:w-5 flex items-center justify-center p-0 text-xs bg-gradient-warm text-white border-0 glow-orange">
                                        {notificationCount}
                                    </Badge>
                                )}
                            </Button>
                        </div>

                        {/* Settings - Hidden on mobile */}
                        <Button variant="ghost" size="sm" className="hidden sm:flex p-2 text-cream-300 hover:text-cream-50 hover:bg-primary-800 transition-all duration-200">
                            <Settings className="h-4 w-4 sm:h-5 sm:w-5" />
                        </Button>

                        {/* Theme Toggle */}
                        <ThemeToggle />

                        {/* User Profile Dropdown */}
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" className="flex items-center space-x-2 sm:space-x-3 p-2 hover:bg-primary-800 transition-all duration-200">
                                    <div className="w-7 h-7 sm:w-8 sm:h-8 bg-gradient-warm rounded-full flex items-center justify-center glow-orange">
                                        <User className="h-3 w-3 sm:h-4 sm:w-4 text-white" />
                                    </div>
                                    <div className="text-left hidden sm:block">
                                        {loading ? (
                                            <div className="space-y-1">
                                                <div className="h-4 w-20 bg-primary-700 rounded animate-pulse"></div>
                                                <div className="h-3 w-16 bg-primary-700 rounded animate-pulse"></div>
                                            </div>
                                        ) : (
                                            <>
                                                <p className="text-sm font-medium text-cream-50">Hello, {userName.split(' ')[0]}!</p>
                                                <p className="text-xs text-cream-300">Welcome back!</p>
                                            </>
                                        )}
                                    </div>
                                    <ChevronDown className="h-3 w-3 sm:h-4 sm:w-4 text-cream-300" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-56 bg-primary-800 border-primary-600 shadow-card-elevated">
                                <DropdownMenuLabel className="text-cream-50">
                                    <div>
                                        <p className="font-medium">{userName}</p>
                                        <p className="text-xs text-cream-300">{userEmail}</p>
                                    </div>
                                </DropdownMenuLabel>
                                <DropdownMenuSeparator className="bg-primary-600" />
                                <DropdownMenuItem
                                    className="text-cream-50 hover:bg-primary-700 transition-colors duration-200 cursor-pointer"
                                    onClick={handleProfileClick}
                                >
                                    <User className="mr-2 h-4 w-4" />
                                    <span>Profile</span>
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                    className="text-cream-50 hover:bg-primary-700 transition-colors duration-200 cursor-pointer"
                                    onClick={handleSettingsClick}
                                >
                                    <Settings className="mr-2 h-4 w-4" />
                                    <span>Settings</span>
                                </DropdownMenuItem>
                                <DropdownMenuSeparator className="bg-primary-600" />
                                <DropdownMenuItem
                                    className="text-red-400 hover:bg-primary-700 transition-colors duration-200"
                                    onClick={async () => {
                                        try {
                                            await signOutUser()
                                        } catch (error) {
                                            console.error('Error signing out:', error)
                                        }
                                    }}
                                >
                                    <span>Log out</span>
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </div>
            </div>

            {/* Search Modal */}
            <JobSearchModal
                isOpen={isSearchModalOpen}
                onClose={() => setIsSearchModalOpen(false)}
                initialQuery={searchQuery}
            />
        </div>
    )
}
