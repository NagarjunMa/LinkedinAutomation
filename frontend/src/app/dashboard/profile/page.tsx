'use client'

import React, { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { useToast } from "@/components/ui/use-toast"
import {
  User,
  Mail,
  MapPin,
  DollarSign,
  GraduationCap,
  Building,
  Calendar,
  Plus,
  Save,
  Edit2,
  Trash2,
  MessageSquare,
  Briefcase,
  Award,
  TrendingUp,
  FileText,
  Upload,
  Download,
  Eye
} from "lucide-react"
import { profileApi, resumeApi, UserProfile, WorkExperience, Education, ResumeFile } from '@/app/lib/api'
import { useAuth } from '@/contexts/auth-context'

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editingSection, setEditingSection] = useState<string | null>(null)
  const [workExperiences, setWorkExperiences] = useState<WorkExperience[]>([])
  const [educationHistory, setEducationHistory] = useState<Education[]>([])
  const [referralTemplate, setReferralTemplate] = useState('')
  const [resumes, setResumes] = useState<ResumeFile[]>([])
  const [uploadingResume, setUploadingResume] = useState(false)
  const { user } = useAuth()
  const { toast } = useToast()

  useEffect(() => {
    if (user) {
      fetchProfile()
      fetchResumes()
    }
  }, [user])

  const fetchProfile = async () => {
    try {
      setLoading(true)
      // Debug log to see what user object contains
      console.log('User object:', user)
      console.log('User ID:', user?.id)

      const userId = user?.id ? String(user.id) : 'current'
      console.log('Using userId:', userId)

      const data = await profileApi.getProfile(userId)
      setProfile(data)
      setWorkExperiences(data.work_experiences || [])
      setEducationHistory(data.education_history || [])
      setReferralTemplate(data.referral_template || getDefaultReferralTemplate())
    } catch (error) {
      console.error('Error fetching profile:', error)
      toast({
        title: "Error",
        description: "Failed to load profile data.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const getDefaultReferralTemplate = () => {
    return `Hi [REFEREE_NAME],

I hope you're doing well! I'm reaching out because I saw an interesting opportunity at [COMPANY_NAME] for the [JOB_TITLE] position and would love to get your insights.

[PERSONAL_CONNECTION] // This will be replaced with relevant connection info based on shared experiences

I believe my background in [RELEVANT_SKILLS] aligns well with what they're looking for. Would you be open to having a brief chat about the role and the company culture?

I'd be happy to send over my resume if you think it would be helpful.

Thanks for your time, and I'd love to catch up regardless!

Best regards,
[YOUR_NAME]`
  }

  const handleSaveProfile = async (section: string, data: any) => {
    try {
      setSaving(true)
      const userId = user?.id ? String(user.id) : 'current'
      console.log('Saving with userId:', userId, 'Data:', data)
      await profileApi.updateProfile(data, userId)
      await fetchProfile()
      setEditingSection(null)
      toast({
        title: "Success",
        description: `${section} updated successfully!`,
      })
    } catch (error) {
      console.error('Error updating profile:', error)
      toast({
        title: "Error",
        description: `Failed to update ${section.toLowerCase()}.`,
        variant: "destructive",
      })
    } finally {
      setSaving(false)
    }
  }

  const addWorkExperience = () => {
    const newExp: WorkExperience = {
      job_title: '',
      company: '',
      location: '',
      start_date: '',
      end_date: ''
    }
    setWorkExperiences([...workExperiences, newExp])
    setEditingSection('work-experience')
  }

  const addEducation = () => {
    const newEdu: Education = {
      university: '',
      degree: '',
      field_of_study: '',
      location: '',
      start_date: '',
      end_date: ''
    }
    setEducationHistory([...educationHistory, newEdu])
    setEditingSection('education')
  }

  const removeWorkExperience = (index: number) => {
    setWorkExperiences(workExperiences.filter((_, i) => i !== index))
  }

  const removeEducation = (index: number) => {
    setEducationHistory(educationHistory.filter((_, i) => i !== index))
  }

  const fetchResumes = async () => {
    try {
      const data = await resumeApi.listResumes()
      setResumes(data.resumes)
    } catch (error) {
      console.error('Error fetching resumes:', error)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      setUploadingResume(true)
      await resumeApi.uploadResume(file)
      await fetchResumes()
      toast({
        title: "Success",
        description: "Resume uploaded successfully!",
      })
    } catch (error) {
      console.error('Error uploading resume:', error)
      toast({
        title: "Error",
        description: "Failed to upload resume.",
        variant: "destructive",
      })
    } finally {
      setUploadingResume(false)
      // Reset file input
      event.target.value = ''
    }
  }

  const handleDeleteResume = async (resumeId: string) => {
    try {
      await resumeApi.deleteResume(resumeId)
      await fetchResumes()
      toast({
        title: "Success",
        description: "Resume deleted successfully!",
      })
    } catch (error) {
      console.error('Error deleting resume:', error)
      toast({
        title: "Error",
        description: "Failed to delete resume.",
        variant: "destructive",
      })
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-primary-950 p-6">
        <div className="max-w-6xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="h-32 bg-primary-800 rounded-lg"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="h-96 bg-primary-800 rounded-lg"></div>
              <div className="h-96 bg-primary-800 rounded-lg"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-primary-950 p-6">
      <div className="max-w-6xl mx-auto space-y-6">

        {/* Header Section */}
        <div className="bg-gradient-warm/10 backdrop-blur-sm border border-primary-700/50 rounded-lg p-6 glow-orange/20">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-cream-50 mb-2">My Profile</h1>
              <p className="text-cream-300">Manage your professional information and preferences</p>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="secondary" className="bg-accent-500/20 text-accent-400 border-accent-500/30">
                <TrendingUp className="w-4 h-4 mr-1" />
                {profile?.profile_completion || 0}% Complete
              </Badge>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-primary-900/80 border-primary-700/50 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-accent-500/20 rounded-lg">
                  <Briefcase className="w-6 h-6 text-accent-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-cream-50">{profile?.total_applications || 0}</p>
                  <p className="text-sm text-cream-300">Applications</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-primary-900/80 border-primary-700/50 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-accent-500/20 rounded-lg">
                  <FileText className="w-6 h-6 text-accent-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-cream-50">{resumes.length}</p>
                  <p className="text-sm text-cream-300">Resumes</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-primary-900/80 border-primary-700/50 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-accent-500/20 rounded-lg">
                  <Award className="w-6 h-6 text-accent-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-cream-50">{workExperiences.length}</p>
                  <p className="text-sm text-cream-300">Experiences</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Personal Information */}
          <Card className="bg-primary-900/80 border-primary-700/50 backdrop-blur-sm">
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <User className="w-5 h-5 text-accent-400" />
                  <CardTitle className="text-cream-50">Personal Information</CardTitle>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setEditingSection(editingSection === 'personal' ? null : 'personal')}
                  className="text-accent-400 hover:text-accent-300 hover:bg-accent-500/10"
                >
                  <Edit2 className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {editingSection === 'personal' ? (
                <PersonalInfoForm
                  profile={profile}
                  onSave={(data) => handleSaveProfile('Personal Information', data)}
                  onCancel={() => setEditingSection(null)}
                  saving={saving}
                />
              ) : (
                <PersonalInfoDisplay profile={profile} />
              )}
            </CardContent>
          </Card>

          {/* Job Preferences */}
          <Card className="bg-primary-900/80 border-primary-700/50 backdrop-blur-sm">
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Briefcase className="w-5 h-5 text-accent-400" />
                  <CardTitle className="text-cream-50">Job Preferences</CardTitle>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setEditingSection(editingSection === 'preferences' ? null : 'preferences')}
                  className="text-accent-400 hover:text-accent-300 hover:bg-accent-500/10"
                >
                  <Edit2 className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {editingSection === 'preferences' ? (
                <JobPreferencesForm
                  profile={profile}
                  onSave={(data) => handleSaveProfile('Job Preferences', data)}
                  onCancel={() => setEditingSection(null)}
                  saving={saving}
                />
              ) : (
                <JobPreferencesDisplay profile={profile} />
              )}
            </CardContent>
          </Card>
        </div>

        {/* Referral Template */}
        <Card className="bg-primary-900/80 border-primary-700/50 backdrop-blur-sm">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <MessageSquare className="w-5 h-5 text-accent-400" />
                <CardTitle className="text-cream-50">Referral Email Template</CardTitle>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setEditingSection(editingSection === 'referral' ? null : 'referral')}
                className="text-accent-400 hover:text-accent-300 hover:bg-accent-500/10"
              >
                <Edit2 className="w-4 h-4" />
              </Button>
            </div>
            <CardDescription className="text-cream-400">
              Customize your referral email template. Use placeholders like [REFEREE_NAME], [COMPANY_NAME], [JOB_TITLE], and [YOUR_NAME] for personalization.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {editingSection === 'referral' ? (
              <ReferralTemplateForm
                template={referralTemplate}
                setTemplate={setReferralTemplate}
                onSave={() => handleSaveProfile('Referral Template', { referral_template: referralTemplate })}
                onCancel={() => setEditingSection(null)}
                saving={saving}
              />
            ) : (
              <div className="bg-primary-800/50 border border-primary-600/50 rounded-lg p-4">
                <p className="text-cream-300 text-center py-4">
                  Click the edit button to customize your referral email template
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Work Experience */}
        <Card className="bg-primary-900/80 border-primary-700/50 backdrop-blur-sm">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Building className="w-5 h-5 text-accent-400" />
                <CardTitle className="text-cream-50">Work Experience</CardTitle>
              </div>
              <div className="flex space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setEditingSection(editingSection === 'work-experience' ? null : 'work-experience')}
                  className="text-accent-400 hover:text-accent-300 hover:bg-accent-500/10"
                >
                  <Edit2 className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={addWorkExperience}
                  className="text-accent-400 hover:text-accent-300 hover:bg-accent-500/10"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </div>
            <CardDescription className="text-cream-400">
              Add your employment history to help with resume evaluation and referral matching.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <WorkExperienceSection
              experiences={workExperiences}
              setExperiences={setWorkExperiences}
              editing={editingSection === 'work-experience'}
              onSave={() => handleSaveProfile('Work Experience', { work_experiences: workExperiences })}
              onCancel={() => setEditingSection(null)}
              onRemove={removeWorkExperience}
              saving={saving}
            />
          </CardContent>
        </Card>

        {/* Education History */}
        <Card className="bg-primary-900/80 border-primary-700/50 backdrop-blur-sm">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <GraduationCap className="w-5 h-5 text-accent-400" />
                <CardTitle className="text-cream-50">Education</CardTitle>
              </div>
              <div className="flex space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setEditingSection(editingSection === 'education' ? null : 'education')}
                  className="text-accent-400 hover:text-accent-300 hover:bg-accent-500/10"
                >
                  <Edit2 className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={addEducation}
                  className="text-accent-400 hover:text-accent-300 hover:bg-accent-500/10"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </div>
            <CardDescription className="text-cream-400">
              Add your educational background for better resume analysis and alumni network matching.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <EducationSection
              education={educationHistory}
              setEducation={setEducationHistory}
              editing={editingSection === 'education'}
              onSave={() => handleSaveProfile('Education', { education_history: educationHistory })}
              onCancel={() => setEditingSection(null)}
              onRemove={removeEducation}
              saving={saving}
            />
          </CardContent>
        </Card>

        {/* Resume Management */}
        <Card className="bg-primary-900/80 border-primary-700/50 backdrop-blur-sm">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FileText className="w-5 h-5 text-accent-400" />
                <CardTitle className="text-cream-50">Resume Management</CardTitle>
              </div>
              <div className="flex space-x-2">
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="resume-upload"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => document.getElementById('resume-upload')?.click()}
                  disabled={uploadingResume}
                  className="text-accent-400 hover:text-accent-300 hover:bg-accent-500/10"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  {uploadingResume ? 'Uploading...' : 'Upload'}
                </Button>
              </div>
            </div>
            <CardDescription className="text-cream-400">
              Upload and manage your resumes for evaluation and analysis.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResumeManagementSection
              resumes={resumes}
              onDelete={handleDeleteResume}
              uploading={uploadingResume}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}


