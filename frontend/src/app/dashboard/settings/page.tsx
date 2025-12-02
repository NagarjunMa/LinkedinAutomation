'use client'

import React, { useState, useEffect, Suspense } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useToast } from "@/components/ui/use-toast"
import {
  Settings as SettingsIcon,
  Bell,
  Mail,
  Shield,
  Clock,
  Zap,
} from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import dynamic from 'next/dynamic'

// Lazy load heavy components
const NotificationsTab = dynamic(() => import('./components/notifications-tab'), {
  loading: () => <div className="animate-pulse bg-primary-800 rounded-lg h-64" />
})

const EmailTab = dynamic(() => import('./components/email-tab'), {
  loading: () => <div className="animate-pulse bg-primary-800 rounded-lg h-64" />
})

const PrivacyTab = dynamic(() => import('./components/privacy-tab'), {
  loading: () => <div className="animate-pulse bg-primary-800 rounded-lg h-64" />
})

const HistoryTab = dynamic(() => import('./components/history-tab'), {
  loading: () => <div className="animate-pulse bg-primary-800 rounded-lg h-64" />
})

const EmailScanningTab = dynamic(() => import('@/components/email-scanning-settings'), {
  loading: () => <div className="animate-pulse bg-primary-800 rounded-lg h-64" />
})

export default function SettingsPage() {
  const { user } = useAuth()
  const { toast: _toast } = useToast()
  const [activeTab, setActiveTab] = useState("notifications")

  // Handle URL tab parameter
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const tab = urlParams.get('tab')
    if (tab && ['notifications', 'email', 'privacy', 'history', 'email-scanning'].includes(tab)) {
      setActiveTab(tab)
    }
  }, [])

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
        <div className="mx-auto max-w-4xl space-y-6">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-primary-950 p-6">
      <div className="mx-auto max-w-4xl space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-cream-50 flex items-center">
              <SettingsIcon className="mr-3 h-8 w-8" />
              Settings
            </h1>
            <p className="text-cream-300">Configure your application preferences and privacy settings</p>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5 bg-primary-800 border-primary-600">
            <TabsTrigger value="notifications" className="data-[state=active]:bg-gradient-warm text-cream-50">
              <Bell className="mr-2 h-4 w-4" />
              Notifications
            </TabsTrigger>
            <TabsTrigger value="email" className="data-[state=active]:bg-gradient-warm text-cream-50">
              <Mail className="mr-2 h-4 w-4" />
              Email Tracking
            </TabsTrigger>
            <TabsTrigger value="email-scanning" className="data-[state=active]:bg-gradient-warm text-cream-50">
              <Zap className="mr-2 h-4 w-4" />
              Email Scanning
            </TabsTrigger>
            <TabsTrigger value="privacy" className="data-[state=active]:bg-gradient-warm text-cream-50">
              <Shield className="mr-2 h-4 w-4" />
              Privacy
            </TabsTrigger>
            <TabsTrigger value="history" className="data-[state=active]:bg-gradient-warm text-cream-50">
              <Clock className="mr-2 h-4 w-4" />
              Change History
            </TabsTrigger>
          </TabsList>

          {/* Lazy loaded tab content */}
          <Suspense fallback={<div className="animate-pulse bg-primary-800 rounded-lg h-64" />}>
            <TabsContent value="notifications" className="space-y-6">
              <NotificationsTab userId={user.id} />
            </TabsContent>
          </Suspense>

          <Suspense fallback={<div className="animate-pulse bg-primary-800 rounded-lg h-64" />}>
            <TabsContent value="email" className="space-y-6">
              <EmailTab userId={user.id} />
            </TabsContent>
          </Suspense>

          <Suspense fallback={<div className="animate-pulse bg-primary-800 rounded-lg h-64" />}>
            <TabsContent value="email-scanning" className="space-y-6">
              <EmailScanningTab userId={user.id} />
            </TabsContent>
          </Suspense>

          <Suspense fallback={<div className="animate-pulse bg-primary-800 rounded-lg h-64" />}>
            <TabsContent value="privacy" className="space-y-6">
              <PrivacyTab userId={user.id} />
            </TabsContent>
          </Suspense>

          <Suspense fallback={<div className="animate-pulse bg-primary-800 rounded-lg h-64" />}>
            <TabsContent value="history" className="space-y-6">
              <HistoryTab userId={user.id} />
            </TabsContent>
          </Suspense>
        </Tabs>
      </div>
    </div>
  )
}