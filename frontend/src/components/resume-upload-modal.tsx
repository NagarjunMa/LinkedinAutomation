"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Upload, CheckCircle, Target, Clock, FileText, Sparkles } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import { resumeApi, ResumeFile } from "@/app/lib/api"

interface ResumeUploadModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onUploadSuccess: (resume: ResumeFile) => void
  onEvaluationStart?: (resumeId: string) => void
}

export function ResumeUploadModal({ open, onOpenChange, onUploadSuccess, onEvaluationStart }: ResumeUploadModalProps) {
  const [file, setFile] = useState<File | null>(null)
  const [targetRole, setTargetRole] = useState("")
  const [targetSeniority, setTargetSeniority] = useState("")
  const [uploading, setUploading] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [uploadedResume, setUploadedResume] = useState<ResumeFile | null>(null)
  const [storageInfo, setStorageInfo] = useState<{ totalCount: number; storageUsed: number; storageLimit: number } | null>(null)
  const { toast } = useToast()

  // Fetch storage info when modal opens
  useEffect(() => {
    if (open) {
      fetchStorageInfo()
    }
  }, [open])

  const fetchStorageInfo = async () => {
    try {
      const info = await resumeApi.getStorageInfo()
      setStorageInfo(info)
    } catch (error) {
      console.error('Failed to fetch storage info:', error)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      if (selectedFile.type !== "application/pdf" && selectedFile.type !== "application/msword" && 
          selectedFile.type !== "application/vnd.openxmlformats-officedocument.wordprocessingml.document") {
        toast({
          title: "Invalid file type",
          description: "Please upload a PDF, DOC, or DOCX file.",
          variant: "destructive",
        })
        return
      }
      if (selectedFile.size > 10 * 1024 * 1024) { // 10MB limit
        toast({
          title: "File too large",
          description: "Please upload a file smaller than 10MB.",
          variant: "destructive",
        })
        return
      }
      setFile(selectedFile)
    }
  }

  const handleUpload = async () => {
    if (!file) {
      toast({
        title: "No file selected",
        description: "Please select a resume file to upload.",
        variant: "destructive",
      })
      return
    }

    setUploading(true)
    try {
      const resume = await resumeApi.uploadResume(file, targetRole, targetSeniority)
      setUploadedResume(resume)
      setUploadSuccess(true)
      toast({
        title: "Resume Uploaded Successfully! 🎉",
        description: "Your resume has been uploaded and is ready for AI evaluation.",
      })
    } catch (error) {
      console.error("Upload failed:", error)

      // Handle specific error cases
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'

      if (errorMessage.includes('Storage limit reached') || errorMessage.includes('Maximum 5 resumes')) {
        toast({
          title: "📁 Resume Limit Reached",
          description: "You can only upload 5 resumes. Please delete an old resume before uploading a new one.",
          variant: "destructive",
        })
      } else if (errorMessage.includes('File too large')) {
        toast({
          title: "📄 File Too Large",
          description: "Please upload a file smaller than 10MB.",
          variant: "destructive",
        })
      } else if (errorMessage.includes('File type not allowed')) {
        toast({
          title: "📋 Invalid File Type",
          description: "Please upload a PDF, DOC, or DOCX file.",
          variant: "destructive",
        })
      } else {
        toast({
          title: "❌ Upload Failed",
          description: errorMessage || "Failed to upload resume. Please try again.",
          variant: "destructive",
        })
      }
    } finally {
      setUploading(false)
    }
  }

  const handleEvaluateNow = async () => {
    if (uploadedResume) {
      try {
        // Start evaluation immediately
        await resumeApi.evaluateResume(uploadedResume.id, targetRole || undefined, targetSeniority || undefined)

        toast({
          title: "Evaluation Started! 🚀",
          description: "AI is analyzing your resume with advanced multi-agent system.",
        })

        // Notify parent to show progress screen
        if (onEvaluationStart) {
          onEvaluationStart(uploadedResume.id)
        }

        onUploadSuccess(uploadedResume)
        onOpenChange(false)
        // Reset state
        setFile(null)
        setTargetRole("")
        setTargetSeniority("")
        setUploadSuccess(false)
        setUploadedResume(null)
      } catch (error) {
        console.error("Failed to start evaluation:", error)
        toast({
          title: "Evaluation Failed",
          description: "Failed to start evaluation. You can try again later.",
          variant: "destructive",
        })
        // Still close the modal and show the resume
        onUploadSuccess(uploadedResume)
        onOpenChange(false)
        // Reset state
        setFile(null)
        setTargetRole("")
        setTargetSeniority("")
        setUploadSuccess(false)
        setUploadedResume(null)
      }
    }
  }

  const handleMaybeLater = () => {
    if (uploadedResume) {
      onUploadSuccess(uploadedResume)
      onOpenChange(false)
      // Reset state
      setFile(null)
      setTargetRole("")
      setTargetSeniority("")
      setUploadSuccess(false)
      setUploadedResume(null)
    }
  }

  const handleClose = () => {
    if (!uploading) {
      onOpenChange(false)
      // Reset state
      setFile(null)
      setTargetRole("")
      setTargetSeniority("")
      setUploadSuccess(false)
      setUploadedResume(null)
    }
  }

  if (uploadSuccess && uploadedResume) {
    return (
      <Dialog open={open} onOpenChange={handleClose}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-green-800">
              <CheckCircle className="w-6 h-6" />
              Resume Uploaded Successfully! 🎉
            </DialogTitle>
            <DialogDescription>
              Your resume has been uploaded and is ready for AI-powered evaluation
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            {/* Success Message with Graphics */}
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-center gap-4">
                <div className="flex-shrink-0">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                    <CheckCircle className="w-8 h-8 text-green-600" />
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-green-800 mb-2">
                    {uploadedResume.filename}
                  </h3>
                  <p className="text-green-800 text-sm">
                    File uploaded successfully • Ready for AI evaluation
                  </p>
                  <div className="flex items-center gap-4 mt-3 text-sm text-green-600">
                    <span className="flex items-center gap-1">
                      <FileText className="w-4 h-4" />
                      {uploadedResume.file_size} bytes
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      Just now
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Evaluation Options */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="hover:shadow-lg transition-all duration-300 cursor-pointer border-2 border-transparent hover:border-blue-200">
                <CardContent className="pt-6 text-center">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Target className="w-8 h-8 text-blue-600" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">Evaluate Now</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Start AI evaluation immediately and get detailed analysis
                  </p>
                  <Button 
                    onClick={handleEvaluateNow}
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
                  >
                    <Sparkles className="w-4 h-4 mr-2" />
                    Start Evaluation
                  </Button>
                </CardContent>
              </Card>

              <Card className="hover:shadow-lg transition-all duration-300 cursor-pointer border-2 border-transparent hover:border-green-200">
                <CardContent className="pt-6 text-center">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Clock className="w-8 h-8 text-green-600" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">Maybe Later</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Upload more resumes first, then evaluate all together
                  </p>
                  <Button 
                    onClick={handleMaybeLater}
                    variant="outline"
                    className="w-full"
                  >
                    <FileText className="w-4 h-4 mr-2" />
                    Continue Uploading
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* What Happens Next */}
            <Card className="bg-blue-50 border-blue-200">
              <CardHeader>
                <CardTitle className="text-blue-900 flex items-center gap-2">
                  <Sparkles className="w-5 h-5" />
                  What Happens Next?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm text-blue-900">
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                    <span>AI recruiter analyzes your resume with 15+ years of experience</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                    <span>Get detailed ATS scoring and keyword analysis</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                    <span>Receive actionable improvement recommendations</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                    <span>Create personalized study timeline for career growth</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Upload className="w-6 h-6" />
            Upload New Resume
          </DialogTitle>
          <DialogDescription>
            Upload your resume for AI-powered evaluation and improvement recommendations
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Storage Status */}
          {storageInfo && (
            <Card className={`premium-card border-2 ${storageInfo.totalCount >= 5 ? 'border-orange-500/50 bg-orange-900/20' : 'border-accent-500/50 bg-accent-900/20'}`}>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center justify-between text-cream-50">
                  <span>📂 Storage Status</span>
                  <span className={`text-xs px-2 py-1 rounded-full ${storageInfo.totalCount >= 5 ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30' : 'bg-accent-500/20 text-accent-300 border border-accent-500/30'}`}>
                    {storageInfo.totalCount}/5 resumes
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                {storageInfo.totalCount >= 5 ? (
                  <div className="text-sm text-orange-300 flex items-center gap-2">
                    <span className="w-2 h-2 bg-orange-400 rounded-full flex-shrink-0"></span>
                    Storage limit reached. Please delete an old resume before uploading a new one.
                  </div>
                ) : (
                  <div className="text-sm text-accent-300 flex items-center gap-2">
                    <span className="w-2 h-2 bg-accent-400 rounded-full flex-shrink-0"></span>
                    You have {5 - storageInfo.totalCount} upload slots remaining.
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* File Upload */}
          <Card>
            <CardHeader>
              <CardTitle>Resume File</CardTitle>
              <CardDescription>
                Upload a PDF, DOC, or DOCX file (max 10MB)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid w-full max-w-sm items-center gap-1.5">
                  <Label htmlFor="resume-file">Resume File</Label>
                  <Input
                    id="resume-file"
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={handleFileChange}
                    disabled={uploading}
                  />
                </div>
                {file && (
                  <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg">
                    <FileText className="w-5 h-5 text-blue-600" />
                    <span className="text-sm font-medium">{file.name}</span>
                    <span className="text-xs text-muted-foreground">
                      ({(file.size / 1024 / 1024).toFixed(2)} MB)
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Target Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Target Role</CardTitle>
                <CardDescription>
                  What position are you targeting?
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Input
                  placeholder="e.g., Software Engineer, Data Scientist"
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Target Seniority Level</CardTitle>
                <CardDescription>
                  What experience level are you targeting?
                </CardDescription>
              </CardHeader>
              <CardContent>
                <select
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  value={targetSeniority}
                  onChange={(e) => setTargetSeniority(e.target.value)}
                >
                  <option value="">Select seniority level</option>
                  <option value="entry-level">Entry Level / Fresh Graduate</option>
                  <option value="mid-level">Mid Level (2-5 years)</option>
                  <option value="senior">Senior Level (5+ years)</option>
                  <option value="principal">Principal/Staff Level (8+ years)</option>
                </select>
              </CardContent>
            </Card>
          </div>

          {/* Upload Button */}
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={handleClose} disabled={uploading}>
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!file || uploading || (storageInfo?.totalCount ?? 0) >= 5}
              className="bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Resume
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
