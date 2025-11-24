"use client"

import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { X, User, Briefcase, MapPin, DollarSign, GraduationCap, CheckCircle, AlertCircle } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { useRouter } from "next/navigation"
import { LocationAutoComplete } from "@/components/location-auto-complete"
import { SkillsAutocomplete } from "@/components/skills-autocomplete"
import { FormError } from "@/components/ui/form-error"
import { useFormValidation } from "@/hooks/use-form-validation"
import {
  validateCompleteProfile,
  validatePersonalInfo,
  validateProfessionalInfo,
  validateSkills,
  validateJobPreferences
} from "@/lib/validation/profile-schemas"
import { serializeProfileData } from "./../lib/form-utils"

interface ProfileSetupModalProps {
  isOpen: boolean
  onClose: () => void
  onComplete: () => void
}

export function ProfileSetupModal({ isOpen, onClose, onComplete }: ProfileSetupModalProps) {
  const { user } = useAuth()
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(1)

  // Initialize form with validation
  const form = useFormValidation({
    initialValues: {
      // Personal Info
      full_name: user?.user_metadata?.full_name || "",
      email: user?.email || "",
      phone: "",
      location: "",

      // Professional Info
      years_of_experience: 0,
      career_level: "",
      professional_summary: "",

      // Skills & Tech
      programming_languages: [] as string[],
      frameworks_libraries: [] as string[],
      tools_platforms: [] as string[],

      // Job Preferences
      desired_roles: [] as string[],
      preferred_locations: [] as string[],
      salary_range_min: 0,
      salary_range_max: 0,
    },
    validationSchema: validateCompleteProfile,
    onSubmit: async (data) => {
      try {
        const serializedData = serializeProfileData(data)

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/user-profiles/${user?.id}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(serializedData)
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => null)
          throw new Error(errorData?.detail || 'Failed to create profile')
        }

        onComplete()
        router.push('/dashboard')
      } catch (error: any) {
        console.error('Profile creation error:', error)
        throw new Error(error.message || 'Failed to create profile. Please try again.')
      }
    },
    validateOnChange: true,
    validateOnBlur: true
  })

  const steps = [
    {
      title: "Personal Information",
      description: "Let's start with the basics",
      icon: User,
      fields: ["full_name", "email", "phone", "location"]
    },
    {
      title: "Professional Background",
      description: "Tell us about your experience",
      icon: Briefcase,
      fields: ["years_of_experience", "career_level", "professional_summary"]
    },
    {
      title: "Skills & Technologies",
      description: "What technologies do you work with?",
      icon: GraduationCap,
      fields: ["programming_languages", "frameworks_libraries", "tools_platforms"]
    },
    {
      title: "Job Preferences",
      description: "What are you looking for?",
      icon: MapPin,
      fields: ["desired_roles", "preferred_locations", "salary_range_min", "job_types"]
    }
  ]

  const handleInputChange = (field: string, value: string | string[] | number) => {
    // Convert numeric fields to proper types
    if (field === 'years_of_experience') {
      const stringValue = value as string
      if (stringValue === '') {
        form.setValue(field as any, 0)
      } else {
        const numValue = parseFloat(stringValue)
        if (!isNaN(numValue)) {
          form.setValue(field as any, numValue)
        }
      }
    } else if (field === 'salary_range_min' || field === 'salary_range_max') {
      const stringValue = value as string
      if (stringValue === '') {
        form.setValue(field as any, 0)
      } else {
        const numValue = parseInt(stringValue)
        if (!isNaN(numValue)) {
          form.setValue(field as any, numValue)
        }
      }
    } else {
      form.setValue(field as any, value)
    }
  }

  const handleArrayInput = (field: string, value: string) => {
    if (value.trim()) {
      const items = value.split(',').map(item => item.trim()).filter(Boolean)
      form.setValue(field as any, items)
    } else {
      form.setValue(field as any, [])
    }
  }

  const nextStep = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleFormSubmit = async () => {
    const success = await form.handleSubmit()
    if (success) {
      onComplete()
      router.push('/dashboard')
    }
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="full_name">Full Name *</Label>
                <Input
                  id="full_name"
                  value={form.values.full_name}
                  onChange={(e) => handleInputChange("full_name", e.target.value)}
                  onBlur={() => form.handleBlur("full_name")}
                  placeholder="John Doe"
                  required
                />
                {form.errors.full_name && form.touched.full_name && (
                  <FormError message={form.errors.full_name} />
                )}
              </div>
              <div>
                <Label htmlFor="email">Email *</Label>
                <Input
                  id="email"
                  value={form.values.email}
                  onChange={(e) => handleInputChange("email", e.target.value)}
                  onBlur={() => form.handleBlur("email")}
                  placeholder="john@example.com"
                  type="email"
                  required
                />
                {form.errors.email && form.touched.email && (
                  <FormError message={form.errors.email} />
                )}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="phone">Phone</Label>
                <Input
                  id="phone"
                  value={form.values.phone}
                  onChange={(e) => handleInputChange("phone", e.target.value)}
                  onBlur={() => form.handleBlur("phone")}
                  placeholder="+1 (555) 123-4567"
                />
                {form.errors.phone && form.touched.phone && (
                  <FormError message={form.errors.phone} />
                )}
              </div>
              <div>
                <Label htmlFor="location">Location</Label>
                <LocationAutoComplete
                  id="location"
                  value={form.values.location}
                  onChange={(value) => handleInputChange("location", value)}
                  placeholder="San Francisco, CA"
                />
                {form.errors.location && form.touched.location && (
                  <FormError message={form.errors.location} />
                )}
              </div>
            </div>
          </div>
        )

      case 2:
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="years_of_experience">Years of Experience</Label>
                <Select onValueChange={(value) => handleInputChange("years_of_experience", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select experience" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">New Graduate</SelectItem>
                    <SelectItem value="0.5">&lt; 1 year</SelectItem>
                    <SelectItem value="1">1-2 years</SelectItem>
                    <SelectItem value="3">3-5 years</SelectItem>
                    <SelectItem value="6">6+ years</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="career_level">Career Level</Label>
                <Select onValueChange={(value) => handleInputChange("career_level", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select level" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="entry">Entry Level</SelectItem>
                    <SelectItem value="mid">Mid Level</SelectItem>
                    <SelectItem value="senior">Senior Level</SelectItem>
                    <SelectItem value="lead">Lead/Principal</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label htmlFor="professional_summary">Professional Summary</Label>
              <Textarea
                id="professional_summary"
                value={form.values.professional_summary}
                onChange={(e) => handleInputChange("professional_summary", e.target.value)}
                onBlur={() => form.handleBlur("professional_summary")}
                placeholder="Brief description of your background and goals..."
                rows={3}
              />
              {form.errors.professional_summary && form.touched.professional_summary && (
                <FormError message={form.errors.professional_summary} />
              )}
            </div>
          </div>
        )

      case 3:
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="programming_languages">Programming Languages</Label>
              <Input
                id="programming_languages"
                onChange={(e) => handleArrayInput("programming_languages", e.target.value)}
                placeholder="JavaScript, Python, Java (comma-separated)"
              />
            </div>
            <div>
              <Label htmlFor="frameworks_libraries">Frameworks & Libraries</Label>
              <Input
                id="frameworks_libraries"
                onChange={(e) => handleArrayInput("frameworks_libraries", e.target.value)}
                placeholder="React, Node.js, Express (comma-separated)"
              />
            </div>
            <div>
              <Label htmlFor="tools_platforms">Tools & Platforms</Label>
              <Input
                id="tools_platforms"
                onChange={(e) => handleArrayInput("tools_platforms", e.target.value)}
                placeholder="AWS, Docker, Git (comma-separated)"
              />
            </div>
          </div>
        )

      case 4:
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="desired_roles">Desired Job Roles</Label>
              <Input
                id="desired_roles"
                onChange={(e) => handleArrayInput("desired_roles", e.target.value)}
                placeholder="Software Engineer, Full Stack Developer (comma-separated)"
              />
            </div>
            <div>
              <Label htmlFor="preferred_locations">Preferred Locations</Label>
              <Input
                id="preferred_locations"
                onChange={(e) => handleArrayInput("preferred_locations", e.target.value)}
                placeholder="Remote, San Francisco, New York (comma-separated)"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="salary_range_min">Minimum Salary ($)</Label>
                <Input
                  id="salary_range_min"
                  value={form.values.salary_range_min === 0 ? '' : form.values.salary_range_min}
                  onChange={(e) => handleInputChange("salary_range_min", e.target.value)}
                  onBlur={() => form.handleBlur("salary_range_min")}
                  placeholder="80000"
                  type="number"
                />
                {form.errors.salary_range_min && form.touched.salary_range_min && (
                  <FormError message={form.errors.salary_range_min} />
                )}
              </div>
              <div>
                <Label htmlFor="salary_range_max">Maximum Salary ($)</Label>
                <Input
                  id="salary_range_max"
                  value={form.values.salary_range_max === 0 ? '' : form.values.salary_range_max}
                  onChange={(e) => handleInputChange("salary_range_max", e.target.value)}
                  onBlur={() => form.handleBlur("salary_range_max")}
                  placeholder="120000"
                  type="number"
                />
                {form.errors.salary_range_max && form.touched.salary_range_max && (
                  <FormError message={form.errors.salary_range_max} />
                )}
              </div>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            className="relative w-full max-w-2xl max-h-[90vh] overflow-hidden"
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
          >
            <Card className="premium-card border-accent-500/20">
              <CardHeader className="text-center pb-4">
                <div className="flex items-center justify-between mb-4">
                  <Badge variant="secondary" className="bg-accent-500/10 text-accent-400">
                    Step {currentStep} of {steps.length}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onClose}
                    className="text-cream-400 hover:text-cream-50"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                <div className="flex items-center justify-center mb-4">
                  <div className="w-16 h-16 bg-gradient-warm rounded-full flex items-center justify-center">
                    {React.createElement(steps[currentStep - 1].icon, {
                      className: "w-8 h-8 text-white"
                    })}
                  </div>
                </div>

                <CardTitle className="text-2xl text-cream-50">
                  {steps[currentStep - 1].title}
                </CardTitle>
                <CardDescription className="text-lg text-cream-300">
                  {steps[currentStep - 1].description}
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-6">
                {/* Progress Bar */}
                <div className="w-full bg-primary-700 rounded-full h-2">
                  <motion.div
                    className="bg-gradient-warm h-2 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${(currentStep / steps.length) * 100}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>

                {/* Step Content */}
                <motion.div
                  key={currentStep}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  {renderStepContent()}
                </motion.div>

                {/* Navigation Buttons */}
                <div className="flex justify-between pt-6">
                  <Button
                    variant="outline"
                    onClick={prevStep}
                    disabled={currentStep === 1}
                    className="border-accent-500/50 text-accent-400"
                  >
                    Previous
                  </Button>

                  {currentStep === steps.length ? (
                    <Button
                      onClick={handleFormSubmit}
                      disabled={form.isSubmitting || !form.values.full_name || !form.values.email}
                      className="bg-gradient-warm hover:bg-gradient-gold text-white px-8"
                    >
                      {form.isSubmitting ? "Creating Profile..." : "Complete Setup"}
                      <CheckCircle className="ml-2 h-4 w-4" />
                    </Button>
                  ) : (
                    <Button
                      onClick={nextStep}
                      className="bg-gradient-warm hover:bg-gradient-gold text-white px-8"
                    >
                      Next Step
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}