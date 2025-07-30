"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ResumeUpload } from "./resume-upload"
import { AIJobMatches } from "./ai-job-matches"
import { PreferencesForm } from "./preferences-form"

import { UserIcon, BrainIcon, TargetIcon, SettingsIcon } from "lucide-react"

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

interface ProfileTabProps {
    userId: string
}

export function ProfileTab({ userId }: ProfileTabProps) {
    const [currentProfile, setCurrentProfile] = useState<ParsedProfile | null>(null)
    const [activeTab, setActiveTab] = useState("upload")

    const handleProfileUpdate = (profile: ParsedProfile) => {
        setCurrentProfile(profile)
        // Automatically switch to preferences tab after successful profile creation
        setActiveTab("preferences")
    }

    return (
        <div className="space-y-6">
            <div className="space-y-2">
                <h2 className="text-2xl font-bold tracking-tight">AI Profile & Job Matching</h2>
                <p className="text-muted-foreground">
                    Upload your resume, let AI extract your profile, and get personalized job matches with compatibility scores.
                </p>
            </div>

            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
                <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="upload" className="flex items-center gap-2">
                        <UserIcon className="h-4 w-4" />
                        Resume & Profile
                    </TabsTrigger>
                    <TabsTrigger value="preferences" className="flex items-center gap-2">
                        <SettingsIcon className="h-4 w-4" />
                        Job Preferences
                    </TabsTrigger>
                    <TabsTrigger value="matches" className="flex items-center gap-2">
                        <BrainIcon className="h-4 w-4" />
                        AI Job Matches
                    </TabsTrigger>
                    <TabsTrigger value="profile" className="flex items-center gap-2">
                        <TargetIcon className="h-4 w-4" />
                        Profile Details
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="upload" className="space-y-4">
                    <ResumeUpload
                        userId={userId}
                        onProfileUpdate={handleProfileUpdate}
                    />
                </TabsContent>

                <TabsContent value="preferences" className="space-y-4">
                    <PreferencesForm
                        userId={userId}
                        onSave={(preferences) => {
                            // Auto-switch to matches tab after saving preferences
                            setActiveTab("matches")
                        }}
                    />
                </TabsContent>

                <TabsContent value="matches" className="space-y-4">
                    <AIJobMatches
                        userId={userId}
                        minScore={70}
                        limit={20}
                    />
                </TabsContent>

                <TabsContent value="profile" className="space-y-4">
                    {currentProfile ? (
                        <ProfileDetails profile={currentProfile} />
                    ) : (
                        <Card>
                            <CardContent className="p-8 text-center">
                                <UserIcon className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                                <h3 className="text-lg font-medium mb-2">No profile yet</h3>
                                <p className="text-sm text-muted-foreground">
                                    Upload your resume in the "Resume & Profile" tab to see your detailed profile information here.
                                </p>
                            </CardContent>
                        </Card>
                    )}
                </TabsContent>
            </Tabs>
        </div>
    )
}