// Personal Info Components
function PersonalInfoDisplay({ profile }: { profile: UserProfile | null }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <User className="w-4 h-4 text-cream-400" />
        <span className="text-cream-200">{profile?.full_name || 'Not set'}</span>
      </div>
      <div className="flex items-center space-x-2">
        <Mail className="w-4 h-4 text-cream-400" />
        <span className="text-cream-200">{profile?.email || 'Not set'}</span>
      </div>
      <div className="flex items-center space-x-2">
        <MapPin className="w-4 h-4 text-cream-400" />
        <span className="text-cream-200">{profile?.location || 'Not set'}</span>
      </div>
      <div className="flex items-center space-x-2">
        <Briefcase className="w-4 h-4 text-cream-400" />
        <span className="text-cream-200">{profile?.years_of_experience ? `${profile.years_of_experience} years experience` : 'Not set'}</span>
      </div>
      {profile?.professional_summary && (
        <div className="mt-3 p-3 bg-primary-800/50 rounded-lg">
          <p className="text-cream-200 text-sm">{profile.professional_summary}</p>
        </div>
      )}
    </div>
  )
}

function PersonalInfoForm({ profile, onSave, onCancel, saving }: {
  profile: UserProfile | null;
  onSave: (data: any) => void;
  onCancel: () => void;
  saving: boolean;
}) {
  const [formData, setFormData] = useState({
    full_name: profile?.full_name || '',
    email: profile?.email || '',
    phone: profile?.phone || '',
    location: profile?.location || '',
    years_of_experience: profile?.years_of_experience || 0,
    professional_summary: profile?.professional_summary || ''
  })

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label className="text-cream-200">Full Name</Label>
          <Input
            value={formData.full_name}
            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            className="bg-primary-800/50 border-primary-600 text-cream-50"
          />
        </div>
        <div>
          <Label className="text-cream-200">Email</Label>
          <Input
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="bg-primary-800/50 border-primary-600 text-cream-50"
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label className="text-cream-200">Phone</Label>
          <Input
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            className="bg-primary-800/50 border-primary-600 text-cream-50"
            placeholder="+1 (555) 123-4567"
          />
        </div>
        <div>
          <Label className="text-cream-200">Location</Label>
          <Input
            value={formData.location}
            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            className="bg-primary-800/50 border-primary-600 text-cream-50"
            placeholder="San Francisco, CA"
          />
        </div>
      </div>
      <div>
        <Label className="text-cream-200">Years of Experience</Label>
        <Input
          type="number"
          step="0.5"
          value={formData.years_of_experience === 0 ? '' : formData.years_of_experience}
          onChange={(e) => setFormData({ ...formData, years_of_experience: parseFloat(e.target.value) || 0 })}
          className="bg-primary-800/50 border-primary-600 text-cream-50"
          placeholder="2.5"
        />
      </div>
      <div>
        <Label className="text-cream-200">Professional Summary</Label>
        <Textarea
          value={formData.professional_summary}
          onChange={(e) => setFormData({ ...formData, professional_summary: e.target.value })}
          className="bg-primary-800/50 border-primary-600 text-cream-50"
          rows={4}
          placeholder="Brief description of your background and goals..."
        />
      </div>
      <div className="flex space-x-2">
        <Button
          onClick={() => onSave(formData)}
          disabled={saving}
          className="bg-gradient-warm hover:bg-gradient-warm/90"
        >
          <Save className="w-4 h-4 mr-2" />
          {saving ? 'Saving...' : 'Save'}
        </Button>
        <Button variant="ghost" onClick={onCancel} className="text-cream-300 hover:text-cream-50">
          Cancel
        </Button>
      </div>
    </div>
  )
}


