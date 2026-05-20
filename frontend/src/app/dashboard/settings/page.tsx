'use client'

import React, { useState, useEffect, Suspense } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useToast } from "@/components/ui/use-toast"
import {
  Settings as SettingsIcon,
  Shield,
  Clock,
} from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import dynamic from 'next/dynamic'

// Lazy load heavy components
const PrivacyTab = dynamic(() => import('./components/privacy-tab'), {
  loading: () => <div className="animate-pulse bg-muted rounded-lg h-64" />
})

const HistoryTab = dynamic(() => import('./components/history-tab'), {
  loading: () => <div className="animate-pulse bg-muted rounded-lg h-64" />
})

export default function SettingsPage() {
  const { user } = useAuth()
  const { toast: _toast } = useToast()
  const [activeTab, setActiveTab] = useState("privacy")

  // Handle URL tab parameter
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const tab = urlParams.get('tab')
    if (tab && ['privacy', 'history'].includes(tab)) {
      setActiveTab(tab)
    }
  }, [])

  if (!user) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="mx-auto max-w-4xl space-y-6">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-4xl space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground flex items-center">
              <SettingsIcon className="mr-3 h-8 w-8" />
              Settings
            </h1>
            <p className="text-muted-foreground">Configure your application preferences and privacy settings</p>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 bg-muted border border-border">
            <TabsTrigger value="privacy" className="data-[state=active]:bg-card data-[state=active]:text-foreground text-muted-foreground">
              <Shield className="mr-2 h-4 w-4" />
              Privacy
            </TabsTrigger>
            <TabsTrigger value="history" className="data-[state=active]:bg-card data-[state=active]:text-foreground text-muted-foreground">
              <Clock className="mr-2 h-4 w-4" />
              Change History
            </TabsTrigger>
          </TabsList>

          {/* Lazy loaded tab content */}
          <Suspense fallback={<div className="animate-pulse bg-muted rounded-lg h-64" />}>
            <TabsContent value="privacy" className="space-y-6">
              <PrivacyTab userId={user.id} />
            </TabsContent>
          </Suspense>

          <Suspense fallback={<div className="animate-pulse bg-muted rounded-lg h-64" />}>
            <TabsContent value="history" className="space-y-6">
              <HistoryTab userId={user.id} />
            </TabsContent>
          </Suspense>
        </Tabs>
      </div>
    </div>
  )
}
