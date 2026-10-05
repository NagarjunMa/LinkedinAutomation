import React from "react"
import { AlertCircle, XCircle } from "lucide-react"
import { cn } from "@/lib/utils"

interface FormErrorProps {
  message?: string | null
  className?: string
  variant?: "inline" | "toast" | "banner"
  icon?: boolean
}

export function FormError({
  message,
  className,
  variant = "inline",
  icon = true
}: FormErrorProps) {
  if (!message) return null

  const baseStyles = "flex items-center text-sm font-medium"

  const variants = {
    inline: "text-red-600 mt-1",
    toast: "bg-red-50 border border-red-200 rounded-md p-3 text-red-800",
    banner: "bg-red-50 border-l-4 border-red-400 p-4 text-red-700"
  }

  const IconComponent = variant === "banner" ? XCircle : AlertCircle

  return (
    <div className={cn(baseStyles, variants[variant], className)}>
      {icon && <IconComponent className="h-4 w-4 mr-2 shrink-0" />}
      <span>{message}</span>
    </div>
  )
}

interface FormSuccessProps {
  message?: string | null
  className?: string
  variant?: "inline" | "toast" | "banner"
  icon?: boolean
}

export function FormSuccess({
  message,
  className,
  variant = "inline",
  icon = true
}: FormSuccessProps) {
  if (!message) return null

  const baseStyles = "flex items-center text-sm font-medium"

  const variants = {
    inline: "text-green-600 mt-1",
    toast: "bg-green-50 border border-green-200 rounded-md p-3 text-green-800",
    banner: "bg-green-50 border-l-4 border-green-400 p-4 text-green-700"
  }

  return (
    <div className={cn(baseStyles, variants[variant], className)}>
      {icon && <AlertCircle className="h-4 w-4 mr-2 shrink-0" />}
      <span>{message}</span>
    </div>
  )
}

interface FieldErrorProps {
  error?: string | null
  touched?: boolean
  className?: string
}

export function FieldError({ error, touched, className }: FieldErrorProps) {
  if (!error || !touched) return null

  return <FormError message={error} className={className} />
}

interface FormErrorsListProps {
  errors: Record<string, string>
  className?: string
}

export function FormErrorsList({ errors, className }: FormErrorsListProps) {
  const errorMessages = Object.values(errors).filter(Boolean)

  if (errorMessages.length === 0) return null

  return (
    <div className={cn("space-y-2", className)}>
      {errorMessages.map((error, index) => (
        <FormError key={index} message={error} variant="toast" />
      ))}
    </div>
  )
}