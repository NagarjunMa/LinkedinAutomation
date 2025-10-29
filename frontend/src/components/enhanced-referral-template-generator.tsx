"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/components/ui/use-toast"
import { referralTemplatesAPI } from '@/app/lib/api'
import {
    MessageSquare,
    User,
    Building,
    Briefcase,
    Sparkles,
    Send,
    Copy,
    Save,
    Settings
} from "lucide-react"
import { cn } from "@/lib/utils"

interface TemplateGeneratorProps {
    onTemplateGenerated?: (template: any) => void
    onClose?: () => void
}

export function EnhancedReferralTemplateGenerator({ onTemplateGenerated, onClose }: TemplateGeneratorProps) {
    const [loading, setLoading] = useState(false)
    const [generatedTemplate, setGeneratedTemplate] = useState<any>(null)
    const [pastedText, setPastedText] = useState("")
    const [showManualEdit, setShowManualEdit] = useState(false)
    const { toast } = useToast()

    // Form state
    const [contactInfo, setContactInfo] = useState({
        name: "",
        email: "",
        company: "",
        position: "",
        linkedin_url: ""
    })

    const [userBackground, setUserBackground] = useState("")

    const [preferences, setPreferences] = useState({
        preferred_tone: "professional",
        preferred_length: "medium",
        include_resume: true,
        include_portfolio: false
    })

    const handleParseContact = async () => {
        if (!pastedText.trim()) return

        try {
            // Simple parsing logic - try to extract common patterns
            const lines = pastedText.split('\n').map(line => line.trim()).filter(line => line)

            let name = ""
            let position = ""
            let company = ""
            let email = ""

            // Look for name (usually first line or most prominent)
            if (lines.length > 0) {
                name = lines[0]
            }

            // Look for email pattern
            const emailMatch = pastedText.match(/[\w\.-]+@[\w\.-]+\.\w+/)
            if (emailMatch) {
                email = emailMatch[0]
            }

            // Look for common LinkedIn patterns
            for (const line of lines) {
                // Skip obviously non-relevant lines
                if (line.includes('LinkedIn') || line.includes('connections') || line.includes('followers')) continue
                if (line.length < 3) continue

                // Look for "at [Company]" pattern
                const atMatch = line.match(/(.+)\s+at\s+(.+)/)
                if (atMatch) {
                    position = atMatch[1].trim()
                    company = atMatch[2].trim()
                    continue
                }

                // Look for company indicators
                if (line.includes('Engineer') || line.includes('Manager') || line.includes('Developer') ||
                    line.includes('Director') || line.includes('Lead') || line.includes('Senior')) {
                    if (!position) position = line
                }
            }

            // Try to extract company from position if pattern like "Software Engineer at Google"
            if (position && !company) {
                const companyMatch = position.match(/(.+)\s+at\s+(.+)/)
                if (companyMatch) {
                    position = companyMatch[1].trim()
                    company = companyMatch[2].trim()
                }
            }

            // Update contact info
            setContactInfo({
                name: name || contactInfo.name,
                email: email || contactInfo.email,
                company: company || contactInfo.company,
                position: position || contactInfo.position,
                linkedin_url: contactInfo.linkedin_url
            })

            if (name) {
                toast({
                    title: "Contact Parsed!",
                    description: `Extracted info for ${name}`,
                })
            }
        } catch (error) {
            console.error('Error parsing contact:', error)
            toast({
                title: "Parsing Error",
                description: "Could not automatically parse. Please edit manually.",
                variant: "destructive",
            })
        }
    }

    const generateTemplate = async () => {
        if (!contactInfo.name || !contactInfo.company) {
            toast({
                title: "Missing Information",
                description: "Please fill in the contact name and company.",
                variant: "destructive",
            })
            return
        }

        try {
            setLoading(true)

            // Use contact's position and company as the "job" they can refer for
            const jobInfo = {
                title: contactInfo.position || "Position at their company",
                company: contactInfo.company,
                industry: "",
                level: "",
                description: "Referral opportunity at their company",
                user_background: userBackground
            }

            const response = await referralTemplatesAPI.generate({
                contact_info: contactInfo,
                job_info: jobInfo,
                user_preferences: preferences
            })

            setGeneratedTemplate(response)

            toast({
                title: "Template Generated!",
                description: "Your personalized referral template has been created.",
            })

            if (onTemplateGenerated) {
                onTemplateGenerated(response)
            }

        } catch (error) {
            console.error('Error generating template:', error)
            toast({
                title: "Error",
                description: "Failed to generate template. Please try again.",
                variant: "destructive",
            })
        } finally {
            setLoading(false)
        }
    }

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text)
        toast({
            title: "Copied!",
            description: "Template content copied to clipboard.",
        })
    }

    const markAsSent = async () => {
        if (!generatedTemplate?.template_id) return

        try {
            await referralTemplatesAPI.markSent(generatedTemplate.template_id)
            toast({
                title: "Marked as Sent",
                description: "Template has been marked as sent for tracking.",
            })
        } catch (error) {
            console.error('Error marking as sent:', error)
            toast({
                title: "Error",
                description: "Failed to mark template as sent.",
                variant: "destructive",
            })
        }
    }

    return (
        <div className="space-y-6">
            {/* Contact Information - Paste and Parse */}
            <Card className="bg-primary-900/50 border-primary-800">
                <CardHeader>
                    <CardTitle className="text-cream-50 flex items-center gap-2">
                        <User className="h-5 w-5 text-accent-400" />
                        Contact Information
                    </CardTitle>
                    <p className="text-cream-400 text-sm mt-2">
                        Copy contact info from LinkedIn and paste below. We'll extract the details automatically.
                    </p>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="pastedText" className="text-cream-200 text-sm md:text-base">
                            Paste LinkedIn Profile Info
                        </Label>
                        <Textarea
                            id="pastedText"
                            placeholder={`Paste contact info from LinkedIn:

Nikin Tharan
Helping high-skilled immigrants | O1 & EB1A Recipient
New York City Metropolitan Area
Software Engineer at Meta

Or manually enter:
Name: John Doe
Position: Senior Software Engineer
Company: Tech Corp Inc.
Email: john@techcorp.com`}
                            value={pastedText}
                            onChange={(e) => setPastedText(e.target.value)}
                            onBlur={handleParseContact}
                            className="bg-primary-950 border-primary-700 text-cream-50 text-sm md:text-base min-h-[120px] md:min-h-[150px] touch-manipulation"
                            rows={6}
                        />
                    </div>

                    {/* Parsed Contact Preview */}
                    {contactInfo.name && (
                        <div className="bg-primary-950 border border-primary-700 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-3">
                                <div className="text-sm text-cream-400">Detected Contact:</div>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setShowManualEdit(!showManualEdit)}
                                    className="text-accent-400 hover:text-accent-300 text-xs"
                                >
                                    {showManualEdit ? "Hide" : "Edit"} Details
                                </Button>
                            </div>
                            <div className="text-cream-50 space-y-1">
                                <div className="font-medium">{contactInfo.name}</div>
                                {contactInfo.position && <div className="text-sm">{contactInfo.position}</div>}
                                {contactInfo.company && <div className="text-sm">{contactInfo.company}</div>}
                                {contactInfo.email && <div className="text-sm">{contactInfo.email}</div>}
                            </div>
                        </div>
                    )}

                    {/* Manual Edit Fields (Hidden by default) */}
                    {showManualEdit && contactInfo.name && (
                        <div className="grid grid-cols-2 gap-4 p-4 bg-primary-950 border border-primary-700 rounded-lg">
                            <div className="space-y-2">
                                <Label className="text-cream-200 text-sm">Name *</Label>
                                <Input
                                    value={contactInfo.name}
                                    onChange={(e) => setContactInfo({...contactInfo, name: e.target.value})}
                                    className="bg-primary-900 border-primary-600 text-cream-50"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label className="text-cream-200 text-sm">Email</Label>
                                <Input
                                    value={contactInfo.email}
                                    onChange={(e) => setContactInfo({...contactInfo, email: e.target.value})}
                                    className="bg-primary-900 border-primary-600 text-cream-50"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label className="text-cream-200 text-sm">Company *</Label>
                                <Input
                                    value={contactInfo.company}
                                    onChange={(e) => setContactInfo({...contactInfo, company: e.target.value})}
                                    className="bg-primary-900 border-primary-600 text-cream-50"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label className="text-cream-200 text-sm">Position</Label>
                                <Input
                                    value={contactInfo.position}
                                    onChange={(e) => setContactInfo({...contactInfo, position: e.target.value})}
                                    className="bg-primary-900 border-primary-600 text-cream-50"
                                />
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Your Background */}
            <Card className="bg-primary-900/50 border-primary-800">
                <CardHeader>
                    <CardTitle className="text-cream-50 flex items-center gap-2">
                        <User className="h-5 w-5 text-accent-400" />
                        Your Background
                    </CardTitle>
                    <p className="text-cream-400 text-sm mt-2">
                        Brief summary of your relevant experience and why you're interested in their company.
                    </p>
                </CardHeader>
                <CardContent>
                    <div className="space-y-2">
                        <Label htmlFor="userBackground" className="text-cream-200">Your Relevant Background</Label>
                        <Textarea
                            id="userBackground"
                            placeholder="Brief summary of your experience and skills that would be relevant to their company..."
                            value={userBackground}
                            onChange={(e) => setUserBackground(e.target.value)}
                            className="bg-primary-950 border-primary-700 text-cream-50"
                            rows={4}
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Preferences */}
            <Card className="bg-primary-900/50 border-primary-800">
                <CardHeader>
                    <CardTitle className="text-cream-50 flex items-center gap-2">
                        <Settings className="h-5 w-5 text-accent-400" />
                        Template Preferences
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label className="text-cream-200">Tone</Label>
                            <Select value={preferences.preferred_tone} onValueChange={(value) => setPreferences({...preferences, preferred_tone: value})}>
                                <SelectTrigger className="bg-primary-950 border-primary-700 text-cream-50">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="professional">Professional</SelectItem>
                                    <SelectItem value="casual">Casual</SelectItem>
                                    <SelectItem value="direct">Direct</SelectItem>
                                    <SelectItem value="friendly">Friendly</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label className="text-cream-200">Length</Label>
                            <Select value={preferences.preferred_length} onValueChange={(value) => setPreferences({...preferences, preferred_length: value})}>
                                <SelectTrigger className="bg-primary-950 border-primary-700 text-cream-50">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="short">Short</SelectItem>
                                    <SelectItem value="medium">Medium</SelectItem>
                                    <SelectItem value="long">Long</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Generate Button */}
            <Button
                onClick={generateTemplate}
                disabled={loading}
                className="w-full bg-accent-500 hover:bg-accent-600 text-white min-h-[48px] md:min-h-[52px] text-sm md:text-base touch-manipulation"
                size="lg"
            >
                {loading ? (
                    <>
                        <Sparkles className="h-5 w-5 mr-2 animate-spin" />
                        <span className="hidden sm:inline">Generating Template...</span>
                        <span className="sm:hidden">Generating...</span>
                    </>
                ) : (
                    <>
                        <Sparkles className="h-5 w-5 mr-2" />
                        <span className="hidden sm:inline">Generate Referral Template</span>
                        <span className="sm:hidden">Generate Template</span>
                    </>
                )}
            </Button>

            {/* Generated Template */}
            {generatedTemplate && (
                <Card className="bg-primary-900/50 border-primary-800">
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle className="text-cream-50 flex items-center gap-2">
                            <MessageSquare className="h-5 w-5 text-accent-400" />
                            Generated Template
                        </CardTitle>
                        <div className="flex items-center gap-2">
                            <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                                Confidence: {Math.round(generatedTemplate.confidence_score * 100)}%
                            </Badge>
                            <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                                {generatedTemplate.style}
                            </Badge>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <Label className="text-cream-200">Subject Line</Label>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => copyToClipboard(generatedTemplate.subject_line)}
                                    className="text-accent-400 hover:text-accent-300"
                                >
                                    <Copy className="h-4 w-4" />
                                </Button>
                            </div>
                            <div className="bg-primary-950 border border-primary-700 rounded-lg p-3">
                                <p className="text-cream-50 text-sm">{generatedTemplate.subject_line}</p>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <Label className="text-cream-200">Email Body</Label>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => copyToClipboard(generatedTemplate.email_body)}
                                    className="text-accent-400 hover:text-accent-300"
                                >
                                    <Copy className="h-4 w-4" />
                                </Button>
                            </div>
                            <div className="bg-primary-950 border border-primary-700 rounded-lg p-4">
                                <pre className="text-cream-50 text-sm whitespace-pre-wrap font-sans">
                                    {generatedTemplate.email_body}
                                </pre>
                            </div>
                        </div>

                        <div className="flex items-center gap-3 pt-4">
                            <Button
                                onClick={markAsSent}
                                className="bg-blue-600 hover:bg-blue-700 text-white"
                            >
                                <Send className="h-4 w-4 mr-2" />
                                Mark as Sent
                            </Button>
                            <Button
                                variant="outline"
                                onClick={() => copyToClipboard(`Subject: ${generatedTemplate.subject_line}\n\n${generatedTemplate.email_body}`)}
                                className="border-primary-700 text-cream-200 hover:bg-primary-800"
                            >
                                <Copy className="h-4 w-4 mr-2" />
                                Copy Full Template
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}