function JobPreferencesDisplay({ profile }: { profile: UserProfile | null }) {
  return (
    <div className="space-y-3">
      <div>
        <Label className="text-cream-400">Desired Job Roles</Label>
        <div className="flex flex-wrap gap-2 mt-1">
          {profile?.desired_roles?.map((title, index) => (
            <Badge key={index} variant="secondary" className="bg-accent-500/20 text-accent-400">
              {title}
            </Badge>
          )) || <span className="text-cream-300">Not set</span>}
        </div>
      </div>
      <div>
        <Label className="text-cream-400">Preferred Locations</Label>
        <div className="flex flex-wrap gap-2 mt-1">
          {profile?.preferred_locations?.map((location, index) => (
            <Badge key={index} variant="secondary" className="bg-accent-500/20 text-accent-400">
              <MapPin className="w-3 h-3 mr-1" />
              {location}
            </Badge>
          )) || <span className="text-cream-300">Not set</span>}
        </div>
      </div>
      <div className="flex items-center space-x-2">
        <DollarSign className="w-4 h-4 text-cream-400" />
        <span className="text-cream-200">
          Min Salary: ${profile?.salary_range_min?.toLocaleString() || 'Not set'}
        </span>
      </div>
      <div className="flex items-center space-x-2">
        <DollarSign className="w-4 h-4 text-cream-400" />
        <span className="text-cream-200">
          Max Salary: ${profile?.salary_range_max?.toLocaleString() || 'Not set'}
        </span>
      </div>
      <div className="flex items-center space-x-2">
        <TrendingUp className="w-4 h-4 text-cream-400" />
        <span className="text-cream-200">
          Experience: {profile?.career_level || 'Not set'}
        </span>
      </div>
    </div>
  )
}


