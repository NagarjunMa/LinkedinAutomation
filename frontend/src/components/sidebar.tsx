"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Logo } from "@/components/logo"
import {
  BarChart3,
  Briefcase,
  FileText,
  Home,
} from "lucide-react"

const navigation = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: Home,
  },
  {
    name: "Jobs",
    href: "/dashboard/jobs",
    icon: Briefcase,
  },
  {
    name: "Resume",
    href: "/dashboard/resume-evaluation",
    icon: FileText,
  },
  {
    name: "Analytics",
    href: "/dashboard/analytics",
    icon: BarChart3,
  },
]

interface SidebarProps {
  className?: string
}

export function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname()

  return (
    <div className={cn(
      "flex h-full w-16 flex-col bg-white/70 backdrop-blur-md border-r border-gray-100/50",
      className
    )}>
      {/* Logo */}
      <div className="flex h-16 items-center justify-center border-b border-gray-100/50">
        <Logo size={24} showText={false} />
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-8">
        <div className="space-y-4">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "group flex h-12 w-12 items-center justify-center rounded-2xl transition-all duration-300 relative",
                  isActive
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-500/25"
                    : "text-gray-400 hover:bg-gray-100 hover:text-gray-700"
                )}
                title={item.name}
              >
                <item.icon className="h-5 w-5" />
                {isActive && (
                  <div className="absolute -right-1 top-1/2 h-6 w-1 -translate-y-1/2 rounded-full bg-blue-600" />
                )}
              </Link>
            )
          })}
        </div>
      </nav>
    </div>
  )
}