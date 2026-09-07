"use client"

import React, { FormEvent, useId, useRef, useState } from 'react'
import Link from 'next/link'
import { ArrowRight, CheckCircle2 } from 'lucide-react'

import {
  CAREER_STAGES,
  submitWaitlist,
  type CareerStage,
  WaitlistError,
} from '@/app/lib/api/waitlist'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import {
  trackPublicPreviewEvent,
  type PublicPreviewFormLocation,
  type PublicPreviewValidationCategory,
} from '@/lib/public-preview-analytics'

interface WaitlistFormProps {
  compact?: boolean
  className?: string
  formLabel?: string
}

export function WaitlistForm({
  compact = false,
  className,
  formLabel = 'Join the PrismPro private preview',
}: WaitlistFormProps) {
  const fieldId = useId()
  const [careerStage, setCareerStage] = useState<CareerStage | ''>('')
  const [consent, setConsent] = useState(false)
  const [status, setStatus] = useState<'idle' | 'submitting' | 'success'>('idle')
  const [message, setMessage] = useState('')
  const formStarted = useRef(false)
  const formLocation: PublicPreviewFormLocation = compact ? 'hero' : 'final_cta'

  const handleFormStart = () => {
    if (formStarted.current) return
    formStarted.current = true
    trackPublicPreviewEvent({
      event_name: 'form_start',
      form_location: formLocation,
    })
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setMessage('')

    if (compact) {
      trackPublicPreviewEvent({
        event_name: 'hero_cta',
        form_location: formLocation,
      })
    }

    if (!consent) {
      trackPublicPreviewEvent({
        event_name: 'form_validation_failure',
        form_location: formLocation,
        validation_category: 'consent',
      })
      setMessage('Please confirm that we may contact you about PrismPro research and early access.')
      return
    }

    const form = event.currentTarget
    const data = new FormData(form)
    setStatus('submitting')

    try {
      const result = await submitWaitlist({
        email: String(data.get('email') || ''),
        career_stage: careerStage || undefined,
        target_role: String(data.get('target_role') || '') || undefined,
        communication_challenge:
          String(data.get('communication_challenge') || '') || undefined,
        consent: true,
        company_website: String(data.get('company_website') || ''),
      })
      trackPublicPreviewEvent({
        event_name: 'form_success',
        form_location: formLocation,
      })
      setMessage(result.message)
      setStatus('success')
      form.reset()
      setCareerStage('')
      setConsent(false)
    } catch (error) {
      const validationCategory: PublicPreviewValidationCategory =
        error instanceof WaitlistError
          ? error.kind === 'validation'
            ? 'server_validation'
            : error.kind
          : 'unavailable'
      trackPublicPreviewEvent({
        event_name: 'form_validation_failure',
        form_location: formLocation,
        validation_category: validationCategory,
      })
      setMessage(
        error instanceof WaitlistError
          ? error.message
          : 'The waitlist is temporarily unavailable. Please try again later.',
      )
      setStatus('idle')
    }
  }

  if (status === 'success') {
    return (
      <div
        className={cn(
          'border border-foreground/20 bg-background/70 p-6 text-left',
          className,
        )}
        role="status"
        aria-live="polite"
      >
        <CheckCircle2 className="mb-4 h-7 w-7" strokeWidth={1.4} aria-hidden="true" />
        <p className="font-serif text-2xl leading-snug text-foreground">{message}</p>
        <p className="mt-3 text-sm leading-relaxed text-foreground/60">
          No account was created. Your information is used only for PrismPro research and
          private-preview contact.
        </p>
      </div>
    )
  }

  return (
    <form
      className={cn('relative space-y-5 text-left', className)}
      onSubmit={handleSubmit}
      onFocusCapture={handleFormStart}
      aria-label={formLabel}
      noValidate
    >
      <div
        className="absolute -left-[10000px] top-auto h-px w-px overflow-hidden"
        aria-hidden="true"
      >
        <Label htmlFor={`${fieldId}-company-website`}>Company website</Label>
        <Input
          id={`${fieldId}-company-website`}
          name="company_website"
          type="text"
          tabIndex={-1}
          autoComplete="off"
        />
      </div>

      <div className={cn('grid gap-5', compact ? 'sm:grid-cols-[1fr_auto]' : '')}>
        <div className="space-y-2">
          <Label
            htmlFor={`${fieldId}-email`}
            className="text-xs font-bold uppercase tracking-[0.14em] text-foreground/70"
          >
            Work email <span aria-hidden="true">*</span>
          </Label>
          <Input
            id={`${fieldId}-email`}
            name="email"
            type="email"
            inputMode="email"
            autoComplete="email"
            required
            maxLength={254}
            placeholder="you@example.com"
            className="min-h-12 rounded-none border-foreground/25 bg-background/60 px-4 shadow-none focus-visible:ring-foreground"
            aria-describedby={`${fieldId}-privacy`}
          />
        </div>

        {compact && (
          <Button
            type="submit"
            disabled={status === 'submitting'}
            className="min-h-12 self-end rounded-none bg-foreground px-6 uppercase tracking-[0.12em] text-background hover:bg-foreground/90"
          >
            {status === 'submitting' ? 'Joining…' : 'Join the preview'}
            {status !== 'submitting' && <ArrowRight aria-hidden="true" />}
          </Button>
        )}
      </div>

      {!compact && (
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="space-y-2">
            <Label
              htmlFor={`${fieldId}-career-stage`}
              className="text-xs font-bold uppercase tracking-[0.14em] text-foreground/70"
            >
              Career stage <span className="font-normal normal-case tracking-normal">(optional)</span>
            </Label>
            <select
              id={`${fieldId}-career-stage`}
              name="career_stage"
              value={careerStage}
              onChange={(event) => setCareerStage(event.target.value as CareerStage | '')}
              className="flex min-h-12 w-full rounded-none border border-foreground/25 bg-background/60 px-4 text-base text-foreground outline-none focus-visible:ring-2 focus-visible:ring-foreground"
            >
              <option value="">Select your stage</option>
              {CAREER_STAGES.map((stage) => (
                <option key={stage.value} value={stage.value}>
                  {stage.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label
              htmlFor={`${fieldId}-target-role`}
              className="text-xs font-bold uppercase tracking-[0.14em] text-foreground/70"
            >
              Target role <span className="font-normal normal-case tracking-normal">(optional)</span>
            </Label>
            <Input
              id={`${fieldId}-target-role`}
              name="target_role"
              type="text"
              maxLength={120}
              placeholder="e.g. Staff platform engineer"
              className="min-h-12 rounded-none border-foreground/25 bg-background/60 px-4 shadow-none focus-visible:ring-foreground"
            />
          </div>

          <div className="space-y-2 sm:col-span-2">
            <Label
              htmlFor={`${fieldId}-challenge`}
              className="text-xs font-bold uppercase tracking-[0.14em] text-foreground/70"
            >
              Hardest part to communicate{' '}
              <span className="font-normal normal-case tracking-normal">(optional)</span>
            </Label>
            <Textarea
              id={`${fieldId}-challenge`}
              name="communication_challenge"
              maxLength={1000}
              rows={4}
              placeholder="What important work is missing or hard to explain?"
              className="rounded-none border-foreground/25 bg-background/60 px-4 py-3 text-base shadow-none focus-visible:ring-foreground"
            />
          </div>
        </div>
      )}

      <div className="flex items-start gap-3">
        <Checkbox
          id={`${fieldId}-consent`}
          checked={consent}
          onCheckedChange={(checked) => setConsent(checked === true)}
          className="mt-0.5 h-5 w-5 rounded-none border-foreground/45 data-[state=checked]:bg-foreground data-[state=checked]:text-background"
          aria-describedby={`${fieldId}-privacy`}
        />
        <Label
          htmlFor={`${fieldId}-consent`}
          className="cursor-pointer text-sm font-normal leading-relaxed text-foreground/70"
        >
          PrismPro may contact me about product research and private-preview access.
        </Label>
      </div>

      {!compact && (
        <Button
          type="submit"
          disabled={status === 'submitting'}
          className="min-h-14 w-full rounded-none bg-foreground px-8 uppercase tracking-[0.14em] text-background hover:bg-foreground/90 sm:w-auto"
        >
          {status === 'submitting' ? 'Joining the preview…' : 'Join the private preview'}
          {status !== 'submitting' && <ArrowRight aria-hidden="true" />}
        </Button>
      )}

      <p id={`${fieldId}-privacy`} className="text-xs leading-relaxed text-foreground/55">
        No account will be created. We will only use this information for PrismPro research
        and early access. Read our{' '}
        <Link href="/privacy-policy" className="underline underline-offset-4 hover:text-foreground">
          Privacy Policy
        </Link>
        .
      </p>

      {message && (
        <p className="text-sm font-medium text-destructive" role="alert" aria-live="assertive">
          {message}
        </p>
      )}
    </form>
  )
}
