/**
 * Utility functions for form data handling and serialization
 */

export interface FormError {
  field: string
  message: string
}

export interface ProfileFormData {
  full_name?: string
  email?: string
  phone?: string
  location?: string
  years_of_experience?: number | string
  career_level?: string
  professional_summary?: string
  programming_languages?: string[]
  frameworks_libraries?: string[]
  tools_platforms?: string[]
  desired_roles?: string[]
  preferred_locations?: string[]
  salary_range_min?: number | string
  salary_range_max?: number | string
}

type ProfileApiData = ProfileFormData & Record<string, unknown>

interface ZodIssueLike {
  path: (string | number)[]
  message: string
}

interface ZodErrorLike {
  issues?: ZodIssueLike[]
}

/**
 * Serialize array inputs for API submission
 */
export function serializeArrayField(value: string[]): string[] {
  if (!Array.isArray(value)) return []
  return value.filter(item => item && item.trim().length > 0)
}

/**
 * Parse comma-separated string into array with validation
 */
export function parseCommaSeparatedInput(
  value: string,
  maxItems = 20,
  minLength = 1
): string[] {
  if (!value || typeof value !== 'string') return []

  return value
    .split(',')
    .map(item => item.trim())
    .filter(item => item.length >= minLength)
    .slice(0, maxItems) // Limit to prevent too many items
}

/**
 * Convert array back to comma-separated string for display
 */
export function arrayToCommaSeparated(arr: string[]): string {
  if (!Array.isArray(arr)) return ''
  return arr.join(', ')
}

/**
 * Safely convert string to number with validation
 */
export function safeNumberConversion(value: string | number, defaultValue = 0): number {
  if (typeof value === 'number') return isNaN(value) ? defaultValue : value

  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (trimmed === '') return defaultValue

    const parsed = parseFloat(trimmed)
    return isNaN(parsed) ? defaultValue : parsed
  }

  return defaultValue
}

/**
 * Validate and serialize complete profile data for API submission
 */
export function serializeProfileData(formData: ProfileFormData) {
  return {
    // Personal info
    full_name: formData.full_name?.trim() || '',
    email: formData.email?.trim() || '',
    phone: formData.phone?.trim() || '',
    location: formData.location?.trim() || '',

    // Professional info
    years_of_experience: safeNumberConversion(formData.years_of_experience as string | number, 0),
    career_level: formData.career_level?.trim() || '',
    professional_summary: formData.professional_summary?.trim() || '',

    // Skills (ensure arrays)
    programming_languages: serializeArrayField(formData.programming_languages || []),
    frameworks_libraries: serializeArrayField(formData.frameworks_libraries || []),
    tools_platforms: serializeArrayField(formData.tools_platforms || []),

    // Job preferences
    desired_roles: serializeArrayField(formData.desired_roles || []),
    preferred_locations: serializeArrayField(formData.preferred_locations || []),
    salary_range_min: safeNumberConversion(formData.salary_range_min as string | number, 0),
    salary_range_max: safeNumberConversion(formData.salary_range_max as string | number, 0),
  }
}

/**
 * Deserialize profile data from API for form display
 */
export function deserializeProfileData(apiData: ProfileApiData) {
  return {
    // Personal info
    full_name: apiData.full_name || '',
    email: apiData.email || '',
    phone: apiData.phone || '',
    location: apiData.location || '',

    // Professional info
    years_of_experience: apiData.years_of_experience || 0,
    career_level: apiData.career_level || '',
    professional_summary: apiData.professional_summary || '',

    // Skills (ensure arrays)
    programming_languages: Array.isArray(apiData.programming_languages)
      ? apiData.programming_languages
      : [],
    frameworks_libraries: Array.isArray(apiData.frameworks_libraries)
      ? apiData.frameworks_libraries
      : [],
    tools_platforms: Array.isArray(apiData.tools_platforms)
      ? apiData.tools_platforms
      : [],

    // Job preferences
    desired_roles: Array.isArray(apiData.desired_roles)
      ? apiData.desired_roles
      : [],
    preferred_locations: Array.isArray(apiData.preferred_locations)
      ? apiData.preferred_locations
      : [],
    salary_range_min: apiData.salary_range_min || 0,
    salary_range_max: apiData.salary_range_max || 0,
  }
}

/**
 * Format form errors for display
 */
export function formatFormErrors(errors: FormError[]): Record<string, string> {
  const formattedErrors: Record<string, string> = {}
  errors.forEach(error => {
    formattedErrors[error.field] = error.message
  })
  return formattedErrors
}

/**
 * Extract validation errors from Zod error
 */
export function extractZodErrors(zodError: ZodErrorLike | undefined | null): FormError[] {
  if (!zodError?.issues) return []

  return zodError.issues.map((issue: ZodIssueLike) => ({
    field: issue.path.join('.'),
    message: issue.message
  }))
}

/**
 * Validate individual field in real-time
 */
export function validateSingleField<T extends Record<string, unknown>>(
  field: keyof T & string,
  value: T[keyof T],
  validator: (data: Partial<T>) => { success: boolean; error?: ZodErrorLike }
): string | null {
  try {
    const testData = { [field]: value } as Partial<T>
    const result = validator(testData)
    if (!result.success) {
      const fieldErrors = result.error?.issues?.filter(issue => issue.path.includes(field))
      return fieldErrors?.[0]?.message || null
    }
    return null
  } catch {
    return "Validation error"
  }
}

/**
 * Clean and normalize user input
 */
export function sanitizeInput(input: string, maxLength = 1000): string {
  if (typeof input !== 'string') return ''

  return input
    .trim()
    .replace(/\s+/g, ' ') // Replace multiple spaces with single space
    .slice(0, maxLength)
}

/**
 * Debounce function for real-time validation
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func(...args), delay)
  }
}

/**
 * Check if form data has changed
 */
export function hasFormChanged(current: ProfileFormData, original: ProfileFormData): boolean {
  return JSON.stringify(serializeProfileData(current)) !== JSON.stringify(serializeProfileData(original))
}

/**
 * Get form completion percentage
 */
export function getFormCompletionPercentage(formData: ProfileFormData): number {
  const requiredFields = [
    'full_name',
    'email',
    'location',
    'career_level',
    'professional_summary',
    'programming_languages',
    'desired_roles',
    'preferred_locations'
  ]

  let completed = 0

  requiredFields.forEach(field => {
    const value = formData[field]
    if (Array.isArray(value)) {
      if (value.length > 0) completed++
    } else {
      if (value && value.toString().trim().length > 0) completed++
    }
  })

  return Math.round((completed / requiredFields.length) * 100)
}