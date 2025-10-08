import { Toaster } from "@/components/ui/toaster"
import { ThemeSwitcher } from "@/components/theme-switcher"
import { Logo } from "@/components/logo"

export default function JobsLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <div className="min-h-screen bg-background">
            <div className="border-b">
                <div className="flex h-16 items-center px-4">
                    <Logo size={32} showText={false} />
                    <div className="flex items-center space-x-4 ml-6">
                        <nav className="flex items-center space-x-4">
                            <a
                                href="/dashboard"
                                className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
                            >
                                Dashboard
                            </a>
                            <a
                                href="/jobs"
                                className="text-sm font-medium transition-colors hover:text-primary"
                            >
                                Jobs
                            </a>
                        </nav>
                    </div>
                    <div className="ml-auto flex items-center space-x-4">
                        <ThemeSwitcher />
                    </div>
                </div>
            </div>
            {children}
            <Toaster />
        </div>
    )
} 