function JobPreferencesForm({ profile, onSave, onCancel, saving }: {
  profile: UserProfile | null;
  onSave: (data: any) => void;
  onCancel: () => void;
  saving: boolean;
}) {
  const [formData, setFormData] = useState({
    desired_roles: profile?.desired_roles || [],
    preferred_locations: profile?.preferred_locations || [],
    salary_range_min: profile?.salary_range_min || 0,
    salary_range_max: profile?.salary_range_max || 0,
    career_level: profile?.career_level || ''
  })

  return (
    <div className="space-y-4">
      <div>
        <Label className="text-cream-200">Desired Job Roles (comma-separated)</Label>
        <Input
          value={formData.desired_roles.join(', ')}
          onChange={(e) => setFormData({ ...formData, desired_roles: e.target.value.split(',').map(s => s.trim()) })}
          className="bg-primary-800/50 border-primary-600 text-cream-50"
          placeholder="Software Engineer, Frontend Developer"
        />
      </div>
      <div>
        <Label className="text-cream-200">Preferred Locations (comma-separated)</Label>
        <Input
          value={formData.preferred_locations.join(', ')}
          onChange={(e) => setFormData({ ...formData, preferred_locations: e.target.value.split(',').map(s => s.trim()) })}
          className="bg-primary-800/50 border-primary-600 text-cream-50"
          placeholder="Boston, Remote, San Francisco"
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label className="text-cream-200">Minimum Salary</Label>
          <Input
            type="number"
            value={formData.salary_range_min === 0 ? '' : formData.salary_range_min}
            onChange={(e) => setFormData({ ...formData, salary_range_min: parseInt(e.target.value) || 0 })}
            className="bg-primary-800/50 border-primary-600 text-cream-50"
            placeholder="80000"
          />
        </div>
        <div>
          <Label className="text-cream-200">Maximum Salary</Label>
          <Input
            type="number"
            value={formData.salary_range_max === 0 ? '' : formData.salary_range_max}
            onChange={(e) => setFormData({ ...formData, salary_range_max: parseInt(e.target.value) || 0 })}
            className="bg-primary-800/50 border-primary-600 text-cream-50"
            placeholder="120000"
          />
        </div>
      </div>
      <div>
        <Label className="text-cream-200">Career Level</Label>
        <select
          value={formData.career_level}
          onChange={(e) => setFormData({ ...formData, career_level: e.target.value })}
          className="w-full p-2 bg-primary-800/50 border border-primary-600 text-cream-50 rounded-md"
        >
          <option value="">Select career level</option>
          <option value="entry">Entry Level</option>
          <option value="mid">Mid Level</option>
          <option value="senior">Senior Level</option>
          <option value="lead">Lead/Principal</option>
        </select>
      </div>
      <div className="flex space-x-2">
        <Button
          onClick={() => onSave(formData)}
          disabled={saving}
          className="bg-gradient-warm hover:bg-gradient-warm/90"
        >
          <Save className="w-4 h-4 mr-2" />
          {saving ? 'Saving...' : 'Save'}
        </Button>
        <Button variant="ghost" onClick={onCancel} className="text-cream-300 hover:text-cream-50">
          Cancel
        </Button>
      </div>
    </div>
  )
}


