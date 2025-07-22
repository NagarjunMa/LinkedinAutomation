"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/components/ui/use-toast"
import { SettingsIcon, MapPinIcon, DollarSignIcon, BriefcaseIcon, XIcon } from "lucide-react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface UserPreferences {
    // Job Preferences
    desired_roles: string[]
    preferred_locations: string[]
    salary_range_min: number
    salary_range_max: number
    job_types: string[]
    company_size_preference: string[]
    work_authorization: string

    // Additional Details
    availability: string
    notice_period: string
    relocation_willingness: boolean
    remote_work_preference: string

    // Skills & Career
    current_title: string
    career_goals: string
    additional_skills: string[]
    certifications: string[]
}

interface PreferencesFormProps {
    userId: string
    initialData?: Partial<UserPreferences>
    onSave?: (preferences: UserPreferences) => void
}

const JOB_TYPES = ["Full-time", "Part-time", "Contract", "Temporary", "Internship", "Remote", "Hybrid"]
const COMPANY_SIZES = ["Startup (1-50)", "Small (51-200)", "Medium (201-1000)", "Large (1001-5000)", "Enterprise (5000+)"]
const REMOTE_PREFERENCES = ["Fully Remote", "Hybrid", "On-site", "No Preference"]
const AVAILABILITY_OPTIONS = ["Immediate", "2 weeks", "1 month", "2 months", "3+ months"]

