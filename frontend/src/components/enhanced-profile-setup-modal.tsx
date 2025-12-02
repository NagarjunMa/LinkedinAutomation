"use client"

import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { X, User, Briefcase, Code, MapPin, CheckCircle, AlertTriangle } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { useRouter } from "next/navigation"
import { LocationAutoComplete } from "@/components/location-auto-complete"
import { SkillsAutocomplete } from "@/components/skills-autocomplete"
import { FormError, FormErrorsList } from "@/components/ui/form-error"
import { useFormValidation } from "@/hooks/use-form-validation"
import {
  validateCompleteProfile,
  validatePersonalInfo,
  validateProfessionalInfo,
  validateSkills,
  validateJobPreferences
} from "@/lib/validation/profile-schemas"
import { serializeProfileData, getFormCompletionPercentage } from "@/lib/form-utils"

interface EnhancedProfileSetupModalProps {
  isOpen: boolean
  onClose: () => void
  onComplete: () => void
}

export function EnhancedProfileSetupModal({ isOpen, onClose, onComplete }: EnhancedProfileSetupModalProps) {
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
      } catch (error: unknown) {
        console.error('Profile creation error:', error)
        const errorMessage = error instanceof Error ? error.message : 'Failed to create profile. Please try again.'
        throw new Error(errorMessage)
      }
    },
    validateOnChange: false,
    validateOnBlur: true
  })

  const steps = [
    {
      title: "Personal Information",
      description: "Let's start with the basics",
      icon: User,
      fields: ["full_name", "email", "phone", "location"],
      validator: validatePersonalInfo
    },
    {
      title: "Professional Background",
      description: "Tell us about your experience",
      icon: Briefcase,
      fields: ["years_of_experience", "career_level", "professional_summary"],
      validator: validateProfessionalInfo
    },
    {
      title: "Skills & Technologies",
      description: "What are your technical skills?",
      icon: Code,
      fields: ["programming_languages", "frameworks_libraries", "tools_platforms"],
      validator: validateSkills
    },
    {
      title: "Job Preferences",
      description: "What kind of roles are you looking for?",
      icon: MapPin,
      fields: ["desired_roles", "preferred_locations", "salary_range_min", "salary_range_max"],
      validator: validateJobPreferences
    }
  ]

  // Step validation for better UX
  const validateCurrentStep = () => {
    const currentStepData = steps[currentStep - 1]
    const stepData: Record<string, unknown> = {}

    currentStepData.fields.forEach(field => {
      stepData[field] = (form.values as Record<string, unknown>)[field]
    })

    const result = currentStepData.validator(stepData)
    return result.success
  }

  const nextStep = () => {
    // Validate current step before proceeding
    if (validateCurrentStep() && currentStep < steps.length) {
      setCurrentStep(currentStep + 1)
    } else {
      // Mark fields as touched to show validation errors
      steps[currentStep - 1].fields.forEach(field => {
        form.setFieldTouched(field as keyof typeof form.values, true)
      })
    }
  }

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const completionPercentage = getFormCompletionPercentage(form.values)

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
                  {...form.getFieldProps("full_name")}
                  placeholder="John Doe"
                  className={form.errors.full_name ? "border-red-500" : ""}
                />
                <FormError message={form.errors.full_name} />
              </div>

              <div>
                <Label htmlFor="email">Email Address *</Label>
                <Input
                  id="email"
                  {...form.getFieldProps("email")}
                  placeholder="john@example.com"
                  type="email"
                  className={form.errors.email ? "border-red-500" : ""}
                />
                <FormError message={form.errors.email} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="phone">Phone Number</Label>
                <Input
                  id="phone"
                  {...form.getFieldProps("phone")}
                  placeholder="+1 (555) 123-4567"
                  className={form.errors.phone ? "border-red-500" : ""}
                />
                <FormError message={form.errors.phone} />
              </div>

              <div>
                <Label htmlFor="location">Location *</Label>
                <LocationAutoComplete
                  id="location"
                  value={form.values.location}
                  onChange={(value) => form.setValue("location", value)}
                  placeholder="San Francisco, CA"
                  className={form.errors.location ? "border-red-500" : ""}
                />
                <FormError message={form.errors.location} />
              </div>
            </div>
          </div>
        )

      case 2:
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="years_of_experience">Years of Experience *</Label>
                <Select
                  value={form.values.years_of_experience.toString()}
                  onValueChange={(value) => form.setValue("years_of_experience", parseFloat(value))}
                >
                  <SelectTrigger className={form.errors.years_of_experience ? "border-red-500" : ""}>
                    <SelectValue placeholder="Select experience" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">0 - Fresh Graduate</SelectItem>
                    <SelectItem value="1">1 year</SelectItem>
                    <SelectItem value="2">2 years</SelectItem>
                    <SelectItem value="3">3 years</SelectItem>
                    <SelectItem value="4">4 years</SelectItem>
                    <SelectItem value="5">5+ years</SelectItem>
                    <SelectItem value="10">10+ years</SelectItem>
                  </SelectContent>
                </Select>
                <FormError message={form.errors.years_of_experience} />
              </div>

              <div>
                <Label htmlFor="career_level">Career Level *</Label>
                <Select
                  value={form.values.career_level}
                  onValueChange={(value) => form.setValue("career_level", value)}
                >
                  <SelectTrigger className={form.errors.career_level ? "border-red-500" : ""}>
                    <SelectValue placeholder="Select level" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="entry">Entry Level</SelectItem>
                    <SelectItem value="mid">Mid Level</SelectItem>
                    <SelectItem value="senior">Senior Level</SelectItem>
                    <SelectItem value="lead">Lead/Principal</SelectItem>
                    <SelectItem value="manager">Manager</SelectItem>
                  </SelectContent>
                </Select>
                <FormError message={form.errors.career_level} />
              </div>
            </div>

            <div>
              <Label htmlFor="professional_summary">Professional Summary *</Label>
              <Textarea
                id="professional_summary"
                value={form.values.professional_summary}
                onChange={(e) => form.setValue("professional_summary", e.target.value)}
                onBlur={() => form.handleBlur("professional_summary")}
                placeholder="Brief description of your background, key skills, and career goals..."
                rows={4}
                className={form.errors.professional_summary ? "border-red-500" : ""}
              />
              <FormError message={form.errors.professional_summary} />
              <p className="text-xs text-gray-500 mt-1">
                {form.values.professional_summary.length}/1000 characters
              </p>
            </div>
          </div>
        )

      case 3:
        return (
          <div className="space-y-6">
            <SkillsAutocomplete
              category="programming_languages"
              value={form.values.programming_languages}
              onChange={(skills) => form.setValue("programming_languages", skills)}
              label="Programming Languages *"
              placeholder="Search for programming languages..."
              maxSkills={20}
            />
            <FormError message={form.errors.programming_languages} />

            <SkillsAutocomplete
              category="frameworks_libraries"
              value={form.values.frameworks_libraries}
              onChange={(skills) => form.setValue("frameworks_libraries", skills)}
              label="Frameworks & Libraries"
              placeholder="Search for frameworks and libraries..."
              maxSkills={20}
            />

            <SkillsAutocomplete
              category="tools_platforms"
              value={form.values.tools_platforms}
              onChange={(skills) => form.setValue("tools_platforms", skills)}
              label="Tools & Platforms"
              placeholder="Search for tools and platforms..."
              maxSkills={20}
            />
          </div>
        )

      case 4:
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="desired_roles">Desired Job Roles *</Label>
              <Input
                id="desired_roles"
                value={form.values.desired_roles.join(", ")}
                onChange={(e) => {
                  const roles = e.target.value.split(",").map(role => role.trim()).filter(Boolean)
                  form.setValue("desired_roles", roles)
                }}
                onBlur={() => form.handleBlur("desired_roles")}
                placeholder="Software Engineer, Full Stack Developer, Frontend Developer"
                className={form.errors.desired_roles ? "border-red-500" : ""}
              />
              <FormError message={form.errors.desired_roles} />
              <p className="text-xs text-gray-500">Separate multiple roles with commas</p>
            </div>

            <div>
              <Label htmlFor="preferred_locations">Preferred Locations *</Label>
              <Input
                id="preferred_locations"
                value={form.values.preferred_locations.join(", ")}
                onChange={(e) => {
                  const locations = e.target.value.split(",").map(loc => loc.trim()).filter(Boolean)
                  form.setValue("preferred_locations", locations)
                }}
                onBlur={() => form.handleBlur("preferred_locations")}
                placeholder="Remote, San Francisco, New York"
                className={form.errors.preferred_locations ? "border-red-500" : ""}
              />
              <FormError message={form.errors.preferred_locations} />
              <p className="text-xs text-gray-500">Separate multiple locations with commas</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="salary_range_min">Minimum Salary ($)</Label>
                <Input
                  id="salary_range_min"
                  type="number"
                  value={form.values.salary_range_min || ""}
                  onChange={(e) => form.setValue("salary_range_min", parseInt(e.target.value) || 0)}
                  onBlur={() => form.handleBlur("salary_range_min")}
                  placeholder="80000"
                  className={form.errors.salary_range_min ? "border-red-500" : ""}
                />
                <FormError message={form.errors.salary_range_min} />
              </div>

              <div>
                <Label htmlFor="salary_range_max">Maximum Salary ($)</Label>
                <Input
                  id="salary_range_max"
                  type="number"
                  value={form.values.salary_range_max || ""}
                  onChange={(e) => form.setValue("salary_range_max", parseInt(e.target.value) || 0)}
                  onBlur={() => form.handleBlur("salary_range_max")}
                  placeholder="120000"
                  className={form.errors.salary_range_max ? "border-red-500" : ""}
                />
                <FormError message={form.errors.salary_range_max} />
              </div>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
        onClick={(e) => e.target === e.currentTarget && onClose()}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="w-full max-w-4xl"
        >
          <Card className="border-accent-500/30 bg-gradient-to-br from-dark-800 to-dark-900">
            <CardHeader className="relative">
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="absolute right-2 top-2 text-gray-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </Button>

              <div className="flex items-center space-x-4">
                {React.createElement(steps[currentStep - 1].icon, {
                  className: "h-8 w-8 text-accent-400"
                })}
                <div>
                  <CardTitle className="text-white text-xl">
                    {steps[currentStep - 1].title}
                  </CardTitle>
                  <CardDescription className="text-gray-300">
                    {steps[currentStep - 1].description}
                  </CardDescription>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-gray-700 rounded-full h-2 mt-4">
                <motion.div
                  className="bg-gradient-warm h-2 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${(currentStep / steps.length) * 100}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>

              <div className="flex justify-between text-sm text-gray-400 mt-2">
                <span>Step {currentStep} of {steps.length}</span>
                <span>{completionPercentage}% complete</span>
              </div>
            </CardHeader>

            <CardContent className="space-y-6">
              {/* Show form-level errors */}
              {form.submitErrors.length > 0 && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                  <div className="flex items-center space-x-2 text-red-800">
                    <AlertTriangle className="h-5 w-5" />
                    <span className="font-medium">Please fix the following errors:</span>
                  </div>
                  <FormErrorsList errors={Object.fromEntries(
                    Object.entries(form.errors).filter(([_, value]) => value !== null)
                  ) as Record<string, string>} className="mt-2" />
                </div>
              )}

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
                    onClick={() => form.handleSubmit()}
                    disabled={form.isSubmitting || !form.isValid}
                    className="bg-gradient-warm hover:bg-gradient-gold text-white px-8"
                  >
                    {form.isSubmitting ? "Creating Profile..." : "Complete Setup"}
                    <CheckCircle className="ml-2 h-4 w-4" />
                  </Button>
                ) : (
                  <Button
                    onClick={nextStep}
                    disabled={!validateCurrentStep()}
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
    </AnimatePresence>
  )
}