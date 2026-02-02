"use client"

import React, { useState, useEffect } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { Minus, Plus, Upload, RotateCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface PDFViewerClientProps {
  fileUrl?: string
  onBack?: () => void
}

export function PDFViewerClient({ fileUrl, onBack }: PDFViewerClientProps) {
  const [pageNumber] = useState<number>(1)
  const [scale, setScale] = useState<number>(1.0)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // Initialize PDF.js worker
  useEffect(() => {
    // Polyfill Promise.withResolvers if needed (required for pdfjs-dist v4+)
    if (typeof Promise.withResolvers === 'undefined') {
      if (typeof window !== 'undefined') {
        // @ts-expect-error - Polyfill for older browsers/environments
        window.Promise.withResolvers = function () {
          let resolve, reject;
          const promise = new Promise((res, rej) => {
            resolve = res;
            reject = rej;
          });
          return { promise, resolve, reject };
        };
      }
    }

    if (typeof window !== 'undefined') {
      // Use CDN worker to avoid webpack/build issues with pdfjs-dist
      // Matching version from package.json: 5.3.228
      pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@5.3.228/build/pdf.worker.min.mjs`
    }
  }, [])

  function onDocumentLoadSuccess() {
    setLoading(false)
    setError(null)
  }

  function onDocumentLoadError(error: Error) {
    console.error('Error loading PDF:', error)
    setError('Failed to load PDF document')
    setLoading(false)
  }

  // Fetch auth headers
  const [pdfHeaders, setPdfHeaders] = useState<Record<string, string> | null>(null);

  useEffect(() => {
    const fetchHeaders = async () => {
      try {
        // Import dynamically to avoid SSR issues if any, though getAuthHeaders is safe
        const { getAuthHeaders } = await import('@/app/lib/api/config');
        const headers = await getAuthHeaders();
        setPdfHeaders(headers);
      } catch (e) {
        console.error("Failed to fetch PDF headers", e);
      }
    };
    fetchHeaders();
  }, []);

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.25, 3.0))
  }

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.25, 0.5))
  }

  const handleResetZoom = () => {
    setScale(1.0)
  }

  return (
    <div className="flex-[3] flex flex-col border-r border-border bg-background relative">
      {/* Header Controls */}
      <div className="absolute top-6 left-6 right-6 z-10 flex items-center justify-between">
        <div className="flex items-center gap-4">
          {onBack && (
            <Button
              onClick={onBack}
              variant="ghost"
              size="sm"
              className="p-2 hover:bg-white/50 rounded-full transition-colors text-foreground"
            >
              <RotateCw className="w-5 h-5 rotate-90" />
            </Button>
          )}
          <h2 className="text-sm font-black uppercase tracking-widest text-muted-foreground">
            Document View
          </h2>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-2 bg-white/80 backdrop-blur-md px-4 py-2 rounded-full border border-white shadow-sm">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleZoomOut}
            className="p-1.5 hover:bg-gray-100 rounded-lg text-foreground"
          >
            <Minus className="w-4 h-4" />
          </Button>
          <span className="text-xs font-bold w-12 text-center text-foreground">
            {Math.round(scale * 100)}%
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleZoomIn}
            className="p-1.5 hover:bg-gray-100 rounded-lg text-foreground"
          >
            <Plus className="w-4 h-4" />
          </Button>
          <div className="w-[1px] h-4 bg-border mx-1"></div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleResetZoom}
            className="flex items-center gap-2 text-xs font-bold text-foreground hover:text-primary transition-colors"
          >
            <Upload className="w-4 h-4" /> Reset
          </Button>
        </div>
      </div>

      {/* Document Viewer */}
      <div className="flex-1 overflow-auto p-24 flex justify-center items-start pt-32">
        {error ? (
          <div className="text-center text-muted-foreground">
            <p className="mb-4">Unable to load PDF document</p>
            <p className="text-sm">{error}</p>
          </div>
        ) : fileUrl && pdfHeaders ? (
          <div className="relative">
            {loading && (
              <div className="absolute inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm rounded-lg z-10">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            )}
            <Document
              file={{ url: fileUrl, httpHeaders: pdfHeaders } as any}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>}
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
          <div className="text-center text-muted-foreground">
            {fileUrl ? <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div> : <p>No PDF file provided</p>}
          </div>
        )}
      </div>
    </div>
  )
}