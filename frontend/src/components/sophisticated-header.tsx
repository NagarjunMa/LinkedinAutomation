"use client"

import { useState, useEffect } from "react"
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
    Menu,
    LayoutGrid,
    Sun,
    Moon,
    LogOut
} from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { useTheme } from "@/contexts/theme-context"
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
        <header className="flex items-center justify-between h-24 bg-app-bg bg-opacity-80 border-b border-app-text border-opacity-5 px-6 backdrop-blur-md sticky top-0 z-40 transition-colors duration-300">
            <div className="flex items-center gap-8">
                {/* Mobile Menu Toggle */}
                {onMenuClick && (
                    <button
                        onClick={onMenuClick}
                        className="lg:hidden p-2 -ml-2 text-app-text opacity-50 hover:opacity-100 transition-opacity"
                    >
                        <Menu className="w-5 h-5" />
                    </button>
                )}

                <div className="flex items-center gap-4">
                    <div className="w-10 h-10 border border-app-text border-opacity-10 flex items-center justify-center bg-app-card hidden sm:flex shadow-sm rounded-sm">
                        <LayoutGrid className="w-5 h-5 text-app-text" />
                    </div>
                    <Link href="/dashboard" className="hidden sm:block">
                        <h1 className="text-xl font-light tracking-tight text-app-text">Prism <span className="font-serif-italic font-medium text-app-accent">Pro</span></h1>
                    </Link>
                </div>

                <div className="h-8 w-px bg-app-text bg-opacity-10 hidden md:block" />

                {/* Search Bar */}
                <div className="relative group hidden md:block">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-app-text opacity-40" />
                    <input
                        type="text"
                        placeholder="Search jobs, companies... (⌘F)"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onFocus={() => setIsSearchModalOpen(true)}
                        className="bg-app-card border border-app-text border-opacity-10 pl-11 pr-6 py-2.5 text-xs w-80 focus:outline-none focus:border-app-text focus:border-opacity-30 transition-all duration-700 font-medium rounded-sm text-app-text placeholder:text-app-text placeholder:opacity-30"
                    />
                </div>
            </div>

            <div className="flex items-center gap-4 sm:gap-8">
                <div className="flex gap-4 sm:gap-6 items-center">
                    {/* Search Icon Mobile */}
                    <button
                        onClick={() => setIsSearchModalOpen(true)}
                        className="md:hidden text-app-text opacity-40 hover:opacity-100 transition-opacity"
                    >
                        <Search className="w-5 h-5" />
                    </button>

                    {/* Notifications */}
                    <div className="relative cursor-pointer group">
                        <Bell className="w-5 h-5 text-app-text opacity-40 group-hover:opacity-100 transition-opacity" />
                        {notificationCount > 0 && (
                            <span className="absolute -top-1.5 -right-1.5 w-3.5 h-3.5 bg-app-text text-app-bg text-[8px] flex items-center justify-center font-bold rounded-sm shadow-sm">
                                {notificationCount}
                            </span>
                        )}
                    </div>

                    <Settings
                        onClick={handleSettingsClick}
                        className="w-5 h-5 text-app-text opacity-40 hover:opacity-100 transition-opacity cursor-pointer"
                    />

                    {/* Theme Toggle Wrapper */}
                    <button
                        onClick={toggleTheme}
                        className="text-app-text opacity-40 hover:opacity-100 transition-opacity cursor-pointer relative w-5 h-5 flex items-center justify-center"
                        aria-label="Toggle theme"
                    >
                        <Sun className={`w-5 h-5 absolute transition-all duration-500 ${isDark ? 'rotate-90 scale-0 opacity-0' : 'rotate-0 scale-100 opacity-100'}`} />
                        <Moon className={`w-5 h-5 absolute transition-all duration-500 ${isDark ? 'rotate-0 scale-100 opacity-100' : '-rotate-90 scale-0 opacity-0'}`} />
                    </button>
                </div>

                <div className="h-8 w-px bg-app-text bg-opacity-10 hidden sm:block" />

                {/* User Dropdown */}
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <div className="flex items-center gap-4 cursor-pointer group select-none">
                            <div className="text-right hidden sm:block">
                                <p className="text-xs font-extrabold uppercase tracking-tighter text-app-text">
                                    {loading ? 'Loading...' : userName}
                                </p>
                                <p className="text-[10px] text-app-text opacity-50 italic font-medium">Professional Account</p>
                            </div>
                            <div className="w-10 h-10 bg-app-card border border-app-text border-opacity-10 flex items-center justify-center text-xs font-bold group-hover:bg-app-text group-hover:text-app-bg transition-all duration-700 text-app-text shadow-sm rounded-sm">
                                {user?.email?.[0].toUpperCase() || 'U'}
                            </div>
                            <ChevronDown className="w-3 h-3 text-app-text opacity-30" />
                        </div>
                    </DropdownMenuTrigger>

                    <DropdownMenuContent align="end" className="w-56 bg-app-card backdrop-blur-xl border border-app-text border-opacity-10 shadow-xl rounded-sm p-0">
                        <div className="p-4 border-b border-app-text border-opacity-5 bg-app-text bg-opacity-5">
                            <p className="font-bold text-app-text text-xs uppercase tracking-wider">{userName}</p>
                            <p className="text-[10px] text-app-text opacity-40 font-mono">{userEmail}</p>
                        </div>
                        <div className="p-2">
                            <DropdownMenuItem
                                onClick={handleProfileClick}
                                className="text-xs font-bold tracking-wide text-app-text opacity-70 hover:opacity-100 hover:bg-app-text hover:bg-opacity-5 focus:bg-app-text focus:bg-opacity-5 cursor-pointer py-3 rounded-sm mb-1 uppercase"
                            >
                                <User className="mr-3 h-4 w-4 opacity-70" />
                                PROFILE
                            </DropdownMenuItem>
                            <DropdownMenuItem
                                onClick={handleSettingsClick}
                                className="text-xs font-bold tracking-wide text-app-text opacity-70 hover:opacity-100 hover:bg-app-text hover:bg-opacity-5 focus:bg-app-text focus:bg-opacity-5 cursor-pointer py-3 rounded-sm mb-1 uppercase"
                            >
                                <Settings className="mr-3 h-4 w-4 opacity-70" />
                                SETTINGS
                            </DropdownMenuItem>
                            <DropdownMenuSeparator className="bg-app-text bg-opacity-10 my-1" />
                            <DropdownMenuItem
                                onClick={async () => {
                                    try {
                                        await signOutUser()
                                    } catch (error) {
                                        console.error('Error signing out:', error)
                                    }
                                }}
                                className="text-xs font-bold tracking-wide text-red-500 opacity-70 hover:opacity-100 hover:bg-red-500 hover:bg-opacity-10 focus:bg-red-500 focus:bg-opacity-10 cursor-pointer py-3 rounded-sm uppercase"
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
