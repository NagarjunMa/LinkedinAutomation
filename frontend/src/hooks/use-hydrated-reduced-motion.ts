"use client"

import { useEffect, useState } from 'react'
import { useReducedMotion } from 'framer-motion'

/**
 * Keep the server render and first client render identical, then honor the
 * visitor's reduced-motion preference after hydration.
 */
export function useHydratedReducedMotion(): boolean {
  const prefersReducedMotion = useReducedMotion()
  const [hydrated, setHydrated] = useState(false)

  useEffect(() => {
    setHydrated(true)
  }, [])

  return hydrated && prefersReducedMotion === true
}
