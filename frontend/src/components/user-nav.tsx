"use client"

import { useRouter } from "next/navigation"
import {
    Avatar,
    AvatarFallback,
    AvatarImage,
} from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuShortcut,
    DropdownMenuTrigger,
    DropdownMenuGroup,
} from "@/components/ui/dropdown-menu"
import { useAuth } from "@/contexts/auth-context"
import { LogOut, User, Settings, Mail } from "lucide-react"

export function UserNav() {
    const { user, signOutUser } = useAuth()
    const router = useRouter()

    const handleSignOut = async () => {
        try {
            await signOutUser()
            // The signOutUser function already handles redirect to landing page
        } catch (error) {
            console.error('Error signing out:', error)
        }
    }

    const handleProfileClick = () => {
        router.push('/dashboard/profile')
    }

    const handleSettingsClick = () => {
        router.push('/dashboard/settings')
    }

    const handleEmailSettingsClick = () => {
        router.push('/dashboard/settings?tab=email')
    }

    const getUserInitials = (email: string) => {
        return email.split('@')[0].substring(0, 2).toUpperCase()
    }

    if (!user) {
        return null
    }

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                    <Avatar className="h-8 w-8">
                        <AvatarImage src={user.user_metadata?.avatar_url} alt={user.email || 'User'} />
                        <AvatarFallback>
                            {user.email ? getUserInitials(user.email) : 'U'}
                        </AvatarFallback>
                    </Avatar>
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
                <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium leading-none">
                            {user.user_metadata?.full_name || user.email?.split('@')[0] || 'User'}
                        </p>
                        <p className="text-xs leading-none text-muted-foreground">
                            {user.email}
                        </p>
                    </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuGroup>
                    <DropdownMenuItem onClick={handleProfileClick}>
                        <User className="mr-2 h-4 w-4" />
                        Profile
                        <DropdownMenuShortcut>⇧⌘P</DropdownMenuShortcut>
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={handleEmailSettingsClick}>
                        <Mail className="mr-2 h-4 w-4" />
                        Email Settings
                        <DropdownMenuShortcut>⌘E</DropdownMenuShortcut>
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={handleSettingsClick}>
                        <Settings className="mr-2 h-4 w-4" />
                        Settings
                        <DropdownMenuShortcut>⌘S</DropdownMenuShortcut>
                    </DropdownMenuItem>
                </DropdownMenuGroup>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleSignOut}>
                    <LogOut className="mr-2 h-4 w-4" />
                    Sign out
                    <DropdownMenuShortcut>⇧⌘Q</DropdownMenuShortcut>
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    )
} 