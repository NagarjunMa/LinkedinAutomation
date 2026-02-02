/**
 * Dashboard Loading Component
 * Provides immediate visual feedback while dashboard data loads.
 * Optimized for Next.js 14 App Router streaming patterns.
 */

import React from 'react'
import { motion } from 'framer-motion'
import { BarChart3, Calendar, TrendingUp, Briefcase } from 'lucide-react'

export default function DashboardLoading() {
  return (
    <div className="min-h-screen bg-app-bg text-app-text max-w-[1500px] mx-auto pb-24 px-4 md:px-8 transition-colors duration-300">

      {/* Loading Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-8 md:mb-12"
      >
        <div className="h-8 bg-app-text/10 rounded-sm w-64 mb-4 animate-pulse" />
        <div className="h-4 bg-app-text/5 rounded-sm w-96 animate-pulse" />
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-10">

        {/* Overview Calendar Skeleton */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="lg:col-span-8 p-6 md:p-8 bg-app-card/40 border border-app-text/10 backdrop-blur-sm rounded-lg"
        >
          <div className="flex items-center gap-4 mb-6">
            <div className="w-12 h-12 border border-app-text/10 flex items-center justify-center bg-app-bg">
              <Calendar className="w-5 h-5 text-app-text/40" />
            </div>
            <div>
              <div className="h-5 bg-app-text/10 rounded w-32 mb-2 animate-pulse" />
              <div className="h-3 bg-app-text/5 rounded w-48 animate-pulse" />
            </div>
          </div>

          {/* Calendar Grid Skeleton */}
          <div className="grid grid-cols-7 gap-2">
            {Array.from({ length: 35 }).map((_, i) => (
              <div
                key={i}
                className="aspect-square bg-app-text/5 rounded animate-pulse"
                style={{ animationDelay: `${i * 20}ms` }}
              />
            ))}
          </div>
        </motion.div>

        {/* Quick Actions Skeleton */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="lg:col-span-4 p-6 md:p-8 bg-app-card/40 border border-app-text/10 backdrop-blur-sm rounded-lg"
        >
          <div className="flex items-center gap-4 mb-6">
            <div className="w-12 h-12 border border-app-text/10 flex items-center justify-center bg-app-bg">
              <TrendingUp className="w-5 h-5 text-app-text/40" />
            </div>
            <div>
              <div className="h-5 bg-app-text/10 rounded w-24 mb-2 animate-pulse" />
              <div className="h-3 bg-app-text/5 rounded w-36 animate-pulse" />
            </div>
          </div>

          <div className="space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="p-4 border border-app-text/5 rounded bg-app-bg/50 animate-pulse"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className="h-4 bg-app-text/10 rounded w-3/4 mb-2" />
                <div className="h-3 bg-app-text/5 rounded w-1/2" />
              </div>
            ))}
          </div>
        </motion.div>

        {/* Interactive Chart Skeleton */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          className="lg:col-span-12 p-6 md:p-8 bg-app-card/40 border border-app-text/10 backdrop-blur-sm rounded-lg"
        >
          <div className="flex items-center gap-4 mb-6">
            <div className="w-12 h-12 border border-app-text/10 flex items-center justify-center bg-app-bg">
              <BarChart3 className="w-5 h-5 text-app-text/40" />
            </div>
            <div>
              <div className="h-5 bg-app-text/10 rounded w-40 mb-2 animate-pulse" />
              <div className="h-3 bg-app-text/5 rounded w-64 animate-pulse" />
            </div>
          </div>

          {/* Chart Area Skeleton */}
          <div className="h-64 bg-app-text/5 rounded mb-4 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-app-text/10 to-transparent animate-shimmer" />
          </div>

          {/* Chart Controls */}
          <div className="flex gap-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="h-8 bg-app-text/5 rounded w-16 animate-pulse"
                style={{ animationDelay: `${i * 50}ms` }}
              />
            ))}
          </div>
        </motion.div>

        {/* Recent Applications Skeleton */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: 0.4 }}
          className="lg:col-span-12 p-6 md:p-8 bg-app-card/40 border border-app-text/10 backdrop-blur-sm rounded-lg"
        >
          <div className="flex items-center gap-4 mb-6">
            <div className="w-12 h-12 border border-app-text/10 flex items-center justify-center bg-app-bg">
              <Briefcase className="w-5 h-5 text-app-text/40" />
            </div>
            <div>
              <div className="h-5 bg-app-text/10 rounded w-36 mb-2 animate-pulse" />
              <div className="h-3 bg-app-text/5 rounded w-52 animate-pulse" />
            </div>
          </div>

          {/* Table Skeleton */}
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-4 border border-app-text/5 rounded bg-app-bg/30 animate-pulse"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-app-text/10 rounded" />
                  <div>
                    <div className="h-4 bg-app-text/10 rounded w-32 mb-2" />
                    <div className="h-3 bg-app-text/5 rounded w-24" />
                  </div>
                </div>
                <div className="flex gap-2">
                  <div className="h-6 bg-app-text/5 rounded w-16" />
                  <div className="h-6 bg-app-text/5 rounded w-20" />
                </div>
              </div>
            ))}
          </div>
        </motion.div>

      </div>

      {/* Footer Skeleton */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, delay: 0.5 }}
        className="mt-32 pt-16 border-t border-app-text/10 flex flex-col sm:flex-row gap-4 justify-between items-center text-center sm:text-left"
      >
        <div className="h-3 bg-app-text/5 rounded w-64 animate-pulse" />
        <div className="h-3 bg-app-text/5 rounded w-48 animate-pulse" />
      </motion.div>

      <style jsx>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
      `}</style>
    </div>
  )
}