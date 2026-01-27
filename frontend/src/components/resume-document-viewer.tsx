"use client"

import React, { useState, useEffect } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { Minus, Plus, Upload, RotateCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { COLORS } from '@/lib/constants/resume-evaluation-design'

interface ResumeDocumentViewerProps {
  fileUrl?: string
  fileName?: string
  onBack?: () => void
}

export function ResumeDocumentViewer({ fileUrl, fileName, onBack }: ResumeDocumentViewerProps) {
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [scale, setScale] = useState<number>(1.0)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // Initialize PDF.js worker on component mount
  useEffect(() => {
    if (typeof window !== 'undefined' && !pdfjs.GlobalWorkerOptions.workerSrc) {
      try {
        pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`
      } catch (err) {
        console.warn('Failed to set PDF.js worker, using fallback:', err)
        pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.js`
      }
    }
  }, [])

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages)
    setLoading(false)
    setError(null)
  }

  function onDocumentLoadError(error: Error) {
    console.error('Error loading PDF:', error)
    setError('Failed to load PDF document')
    setLoading(false)
  }

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.25, 3.0))
  }

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.25, 0.5))
  }

  const handleResetZoom = () => {
    setScale(1.0)
  }

  // Mock resume content when no PDF is available
  const MockResumeContent = () => (
    <div className="w-full max-w-2xl bg-white shadow-[0_32px_64px_-16px_rgba(0,0,0,0.1)] p-12 min-h-[1050px] text-resume-primary border border-white/50 relative">
      <div className="absolute top-0 left-0 w-full h-1.5 bg-resume-accent/10"></div>

      <header className="text-center mb-12">
        <h1 className="text-3xl font-bold tracking-tight mb-2">Nagarjun Mallesh</h1>
        <div className="flex flex-wrap justify-center gap-2 text-micro-sm font-medium text-resume-text-xs-muted uppercase tracking-tight">
          <span>nagarjunmallesh@gmail.com</span>
          <span>•</span>
          <span>+1-(857)-799-0214</span>
          <span>•</span>
          <span>New York, NY</span>
        </div>
      </header>

      <div className="space-y-8">
        <section>
          <h3 className="text-11px font-black uppercase tracking-ultra-wide text-resume-primary border-b border-resume-border pb-1 mb-3">
            Professional Summary
          </h3>
          <p className="text-11px leading-relaxed text-resume-text-secondary">
            <strong>Full-stack Software Engineer</strong> with 4 years of experience building scalable systems.
            Expert in <strong>TypeScript, Python, and AWS</strong>. Specialized in cloud-native automation and
            high-performance backend orchestration.
          </p>
        </section>

        <section>
          <h3 className="text-11px font-black uppercase tracking-ultra-wide text-resume-primary border-b border-resume-border pb-1 mb-3">
            Core Experience
          </h3>
          <div className="space-y-6">
            <div>
              <div className="flex justify-between items-baseline">
                <h4 className="text-11px font-bold">Systems Analyst | ML Technologies LLC</h4>
                <span className="text-micro-sm font-bold text-resume-text-muted italic">2025 - Present</span>
              </div>
              <ul className="list-disc ml-4 text-micro-sm text-resume-text-secondary space-y-2 mt-2 leading-relaxed">
                <li>Developed a RAG-based vehicle recovery system using <strong>TypeScript</strong> and <strong>AWS Bedrock</strong>.</li>
                <li>Automated manual verification workflows with <strong>FastAPI</strong>, reducing processing time by 80%.</li>
                <li>Implemented infrastructure-as-code using <strong>Terraform</strong> for global AWS deployments.</li>
              </ul>
            </div>

            <div>
              <div className="flex justify-between items-baseline">
                <h4 className="text-11px font-bold">Senior Software Engineer | TechCorp Solutions</h4>
                <span className="text-micro-sm font-bold text-resume-text-muted italic">2022 - 2024</span>
              </div>
              <ul className="list-disc ml-4 text-micro-sm text-resume-text-secondary space-y-2 mt-2 leading-relaxed">
                <li>Led development of microservices architecture serving 1M+ daily active users.</li>
                <li>Built high-performance APIs with <strong>Node.js</strong> and <strong>PostgreSQL</strong>.</li>
                <li>Implemented CI/CD pipelines using <strong>Docker</strong> and <strong>Kubernetes</strong>.</li>
              </ul>
            </div>
          </div>
        </section>

        <section>
          <h3 className="text-11px font-black uppercase tracking-ultra-wide text-resume-primary border-b border-resume-border pb-1 mb-3">
            Technical Skills
          </h3>
          <div className="grid grid-cols-2 gap-4 text-micro-sm text-resume-text-secondary">
            <div>
              <p><strong>Languages:</strong> TypeScript, Python, JavaScript, Go</p>
              <p><strong>Frameworks:</strong> React, Next.js, FastAPI, Express</p>
            </div>
            <div>
              <p><strong>Cloud:</strong> AWS, Docker, Kubernetes, Terraform</p>
              <p><strong>Databases:</strong> PostgreSQL, Redis, MongoDB</p>
            </div>
          </div>
        </section>

        <section>
          <h3 className="text-11px font-black uppercase tracking-ultra-wide text-resume-primary border-b border-resume-border pb-1 mb-3">
            Education
          </h3>
          <div className="text-micro-sm text-resume-text-secondary">
            <p><strong>Master of Science in Computer Science</strong></p>
            <p>Northeastern University, Boston, MA | 2020</p>
          </div>
        </section>
      </div>
    </div>
  )

  return (
    <div className="flex-[3] flex flex-col border-r border-resume-border bg-resume-surface-secondary relative">
      {/* Header Controls */}
      <div className="absolute top-6 left-6 right-6 z-10 flex items-center justify-between">
        <div className="flex items-center gap-4">
          {onBack && (
            <Button
              onClick={onBack}
              variant="ghost"
              size="sm"
              className="p-2 hover:bg-white/50 rounded-full transition-colors text-resume-primary"
            >
              <RotateCw className="w-5 h-5 rotate-90" />
            </Button>
          )}
          <h2 className="text-sm font-black uppercase tracking-widest text-resume-text-muted">
            Document View
          </h2>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-2 bg-white/80 backdrop-blur-md px-4 py-2 rounded-full border border-white shadow-sm">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleZoomOut}
            className="p-1.5 hover:bg-gray-100 rounded-lg text-resume-primary"
          >
            <Minus className="w-4 h-4" />
          </Button>
          <span className="text-xs font-bold w-12 text-center text-resume-primary">
            {Math.round(scale * 100)}%
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleZoomIn}
            className="p-1.5 hover:bg-gray-100 rounded-lg text-resume-primary"
          >
            <Plus className="w-4 h-4" />
          </Button>
          <div className="w-[1px] h-4 bg-resume-border mx-1"></div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleResetZoom}
            className="flex items-center gap-2 text-xs font-bold text-resume-primary hover:text-resume-accent transition-colors"
          >
            <Upload className="w-4 h-4" /> Reset
          </Button>
        </div>
      </div>

      {/* Document Viewer */}
      <div className="flex-1 overflow-auto p-24 flex justify-center items-start pt-32">
        {error ? (
          <div className="text-center text-resume-text-muted">
            <p className="mb-4">Unable to load PDF document</p>
            <MockResumeContent />
          </div>
        ) : fileUrl ? (
          <div className="relative">
            {loading && (
              <div className="absolute inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm rounded-lg z-10">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-resume-primary"></div>
              </div>
            )}
            <Document
              file={fileUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-resume-primary"></div>}
              className="shadow-[0_32px_64px_-16px_rgba(0,0,0,0.1)] border border-white/50"
            >
              <Page
                pageNumber={pageNumber}
                scale={scale}
                className="max-w-full"
                renderTextLayer={false}
                renderAnnotationLayer={false}
              />
            </Document>
          </div>
        ) : (
          <MockResumeContent />
        )}
      </div>
    </div>
  )
}