function ProfileDetails({ profile }: { profile: ParsedProfile }) {
    return (
        <div className="grid gap-6">
            {/* Personal Information */}
            <Card>
                <CardHeader>
                    <CardTitle>Personal Information</CardTitle>
                    <CardDescription>Basic profile details extracted from your resume</CardDescription>
                </CardHeader>
                <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <h4 className="font-medium mb-2">Contact Details</h4>
                        <div className="space-y-1 text-sm">
                            <p><strong>Full Name:</strong> {profile.personal_info.full_name || 'Not specified'}</p>
                            <p><strong>Email:</strong> {profile.personal_info.email || 'Not specified'}</p>
                            <p><strong>Phone:</strong> {profile.personal_info.phone || 'Not specified'}</p>
                            <p><strong>Location:</strong> {profile.personal_info.location || 'Not specified'}</p>
                        </div>
                    </div>
                    <div>
                        <h4 className="font-medium mb-2">Professional Status</h4>
                        <div className="space-y-1 text-sm">
                            <p><strong>Work Authorization:</strong> {profile.personal_info.work_authorization || 'Not specified'}</p>
                            <p><strong>Experience Level:</strong> {profile.professional_summary.career_level}</p>
                            <p><strong>Years of Experience:</strong> {profile.professional_summary.years_of_experience}</p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Skills */}
            <Card>
                <CardHeader>
                    <CardTitle>Skills & Technologies</CardTitle>
                    <CardDescription>Technical and soft skills identified by AI</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div>
                        <h4 className="font-medium mb-2">Programming Languages</h4>
                        <div className="flex flex-wrap gap-2">
                            {profile.skills.programming_languages?.map((skill, index) => (
                                <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-sm">
                                    {skill}
                                </span>
                            )) || <span className="text-sm text-muted-foreground">None specified</span>}
                        </div>
                    </div>
                    <div>
                        <h4 className="font-medium mb-2">Frameworks & Libraries</h4>
                        <div className="flex flex-wrap gap-2">
                            {profile.skills.frameworks_libraries?.map((skill, index) => (
                                <span key={index} className="px-2 py-1 bg-green-100 text-green-800 rounded-md text-sm">
                                    {skill}
                                </span>
                            )) || <span className="text-sm text-muted-foreground">None specified</span>}
                        </div>
                    </div>
                    <div>
                        <h4 className="font-medium mb-2">Tools & Platforms</h4>
                        <div className="flex flex-wrap gap-2">
                            {profile.skills.tools_platforms?.map((skill, index) => (
                                <span key={index} className="px-2 py-1 bg-purple-100 text-purple-800 rounded-md text-sm">
                                    {skill}
                                </span>
                            )) || <span className="text-sm text-muted-foreground">None specified</span>}
                        </div>
                    </div>
                    <div>
                        <h4 className="font-medium mb-2">Soft Skills</h4>
                        <div className="flex flex-wrap gap-2">
                            {profile.skills.soft_skills?.map((skill, index) => (
                                <span key={index} className="px-2 py-1 bg-orange-100 text-orange-800 rounded-md text-sm">
                                    {skill}
                                </span>
                            )) || <span className="text-sm text-muted-foreground">None specified</span>}
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* AI Insights */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <BrainIcon className="h-5 w-5" />
                        AI Insights & Career Advice
                    </CardTitle>
                    <CardDescription>Personalized analysis and recommendations from our AI</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div>
                        <h4 className="font-medium mb-2">Profile Summary</h4>
                        <p className="text-sm text-muted-foreground leading-relaxed">
                            {profile.ai_insights.profile_summary || 'No summary available'}
                        </p>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <h4 className="font-medium mb-2 text-green-700">Strengths</h4>
                            <ul className="text-sm space-y-1">
                                {profile.ai_insights.strengths?.map((strength, index) => (
                                    <li key={index} className="flex items-start gap-2">
                                        <span className="text-green-500 mt-1">•</span>
                                        {strength}
                                    </li>
                                )) || <li className="text-muted-foreground">None identified</li>}
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-medium mb-2 text-orange-700">Areas for Improvement</h4>
                            <ul className="text-sm space-y-1">
                                {profile.ai_insights.improvement_areas?.map((area, index) => (
                                    <li key={index} className="flex items-start gap-2">
                                        <span className="text-orange-500 mt-1">•</span>
                                        {area}
                                    </li>
                                )) || <li className="text-muted-foreground">None identified</li>}
                            </ul>
                        </div>
                    </div>
                    <div>
                        <h4 className="font-medium mb-2">Career Advice</h4>
                        <p className="text-sm text-muted-foreground leading-relaxed">
                            {profile.ai_insights.career_advice || 'No advice available'}
                        </p>
                    </div>
                </CardContent>
            </Card>

            {/* Job Preferences */}
            <Card>
                <CardHeader>
                    <CardTitle>Job Preferences</CardTitle>
                    <CardDescription>Your career preferences identified from your resume</CardDescription>
                </CardHeader>
                <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <h4 className="font-medium mb-2">Desired Roles</h4>
                        <div className="flex flex-wrap gap-2">
                            {profile.preferences.desired_roles?.map((role, index) => (
                                <span key={index} className="px-2 py-1 bg-indigo-100 text-indigo-800 rounded-md text-sm">
                                    {role}
                                </span>
                            )) || <span className="text-sm text-muted-foreground">None specified</span>}
                        </div>
                    </div>
                    <div>
                        <h4 className="font-medium mb-2">Preferred Locations</h4>
                        <div className="flex flex-wrap gap-2">
                            {profile.preferences.preferred_locations?.map((location, index) => (
                                <span key={index} className="px-2 py-1 bg-teal-100 text-teal-800 rounded-md text-sm">
                                    {location}
                                </span>
                            )) || <span className="text-sm text-muted-foreground">None specified</span>}
                        </div>
                    </div>
                    <div>
                        <h4 className="font-medium mb-2">Salary Range</h4>
                        <p className="text-sm">
                            {profile.preferences.salary_range_min || profile.preferences.salary_range_max
                                ? `$${profile.preferences.salary_range_min?.toLocaleString() || '0'} - $${profile.preferences.salary_range_max?.toLocaleString() || 'Not specified'}`
                                : 'Not specified'
                            }
                        </p>
                    </div>
                    <div>
                        <h4 className="font-medium mb-2">Job Types</h4>
                        <div className="flex flex-wrap gap-2">
                            {profile.preferences.job_types?.map((type, index) => (
                                <span key={index} className="px-2 py-1 bg-gray-100 text-gray-800 rounded-md text-sm">
                                    {type}
                                </span>
                            )) || <span className="text-sm text-muted-foreground">None specified</span>}
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
} 