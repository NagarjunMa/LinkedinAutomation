/**
 * Reusable Dashboard Skeleton Components
 * Optimized for progressive loading and user experience
 */

import React from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

// Base skeleton component with animation
export function Skeleton({
  className,
  delay = 0,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0.6 }}
      animate={{ opacity: [0.6, 1, 0.6] }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        delay,
        ease: "easeInOut"
      }}
      className={cn("bg-app-text/10 rounded", className)}
      {...props}
    />
  )
}

// Job Stats Card Skeleton
export function JobStatsSkeleton() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
    >
      {Array.from({ length: 3 }).map((_, i) => (
        <div
          key={i}
          className="p-6 bg-app-card/40 border border-app-text/10 backdrop-blur-sm rounded-lg"
        >
          <div className="flex items-center justify-between mb-4">
            <Skeleton className="h-5 w-24" delay={i * 100} />
            <Skeleton className="h-8 w-8 rounded-full" delay={i * 100 + 50} />
          </div>
          <Skeleton className="h-8 w-16 mb-2" delay={i * 100 + 100} />
          <Skeleton className="h-3 w-32" delay={i * 100 + 150} />
        </div>
      ))}
    </motion.div>
  )
}

// Chart Skeleton
export function ChartSkeleton({ height = "h-64" }: { height?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
      className="p-6 bg-app-card/40 border border-app-text/10 backdrop-blur-sm rounded-lg"
    >
      {/* Chart Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <Skeleton className="h-6 w-40 mb-2" />
          <Skeleton className="h-3 w-64" delay={100} />
        </div>
        <div className="flex gap-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton
              key={i}
              className="h-8 w-16 rounded-full"
              delay={i * 50}
            />
          ))}
        </div>
      </div>

      {/* Chart Area */}
      <div className={cn("relative overflow-hidden rounded mb-4", height)}>
        <Skeleton className="w-full h-full" />
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-app-text/5 to-transparent animate-pulse" />
      </div>

      {/* Chart Legend */}
      <div className="flex items-center gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex items-center gap-2">
            <Skeleton className="w-3 h-3 rounded-full" delay={i * 50} />
            <Skeleton className="h-3 w-16" delay={i * 50 + 25} />
          </div>
        ))}
      </div>
    </motion.div>
  )
}

// Table Skeleton
export function TableSkeleton({
  rows = 5,
  columns = 4,
  title = "Recent Activity"
}: {
  rows?: number
  columns?: number
  title?: string
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="p-6 bg-app-card/40 border border-app-text/10 backdrop-blur-sm rounded-lg"
    >
      {/* Table Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <Skeleton className="h-6 w-32 mb-2" />
          <Skeleton className="h-3 w-48" delay={50} />
        </div>
        <Skeleton className="h-8 w-24 rounded-full" delay={100} />
      </div>

      {/* Table Content */}
      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <motion.div
            key={rowIndex}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{
              duration: 0.3,
              delay: rowIndex * 50
            }}
            className="flex items-center justify-between p-4 border border-app-text/5 rounded bg-app-bg/30"
          >
            <div className="flex items-center gap-4">
              <Skeleton className="w-10 h-10 rounded-full" />
              <div className="space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-24" delay={25} />
              </div>
            </div>

            <div className="flex items-center gap-3">
              {Array.from({ length: columns - 2 }).map((_, colIndex) => (
                <Skeleton
                  key={colIndex}
                  className="h-6 w-16 rounded-full"
                  delay={colIndex * 25}
                />
              ))}
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

// Resume Upload Skeleton (for lazy loading)
export function ResumeUploadSkeleton() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
      className="p-8 bg-app-card/40 border border-app-text/10 backdrop-blur-sm rounded-lg"
    >
      {/* Header */}
      <div className="text-center mb-8">
        <Skeleton className="h-8 w-64 mx-auto mb-4" />
        <Skeleton className="h-4 w-96 mx-auto" delay={100} />
      </div>

      {/* Upload Area */}
      <div className="border-2 border-dashed border-app-text/20 rounded-lg p-12 mb-8">
        <div className="text-center">
          <Skeleton className="w-16 h-16 rounded-full mx-auto mb-4" />
          <Skeleton className="h-5 w-48 mx-auto mb-2" delay={100} />
          <Skeleton className="h-3 w-64 mx-auto" delay={150} />
        </div>
      </div>

      {/* Form Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i}>
            <Skeleton className="h-4 w-24 mb-2" delay={i * 50} />
            <Skeleton className="h-10 w-full rounded-md" delay={i * 50 + 25} />
          </div>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end gap-4 mt-8">
        <Skeleton className="h-10 w-24 rounded-md" delay={200} />
        <Skeleton className="h-10 w-32 rounded-md" delay={250} />
      </div>
    </motion.div>
  )
}

// Modal Skeleton (for lazy-loaded modals)
export function ModalSkeleton() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div className="bg-app-bg border border-app-text/10 rounded-lg w-full max-w-2xl">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 border-b border-app-text/10">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-6 w-6 rounded" />
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-4 w-32" delay={i * 50} />
              <Skeleton className="h-20 w-full rounded" delay={i * 50 + 25} />
            </div>
          ))}
        </div>

        {/* Modal Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-app-text/10">
          <Skeleton className="h-10 w-24 rounded" delay={200} />
          <Skeleton className="h-10 w-32 rounded" delay={250} />
        </div>
      </div>
    </motion.div>
  )
}

// Profile Section Skeleton
export function ProfileSkeleton() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* Profile Header */}
      <div className="flex items-center gap-6 p-6 bg-app-card/40 border border-app-text/10 rounded-lg">
        <Skeleton className="w-20 h-20 rounded-full" />
        <div className="flex-1">
          <Skeleton className="h-6 w-48 mb-2" />
          <Skeleton className="h-4 w-32 mb-2" delay={50} />
          <Skeleton className="h-3 w-64" delay={100} />
        </div>
        <Skeleton className="h-10 w-24 rounded" delay={150} />
      </div>

      {/* Profile Sections */}
      {Array.from({ length: 3 }).map((_, i) => (
        <div
          key={i}
          className="p-6 bg-app-card/40 border border-app-text/10 rounded-lg"
        >
          <Skeleton className="h-5 w-32 mb-4" delay={i * 100} />
          <div className="space-y-3">
            {Array.from({ length: 2 }).map((_, j) => (
              <Skeleton
                key={j}
                className="h-4 w-full"
                delay={i * 100 + j * 25}
              />
            ))}
          </div>
        </div>
      ))}
    </motion.div>
  )
}