export function PreferencesForm({ userId, initialData, onSave }: PreferencesFormProps) {
    const [preferences, setPreferences] = useState<UserPreferences>({
        desired_roles: [],
        preferred_locations: [],
        salary_range_min: 0,
        salary_range_max: 0,
        job_types: [],
        company_size_preference: [],
        work_authorization: "",
        availability: "",
        notice_period: "",
        relocation_willingness: false,
        remote_work_preference: "",
        current_title: "",
        career_goals: "",
        additional_skills: [],
        certifications: [],
        ...initialData
    })

    const [inputValues, setInputValues] = useState({
        roleInput: "",
        locationInput: "",
        skillInput: "",
        certificationInput: ""
    })

    const [saving, setSaving] = useState(false)
    const { toast } = useToast()

    const addToArray = (field: keyof UserPreferences, value: string, inputField: string) => {
        if (value.trim() && !preferences[field].includes(value.trim())) {
            setPreferences(prev => ({
                ...prev,
                [field]: [...(prev[field] as string[]), value.trim()]
            }))
            setInputValues(prev => ({ ...prev, [inputField]: "" }))
        }
    }

    const removeFromArray = (field: keyof UserPreferences, value: string) => {
        setPreferences(prev => ({
            ...prev,
            [field]: (prev[field] as string[]).filter(item => item !== value)
        }))
    }

    const handleSelectChange = (field: keyof UserPreferences, value: string | string[]) => {
        setPreferences(prev => ({ ...prev, [field]: value }))
    }

    const handleSave = async () => {
        setSaving(true)
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/profiles/preferences/${userId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(preferences)
            })

            if (!response.ok) {
                throw new Error('Failed to save preferences')
            }

            toast({
                title: "Preferences saved!",
                description: "Your job preferences have been updated successfully.",
            })

            onSave?.(preferences)

        } catch (error) {
            console.error('Error saving preferences:', error)
            toast({
                title: "Save failed",
                description: "Please try again or contact support.",
                variant: "destructive"
            })
        } finally {
            setSaving(false)
        }
    }

    return (
        <div className="space-y-6">
            <div className="space-y-2">
                <h3 className="text-xl font-semibold flex items-center gap-2">
                    <SettingsIcon className="h-5 w-5" />
                    Job Preferences & Details
                </h3>
                <p className="text-muted-foreground">
                    Complete your profile with job preferences to get better AI job matches
                </p>
            </div>

            <div className="grid gap-6">
                {/* Job Roles */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <BriefcaseIcon className="h-4 w-4" />
                            Desired Job Roles
                        </CardTitle>
                        <CardDescription>What roles are you looking for?</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex gap-2">
                            <Input
                                placeholder="e.g., Software Engineer, Full Stack Developer"
                                value={inputValues.roleInput}
                                onChange={(e) => setInputValues(prev => ({ ...prev, roleInput: e.target.value }))}
                                onKeyPress={(e) => {
                                    if (e.key === 'Enter') {
                                        addToArray('desired_roles', inputValues.roleInput, 'roleInput')
                                    }
                                }}
                            />
                            <Button
                                type="button"
                                onClick={() => addToArray('desired_roles', inputValues.roleInput, 'roleInput')}
                            >
                                Add
                            </Button>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {preferences.desired_roles.map((role) => (
                                <Badge key={role} variant="secondary" className="flex items-center gap-1">
                                    {role}
                                    <XIcon
                                        className="h-3 w-3 cursor-pointer"
                                        onClick={() => removeFromArray('desired_roles', role)}
                                    />
                                </Badge>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Location & Salary */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <MapPinIcon className="h-4 w-4" />
                                Preferred Locations
                            </CardTitle>
                            <CardDescription>Where would you like to work?</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex gap-2">
                                <Input
                                    placeholder="e.g., San Francisco, Remote, New York"
                                    value={inputValues.locationInput}
                                    onChange={(e) => setInputValues(prev => ({ ...prev, locationInput: e.target.value }))}
                                    onKeyPress={(e) => {
                                        if (e.key === 'Enter') {
                                            addToArray('preferred_locations', inputValues.locationInput, 'locationInput')
                                        }
                                    }}
                                />
                                <Button
                                    type="button"
                                    onClick={() => addToArray('preferred_locations', inputValues.locationInput, 'locationInput')}
                                >
                                    Add
                                </Button>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {preferences.preferred_locations.map((location) => (
                                    <Badge key={location} variant="secondary" className="flex items-center gap-1">
                                        {location}
                                        <XIcon
                                            className="h-3 w-3 cursor-pointer"
                                            onClick={() => removeFromArray('preferred_locations', location)}
                                        />
                                    </Badge>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <DollarSignIcon className="h-4 w-4" />
                                Salary Range
                            </CardTitle>
                            <CardDescription>Your expected salary range (USD)</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <Label htmlFor="min-salary">Minimum</Label>
                                    <Input
                                        id="min-salary"
                                        type="number"
                                        placeholder="80000"
                                        value={preferences.salary_range_min || ""}
                                        onChange={(e) => setPreferences(prev => ({
                                            ...prev,
                                            salary_range_min: parseInt(e.target.value) || 0
                                        }))}
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="max-salary">Maximum</Label>
                                    <Input
                                        id="max-salary"
                                        type="number"
                                        placeholder="120000"
                                        value={preferences.salary_range_max || ""}
                                        onChange={(e) => setPreferences(prev => ({
                                            ...prev,
                                            salary_range_max: parseInt(e.target.value) || 0
                                        }))}
                                    />
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Work Preferences */}
                <Card>
                    <CardHeader>
                        <CardTitle>Work Preferences</CardTitle>
                        <CardDescription>Your employment and work style preferences</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <Label>Job Types</Label>
                                <div className="flex flex-wrap gap-2 mt-2">
                                    {JOB_TYPES.map((type) => (
                                        <Badge
                                            key={type}
                                            variant={preferences.job_types.includes(type) ? "default" : "outline"}
                                            className="cursor-pointer"
                                            onClick={() => {
                                                const newTypes = preferences.job_types.includes(type)
                                                    ? preferences.job_types.filter(t => t !== type)
                                                    : [...preferences.job_types, type]
                                                handleSelectChange('job_types', newTypes)
                                            }}
                                        >
                                            {type}
                                        </Badge>
                                    ))}
                                </div>
                            </div>

                            <div>
                                <Label>Company Size</Label>
                                <div className="flex flex-wrap gap-2 mt-2">
                                    {COMPANY_SIZES.map((size) => (
                                        <Badge
                                            key={size}
                                            variant={preferences.company_size_preference.includes(size) ? "default" : "outline"}
                                            className="cursor-pointer"
                                            onClick={() => {
                                                const newSizes = preferences.company_size_preference.includes(size)
                                                    ? preferences.company_size_preference.filter(s => s !== size)
                                                    : [...preferences.company_size_preference, size]
                                                handleSelectChange('company_size_preference', newSizes)
                                            }}
                                        >
                                            {size}
                                        </Badge>
                                    ))}
                                </div>
                            </div>

                            <div>
                                <Label htmlFor="remote-preference">Remote Work Preference</Label>
                                <Select
                                    value={preferences.remote_work_preference}
                                    onValueChange={(value) => handleSelectChange('remote_work_preference', value)}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select preference" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {REMOTE_PREFERENCES.map((pref) => (
                                            <SelectItem key={pref} value={pref}>{pref}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            <div>
                                <Label htmlFor="availability">Availability</Label>
                                <Select
                                    value={preferences.availability}
                                    onValueChange={(value) => handleSelectChange('availability', value)}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="When can you start?" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {AVAILABILITY_OPTIONS.map((option) => (
                                            <SelectItem key={option} value={option}>{option}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Additional Information */}
                <Card>
                    <CardHeader>
                        <CardTitle>Additional Information</CardTitle>
                        <CardDescription>Help us understand your background better</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <Label htmlFor="current-title">Current Title</Label>
                            <Input
                                id="current-title"
                                placeholder="e.g., Senior Software Engineer"
                                value={preferences.current_title}
                                onChange={(e) => setPreferences(prev => ({ ...prev, current_title: e.target.value }))}
                            />
                        </div>

                        <div>
                            <Label htmlFor="career-goals">Career Goals</Label>
                            <Textarea
                                id="career-goals"
                                placeholder="Describe your career aspirations and what you're looking for in your next role..."
                                value={preferences.career_goals}
                                onChange={(e) => setPreferences(prev => ({ ...prev, career_goals: e.target.value }))}
                                className="min-h-[100px]"
                            />
                        </div>

                        <div>
                            <Label>Additional Skills</Label>
                            <div className="flex gap-2">
                                <Input
                                    placeholder="e.g., Project Management, DevOps"
                                    value={inputValues.skillInput}
                                    onChange={(e) => setInputValues(prev => ({ ...prev, skillInput: e.target.value }))}
                                    onKeyPress={(e) => {
                                        if (e.key === 'Enter') {
                                            addToArray('additional_skills', inputValues.skillInput, 'skillInput')
                                        }
                                    }}
                                />
                                <Button
                                    type="button"
                                    onClick={() => addToArray('additional_skills', inputValues.skillInput, 'skillInput')}
                                >
                                    Add
                                </Button>
                            </div>
                            <div className="flex flex-wrap gap-2 mt-2">
                                {preferences.additional_skills.map((skill) => (
                                    <Badge key={skill} variant="secondary" className="flex items-center gap-1">
                                        {skill}
                                        <XIcon
                                            className="h-3 w-3 cursor-pointer"
                                            onClick={() => removeFromArray('additional_skills', skill)}
                                        />
                                    </Badge>
                                ))}
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Save Button */}
                <Card>
                    <CardContent className="pt-6">
                        <Button onClick={handleSave} disabled={saving} className="w-full">
                            {saving ? "Saving..." : "Save Preferences"}
                        </Button>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
} 