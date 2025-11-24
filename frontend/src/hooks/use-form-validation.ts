import { useState, useCallback, useMemo } from 'react'
import { debounce, extractZodErrors, type FormError } from '@/lib/form-utils'
interface UseFormValidationOptions<T> {
  initialValues: T
  validationSchema?: (data: T) => { success: boolean; error?: any; data?: T }
  onSubmit?: (data: T) => Promise<void> | void
  validateOnChange?: boolean
  validateOnBlur?: boolean
  debounceMs?: number
}

interface FormField {
  value: any
  error: string | null
  touched: boolean
}

export function useFormValidation<T extends Record<string, any>>({
  initialValues,
  validationSchema,
  onSubmit,
  validateOnChange = true,
  validateOnBlur = true,
  debounceMs = 300
}: UseFormValidationOptions<T>) {
  const [values, setValues] = useState<T>(initialValues)
  const [errors, setErrors] = useState<Record<string, string | null>>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitErrors, setSubmitErrors] = useState<FormError[]>([])

  // Debounced validation function
  const debouncedValidate = useMemo(
    () => debounce((fieldName: string, value: any) => {
      if (!validationSchema) return

      const result = validationSchema({ ...values, [fieldName]: value } as T)
      if (!result.success && result.error) {
        const fieldErrors = extractZodErrors(result.error)
        const fieldError = fieldErrors.find(err => err.field === fieldName)

        setErrors(prev => {
          const newErrors = { ...prev }
          if (fieldError?.message) {
            newErrors[fieldName] = fieldError.message
          } else {
            delete newErrors[fieldName]
          }
          return newErrors
        })
      } else {
        setErrors(prev => {
          const newErrors = { ...prev }
          delete newErrors[fieldName]
          return newErrors
        })
      }
    }, debounceMs),
    [values, validationSchema, debounceMs]
  )

  // Validate all fields
  const validateAll = useCallback(() => {
    if (!validationSchema) return true

    const result = validationSchema(values)
    if (result.success) {
      setErrors({})
      setSubmitErrors([])
      return true
    }

    if (result.error) {
      const formErrors = extractZodErrors(result.error)
      const errorMap: Record<string, string | null> = {}

      formErrors.forEach(error => {
        errorMap[error.field] = error.message
      })

      setErrors(errorMap)
      setSubmitErrors(formErrors)
    }

    return false
  }, [values, validationSchema])

  // Set field value
  const setValue = useCallback((name: keyof T, value: any) => {
    setValues(prev => ({ ...prev, [name]: value }))

    if (validateOnChange && touched[name as string]) {
      debouncedValidate(name as string, value)
    }
  }, [validateOnChange, touched, debouncedValidate])

  // Set field touched
  const setFieldTouched = useCallback((name: keyof T, isTouched = true) => {
    setTouched(prev => ({ ...prev, [name]: isTouched }))
  }, [])

  // Handle field blur
  const handleBlur = useCallback((name: keyof T) => {
    setFieldTouched(name, true)

    if (validateOnBlur && validationSchema) {
      const result = validationSchema(values)
      if (!result.success && result.error) {
        const fieldErrors = extractZodErrors(result.error)
        const fieldError = fieldErrors.find(err => err.field === name)

        if (fieldError) {
          setErrors(prev => ({
            ...prev,
            [name]: fieldError.message
          }))
        }
      }
    }
  }, [values, validateOnBlur, validationSchema, setFieldTouched])

  // Handle form submission
  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    if (e) {
      e.preventDefault()
    }

    setIsSubmitting(true)
    setSubmitErrors([])

    try {
      // Validate all fields
      const isValid = validateAll()
      if (!isValid) {
        return false
      }

      // Mark all fields as touched
      const touchedFields: Record<string, boolean> = {}
      Object.keys(values).forEach(key => {
        touchedFields[key] = true
      })
      setTouched(touchedFields)

      // Call onSubmit if provided
      if (onSubmit) {
        await onSubmit(values)
      }

      return true
    } catch (error: any) {
      console.error('Form submission error:', error)
      setSubmitErrors([{
        field: 'form',
        message: error.message || 'An error occurred while submitting the form'
      }])
      return false
    } finally {
      setIsSubmitting(false)
    }
  }, [values, validateAll, onSubmit])

  // Reset form
  const reset = useCallback(() => {
    setValues(initialValues)
    setErrors({})
    setTouched({})
    setIsSubmitting(false)
    setSubmitErrors([])
  }, [initialValues])

  // Get field props for easy integration
  const getFieldProps = useCallback((name: keyof T) => ({
    value: values[name] || '',
    onChange: (value: any) => setValue(name, value),
    onBlur: () => handleBlur(name),
    error: errors[name as string] || null,
    touched: touched[name as string] || false
  }), [values, setValue, handleBlur, errors, touched])

  // Check if form is valid
  const isValid = useMemo(() => {
    return Object.keys(errors).length === 0 && submitErrors.length === 0
  }, [errors, submitErrors])

  // Check if form has been modified
  const isDirty = useMemo(() => {
    return JSON.stringify(values) !== JSON.stringify(initialValues)
  }, [values, initialValues])

  return {
    // Form state
    values,
    errors,
    touched,
    isSubmitting,
    submitErrors,
    isValid,
    isDirty,

    // Actions
    setValue,
    setFieldTouched,
    handleBlur,
    handleSubmit,
    validateAll,
    reset,
    getFieldProps,

    // Utilities
    setValues,
    setErrors
  }
}