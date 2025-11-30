"use client"

import React, { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { X, User, Briefcase, MapPin, DollarSign, GraduationCap, CheckCircle, AlertCircle, ArrowRight } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { ProfileSetupModal } from "@/components/profile-setup-modal"

interface ProfileData {
  full_name?: string
  email?: string
  phone?: string
  location?: string
  years_of_experience?: number
  career_level?: string
  professional_summary?: string
  programming_languages?: string[]
  frameworks_libraries?: string[]
  tools_platforms?: string[]
  desired_roles?: string[]
  preferred_locations?: string[]
  salary_range_min?: number
  salary_range_max?: number
  job_types?: string[]
  degrees?: string[]
  institutions?: string[]
  graduation_years?: string[]
  profile_completion?: number
}

interface ActionItem {
  id: string
  title: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  category: string
  fields: string[]
}

const actionItems: ActionItem[] = [
  {
    id: "personal_info",
    title: "Complete Personal Information",
    description: "Add your full name, email, phone, and location",
    icon: User,
    category: "Personal",
    fields: ["full_name", "email", "phone", "location"]
  },
  {
    id: "professional_background",
    title: "Add Professional Background",
    description: "Include your experience level, career stage, and summary",
    icon: Briefcase,
    category: "Professional",
    fields: ["years_of_experience", "career_level", "professional_summary"]
  },
  {
    id: "skills_tech",
    title: "List Skills & Technologies",
    description: "Add programming languages, frameworks, and tools you use",
    icon: GraduationCap,
    category: "Skills",
    fields: ["programming_languages", "frameworks_libraries", "tools_platforms"]
  },
  {
    id: "job_preferences",
    title: "Set Job Preferences",
    description: "Define desired roles, locations, and salary expectations",
    icon: MapPin,
    category: "Preferences",
    fields: ["desired_roles", "preferred_locations", "salary_range_min", "job_types"]
  },
  {
    id: "education",
    title: "Add Education Details",
    description: "Include your degrees, institutions, and graduation years",
    icon: GraduationCap,
    category: "Education",
    fields: ["degrees", "institutions", "graduation_years"]
  }
]

export function ProfileCompletionBanner() {
  const { user } = useAuth()
  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [loading, setLoading] = useState(true)
  const [dismissed, setDismissed] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [missingItems, setMissingItems] = useState<ActionItem[]>([])

  useEffect(() => {
    if (user?.id) {
      fetchProfile()
    }
  }, [user?.id])

  // Listen for profile update events
  useEffect(() => {
    const handleProfileUpdate = () => {
      if (user?.id) {
        fetchProfile()
      }
    }

    window.addEventListener('profileUpdated', handleProfileUpdate)

    return () => {
      window.removeEventListener('profileUpdated', handleProfileUpdate)
    }
  }, [user?.id])

  const fetchProfile = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/user-profiles/${user?.id}`)
      if (response.ok) {
        const profileData = await response.json()
        setProfile(profileData)
        calculateMissingItems(profileData)
      } else {
        // No profile exists, show all action items
        setMissingItems(actionItems)
      }
    } catch (error) {
      console.error('Error fetching profile:', error)
      setMissingItems(actionItems)
    } finally {
      setLoading(false)
    }
  }

  const calculateMissingItems = (profileData: ProfileData) => {
    const missing = actionItems.filter(item => {
      return item.fields.some(field => {
        const value = profileData[field as keyof ProfileData]
        if (Array.isArray(value)) {
          return !value || value.length === 0
        }
        return !value || value === 0 || value === ""
      })
    })
    setMissingItems(missing)
  }

  const getCompletionPercentage = () => {
    if (!profile) return 0
    if (profile.profile_completion !== undefined) {
      return profile.profile_completion
    }

    // Calculate manually if not provided
    const totalFields = actionItems.flatMap(item => item.fields).length
    const completedFields = actionItems.flatMap(item => item.fields).filter(field => {
      const value = profile[field as keyof ProfileData]
      if (Array.isArray(value)) {
        return value && value.length > 0
      }
      return value && value !== 0 && value !== ""
    }).length

    return Math.round((completedFields / totalFields) * 100)
  }

  const handleCompleteProfile = () => {
    setShowModal(true)
  }

  const handleModalComplete = () => {
    setShowModal(false)
    fetchProfile() // Refresh profile data
  }

  if (loading) return null
  if (dismissed) return null
  if (missingItems.length === 0) return null

  const completionPercentage = getCompletionPercentage()

  return (
    <>
      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
          className="mb-6"
        >
          <Card className="border-l-4 border-l-amber-500 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/20 dark:to-orange-950/20">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-4">
                    <AlertCircle className="h-6 w-6 text-amber-600 dark:text-amber-400" />
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        Complete Your Profile
                      </h3>
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        {completionPercentage}% complete • {missingItems.length} action{missingItems.length !== 1 ? 's' : ''} remaining
                      </p>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-4">
                    <Progress
                      value={completionPercentage}
                      className="h-2 bg-amber-200 dark:bg-amber-800"
                    />
                  </div>

                  {/* Action Items */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
                    {missingItems.slice(0, 6).map((item) => (
                      <div
                        key={item.id}
                        className="flex items-center gap-3 p-3 bg-white/60 dark:bg-black/20 rounded-lg border border-amber-200 dark:border-amber-700"
                      >
                        <item.icon className="h-4 w-4 text-amber-600 dark:text-amber-400 flex-shrink-0" />
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {item.title}
                          </p>
                          <p className="text-xs text-gray-700 dark:text-gray-300 truncate">
                            {item.description}
                          </p>
                        </div>
                      </div>
                    ))}
                    {missingItems.length > 6 && (
                      <div className="flex items-center justify-center p-3 bg-white/60 dark:bg-black/20 rounded-lg border border-amber-200 dark:border-amber-700">
                        <p className="text-sm text-gray-700 dark:text-gray-300">
                          +{missingItems.length - 6} more items
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-3">
                    <Button
                      onClick={handleCompleteProfile}
                      className="bg-gradient-warm hover:bg-gradient-gold text-white"
                    >
                      Complete Profile
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setDismissed(true)}
                      className="border-gray-300 text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
                    >
                      Dismiss
                    </Button>
                  </div>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setDismissed(true)}
                  className="text-gray-600 hover:text-gray-800 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-800"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </AnimatePresence>

      <ProfileSetupModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onComplete={handleModalComplete}
      />
    </>
  )
}