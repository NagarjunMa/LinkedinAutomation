"use client"

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/auth-context'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CheckCircle, Mail, Shield, User, Briefcase, GraduationCap, Plus, Trash2 } from 'lucide-react'
import { createClient } from '@/lib/supabase'

export default function OnboardingPage() {
    const { user, refreshUser } = useAuth()
    const router = useRouter()
    const [loading, setLoading] = useState(false)
    const [formData, setFormData] = useState({
        fullName: '',
        company: '',
        jobTitle: '',
        acceptTerms: false,
        acceptGmailAccess: false,
        acceptJobTracking: false,
        education: [{
            degree: '',
            institution: '',
            graduationYear: '',
            gpa: ''
        }]
    })
    const [step, setStep] = useState(1)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (!user) {
            router.push('/')
            return
        }

        // Pre-fill form with user data if available
        if (user.user_metadata) {
            setFormData(prev => ({
                ...prev,
                fullName: user.user_metadata.full_name || '',
                company: user.user_metadata.company || '',
                jobTitle: user.user_metadata.job_title || ''
            }))
        }
    }, [user, router])

    const handleInputChange = (field: string, value: string | boolean) => {
        setFormData(prev => ({
            ...prev,
            [field]: value
        }))
    }

    const handleEducationChange = (index: number, field: string, value: string) => {
        setFormData(prev => ({
            ...prev,
            education: prev.education.map((edu, i) =>
                i === index ? { ...edu, [field]: value } : edu
            )
        }))
    }

    const addEducation = () => {
        setFormData(prev => ({
            ...prev,
            education: [...prev.education, {
                degree: '',
                institution: '',
                graduationYear: '',
                gpa: ''
            }]
        }))
    }

    const removeEducation = (index: number) => {
        if (formData.education.length > 1) {
            setFormData(prev => ({
                ...prev,
                education: prev.education.filter((_, i) => i !== index)
            }))
        }
    }

    const handleNext = () => {
        if (step === 1 && !formData.fullName.trim()) {
            setError('Please enter your full name')
            return
        }

        if (step === 2 && !formData.acceptTerms) {
            setError('Please accept the terms and conditions')
            return
        }

        if (step === 3) {
            // Validate at least one education entry has degree and institution
            const hasValidEducation = formData.education.some(edu =>
                edu.degree.trim() && edu.institution.trim()
            )
            if (!hasValidEducation) {
                setError('Please provide at least your degree and institution')
                return
            }
        }

        setError(null)
        if (step < 4) {
            setStep(step + 1)
        } else {
            handleComplete()
        }
    }

    const handleBack = () => {
        if (step > 1) {
            setStep(step - 1)
            setError(null)
        }
    }

    const handleComplete = async () => {
        try {
            setLoading(true)
            setError(null)

            const supabase = createClient()

            // Update user metadata with onboarding completion and OAuth provider
            const { error: updateError } = await supabase.auth.updateUser({
                data: {
                    onboarding_completed: true,
                    oauth_provider: 'google', // Mark that user has completed OAuth
                    full_name: formData.fullName,
                    company: formData.company,
                    job_title: formData.jobTitle,
                    permissions: {
                        gmail_access: formData.acceptGmailAccess,
                        job_tracking: formData.acceptJobTracking
                    }
                }
            })

            if (updateError) {
                throw updateError
            }

            // Refresh user data
            await refreshUser()

            // Redirect to dashboard
            router.push('/dashboard')

        } catch (error) {
            console.error('Error completing onboarding:', error)
            setError('Failed to complete onboarding. Please try again.')
        } finally {
            setLoading(false)
        }
    }

    if (!user) {
        return null
    }

    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
            <div className="w-full max-w-2xl">
                <Card>
                    <CardHeader className="text-center">
                        <div className="mx-auto mb-4 w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                            <User className="w-8 h-8 text-primary" />
                        </div>
                        <CardTitle className="text-2xl">Welcome to Prism Pro!</CardTitle>
                        <CardDescription>
                            Let&apos;s set up your account and get you started
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {/* Progress indicator */}
                        <div className="flex items-center justify-between mb-6">
                            {[1, 2, 3, 4].map((stepNumber) => (
                                <div
                                    key={stepNumber}
                                    className={`flex items-center justify-center w-8 h-8 rounded-full border-2 ${stepNumber <= step
                                        ? 'border-primary bg-primary text-primary-foreground'
                                        : 'border-muted-foreground/20'
                                        }`}
                                >
                                    {stepNumber < step ? (
                                        <CheckCircle className="w-5 h-5" />
                                    ) : (
                                        stepNumber
                                    )}
                                </div>
                            ))}
                        </div>

                        {error && (
                            <Alert variant="destructive">
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}

                        {/* Step 1: Basic Information */}
                        {step === 1 && (
                            <div className="space-y-4">
                                <div>
                                    <Label htmlFor="fullName">Full Name</Label>
                                    <Input
                                        id="fullName"
                                        value={formData.fullName}
                                        onChange={(e) => handleInputChange('fullName', e.target.value)}
                                        placeholder="Enter your full name"
                                        className="mt-1"
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="company">Company (Optional)</Label>
                                    <Input
                                        id="company"
                                        value={formData.company}
                                        onChange={(e) => handleInputChange('company', e.target.value)}
                                        placeholder="Where do you work?"
                                        className="mt-1"
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="jobTitle">Job Title (Optional)</Label>
                                    <Input
                                        id="jobTitle"
                                        value={formData.jobTitle}
                                        onChange={(e) => handleInputChange('jobTitle', e.target.value)}
                                        placeholder="What's your role?"
                                        className="mt-1"
                                    />
                                </div>
                            </div>
                        )}

                        {/* Step 2: Permissions */}
                        {step === 2 && (
                            <div className="space-y-4">
                                <div className="space-y-3">
                                    <div className="flex items-start space-x-3">
                                        <Checkbox
                                            id="gmailAccess"
                                            checked={formData.acceptGmailAccess}
                                            onCheckedChange={(checked) =>
                                                handleInputChange('acceptGmailAccess', checked as boolean)
                                            }
                                        />
                                        <div className="space-y-1">
                                            <Label htmlFor="gmailAccess" className="flex items-center space-x-2">
                                                <Mail className="w-4 h-4" />
                                                <span>Gmail Access</span>
                                            </Label>
                                            <p className="text-sm text-muted-foreground">
                                                Allow Prism Pro to access your Gmail to automatically track job application emails
                                            </p>
                                        </div>
                                    </div>

                                    <div className="flex items-start space-x-3">
                                        <Checkbox
                                            id="jobTracking"
                                            checked={formData.acceptJobTracking}
                                            onCheckedChange={(checked) =>
                                                handleInputChange('acceptJobTracking', checked as boolean)
                                            }
                                        />
                                        <div className="space-y-1">
                                            <Label htmlFor="jobTracking" className="flex items-center space-x-2">
                                                <Briefcase className="w-4 h-4" />
                                                <span>Job Application Tracking</span>
                                            </Label>
                                            <p className="text-sm text-muted-foreground">
                                                Track your job applications and get insights on your application performance
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Step 3: Education */}
                        {step === 3 && (
                            <div className="space-y-4">
                                <div className="flex items-center space-x-2 mb-4">
                                    <GraduationCap className="w-5 h-5" />
                                    <h3 className="text-lg font-medium">Education Information</h3>
                                </div>

                                {formData.education.map((edu, index) => (
                                    <div key={index} className="p-4 border rounded-lg space-y-4">
                                        <div className="flex justify-between items-center">
                                            <h4 className="font-medium">Education {index + 1}</h4>
                                            {formData.education.length > 1 && (
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => removeEducation(index)}
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </Button>
                                            )}
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div>
                                                <Label htmlFor={`degree-${index}`}>Degree *</Label>
                                                <Input
                                                    id={`degree-${index}`}
                                                    value={edu.degree}
                                                    onChange={(e) => handleEducationChange(index, 'degree', e.target.value)}
                                                    placeholder="Bachelor's in Computer Science"
                                                    className="mt-1"
                                                />
                                            </div>
                                            <div>
                                                <Label htmlFor={`institution-${index}`}>Institution *</Label>
                                                <Input
                                                    id={`institution-${index}`}
                                                    value={edu.institution}
                                                    onChange={(e) => handleEducationChange(index, 'institution', e.target.value)}
                                                    placeholder="University of California"
                                                    className="mt-1"
                                                />
                                            </div>
                                            <div>
                                                <Label htmlFor={`year-${index}`}>Graduation Year</Label>
                                                <Input
                                                    id={`year-${index}`}
                                                    value={edu.graduationYear}
                                                    onChange={(e) => handleEducationChange(index, 'graduationYear', e.target.value)}
                                                    placeholder="2023"
                                                    className="mt-1"
                                                />
                                            </div>
                                            <div>
                                                <Label htmlFor={`gpa-${index}`}>GPA (Optional)</Label>
                                                <Input
                                                    id={`gpa-${index}`}
                                                    value={edu.gpa}
                                                    onChange={(e) => handleEducationChange(index, 'gpa', e.target.value)}
                                                    placeholder="3.8"
                                                    className="mt-1"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                ))}

                                <Button
                                    variant="outline"
                                    onClick={addEducation}
                                    className="w-full"
                                >
                                    <Plus className="w-4 h-4 mr-2" />
                                    Add Another Education
                                </Button>
                            </div>
                        )}

                        {/* Step 4: Terms and Final Review */}
                        {step === 4 && (
                            <div className="space-y-4">
                                <div className="space-y-3">
                                    <div className="flex items-start space-x-3">
                                        <Checkbox
                                            id="acceptTerms"
                                            checked={formData.acceptTerms}
                                            onCheckedChange={(checked) =>
                                                handleInputChange('acceptTerms', checked as boolean)
                                            }
                                        />
                                        <div className="space-y-1">
                                            <Label htmlFor="acceptTerms" className="flex items-center space-x-2">
                                                <Shield className="w-4 h-4" />
                                                <span>Terms and Conditions</span>
                                            </Label>
                                            <p className="text-sm text-muted-foreground">
                                                I agree to the Terms of Service and Privacy Policy
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                <div className="p-4 bg-muted/50 rounded-lg">
                                    <h4 className="font-medium mb-2">Review Your Setup</h4>
                                    <div className="space-y-2 text-sm">
                                        <p><strong>Name:</strong> {formData.fullName}</p>
                                        {formData.company && <p><strong>Company:</strong> {formData.company}</p>}
                                        {formData.jobTitle && <p><strong>Job Title:</strong> {formData.jobTitle}</p>}

                                        <div className="mt-3">
                                            <p className="font-medium">Education:</p>
                                            {formData.education.map((edu, index) => (
                                                <div key={index} className="ml-4 text-xs space-y-1">
                                                    {edu.degree && <p>• <strong>Degree:</strong> {edu.degree}</p>}
                                                    {edu.institution && <p>• <strong>Institution:</strong> {edu.institution}</p>}
                                                    {edu.graduationYear && <p>• <strong>Year:</strong> {edu.graduationYear}</p>}
                                                    {edu.gpa && <p>• <strong>GPA:</strong> {edu.gpa}</p>}
                                                    {index < formData.education.length - 1 && <div className="border-t pt-1 mt-2" />}
                                                </div>
                                            ))}
                                        </div>

                                        <p><strong>Gmail Access:</strong> {formData.acceptGmailAccess ? 'Enabled' : 'Disabled'}</p>
                                        <p><strong>Job Tracking:</strong> {formData.acceptJobTracking ? 'Enabled' : 'Disabled'}</p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Navigation buttons */}
                        <div className="flex justify-between pt-4">
                            <Button
                                variant="outline"
                                onClick={handleBack}
                                disabled={step === 1}
                            >
                                Back
                            </Button>
                            <Button
                                onClick={handleNext}
                                disabled={loading}
                                className="ml-auto"
                            >
                                {step === 4 ? (loading ? 'Setting up...' : 'Complete Setup') : 'Next'}
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