function ReferralTemplateForm({ template, setTemplate, onSave, onCancel, saving }: {
  template: string;
  setTemplate: (template: string) => void;
  onSave: () => void;
  onCancel: () => void;
  saving: boolean;
}) {
  return (
    <div className="space-y-4">
      <Textarea
        value={template}
        onChange={(e) => setTemplate(e.target.value)}
        className="bg-primary-800/50 border-primary-600 text-cream-50 font-mono"
        rows={15}
        placeholder="Enter your referral email template..."
      />
      <div className="flex space-x-2">
        <Button
          onClick={onSave}
          disabled={saving}
          className="bg-gradient-warm hover:bg-gradient-warm/90"
        >
          <Save className="w-4 h-4 mr-2" />
          {saving ? 'Saving...' : 'Save Template'}
        </Button>
        <Button variant="ghost" onClick={onCancel} className="text-cream-300 hover:text-cream-50">
          Cancel
        </Button>
      </div>
    </div>
  )
}


function WorkExperienceSection({ experiences, setExperiences, editing, onSave, onCancel, onRemove, saving }: {
  experiences: WorkExperience[];
  setExperiences: (exp: WorkExperience[]) => void;
  editing: boolean;
  onSave: () => void;
  onCancel: () => void;
  onRemove: (index: number) => void;
  saving: boolean;
}) {
  const updateExperience = (index: number, field: keyof WorkExperience, value: string) => {
    const updated = [...experiences]
    updated[index] = { ...updated[index], [field]: value }
    setExperiences(updated)
  }

  if (!editing) {
    return (
      <div className="space-y-4">
        {experiences.map((exp, index) => (
          <div key={index} className="bg-primary-800/50 border border-primary-600/50 rounded-lg p-4">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h4 className="text-cream-50 font-semibold">{exp.job_title}</h4>
                <p className="text-accent-400">{exp.company}</p>
                <p className="text-cream-300 text-sm">{exp.location}</p>
                <p className="text-cream-400 text-xs mt-1">
                  {exp.start_date} - {exp.end_date || 'Present'}
                </p>
              </div>
            </div>
          </div>
        ))}
        {experiences.length === 0 && (
          <p className="text-cream-400 text-center py-8">No work experience added yet</p>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {experiences.map((exp, index) => (
        <div key={index} className="bg-primary-800/50 border border-primary-600/50 rounded-lg p-4 space-y-3">
          <div className="flex justify-between items-center">
            <h4 className="text-cream-50 font-semibold">Experience {index + 1}</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onRemove(index)}
              className="text-red-400 hover:text-red-300"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <Label className="text-cream-200">Job Title</Label>
              <Input
                value={exp.job_title}
                onChange={(e) => updateExperience(index, 'job_title', e.target.value)}
                className="bg-primary-700/50 border-primary-600 text-cream-50"
              />
            </div>
            <div>
              <Label className="text-cream-200">Company</Label>
              <Input
                value={exp.company}
                onChange={(e) => updateExperience(index, 'company', e.target.value)}
                className="bg-primary-700/50 border-primary-600 text-cream-50"
              />
            </div>
            <div>
              <Label className="text-cream-200">Location</Label>
              <Input
                value={exp.location}
                onChange={(e) => updateExperience(index, 'location', e.target.value)}
                className="bg-primary-700/50 border-primary-600 text-cream-50"
              />
            </div>
            <div>
              <Label className="text-cream-200">Start Date</Label>
              <Input
                type="date"
                value={exp.start_date}
                onChange={(e) => updateExperience(index, 'start_date', e.target.value)}
                className="bg-primary-700/50 border-primary-600 text-cream-50"
              />
            </div>
            <div>
              <Label className="text-cream-200">End Date (leave empty if current)</Label>
              <Input
                type="date"
                value={exp.end_date || ''}
                onChange={(e) => updateExperience(index, 'end_date', e.target.value)}
                className="bg-primary-700/50 border-primary-600 text-cream-50"
              />
            </div>
          </div>
        </div>
      ))}

      <div className="flex space-x-2">
        <Button
          onClick={onSave}
          disabled={saving}
          className="bg-gradient-warm hover:bg-gradient-warm/90"
        >
          <Save className="w-4 h-4 mr-2" />
          {saving ? 'Saving...' : 'Save Experience'}
        </Button>
        <Button variant="ghost" onClick={onCancel} className="text-cream-300 hover:text-cream-50">
          Cancel
        </Button>
      </div>
    </div>
  )
}


function EducationSection({ education, setEducation, editing, onSave, onCancel, onRemove, saving }: {
  education: Education[];
  setEducation: (edu: Education[]) => void;
  editing: boolean;
  onSave: () => void;
  onCancel: () => void;
  onRemove: (index: number) => void;
  saving: boolean;
}) {
  const updateEducation = (index: number, field: keyof Education, value: string) => {
    const updated = [...education]
    updated[index] = { ...updated[index], [field]: value }
    setEducation(updated)
  }

  if (!editing) {
    return (
      <div className="space-y-4">
        {education.map((edu, index) => (
          <div key={index} className="bg-primary-800/50 border border-primary-600/50 rounded-lg p-4">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h4 className="text-cream-50 font-semibold">{edu.degree}</h4>
                <p className="text-accent-400">{edu.university}</p>
                <p className="text-cream-300 text-sm">{edu.field_of_study}</p>
                <p className="text-cream-300 text-sm">{edu.location}</p>
                <p className="text-cream-400 text-xs mt-1">
                  {edu.start_date} - {edu.end_date || 'Present'}
                </p>
              </div>
            </div>
          </div>
        ))}
        {education.length === 0 && (
          <p className="text-cream-400 text-center py-8">No education history added yet</p>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {education.map((edu, index) => (
        <div key={index} className="bg-primary-800/50 border border-primary-600/50 rounded-lg p-4 space-y-3">
          <div className="flex justify-between items-center">
            <h4 className="text-cream-50 font-semibold">Education {index + 1}</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onRemove(index)}
              className="text-red-400 hover:text-red-300"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <Label className="text-cream-200">University</Label>
              <Input
                value={edu.university}
                onChange={(e) => updateEducation(index, 'university', e.target.value)}
                className="bg-primary-700/50 border-primary-600 text-cream-50"
              />
            </div>
            <div>
              <Label className="text-cream-200">Degree</Label>
              <Input
                value={edu.degree}
                onChange={(e) => updateEducation(index, 'degree', e.target.value)}
                className="bg-primary-700/50 border-primary-600 text-cream-50"
              />
            </div>
            <div>
              <Label className="text-cream-200">Field of Study</Label>
              <Input
                value={edu.field_of_study}
                onChange={(e) => updateEducation(index, 'field_of_study', e.target.value)}
                className="bg-primary-700/50 border-primary-600 text-cream-50"
              />
            </div>
            <div>
              <Label className="text-cream-200">Location</Label>
              <Input
                value={edu.location}
                onChange={(e) => updateEducation(index, 'location', e.target.value)}
                className="bg-primary-700/50 border-primary-600 text-cream-50"
              />
            </div>
            <div>
              <Label className="text-cream-200">Start Date</Label>
              <Input
                type="date"
                value={edu.start_date}
                onChange={(e) => updateEducation(index, 'start_date', e.target.value)}
                className="bg-primary-700/50 border-primary-600 text-cream-50"
              />
            </div>
            <div>
              <Label className="text-cream-200">End Date (leave empty if current)</Label>
              <Input
                type="date"
                value={edu.end_date || ''}
                onChange={(e) => updateEducation(index, 'end_date', e.target.value)}
                className="bg-primary-700/50 border-primary-600 text-cream-50"
              />
            </div>
          </div>
        </div>
      ))}

      <div className="flex space-x-2">
        <Button
          onClick={onSave}
          disabled={saving}
          className="bg-gradient-warm hover:bg-gradient-warm/90"
        >
          <Save className="w-4 h-4 mr-2" />
          {saving ? 'Saving...' : 'Save Education'}
        </Button>
        <Button variant="ghost" onClick={onCancel} className="text-cream-300 hover:text-cream-50">
          Cancel
        </Button>
      </div>
    </div>
  )
}

function ResumeManagementSection({ resumes, onDelete, uploading }: {
  resumes: ResumeFile[];
  onDelete: (resumeId: string) => void;
  uploading: boolean;
}) {
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-400'
      case 'pending':
        return 'text-yellow-400'
      case 'processing':
        return 'text-blue-400'
      case 'failed':
        return 'text-red-400'
      default:
        return 'text-cream-300'
    }
  }

  if (uploading && resumes.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-400 mx-auto mb-4"></div>
        <p className="text-cream-300">Uploading resume...</p>
      </div>
    )
  }

  if (resumes.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText className="w-16 h-16 text-cream-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-cream-50 mb-2">No resumes uploaded</h3>
        <p className="text-cream-400 mb-4">Upload your first resume to get started with AI-powered evaluation</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {resumes.map((resume) => (
        <div key={resume.id} className="bg-primary-800/50 border border-primary-600/50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 flex-1">
              <div className="p-2 bg-accent-500/20 rounded-lg">
                <FileText className="w-5 h-5 text-accent-400" />
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="text-cream-50 font-medium truncate">{resume.original_filename}</h4>
                <div className="flex items-center space-x-4 mt-1">
                  <span className="text-cream-300 text-sm">{formatFileSize(resume.file_size)}</span>
                  <span className="text-cream-400 text-xs">
                    {new Date(resume.uploaded_at).toLocaleDateString()}
                  </span>
                  <Badge variant="secondary" className={`${getStatusColor(resume.evaluation_status)} text-xs`}>
                    {resume.evaluation_status}
                  </Badge>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {resume.evaluation_status === 'completed' && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => window.open(`/dashboard/resume-evaluation?resume=${resume.id}`, '_blank')}
                  className="text-accent-400 hover:text-accent-300 hover:bg-accent-500/10"
                >
                  <Eye className="w-4 h-4" />
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onDelete(resume.id)}
                className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      ))}

      {uploading && (
        <div className="bg-primary-800/50 border border-primary-600/50 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-accent-400"></div>
            <span className="text-cream-300">Uploading new resume...</span>
          </div>
        </div>
      )}
    </div>
  )
}