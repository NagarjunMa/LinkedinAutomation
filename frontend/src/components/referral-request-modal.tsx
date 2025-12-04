"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/components/ui/use-toast"
import {
    User,
    Mail,
    Building,
    Briefcase,
    ArrowLeft,
    Send,
    CheckCircle,
    Edit3,
    Loader2
} from "lucide-react"
import { referralApi } from "@/app/lib/api"

interface Job {
    id: string | number
    title: string
    company: string
    location: string
}

interface ContactInfo {
    name: string
    contact_email: string
    company: string
    position: string
    relationship: string
}

interface GeneratedEmail {
    subject: string
    body: string
    template_used: string
}

interface ReferralRequestModalProps {
    job: Job | null
    isOpen: boolean
    onClose: () => void
}

type Step = 'input' | 'preview' | 'sent'

const RELATIONSHIP_OPTIONS = [
    { value: 'colleague', label: 'Current Colleague' },
    { value: 'alumni', label: 'Alumni Connection' },
    { value: 'friend', label: 'Friend' },
    { value: 'linkedin_connection', label: 'LinkedIn Connection' },
    { value: 'former_colleague', label: 'Former Colleague' },
    { value: 'mentor', label: 'Mentor' },
    { value: 'other', label: 'Other' }
]

export function ReferralRequestModal({ job, isOpen, onClose }: ReferralRequestModalProps) {
    const [step, setStep] = useState<Step>('input')
    const [isLoading, setIsLoading] = useState(false)
    const [contactInfo, setContactInfo] = useState<ContactInfo>({
        name: '',
        contact_email: '',
        company: '',
        position: '',
        relationship: ''
    })
    const [generatedEmail, setGeneratedEmail] = useState<GeneratedEmail | null>(null)
    const [editedEmail, setEditedEmail] = useState<GeneratedEmail | null>(null)
    const [_draftId, setDraftId] = useState<string | null>(null)
    const { toast } = useToast()


    const handleClose = () => {
        // Reset state when closing
        setStep('input')
        setContactInfo({
            name: '',
            contact_email: '',
            company: '',
            position: '',
            relationship: ''
        })
        setGeneratedEmail(null)
        setEditedEmail(null)
        setDraftId(null)
        setIsLoading(false)
        onClose()
    }

    const handleGenerate = async () => {

        if (!job) {
            return
        }

        // Validate required fields
        if (!contactInfo.name || !contactInfo.contact_email || !contactInfo.company || !contactInfo.relationship) {
            toast({
                title: "Missing Information",
                description: "Please fill in all required fields (Name, Email, Company, and Relationship)",
                variant: "destructive"
            })
            return
        }

        setIsLoading(true)
        try {
            // Generate email preview
            const draft = await referralApi.generateEmail(job.id, contactInfo as any)
            setGeneratedEmail(draft)
            setEditedEmail({ ...draft }) // Create editable copy
            setStep('preview')

            toast({
                title: "Email Generated",
                description: "Review and edit the email before sending"
            })
        } catch (error) {
            console.error('Failed to generate email:', error)
            const errorMessage = error instanceof Error ? error.message : 'Failed to generate referral email. Please try again.'
            toast({
                title: "Generation Failed",
                description: errorMessage,
                variant: "destructive"
            })
        } finally {
            setIsLoading(false)
        }
    }

    const handleSendEmail = async () => {
        if (!job || !editedEmail) return

        setIsLoading(true)
        try {
            // Create the referral request (saves contact and draft)
            const result = await referralApi.createRequest(job.id, contactInfo as any)
            setDraftId(result.draft.id)

            // Update the draft with any edits
            if (editedEmail.subject !== generatedEmail?.subject || editedEmail.body !== generatedEmail?.body) {
                await referralApi.updateDraft(result.draft.id, {
                    subject: editedEmail.subject,
                    email_body: editedEmail.body
                })
            }

            // Mark as sent (this doesn't actually send - user needs to send manually)
            await referralApi.sendEmail(result.draft.id)

            setStep('sent')
            toast({
                title: "Referral Request Ready",
                description: "Your referral request has been prepared. Copy the email content to send manually."
            })
        } catch (error) {
            console.error('Failed to send email:', error)
            const errorMessage = error instanceof Error ? error.message : 'Failed to prepare referral request. Please try again.'
            toast({
                title: "Send Failed",
                description: errorMessage,
                variant: "destructive"
            })
        } finally {
            setIsLoading(false)
        }
    }

    const updateEmail = (field: keyof GeneratedEmail, value: string) => {
        if (editedEmail) {
            setEditedEmail({
                ...editedEmail,
                [field]: value
            })
        }
    }

    const copyEmailToClipboard = async () => {
        if (!editedEmail) return

        const emailContent = `Subject: ${editedEmail.subject}\n\n${editedEmail.body}`

        try {
            await navigator.clipboard.writeText(emailContent)
            toast({
                title: "Copied to Clipboard",
                description: "Email content copied. Paste into your email client to send."
            })
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to copy to clipboard. Please copy manually.'
            toast({
                title: "Copy Failed",
                description: errorMessage,
                variant: "destructive"
            })
        }
    }

    if (!job) return null

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Send className="h-5 w-5" />
                        Request Referral - {job.title} at {job.company}
                    </DialogTitle>
                </DialogHeader>

                {step === 'input' && (
                    <div className="space-y-6">
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-lg">Contact Information</CardTitle>
                                <CardDescription>
                                    Who should we reach out to for this referral?
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="name">
                                            Contact Name *
                                        </Label>
                                        <div className="relative">
                                            <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                            <Input
                                                id="name"
                                                placeholder="John Doe"
                                                value={contactInfo.name}
                                                onChange={(e) => setContactInfo(prev => ({ ...prev, name: e.target.value }))}
                                                className="pl-10"
                                            />
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <Label htmlFor="contact_email">
                                            Email Address *
                                        </Label>
                                        <div className="relative">
                                            <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                            <Input
                                                id="contact_email"
                                                type="email"
                                                placeholder="john@company.com"
                                                value={contactInfo.contact_email}
                                                onChange={(e) => setContactInfo(prev => ({ ...prev, contact_email: e.target.value }))}
                                                className="pl-10"
                                            />
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <Label htmlFor="company">
                                            Company *
                                        </Label>
                                        <div className="relative">
                                            <Building className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                            <Input
                                                id="company"
                                                placeholder="Company Name"
                                                value={contactInfo.company}
                                                onChange={(e) => setContactInfo(prev => ({ ...prev, company: e.target.value }))}
                                                className="pl-10"
                                            />
                                        </div>
                                    </div>

                                    <div className="space-y-2">
                                        <Label htmlFor="position">
                                            Position
                                        </Label>
                                        <div className="relative">
                                            <Briefcase className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                            <Input
                                                id="position"
                                                placeholder="Software Engineer"
                                                value={contactInfo.position}
                                                onChange={(e) => setContactInfo(prev => ({ ...prev, position: e.target.value }))}
                                                className="pl-10"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="relationship">
                                        Relationship *
                                    </Label>
                                    <Select
                                        value={contactInfo.relationship}
                                        onValueChange={(value) => setContactInfo(prev => ({ ...prev, relationship: value }))}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select your relationship" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {RELATIONSHIP_OPTIONS.map((option) => (
                                                <SelectItem key={option.value} value={option.value}>
                                                    {option.label}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                            </CardContent>
                        </Card>

                        <div className="flex justify-end space-x-3">
                            <Button variant="outline" onClick={handleClose}>
                                Cancel
                            </Button>
                            <Button
                                type="button"
                                onClick={(e) => {
                                    e.preventDefault()
                                    e.stopPropagation()
                                    handleGenerate()
                                }}
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                        Generating...
                                    </>
                                ) : (
                                    <>
                                        <Edit3 className="h-4 w-4 mr-2" />
                                        Generate Email Preview
                                    </>
                                )}
                            </Button>
                        </div>
                    </div>
                )}

                {step === 'preview' && editedEmail && (
                    <div className="space-y-6">
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-lg">Email Preview & Edit</CardTitle>
                                <CardDescription>
                                    Review and customize your referral email before sending
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="subject">Subject Line</Label>
                                    <Input
                                        id="subject"
                                        value={editedEmail.subject}
                                        onChange={(e) => updateEmail('subject', e.target.value)}
                                        className="font-medium"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="body">Email Body</Label>
                                    <Textarea
                                        id="body"
                                        value={editedEmail.body}
                                        onChange={(e) => updateEmail('body', e.target.value)}
                                        rows={12}
                                        className="font-mono text-sm"
                                    />
                                </div>

                                <div className="flex items-center gap-2">
                                    <Badge variant="secondary">
                                        Template: {editedEmail.template_used}
                                    </Badge>
                                </div>
                            </CardContent>
                        </Card>

                        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                            <div className="flex items-start gap-3">
                                <div className="flex-shrink-0">
                                    <div className="w-2 h-2 bg-amber-400 rounded-full mt-2"></div>
                                </div>
                                <div className="text-sm text-amber-700">
                                    <p className="font-medium">Important Note</p>
                                    <p>This will prepare your referral request. You&apos;ll need to manually send the email from your own email client to maintain authenticity and control.</p>
                                </div>
                            </div>
                        </div>

                        <div className="flex justify-between">
                            <Button
                                variant="outline"
                                onClick={() => setStep('input')}
                                disabled={isLoading}
                            >
                                <ArrowLeft className="h-4 w-4 mr-2" />
                                Back to Edit Contact
                            </Button>
                            <div className="space-x-3">
                                <Button variant="outline" onClick={handleClose}>
                                    Cancel
                                </Button>
                                <Button onClick={handleSendEmail} disabled={isLoading}>
                                    {isLoading ? (
                                        <>
                                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                            Preparing...
                                        </>
                                    ) : (
                                        <>
                                            <Send className="h-4 w-4 mr-2" />
                                            Prepare Referral Request
                                        </>
                                    )}
                                </Button>
                            </div>
                        </div>
                    </div>
                )}

                {step === 'sent' && editedEmail && (
                    <div className="space-y-6 text-center">
                        <div className="flex flex-col items-center space-y-4">
                            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                                <CheckCircle className="h-8 w-8 text-green-600" />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold">Referral Request Prepared!</h3>
                                <p className="text-muted-foreground">
                                    Your referral request has been saved and is ready to send.
                                </p>
                            </div>
                        </div>

                        <Card>
                            <CardHeader>
                                <CardTitle className="text-sm">Ready to Send</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="text-sm text-left">
                                    <p><strong>To:</strong> {contactInfo.contact_email}</p>
                                    <p><strong>Subject:</strong> {editedEmail.subject}</p>
                                </div>

                                <div className="border rounded-lg p-3 text-left text-sm bg-gray-50 max-h-40 overflow-y-auto">
                                    <pre className="whitespace-pre-wrap font-sans">{editedEmail.body}</pre>
                                </div>
                            </CardContent>
                        </Card>

                        <div className="space-y-3">
                            <Button onClick={copyEmailToClipboard} className="w-full">
                                <Mail className="h-4 w-4 mr-2" />
                                Copy Email Content
                            </Button>
                            <Button variant="outline" onClick={handleClose} className="w-full">
                                Close
                            </Button>
                        </div>

                        <div className="text-xs text-muted-foreground">
                            Tip: Open your email client, paste the content, and send from your personal email for best results.
                        </div>
                    </div>
                )}
            </DialogContent>
        </Dialog>
    )
}