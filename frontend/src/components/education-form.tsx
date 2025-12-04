"use client"

import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Plus, Trash2, GraduationCap, Award, Calendar } from "lucide-react"
import { SkillsAutocomplete } from "@/components/skills-autocomplete"
import { FormError } from "@/components/ui/form-error"
import { useFormValidation } from "@/hooks/use-form-validation"
import { validateEducation, validateCertification, type Education, type Certification } from "@/lib/validation/profile-schemas"

interface EducationFormProps {
  value: {
    education_records: Education[]
    certifications: Certification[]
  }
  onChange: (data: { education_records: Education[], certifications: Certification[] }) => void
  className?: string
}

export function EducationForm({ value, onChange, className }: EducationFormProps) {
  const [activeTab, setActiveTab] = useState<'education' | 'certifications'>('education')

  // Education Record Form
  const educationForm = useFormValidation({
    initialValues: {
      institution_name: "",
      degree_type: "",
      field_of_study: "",
      major: "",
      gpa: undefined as number | undefined,
      start_date: "",
      end_date: "",
      graduation_date: "",
      is_current: false,
      coursework: [] as string[],
      technical_skills_gained: [] as string[],
    },
    validationSchema: (data: Record<string, unknown>) => validateEducation(data),
    onSubmit: (data) => {
      const newEducation: Education = {
        institution_name: data.institution_name as string,
        degree_type: data.degree_type as string,
        field_of_study: data.field_of_study as string,
        major: data.major as string,
        gpa: data.gpa as number,
        start_date: new Date(data.start_date as string),
        end_date: data.end_date ? new Date(data.end_date as string) : undefined,
        graduation_date: data.graduation_date ? new Date(data.graduation_date as string) : undefined,
        is_current: data.is_current as boolean,
        coursework: data.coursework as string[],
        technical_skills_gained: data.technical_skills_gained as string[],
      }
      onChange({
        education_records: [...value.education_records, newEducation],
        certifications: value.certifications
      })
      educationForm.reset()
    }
  })

  // Certification Form
  const certificationForm = useFormValidation({
    initialValues: {
      name: "",
      issuing_organization: "",
      issue_date: "",
      expiration_date: "",
      never_expires: false,
      skills_validated: [] as string[],
    },
    validationSchema: (data: Record<string, unknown>) => validateCertification(data),
    onSubmit: (data) => {
      const newCertification: Certification = {
        name: data.name as string,
        issuing_organization: data.issuing_organization as string,
        issue_date: new Date(data.issue_date as string),
        expiration_date: data.expiration_date ? new Date(data.expiration_date as string) : undefined,
        never_expires: data.never_expires as boolean,
        skills_validated: data.skills_validated as string[],
      }
      onChange({
        education_records: value.education_records,
        certifications: [...value.certifications, newCertification]
      })
      certificationForm.reset()
    }
  })

  const removeEducationRecord = (index: number) => {
    const updatedRecords = value.education_records.filter((_, i) => i !== index)
    onChange({
      education_records: updatedRecords,
      certifications: value.certifications
    })
  }

  const removeCertification = (index: number) => {
    const updatedCertifications = value.certifications.filter((_, i) => i !== index)
    onChange({
      education_records: value.education_records,
      certifications: updatedCertifications
    })
  }

  const degreeTypes = [
    "Associate's",
    "Bachelor's",
    "Master's",
    "Doctoral",
    "PhD",
    "Certificate",
    "Diploma",
    "Bootcamp",
    "Professional Certificate"
  ]

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
        <button
          onClick={() => setActiveTab('education')}
          className={`flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-md transition-colors ${
            activeTab === 'education'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-blue-600'
          }`}
        >
          <GraduationCap className="h-4 w-4" />
          <span>Education</span>
          {value.education_records.length > 0 && (
            <span className="bg-blue-100 text-blue-600 text-xs px-2 py-1 rounded-full">
              {value.education_records.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('certifications')}
          className={`flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-md transition-colors ${
            activeTab === 'certifications'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-blue-600'
          }`}
        >
          <Award className="h-4 w-4" />
          <span>Certifications</span>
          {value.certifications.length > 0 && (
            <span className="bg-blue-100 text-blue-600 text-xs px-2 py-1 rounded-full">
              {value.certifications.length}
            </span>
          )}
        </button>
      </div>

      {/* Education Tab */}
      {activeTab === 'education' && (
        <div className="space-y-6">
          {/* Existing Education Records */}
          {value.education_records.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Your Education</h3>
              {value.education_records.map((education, index) => (
                <Card key={index} className="border-l-4 border-blue-500">
                  <CardContent className="pt-6">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 className="font-semibold text-lg">{education.degree_type} in {education.field_of_study}</h4>
                        <p className="text-gray-600">{education.institution_name}</p>
                        {education.major && <p className="text-sm text-gray-500">Major: {education.major}</p>}
                        {education.gpa && <p className="text-sm text-gray-500">GPA: {education.gpa}</p>}
                        <div className="flex items-center space-x-4 text-sm text-gray-500 mt-2">
                          <div className="flex items-center space-x-1">
                            <Calendar className="h-4 w-4" />
                            <span>
                              {education.start_date.getFullYear()} - {
                                education.is_current ? 'Present' :
                                education.graduation_date?.getFullYear() ||
                                education.end_date?.getFullYear() || 'Present'
                              }
                            </span>
                          </div>
                        </div>
                        {education.technical_skills_gained && education.technical_skills_gained.length > 0 && (
                          <div className="mt-3">
                            <p className="text-sm font-medium text-gray-700 mb-1">Skills Gained:</p>
                            <div className="flex flex-wrap gap-1">
                              {education.technical_skills_gained.map((skill, skillIndex) => (
                                <span
                                  key={skillIndex}
                                  className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
                                >
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeEducationRecord(index)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Add New Education Form */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Plus className="h-5 w-5" />
                <span>Add Education</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={educationForm.handleSubmit} className="space-y-4">
                {/* Institution and Degree */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="institution_name">Institution Name *</Label>
                    <Input
                      id="institution_name"
                      value={educationForm.values.institution_name as string}
                      onChange={(e) => educationForm.setValue("institution_name", e.target.value)}
                      onBlur={() => educationForm.handleBlur("institution_name")}
                      placeholder="Harvard University"
                      className={educationForm.errors.institution_name ? "border-red-500" : ""}
                    />
                    <FormError message={educationForm.errors.institution_name} />
                  </div>

                  <div>
                    <Label htmlFor="degree_type">Degree Type *</Label>
                    <Select
                      value={educationForm.values.degree_type as string}
                      onValueChange={(value) => educationForm.setValue("degree_type", value)}
                    >
                      <SelectTrigger className={educationForm.errors.degree_type ? "border-red-500" : ""}>
                        <SelectValue placeholder="Select degree type" />
                      </SelectTrigger>
                      <SelectContent>
                        {degreeTypes.map((type) => (
                          <SelectItem key={type} value={type}>
                            {type}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormError message={educationForm.errors.degree_type} />
                  </div>
                </div>

                {/* Field of Study and Major */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="field_of_study">Field of Study *</Label>
                    <Input
                      id="field_of_study"
                      value={educationForm.values.field_of_study as string}
                      onChange={(e) => educationForm.setValue("field_of_study", e.target.value)}
                      onBlur={() => educationForm.handleBlur("field_of_study")}
                      placeholder="Computer Science"
                      className={educationForm.errors.field_of_study ? "border-red-500" : ""}
                    />
                    <FormError message={educationForm.errors.field_of_study} />
                  </div>

                  <div>
                    <Label htmlFor="major">Major (Optional)</Label>
                    <Input
                      id="major"
                      value={educationForm.values.major as string}
                      onChange={(e) => educationForm.setValue("major", e.target.value)}
                      onBlur={() => educationForm.handleBlur("major")}
                      placeholder="Software Engineering"
                    />
                  </div>
                </div>

                {/* GPA */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="gpa">GPA (Optional)</Label>
                    <Input
                      id="gpa"
                      type="number"
                      step="0.01"
                      max="4.0"
                      value={educationForm.values.gpa as number || ""}
                      onChange={(e) => educationForm.setValue("gpa", parseFloat(e.target.value) || undefined)}
                      placeholder="3.85"
                      className={educationForm.errors.gpa ? "border-red-500" : ""}
                    />
                    <FormError message={educationForm.errors.gpa} />
                    <p className="text-xs text-gray-500 mt-1">On a 4.0 scale</p>
                  </div>

                  <div>
                    <Label htmlFor="start_date">Start Date *</Label>
                    <Input
                      id="start_date"
                      type="date"
                      value={educationForm.values.start_date as string}
                      onChange={(e) => educationForm.setValue("start_date", e.target.value)}
                      onBlur={() => educationForm.handleBlur("start_date")}
                      className={educationForm.errors.start_date ? "border-red-500" : ""}
                    />
                    <FormError message={educationForm.errors.start_date} />
                  </div>

                  <div>
                    <Label htmlFor="end_date">End Date</Label>
                    <Input
                      id="end_date"
                      type="date"
                      value={educationForm.values.end_date as string}
                      onChange={(e) => educationForm.setValue("end_date", e.target.value)}
                      onBlur={() => educationForm.handleBlur("end_date")}
                      disabled={educationForm.values.is_current as boolean}
                    />
                  </div>
                </div>

                {/* Current Status */}
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="is_current"
                    checked={educationForm.values.is_current as boolean}
                    onCheckedChange={(checked) => {
                      educationForm.setValue("is_current", !!checked)
                      if (checked) {
                        educationForm.setValue("end_date", "")
                      }
                    }}
                  />
                  <Label htmlFor="is_current">I am currently enrolled</Label>
                </div>

                {/* Skills Gained */}
                <div>
                    <SkillsAutocomplete
                      category="programming_languages"
                      value={educationForm.values.technical_skills_gained as string[] || []}
                      onChange={(skills) => educationForm.setValue("technical_skills_gained", skills)}
                      label="Technical Skills Gained"
                      placeholder="Skills you learned or improved..."
                      maxSkills={30}
                    />
                </div>

                {/* Submit Button */}
                <div className="flex justify-end">
                  <Button
                    type="submit"
                    disabled={educationForm.isSubmitting || !educationForm.isValid}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    Add Education
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Certifications Tab */}
      {activeTab === 'certifications' && (
        <div className="space-y-6">
          {/* Existing Certifications */}
          {value.certifications.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Your Certifications</h3>
              {value.certifications.map((certification, index) => (
                <Card key={index} className="border-l-4 border-green-500">
                  <CardContent className="pt-6">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 className="font-semibold text-lg">{certification.name}</h4>
                        <p className="text-gray-600">{certification.issuing_organization}</p>
                        <div className="flex items-center space-x-4 text-sm text-gray-500 mt-2">
                          <div className="flex items-center space-x-1">
                            <Calendar className="h-4 w-4" />
                            <span>
                              Issued: {certification.issue_date.getFullYear()}
                              {certification.never_expires ?
                                " • Never expires" :
                                certification.expiration_date ?
                                ` • Expires: ${certification.expiration_date.getFullYear()}` : ""
                              }
                            </span>
                          </div>
                        </div>
                        {certification.skills_validated && certification.skills_validated.length > 0 && (
                          <div className="mt-3">
                            <p className="text-sm font-medium text-gray-700 mb-1">Skills Validated:</p>
                            <div className="flex flex-wrap gap-1">
                              {certification.skills_validated.map((skill, skillIndex) => (
                                <span
                                  key={skillIndex}
                                  className="inline-block bg-green-100 text-green-800 text-xs px-2 py-1 rounded"
                                >
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeCertification(index)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Add New Certification Form */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Plus className="h-5 w-5" />
                <span>Add Certification</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={certificationForm.handleSubmit} className="space-y-4">
                {/* Name and Organization */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="cert_name">Certification Name *</Label>
                    <Input
                      id="cert_name"
                      value={certificationForm.values.name as string}
                      onChange={(e) => certificationForm.setValue("name", e.target.value)}
                      onBlur={() => certificationForm.handleBlur("name")}
                      placeholder="AWS Solutions Architect"
                      className={certificationForm.errors.name ? "border-red-500" : ""}
                    />
                    <FormError message={certificationForm.errors.name} />
                  </div>

                  <div>
                    <Label htmlFor="issuing_organization">Issuing Organization *</Label>
                    <Input
                      id="issuing_organization"
                      value={certificationForm.values.issuing_organization as string}
                      onChange={(e) => certificationForm.setValue("issuing_organization", e.target.value)}
                      onBlur={() => certificationForm.handleBlur("issuing_organization")}
                      placeholder="Amazon Web Services"
                      className={certificationForm.errors.issuing_organization ? "border-red-500" : ""}
                    />
                    <FormError message={certificationForm.errors.issuing_organization} />
                  </div>
                </div>

                {/* Dates */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="issue_date">Issue Date *</Label>
                    <Input
                      id="issue_date"
                      type="date"
                      value={certificationForm.values.issue_date as string || ""}
                      onChange={(e) => certificationForm.setValue("issue_date", e.target.value)}
                      onBlur={() => certificationForm.handleBlur("issue_date")}
                      className={certificationForm.errors.issue_date ? "border-red-500" : ""}
                    />
                    <FormError message={certificationForm.errors.issue_date} />
                  </div>

                  <div>
                    <Label htmlFor="expiration_date">Expiration Date</Label>
                    <Input
                      id="expiration_date"
                      type="date"
                      value={certificationForm.values.expiration_date as string || ""}
                      onChange={(e) => certificationForm.setValue("expiration_date", e.target.value)}
                      onBlur={() => certificationForm.handleBlur("expiration_date")}
                      disabled={certificationForm.values.never_expires as boolean}
                    />
                  </div>
                </div>

                {/* Never Expires */}
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="never_expires"
                    checked={certificationForm.values.never_expires as boolean}
                    onCheckedChange={(checked) => {
                      certificationForm.setValue("never_expires", !!checked)
                      if (checked) {
                        certificationForm.setValue("expiration_date", "")
                      }
                    }}
                  />
                  <Label htmlFor="never_expires">This certification never expires</Label>
                </div>

                {/* Skills Validated */}
                <div>
                    <SkillsAutocomplete
                      category="programming_languages"
                      value={certificationForm.values.skills_validated as string[] || []}
                      onChange={(skills) => certificationForm.setValue("skills_validated", skills)}
                      label="Skills Validated by This Certification"
                      placeholder="Skills this certification validates..."
                      maxSkills={20}
                    />
                </div>

                {/* Submit Button */}
                <div className="flex justify-end">
                  <Button
                    type="submit"
                    disabled={certificationForm.isSubmitting || !certificationForm.isValid}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    Add Certification
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}