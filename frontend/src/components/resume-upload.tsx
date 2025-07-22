"use client"

import { useState, useCallback } from "react"
import { useDropzone } from "react-dropzone"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useToast } from "@/components/ui/use-toast"
import { UploadIcon, FileTextIcon, BrainIcon, CheckCircleIcon, AlertCircleIcon } from "lucide-react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface ParsedProfile {
  personal_info: {
    full_name: string
    email: string
    phone: string
    location: string
    work_authorization: string
  }
  professional_summary: {
    years_of_experience: number
    career_level: string
    summary: string
  }
  skills: {
    programming_languages: string[]
    frameworks_libraries: string[]
    tools_platforms: string[]
    soft_skills: string[]
  }
  experience: {
    job_titles: string[]
    companies: string[]
    industries: string[]
    descriptions: string[]
  }
  education: {
    degrees: string[]
    institutions: string[]
    graduation_years: number[]
    coursework: string[]
  }
  preferences: {
    desired_roles: string[]
    preferred_locations: string[]
    salary_range_min: number
    salary_range_max: number
    job_types: string[]
  }
  ai_insights: {
    profile_summary: string
    strengths: string[]
    improvement_areas: string[]
    career_advice: string
  }
  metadata: {
    created_at: string
    updated_at: string
    last_resume_upload: string
  }
}

interface ResumeUploadProps {
    userId: string
    onProfileUpdate?: (profile: ParsedProfile) => void
}

