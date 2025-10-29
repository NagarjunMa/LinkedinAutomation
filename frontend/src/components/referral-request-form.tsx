"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  Mail,
  User,
  Building,
  Briefcase,
  Users,
  RefreshCw,
  Send,
  Save,
  AlertCircle,
  CheckCircle,
  Wand2,
  Edit,
  Trash2
} from "lucide-react"
import { cn } from "@/lib/utils"
import { referralAPI, ContactInfo, GeneratedEmail, EmailDraft, ReferralContact, isReferralAPIError } from "@/lib/referral-api"
import { useActivity } from "@/contexts/activity-context"

interface ReferralRequestFormProps {
  jobId: string
  jobTitle?: string
  companyName?: string
  onSuccess?: () => void
  className?: string
}

export function ReferralRequestForm({
  jobId,
  jobTitle,
  companyName,
  onSuccess,
  className
}: ReferralRequestFormProps) {
  const [contactInfo, setContactInfo] = useState<ContactInfo>({
    contact_name: '',
    contact_email: '',
    company: companyName || '',
    position: '',
    relationship: ''
  })

  const [generatedEmail, setGeneratedEmail] = useState<GeneratedEmail | null>(null)
  const [savedDraft, setSavedDraft] = useState<{ draft: EmailDraft; contact: ReferralContact } | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [editMode, setEditMode] = useState(false)
  const { trackReferralEmailActivity } = useActivity()

  const relationships = [
    { value: 'colleague', label: 'Current/Former Colleague' },
    { value: 'alumni', label: 'Alumni Connection' },
    { value: 'linkedin_connection', label: 'LinkedIn Connection' },
    { value: 'friend', label: 'Personal Friend' },
    { value: 'other', label: 'Other' }
  ]

  const handleInputChange = (field: keyof ContactInfo, value: string) => {
    setContactInfo(prev => ({ ...prev, [field]: value }))
  }

  const handleGenerate = async () => {

    if (!contactInfo.contact_name || !contactInfo.contact_email) {
      setError('Please provide contact name and email')
      return
    }

    setIsGenerating(true)
    setError(null)

    try {
      const result = await referralAPI.generateEmail(jobId, contactInfo)
      setGeneratedEmail(result)
    } catch (err) {
      console.error('❌ Error generating email:', err)
      if (isReferralAPIError(err)) {
        setError(err.message)
      } else {
        setError('Failed to generate email. Please try again.')
      }
    } finally {
      setIsGenerating(false)
    }
  }

  const handleSaveAndCreate = async () => {
    if (!generatedEmail) {
      setError('Please generate an email first')
      return
    }

    setIsSaving(true)
    setError(null)

    try {
      const result = await referralAPI.createReferralRequest(jobId, contactInfo)
      setSavedDraft(result)
      setSuccess('Referral request saved! You can now edit and send it.')
    } catch (err) {
      if (isReferralAPIError(err)) {
        setError(err.message)
      } else {
        setError('Failed to save draft. Please try again.')
      }
    } finally {
      setIsSaving(false)
    }
  }

  const handleUpdateDraft = async () => {
    if (!savedDraft || !generatedEmail) return

    setIsSaving(true)
    setError(null)

    try {
      const updated = await referralAPI.updateDraft(savedDraft.draft.id, {
        subject: generatedEmail.subject,
        email_body: generatedEmail.body
      })
      setSavedDraft(prev => prev ? { ...prev, draft: updated } : null)
      setEditMode(false)
      setSuccess('Draft updated successfully!')
    } catch (err) {
      if (isReferralAPIError(err)) {
        setError(err.message)
      } else {
        setError('Failed to update draft. Please try again.')
      }
    } finally {
      setIsSaving(false)
    }
  }

  const handleSend = async () => {
    if (!savedDraft) return

    setIsSending(true)
    setError(null)

    try {
      await referralAPI.sendEmail(savedDraft.draft.id)

      // Track activity for successful referral email
      try {
        await trackReferralEmailActivity({
          contact: contactInfo.contact_name,
          company: contactInfo.company,
          position: contactInfo.position
        })
      } catch (error) {
        console.error('Failed to track referral email activity:', error)
      }

      setSuccess('Referral email sent successfully! 🎉')
      if (onSuccess) onSuccess()
    } catch (err) {
      if (isReferralAPIError(err)) {
        setError(err.message)
      } else {
        setError('Failed to send email. Please try again.')
      }
    } finally {
      setIsSending(false)
    }
  }

  const handleEditEmail = () => {
    setEditMode(true)
    setError(null)
    setSuccess(null)
  }

  return (
    <Card className={cn("premium-card max-h-[800px] flex flex-col", className)}>
      <CardHeader className="pb-3 flex-shrink-0">
        <div className="flex items-center space-x-2">
          <Mail className="h-5 w-5 text-accent-400" />
          <CardTitle className="text-cream-50 text-lg">
            Request Referral
          </CardTitle>
          {jobTitle && (
            <Badge className="bg-primary-700 text-cream-300 border-primary-500">
              {jobTitle}
            </Badge>
          )}
        </div>
        {error && (
          <Alert className="border-red-500/20 bg-red-500/10">
            <AlertCircle className="h-4 w-4 text-red-400" />
            <AlertDescription className="text-red-200">
              {error}
            </AlertDescription>
          </Alert>
        )}
        {success && (
          <Alert className="border-green-500/20 bg-green-500/10">
            <CheckCircle className="h-4 w-4 text-green-400" />
            <AlertDescription className="text-green-200">
              {success}
            </AlertDescription>
          </Alert>
        )}
      </CardHeader>

      <CardContent className="flex-1 flex flex-col space-y-4 min-h-0 overflow-y-auto">
        {/* Contact Information Form */}
        {!savedDraft && (
          <div className="space-y-4">
            <div className="flex items-center space-x-2 mb-3">
              <User className="h-4 w-4 text-blue-400" />
              <h4 className="text-sm font-medium text-cream-200">Contact Information</h4>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name" className="text-cream-300">Contact Name *</Label>
                <Input
                  id="name"
                  placeholder="John Doe"
                  value={contactInfo.contact_name}
                  onChange={(e) => handleInputChange('contact_name', e.target.value)}
                  className="bg-primary-700 border-primary-600 text-cream-50"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email" className="text-cream-300">Contact Email *</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="john@company.com"
                  value={contactInfo.contact_email}
                  onChange={(e) => handleInputChange('contact_email', e.target.value)}
                  className="bg-primary-700 border-primary-600 text-cream-50"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="company" className="text-cream-300">Their Company</Label>
                <Input
                  id="company"
                  placeholder="Company Inc."
                  value={contactInfo.company}
                  onChange={(e) => handleInputChange('company', e.target.value)}
                  className="bg-primary-700 border-primary-600 text-cream-50"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="position" className="text-cream-300">Their Position</Label>
                <Input
                  id="position"
                  placeholder="Software Engineer"
                  value={contactInfo.position}
                  onChange={(e) => handleInputChange('position', e.target.value)}
                  className="bg-primary-700 border-primary-600 text-cream-50"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="relationship" className="text-cream-300">Relationship</Label>
              <Select value={contactInfo.relationship} onValueChange={(value) => handleInputChange('relationship', value)}>
                <SelectTrigger className="bg-primary-700 border-primary-600 text-cream-50">
                  <SelectValue placeholder="How do you know them?" />
                </SelectTrigger>
                <SelectContent className="bg-primary-700 border-primary-600">
                  {relationships.map((rel) => (
                    <SelectItem key={rel.value} value={rel.value} className="text-cream-50 focus:bg-primary-600">
                      {rel.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button
              onClick={(e) => {
                alert('BUTTON CLICKED! Check console for logs')
                e.preventDefault()
                handleGenerate()
              }}
              disabled={isGenerating || !contactInfo.contact_name || !contactInfo.contact_email}
              className="w-full bg-gradient-warm text-white font-semibold hover:bg-gradient-gold transition-all duration-200"
            >
              {isGenerating ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Wand2 className="h-4 w-4 mr-2" />
                  Generate Referral Email
                </>
              )}
            </Button>
          </div>
        )}

        {/* Generated Email Preview */}
        {generatedEmail && (
          <div className="space-y-4">
            <Separator />
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Mail className="h-4 w-4 text-accent-400" />
                <h4 className="text-sm font-medium text-cream-200">
                  {savedDraft ? 'Email Draft' : 'Generated Email'}
                </h4>
              </div>
              {savedDraft && !editMode && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleEditEmail}
                  className="text-cream-300 hover:text-cream-50"
                >
                  <Edit className="h-3 w-3 mr-1" />
                  Edit
                </Button>
              )}
            </div>

            <div className="space-y-3">
              <div className="space-y-2">
                <Label className="text-cream-300">Subject</Label>
                {editMode ? (
                  <Input
                    value={generatedEmail.subject}
                    onChange={(e) => setGeneratedEmail(prev => prev ? { ...prev, subject: e.target.value } : null)}
                    className="bg-primary-700 border-primary-600 text-cream-50"
                  />
                ) : (
                  <div className="bg-primary-700 border border-primary-600 rounded-lg px-3 py-2 text-cream-50">
                    {generatedEmail.subject}
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <Label className="text-cream-300">Email Body</Label>
                {editMode ? (
                  <Textarea
                    value={generatedEmail.body}
                    onChange={(e) => setGeneratedEmail(prev => prev ? { ...prev, body: e.target.value } : null)}
                    rows={12}
                    className="bg-primary-700 border-primary-600 text-cream-50 font-mono text-sm"
                  />
                ) : (
                  <div className="bg-primary-700 border border-primary-600 rounded-lg px-3 py-2 text-cream-50 whitespace-pre-wrap font-mono text-sm max-h-60 overflow-y-auto">
                    {generatedEmail.body}
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-2">
                <Badge className="bg-blue-500/20 text-blue-300 border-blue-500/30 text-xs">
                  Template: {generatedEmail.template_used.replace('_', ' ').toUpperCase()}
                </Badge>
                {savedDraft && (
                  <Badge className="bg-green-500/20 text-green-300 border-green-500/30 text-xs">
                    Version {savedDraft.draft.version}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        {generatedEmail && (
          <div className="flex gap-3 pt-4">
            {!savedDraft ? (
              <Button
                onClick={handleSaveAndCreate}
                disabled={isSaving}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
              >
                {isSaving ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Draft
                  </>
                )}
              </Button>
            ) : editMode ? (
              <>
                <Button
                  onClick={handleUpdateDraft}
                  disabled={isSaving}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {isSaving ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Updating...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      Update Draft
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setEditMode(false)}
                  className="border-primary-600 text-cream-300 hover:bg-primary-700"
                >
                  Cancel
                </Button>
              </>
            ) : (
              <Button
                onClick={handleSend}
                disabled={isSending}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white"
              >
                {isSending ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Send Referral Request
                  </>
                )}
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}