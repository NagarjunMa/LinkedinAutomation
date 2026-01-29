"use client"

import React, { useState, useEffect } from 'react'
import { PDFFallback } from './pdf-fallback'

interface ResumeDocumentViewerProps {
  fileUrl?: string
  fileName?: string
  onBack?: () => void
}

export function ResumeDocumentViewer({ fileUrl, fileName, onBack }: ResumeDocumentViewerProps) {
  const [PDFViewerClient, setPDFViewerClient] = useState<React.ComponentType<any> | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadPDFViewer = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // Dynamic import with error handling
        const pdfModule = await import('./pdf-viewer-client')
        setPDFViewerClient(() => pdfModule.PDFViewerClient)
      } catch (err) {
        console.error('Failed to load PDF viewer:', err)
        setError('PDF viewer could not load. This may be due to compatibility issues.')
      } finally {
        setIsLoading(false)
      }
    }

    loadPDFViewer()
  }, [])

  if (isLoading) {
    return (
      <div className="flex-[3] flex flex-col border-r border-border bg-background relative">
        <div className="flex-1 overflow-auto p-24 flex justify-center items-start pt-32">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !PDFViewerClient) {
    return (
      <PDFFallback
        fileUrl={fileUrl}
        fileName={fileName}
        onBack={onBack}
        error={error || undefined}
      />
    )
  }

  return (
    <PDFViewerClient
      fileUrl={fileUrl}
      fileName={fileName}
      onBack={onBack}
    />
  )
}