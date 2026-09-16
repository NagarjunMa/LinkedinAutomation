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
import { CheckCircle, Shield, User, GraduationCap, Plus, Trash2 } from 'lucide-react'
import { createClient } from '@/lib/supabase'

export default function OnboardingPage() {
    const { user, refreshUser } = useAuth()
    const router = useRouter()
    const [loading, setLoading] = useState(false)
    const [formData, setFormData] = useState({
        fullName: '',
        jobTitle: '',
        targetRole: '',
        targetCountry: 'USA',
        careerLevel: 'mid',
        acceptTerms: false,
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

        if (user.user_metadata) {
            setFormData(prev => ({
                ...prev,
                fullName: user.user_metadata.full_name || '',
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

        if (step === 2 && !formData.targetRole.trim()) {
            setError('Please enter your target role')
            return
        }

        if (step === 3) {
            const hasValidEducation = formData.education.some(edu =>
                edu.degree.trim() && edu.institution.trim()
            )
            if (!hasValidEducation) {
                setError('Please provide at least your degree and institution')
                return
            }
        }

        if (step === 4 && !formData.acceptTerms) {
            setError('Please accept the Terms of Service and Privacy Policy')
            return
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

            const { error: updateError } = await supabase.auth.updateUser({
                data: {
                    onboarding_completed: true,
                    full_name: formData.fullName,
                    job_title: formData.jobTitle,
                    target_role: formData.targetRole,
                    target_country: formData.targetCountry,
                    career_level: formData.careerLevel,
                }
            })

            if (updateError) {
                throw updateError
            }

            await refreshUser()
            router.push('/dashboard')

        } catch (error) {
            console.error('Error completing onboarding:', error)
            setError('Failed to complete setup. Please try again.')
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
                        <CardTitle className="text-2xl">Welcome to Prism Pro</CardTitle>
                        <CardDescription>
                            Let&apos;s set up your resume workspace in 4 quick steps.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {/* Step progress */}
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
                                <h3 className="text-base font-semibold">Your details</h3>
                                <p className="text-sm text-muted-foreground">
                                    We use your name and current title to personalise the AI evaluation output and resume header suggestions.
                                </p>
                                <div>
                                    <Label htmlFor="fullName">Full Name *</Label>
                                    <Input
                                        id="fullName"
                                        value={formData.fullName}
                                        onChange={(e) => handleInputChange('fullName', e.target.value)}
                                        placeholder="Your full name"
                                        className="mt-1"
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="jobTitle">Current Title (optional)</Label>
                                    <Input
                                        id="jobTitle"
                                        value={formData.jobTitle}
                                        onChange={(e) => handleInputChange('jobTitle', e.target.value)}
                                        placeholder="e.g. Senior Software Engineer"
                                        className="mt-1"
                                    />
                                </div>
                            </div>
                        )}

                        {/* Step 2: Target Role + Market */}
                        {step === 2 && (
                            <div className="space-y-5">
                                <h3 className="text-base font-semibold">Target role and market</h3>
                                <p className="text-sm text-muted-foreground">
                                    Choose the market you are targeting to guide presentation preferences. This does not predict employer screening rules or change the facts you can claim.
                                </p>
                                <div>
                                    <Label htmlFor="targetRole">Target Role *</Label>
                                    <Input
                                        id="targetRole"
                                        value={formData.targetRole}
                                        onChange={(e) => handleInputChange('targetRole', e.target.value)}
                                        placeholder="e.g. Staff Engineer, Data Scientist, Product Manager"
                                        className="mt-1"
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="targetCountry">Target Market</Label>
                                    <select
                                        id="targetCountry"
                                        value={formData.targetCountry}
                                        onChange={(e) => handleInputChange('targetCountry', e.target.value)}
                                        className="mt-1 w-full border border-input bg-background px-3 py-2 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                                    >
                                        <option value="USA">United States</option>
                                        <option value="India">India</option>
                                        <option value="Both">Both (US + India)</option>
                                    </select>
                                </div>
                                <div>
                                    <Label htmlFor="careerLevel">Career Level</Label>
                                    <select
                                        id="careerLevel"
                                        value={formData.careerLevel}
                                        onChange={(e) => handleInputChange('careerLevel', e.target.value)}
                                        className="mt-1 w-full border border-input bg-background px-3 py-2 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                                    >
                                        <option value="mid">Mid-level (3–6 years)</option>
                                        <option value="senior">Senior (6–10 years)</option>
                                        <option value="staff">Staff / Principal (10+ years)</option>
                                        <option value="manager">Engineering Manager / Director</option>
                                    </select>
                                </div>
                            </div>
                        )}

                        {/* Step 3: Education */}
                        {step === 3 && (
                            <div className="space-y-4">
                                <div className="flex items-center space-x-2 mb-2">
                                    <GraduationCap className="w-5 h-5" />
                                    <h3 className="text-base font-semibold">Education</h3>
                                </div>
                                <p className="text-sm text-muted-foreground">
                                    Record your education accurately. It does not establish skills or seniority without supporting experience.
                                </p>

                                {formData.education.map((edu, index) => (
                                    <div key={index} className="p-4 border rounded-lg space-y-4">
                                        <div className="flex justify-between items-center">
                                            <h4 className="font-medium text-sm">Education {index + 1}</h4>
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
                                                    placeholder="B.Tech. Computer Science"
                                                    className="mt-1"
                                                />
                                            </div>
                                            <div>
                                                <Label htmlFor={`institution-${index}`}>Institution *</Label>
                                                <Input
                                                    id={`institution-${index}`}
                                                    value={edu.institution}
                                                    onChange={(e) => handleEducationChange(index, 'institution', e.target.value)}
                                                    placeholder="IIT Bombay / UC Berkeley"
                                                    className="mt-1"
                                                />
                                            </div>
                                            <div>
                                                <Label htmlFor={`year-${index}`}>Graduation Year</Label>
                                                <Input
                                                    id={`year-${index}`}
                                                    value={edu.graduationYear}
                                                    onChange={(e) => handleEducationChange(index, 'graduationYear', e.target.value)}
                                                    placeholder="2019"
                                                    className="mt-1"
                                                />
                                            </div>
                                            <div>
                                                <Label htmlFor={`gpa-${index}`}>GPA / CGPA (optional)</Label>
                                                <Input
                                                    id={`gpa-${index}`}
                                                    value={edu.gpa}
                                                    onChange={(e) => handleEducationChange(index, 'gpa', e.target.value)}
                                                    placeholder="8.4 / 10"
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
                                    Add Another Degree
                                </Button>
                            </div>
                        )}

                        {/* Step 4: Terms + Review */}
                        {step === 4 && (
                            <div className="space-y-5">
                                <h3 className="text-base font-semibold">Review and agree</h3>

                                <div className="p-4 bg-muted/50 rounded-lg text-sm space-y-2">
                                    <p className="font-semibold mb-3">Your setup summary</p>
                                    <p><strong>Name:</strong> {formData.fullName}</p>
                                    {formData.jobTitle && <p><strong>Current Title:</strong> {formData.jobTitle}</p>}
                                    {formData.targetRole && <p><strong>Target Role:</strong> {formData.targetRole}</p>}
                                    <p><strong>Target Market:</strong> {formData.targetCountry}</p>
                                    <p><strong>Career Level:</strong> {formData.careerLevel}</p>
                                    {formData.education[0]?.degree && (
                                        <p><strong>Education:</strong> {formData.education[0].degree}{formData.education[0].institution ? ` — ${formData.education[0].institution}` : ''}</p>
                                    )}
                                </div>

                                <div className="flex items-start space-x-3">
                                    <Checkbox
                                        id="acceptTerms"
                                        checked={formData.acceptTerms}
                                        onCheckedChange={(checked) =>
                                            handleInputChange('acceptTerms', checked as boolean)
                                        }
                                    />
                                    <div className="space-y-1">
                                        <Label htmlFor="acceptTerms" className="flex items-center space-x-2 cursor-pointer">
                                            <Shield className="w-4 h-4" />
                                            <span>I agree to the Terms of Service and Privacy Policy</span>
                                        </Label>
                                        <p className="text-xs text-muted-foreground">
                                            Prism Pro is Google OAuth verified. We request only your name and email — no Gmail access. Your resume data is private and never shared with third parties.
                                        </p>
                                    </div>
                                </div>

                                <div className="text-xs text-muted-foreground p-3 bg-muted/30 rounded-md">
                                    <strong>What happens next:</strong> You will land on your Resume workspace. Upload your resume to review content feedback and separate document checks. Accept only suggestions supported by your actual experience. Your 90 free monthly credits are waiting.
                                </div>
                            </div>
                        )}

                        {/* Navigation */}
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
                                {step === 4 ? (loading ? 'Setting up...' : 'Enter Prism Pro') : 'Next'}
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
