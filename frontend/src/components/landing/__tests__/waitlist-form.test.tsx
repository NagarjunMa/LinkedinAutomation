import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { WaitlistForm } from '@/components/landing/WaitlistForm'


const submitWaitlistMock = vi.hoisted(() => vi.fn())
const trackPublicPreviewEventMock = vi.hoisted(() => vi.fn())

vi.mock('@/app/lib/api/waitlist', async (importOriginal) => {
  const original = await importOriginal<typeof import('@/app/lib/api/waitlist')>()
  return { ...original, submitWaitlist: submitWaitlistMock }
})

vi.mock('@/lib/public-preview-analytics', () => ({
  trackPublicPreviewEvent: trackPublicPreviewEventMock,
}))

describe('WaitlistForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    submitWaitlistMock.mockResolvedValue({
      message: "You're on the list. We'll be in touch when there is a useful next step.",
    })
  })

  it('requires explicit contact consent before submitting', async () => {
    render(<WaitlistForm compact />)

    fireEvent.change(screen.getByLabelText(/work email/i), {
      target: { value: 'candidate@example.com' },
    })
    fireEvent.click(screen.getByRole('button', { name: /join the preview/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/please confirm/i)
    expect(submitWaitlistMock).not.toHaveBeenCalled()
    expect(trackPublicPreviewEventMock).toHaveBeenCalledWith({
      event_name: 'form_validation_failure',
      form_location: 'hero',
      validation_category: 'consent',
    })
  })

  it('submits the compact form and shows a neutral confirmation', async () => {
    render(<WaitlistForm compact />)

    fireEvent.change(screen.getByLabelText(/work email/i), {
      target: { value: 'candidate@example.com' },
    })
    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.click(screen.getByRole('button', { name: /join the preview/i }))

    await waitFor(() => {
      expect(submitWaitlistMock).toHaveBeenCalledWith(
        expect.objectContaining({
          email: 'candidate@example.com',
          consent: true,
        }),
      )
    })
    expect(await screen.findByRole('status')).toHaveTextContent("You're on the list")
    expect(screen.getByText(/no account was created/i)).toBeInTheDocument()
    expect(trackPublicPreviewEventMock).toHaveBeenCalledWith({
      event_name: 'form_success',
      form_location: 'hero',
    })
  })

  it('submits optional research fields from the full form', async () => {
    render(<WaitlistForm />)

    fireEvent.change(screen.getByLabelText(/work email/i), {
      target: { value: 'candidate@example.com' },
    })
    fireEvent.change(screen.getByLabelText(/career stage/i), {
      target: { value: 'technical_leader' },
    })
    fireEvent.change(screen.getByLabelText(/target role/i), {
      target: { value: 'Engineering manager' },
    })
    fireEvent.change(screen.getByLabelText(/hardest part to communicate/i), {
      target: { value: 'Explaining organizational scope' },
    })
    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.click(screen.getByRole('button', { name: /join the private preview/i }))

    await waitFor(() => {
      expect(submitWaitlistMock).toHaveBeenCalledWith(
        expect.objectContaining({
          career_stage: 'technical_leader',
          target_role: 'Engineering manager',
          communication_challenge: 'Explaining organizational scope',
        }),
      )
    })
  })
})
