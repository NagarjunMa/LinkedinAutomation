"use client"

import { useAuth } from "@/contexts/auth-context"
import { useEffect, useState } from "react"
import { createClient } from "@/lib/supabase"

export function AuthDebug() {
  const { user, session, loading } = useAuth()
  const [authEvents, setAuthEvents] = useState<string[]>([])

  useEffect(() => {
    const supabase = createClient()

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        const timestamp = new Date().toLocaleTimeString()
        const eventData = `${timestamp}: ${event} - hasSession: ${!!session} - userId: ${session?.user?.id || 'none'}`

        setAuthEvents(prev => {
          const newEvents = [eventData, ...prev.slice(0, 9)] // Keep last 10 events
          return newEvents
        })
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  if (process.env.NODE_ENV !== 'development') {
    return null
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 10,
        right: 10,
        width: 400,
        maxHeight: 300,
        background: 'rgba(0,0,0,0.9)',
        color: 'white',
        padding: 10,
        borderRadius: 8,
        fontSize: 11,
        fontFamily: 'monospace',
        zIndex: 9999,
        overflow: 'auto'
      }}
    >
      <div style={{ marginBottom: 10, fontWeight: 'bold', borderBottom: '1px solid #333', paddingBottom: 5 }}>
        🔍 Auth Debug Panel
      </div>

      <div style={{ marginBottom: 10 }}>
        <strong>Current State:</strong><br />
        Loading: {loading ? '✅' : '❌'}<br />
        User: {user ? `✅ ${user.email}` : '❌ None'}<br />
        Session: {session ? '✅ Valid' : '❌ None'}<br />
        UserId: {user?.id || 'None'}
      </div>

      <div>
        <strong>Recent Events:</strong><br />
        {authEvents.length === 0 ? (
          <div style={{ color: '#666' }}>No events yet...</div>
        ) : (
          authEvents.map((event, i) => (
            <div
              key={i}
              style={{
                fontSize: 10,
                marginBottom: 2,
                color: event.includes('SIGNED_OUT') ? '#ff6b6b' :
                      event.includes('SIGNED_IN') ? '#4ecdc4' :
                      event.includes('TOKEN_REFRESHED') ? '#ffe66d' : '#c7c7c7'
              }}
            >
              {event}
            </div>
          ))
        )}
      </div>
    </div>
  )
}