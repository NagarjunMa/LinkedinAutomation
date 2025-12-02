import { z } from "zod"

// Phone number validation
const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/

// Personal Information Schema
export const personalInfoSchema = z.object({
  full_name: z
    .string()
    .min(2, "Name must be at least 2 characters")
    .max(100, "Name must be less than 100 characters")
    .regex(/^[a-zA-Z\s\-'\.]+$/, "Name can only contain letters, spaces, hyphens, apostrophes, and periods"),

  email: z
    .string()
    .email("Please enter a valid email address")
    .max(255, "Email must be less than 255 characters"),

  phone: z
    .string()
    .optional()
    .refine((phone) => !phone || phoneRegex.test(phone.replace(/[\s\-\(\)]/g, '')), {
      message: "Please enter a valid phone number"
    }),

  location: z
    .string()
    .min(1, "Location is required")
    .max(255, "Location must be less than 255 characters"),
})

// Professional Information Schema
export const professionalInfoSchema = z.object({
  years_of_experience: z
    .number()
    .min(0, "Experience cannot be negative")
    .max(50, "Experience cannot exceed 50 years"),

  career_level: z
    .string()
    .min(1, "Career level is required"),

  professional_summary: z
    .string()
    .min(10, "Professional summary must be at least 10 characters")
    .max(1000, "Professional summary must be less than 1000 characters"),
})

// Skills Schema
export const skillsSchema = z.object({
  programming_languages: z
    .array(z.string().min(1))
    .min(1, "At least one programming language is required")
    .max(20, "Cannot have more than 20 programming languages"),

  frameworks_libraries: z
    .array(z.string().min(1))
    .max(20, "Cannot have more than 20 frameworks/libraries"),

  tools_platforms: z
    .array(z.string().min(1))
    .max(20, "Cannot have more than 20 tools/platforms"),
})

// Job Preferences Schema (base object without refine)
const jobPreferencesSchemaBase = z.object({
  desired_roles: z
    .array(z.string().min(1))
    .min(1, "At least one desired role is required")
    .max(10, "Cannot have more than 10 desired roles"),

  preferred_locations: z
    .array(z.string().min(1))
    .min(1, "At least one preferred location is required")
    .max(10, "Cannot have more than 10 preferred locations"),

  salary_range_min: z
    .number()
    .min(0, "Minimum salary cannot be negative")
    .max(1000000, "Minimum salary seems unrealistic"),

  salary_range_max: z
    .number()
    .min(0, "Maximum salary cannot be negative")
    .max(1000000, "Maximum salary seems unrealistic"),
})

// Job Preferences Schema with refine
export const jobPreferencesSchema = jobPreferencesSchemaBase.refine((data) => data.salary_range_max >= data.salary_range_min, {
  message: "Maximum salary must be greater than or equal to minimum salary",
  path: ["salary_range_max"]
})

// Education Schema
export const educationSchema = z.object({
  institution_name: z
    .string()
    .min(1, "Institution name is required")
    .max(255, "Institution name must be less than 255 characters"),

  degree_type: z
    .string()
    .min(1, "Degree type is required"),

  field_of_study: z
    .string()
    .min(1, "Field of study is required")
    .max(255, "Field of study must be less than 255 characters"),

  major: z
    .string()
    .max(255, "Major must be less than 255 characters")
    .optional(),

  gpa: z
    .number()
    .min(0, "GPA cannot be negative")
    .max(4.0, "GPA cannot exceed 4.0")
    .optional(),

  start_date: z
    .date()
    .or(z.string().pipe(z.coerce.date())),

  end_date: z
    .date()
    .or(z.string().pipe(z.coerce.date()))
    .optional(),

  graduation_date: z
    .date()
    .or(z.string().pipe(z.coerce.date()))
    .optional(),

  is_current: z.boolean().optional(),

  coursework: z
    .array(z.string().min(1))
    .max(50, "Cannot have more than 50 courses listed")
    .optional(),

  technical_skills_gained: z
    .array(z.string().min(1))
    .max(30, "Cannot have more than 30 skills listed")
    .optional(),
})

// Certification Schema
export const certificationSchema = z.object({
  name: z
    .string()
    .min(1, "Certification name is required")
    .max(255, "Certification name must be less than 255 characters"),

  issuing_organization: z
    .string()
    .min(1, "Issuing organization is required")
    .max(255, "Organization name must be less than 255 characters"),

  issue_date: z
    .date()
    .or(z.string().pipe(z.coerce.date())),

  expiration_date: z
    .date()
    .or(z.string().pipe(z.coerce.date()))
    .optional(),

  never_expires: z.boolean().optional(),

  skills_validated: z
    .array(z.string().min(1))
    .max(20, "Cannot have more than 20 skills validated")
    .optional(),
})

// Complete Profile Schema - merge base schemas first, then apply refine
export const completeProfileSchema = personalInfoSchema
  .merge(professionalInfoSchema)
  .merge(skillsSchema)
  .merge(jobPreferencesSchemaBase)
  .refine((data) => data.salary_range_max >= data.salary_range_min, {
    message: "Maximum salary must be greater than or equal to minimum salary",
    path: ["salary_range_max"]
  })

// Type definitions
export type PersonalInfo = z.infer<typeof personalInfoSchema>
export type ProfessionalInfo = z.infer<typeof professionalInfoSchema>
export type Skills = z.infer<typeof skillsSchema>
export type JobPreferences = z.infer<typeof jobPreferencesSchema>
export type Education = z.infer<typeof educationSchema>
export type Certification = z.infer<typeof certificationSchema>
export type CompleteProfile = z.infer<typeof completeProfileSchema>

// Validation helper functions
export function validatePersonalInfo(data: unknown) {
  return personalInfoSchema.safeParse(data)
}

export function validateProfessionalInfo(data: unknown) {
  return professionalInfoSchema.safeParse(data)
}

export function validateSkills(data: unknown) {
  return skillsSchema.safeParse(data)
}

export function validateJobPreferences(data: unknown) {
  return jobPreferencesSchema.safeParse(data)
}

export function validateEducation(data: unknown) {
  return educationSchema.safeParse(data)
}

export function validateCertification(data: unknown) {
  return certificationSchema.safeParse(data)
}

export function validateCompleteProfile(data: unknown) {
  return completeProfileSchema.safeParse(data)
}

// Field-specific validation functions
export function validateEmail(email: string): string | null {
  const result = z.string().email().safeParse(email)
  return result.success ? null : "Please enter a valid email address"
}

export function validatePhone(phone: string): string | null {
  if (!phone) return null // Phone is optional
  const result = z.string().regex(phoneRegex).safeParse(phone.replace(/[\s\-\(\)]/g, ''))
  return result.success ? null : "Please enter a valid phone number"
}

export function validateName(name: string): string | null {
  const result = personalInfoSchema.shape.full_name.safeParse(name)
  return result.success ? null : result.error.issues[0]?.message || "Invalid name"
}

export function validateArrayInput(value: string, _minItems = 0, maxItems = 20): string[] {
  if (!value.trim()) return []

  return value
    .split(',')
    .map(item => item.trim())
    .filter(item => item.length > 0)
    .slice(0, maxItems) // Prevent too many items
}

export function validateSalaryRange(min: number, max: number): { valid: boolean; error?: string } {
  if (min < 0) return { valid: false, error: "Minimum salary cannot be negative" }
  if (max < 0) return { valid: false, error: "Maximum salary cannot be negative" }
  if (max < min) return { valid: false, error: "Maximum salary must be greater than minimum" }
  if (min > 1000000 || max > 1000000) return { valid: false, error: "Salary values seem unrealistic" }

  return { valid: true }
}