export function ResumeUpload({ userId, onProfileUpdate }: ResumeUploadProps) {
    const [uploading, setUploading] = useState(false)
    const [parsing, setParsing] = useState(false)
    const [parsedProfile, setParsedProfile] = useState<ParsedProfile | null>(null)
    const [resumeText, setResumeText] = useState("")
    const [uploadProgress, setUploadProgress] = useState(0)
    const { toast } = useToast()

    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        const file = acceptedFiles[0]
        if (!file) return

        // Validate file type
        const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']
        if (!allowedTypes.includes(file.type)) {
            toast({
                title: "Invalid file type",
                description: "Please upload a PDF or Word document (.pdf, .docx, .doc)",
                variant: "destructive"
            })
            return
        }

        // Validate file size (10MB max)
        if (file.size > 10 * 1024 * 1024) {
            toast({
                title: "File too large",
                description: "Please upload a file smaller than 10MB",
                variant: "destructive"
            })
            return
        }

        await uploadResume(file)
    }, [userId, toast])

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'application/msword': ['.doc']
        },
        maxFiles: 1
    })

    const uploadResume = async (file: File) => {
        setUploading(true)
        setUploadProgress(0)

        try {
            const formData = new FormData()
            formData.append('file', file)

            // Simulate progress
            const progressInterval = setInterval(() => {
                setUploadProgress(prev => Math.min(prev + 10, 90))
            }, 200)

            const response = await fetch(`${API_BASE_URL}/api/v1/profiles/upload-resume/${userId}`, {
                method: 'POST',
                body: formData
            })

            clearInterval(progressInterval)
            setUploadProgress(100)

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Upload failed')
            }

            const result = await response.json()

            toast({
                title: "Resume uploaded successfully!",
                description: `Parsed ${result.parsing_summary?.name || 'your profile'} with AI insights`,
            })

            // Fetch the full profile
            await fetchUserProfile()

        } catch (error) {
            console.error('Upload error:', error)
            toast({
                title: "Upload failed",
                description: error instanceof Error ? error.message : "Please try again",
                variant: "destructive"
            })
        } finally {
            setUploading(false)
            setUploadProgress(0)
        }
    }

    const parseResumeText = async () => {
        if (!resumeText.trim()) {
            toast({
                title: "No text to parse",
                description: "Please enter your resume text",
                variant: "destructive"
            })
            return
        }

        setParsing(true)

        try {
            const formData = new FormData()
            formData.append('resume_text', resumeText)

            const response = await fetch(`${API_BASE_URL}/api/v1/profiles/parse-text/${userId}`, {
                method: 'POST',
                body: formData
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Parsing failed')
            }

            const result = await response.json()

            toast({
                title: "Resume parsed successfully!",
                description: `AI extracted profile information for ${result.profile_summary?.name || 'you'}`,
            })

            // Fetch the full profile
            await fetchUserProfile()

        } catch (error) {
            console.error('Parse error:', error)
            toast({
                title: "Parsing failed",
                description: error instanceof Error ? error.message : "Please try again",
                variant: "destructive"
            })
        } finally {
            setParsing(false)
        }
    }

    const fetchUserProfile = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/profiles/profile/${userId}`)

            if (response.ok) {
                const profile = await response.json()
                setParsedProfile(profile)
                onProfileUpdate?.(profile)
            }
        } catch (error) {
            console.error('Error fetching profile:', error)
        }
    }

    return (
        <div className="space-y-6">
            <Tabs defaultValue="upload" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="upload">Upload Resume</TabsTrigger>
                    <TabsTrigger value="text">Paste Text</TabsTrigger>
                </TabsList>

                <TabsContent value="upload" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <UploadIcon className="h-5 w-5" />
                                Upload Resume File
                            </CardTitle>
                            <CardDescription>
                                Upload your resume in PDF or Word format. Our AI will extract and analyze your information.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div
                                {...getRootProps()}
                                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50'
                                    }`}
                            >
                                <input {...getInputProps()} />
                                <div className="space-y-4">
                                    <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                                        <FileTextIcon className="h-6 w-6 text-primary" />
                                    </div>
                                    {isDragActive ? (
                                        <p className="text-lg">Drop your resume here...</p>
                                    ) : (
                                        <>
                                            <p className="text-lg font-medium">
                                                Drag & drop your resume here, or click to browse
                                            </p>
                                            <p className="text-sm text-muted-foreground">
                                                Supports PDF, DOCX, and DOC files (max 10MB)
                                            </p>
                                        </>
                                    )}
                                </div>
                            </div>

                            {uploading && (
                                <div className="mt-4 space-y-2">
                                    <div className="flex items-center justify-between text-sm">
                                        <span>Uploading and parsing with AI...</span>
                                        <span>{uploadProgress}%</span>
                                    </div>
                                    <Progress value={uploadProgress} className="w-full" />
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="text" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <BrainIcon className="h-5 w-5" />
                                Paste Resume Text
                            </CardTitle>
                            <CardDescription>
                                Copy and paste your resume text. Our AI will structure and analyze the information.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <Textarea
                                placeholder="Paste your resume text here...

John Smith
Software Engineer
Email: john.smith@email.com
Phone: (555) 123-4567
Location: San Francisco, CA

EXPERIENCE
Software Engineer - Tech Company (2022-2024)
- Built scalable web applications using React and Node.js
- Collaborated with cross-functional teams..."
                                value={resumeText}
                                onChange={(e) => setResumeText(e.target.value)}
                                className="min-h-[200px] resize-none"
                            />
                            <Button
                                onClick={parseResumeText}
                                disabled={parsing || !resumeText.trim()}
                                className="w-full"
                            >
                                {parsing ? (
                                    <>
                                        <BrainIcon className="mr-2 h-4 w-4 animate-spin" />
                                        AI is analyzing your resume...
                                    </>
                                ) : (
                                    <>
                                        <BrainIcon className="mr-2 h-4 w-4" />
                                        Parse with AI
                                    </>
                                )}
                            </Button>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>

            {parsedProfile && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <CheckCircleIcon className="h-5 w-5 text-green-500" />
                            Profile Successfully Extracted
                        </CardTitle>
                        <CardDescription>
                            AI has analyzed your resume and extracted the following information
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <h4 className="font-medium">Personal Information</h4>
                                <div className="text-sm text-muted-foreground space-y-1">
                                    <p><strong>Name:</strong> {parsedProfile.personal_info.full_name || 'Not specified'}</p>
                                    <p><strong>Email:</strong> {parsedProfile.personal_info.email || 'Not specified'}</p>
                                    <p><strong>Location:</strong> {parsedProfile.personal_info.location || 'Not specified'}</p>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <h4 className="font-medium">Professional Summary</h4>
                                <div className="text-sm text-muted-foreground space-y-1">
                                    <p><strong>Experience:</strong> {parsedProfile.professional_summary.years_of_experience} years</p>
                                    <p><strong>Level:</strong> {parsedProfile.professional_summary.career_level}</p>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <h4 className="font-medium">Skills</h4>
                                <div className="text-sm text-muted-foreground">
                                    <p><strong>Languages:</strong> {parsedProfile.skills.programming_languages?.join(', ') || 'None specified'}</p>
                                    <p><strong>Frameworks:</strong> {parsedProfile.skills.frameworks_libraries?.join(', ') || 'None specified'}</p>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <h4 className="font-medium">AI Insights</h4>
                                <div className="text-sm text-muted-foreground">
                                    <p><strong>Strengths:</strong> {parsedProfile.ai_insights.strengths?.join(', ') || 'None identified'}</p>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    )
} 