"use client"

import { useState, useEffect, type ReactNode } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
    Search,
    Bell,
    Settings,
    User,
    ChevronDown,
    LayoutGrid,
    Sun,
    Moon,
    LogOut
} from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { useTheme } from "@/contexts/theme-context"
import { JobSearchModal } from "@/components/job-search-modal"
import { CreditsBalanceBadge } from '@/components/credits/credits-balance-badge'

interface SophisticatedHeaderProps {
    notificationCount?: number
    navigationControl?: ReactNode
}

const iconControl = "inline-flex size-11 shrink-0 items-center justify-center rounded-sm text-app-text/70 hover:bg-app-text/5 hover:text-app-text focus-visible:outline-2 focus-visible:outline-offset-2"

export function SophisticatedHeader({
    notificationCount = 2,
    navigationControl
}: SophisticatedHeaderProps) {
    const [searchQuery, setSearchQuery] = useState("")
    const [isSearchModalOpen, setIsSearchModalOpen] = useState(false)
    const { user, loading, signOutUser } = useAuth()
    const { isDark, toggleTheme } = useTheme()
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
        <header className="sticky top-0 z-40 flex h-24 items-center justify-between gap-1 border-b border-app-text/5 bg-app-bg/80 px-2 backdrop-blur-md transition-colors duration-300 @min-[540px]:px-4 @min-[900px]:gap-6 @min-[900px]:px-6">
            <div className="flex min-w-0 flex-1 items-center gap-3 @min-[900px]:gap-6">
                {navigationControl}
                <div className="hidden shrink-0 items-center gap-3 @min-[540px]:flex">
                    <div className="w-10 h-10 border border-app-text/10 flex items-center justify-center bg-app-card shadow-sm rounded-sm">
                        <LayoutGrid className="w-5 h-5 text-app-text" />
                    </div>
                    <Link href="/dashboard">
                        <h1 className="text-xl font-light tracking-tight text-app-text">Prism <span className="font-serif-italic font-medium text-app-accent">Pro</span></h1>
                    </Link>
                </div>

                {/* Search Bar */}
                <div className="relative hidden min-w-0 w-full max-w-80 @min-[900px]:block">
                    <Search aria-hidden="true" className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-app-text opacity-40" />
                    <input
                        type="text"
                        aria-label="Search jobs and companies"
                        placeholder="Search jobs, companies... (⌘F)"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onFocus={() => setIsSearchModalOpen(true)}
                        className="h-11 w-full rounded-sm border border-app-text/10 bg-app-card pl-11 pr-3 text-xs font-medium text-app-text placeholder:text-app-text/60 focus-visible:outline-2 focus-visible:outline-offset-2"
                    />
                </div>
            </div>

            <div className="flex shrink-0 items-center gap-1 @min-[540px]:gap-2">
                <div className="flex items-center gap-1 @min-[540px]:gap-2">
                    <CreditsBalanceBadge />
                    {/* Search Icon Mobile */}
                    <button
                        type="button"
                        aria-label="Search jobs and companies"
                        onClick={() => setIsSearchModalOpen(true)}
                        className={`${iconControl} @min-[900px]:hidden`}
                    >
                        <Search className="w-5 h-5" />
                    </button>

                    {/* Notifications */}
                    <div className="relative hidden @min-[540px]:block" aria-label={`${notificationCount} notifications`}>
                        <Bell className="w-5 h-5 text-app-text opacity-40 group-hover:opacity-100 transition-opacity" />
                        {notificationCount > 0 && (
                            <span className="absolute -top-1.5 -right-1.5 w-3.5 h-3.5 bg-app-text text-app-bg text-[8px] flex items-center justify-center font-bold rounded-sm shadow-sm">
                                {notificationCount}
                            </span>
                        )}
                    </div>

                    <Link
                        href="/dashboard/settings"
                        aria-label="Settings"
                        className={`${iconControl} hidden @min-[420px]:inline-flex`}
                    >
                        <Settings aria-hidden="true" className="size-5" />
                    </Link>

                    {/* Theme Toggle Wrapper */}
                    <button
                        type="button"
                        onClick={toggleTheme}
                        className={`${iconControl} relative`}
                        aria-label="Toggle theme"
                    >
                        <Sun className={`w-5 h-5 absolute transition-all duration-500 ${isDark ? 'rotate-90 scale-0 opacity-0' : 'rotate-0 scale-100 opacity-100'}`} />
                        <Moon className={`w-5 h-5 absolute transition-all duration-500 ${isDark ? 'rotate-0 scale-100 opacity-100' : '-rotate-90 scale-0 opacity-0'}`} />
                    </button>
                </div>

                {/* User Dropdown */}
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <button type="button" aria-label="Account menu" className="group flex min-h-11 shrink-0 items-center gap-2 rounded-sm select-none focus-visible:outline-2 focus-visible:outline-offset-2">
                            <span className="hidden max-w-36 text-right @min-[900px]:block">
                                <span className="block truncate text-xs font-extrabold uppercase tracking-tighter text-app-text">
                                    {loading ? 'Loading...' : userName}
                                </span>
                                <span className="block text-[10px] text-app-text opacity-50 italic font-medium">Professional Account</span>
                            </span>
                            <span className="flex size-11 shrink-0 items-center justify-center rounded-sm border border-app-text/10 bg-app-card text-xs font-bold text-app-text shadow-sm transition-colors group-hover:bg-app-text group-hover:text-app-bg">
                                {user?.email?.[0].toUpperCase() || 'U'}
                            </span>
                            <ChevronDown aria-hidden="true" className="hidden size-3 text-app-text/60 @min-[900px]:block" />
                        </button>
                    </DropdownMenuTrigger>

                    <DropdownMenuContent align="end" className="w-56 bg-card text-card-foreground backdrop-blur-xl border border-border shadow-xl rounded-sm p-0">
                        <div className="p-4 border-b border-border bg-muted">
                            <p className="text-xs font-bold text-foreground uppercase tracking-wider [overflow-wrap:anywhere]">{userName}</p>
                            <p className="mt-1 text-[10px] text-muted-foreground [overflow-wrap:anywhere]">{userEmail}</p>
                        </div>
                        <div className="p-2">
                            <DropdownMenuItem
                                onClick={handleProfileClick}
                                className="text-xs font-bold tracking-wide text-foreground/80 hover:text-foreground hover:bg-muted focus:bg-muted cursor-pointer py-3 rounded-sm mb-1 uppercase"
                            >
                                <User className="mr-3 h-4 w-4 opacity-70" />
                                PROFILE
                            </DropdownMenuItem>
                            <DropdownMenuItem
                                onClick={handleSettingsClick}
                                className="text-xs font-bold tracking-wide text-foreground/80 hover:text-foreground hover:bg-muted focus:bg-muted cursor-pointer py-3 rounded-sm mb-1 uppercase"
                            >
                                <Settings className="mr-3 h-4 w-4 opacity-70" />
                                SETTINGS
                            </DropdownMenuItem>
                            <DropdownMenuSeparator className="bg-border my-1" />
                            <DropdownMenuItem
                                onClick={async () => {
                                    try {
                                        await signOutUser()
                                    } catch (error) {
                                        console.error('Error signing out:', error)
                                    }
                                }}
                                className="text-xs font-bold tracking-wide text-destructive/85 hover:text-destructive hover:bg-destructive/10 focus:bg-destructive/10 cursor-pointer py-3 rounded-sm uppercase"
                            >
                                <LogOut className="mr-3 h-4 w-4" />
                                <span>LOG OUT</span>
                            </DropdownMenuItem>
                        </div>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>

            {/* Global Search Modal */}
            <JobSearchModal
                isOpen={isSearchModalOpen}
                onClose={() => setIsSearchModalOpen(false)}
                initialQuery={searchQuery}
            />
        </header>
    )
}
