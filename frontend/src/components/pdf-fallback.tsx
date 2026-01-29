"use client"

import React from 'react'
import { Minus, Plus, Upload, RotateCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface PDFFallbackProps {
  fileUrl?: string
  fileName?: string
  onBack?: () => void
  error?: string
}

export function PDFFallback({ fileUrl, fileName, onBack, error }: PDFFallbackProps) {
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

        {/* Zoom Controls (disabled) */}
        <div className="flex items-center gap-2 bg-white/80 backdrop-blur-md px-4 py-2 rounded-full border border-white shadow-sm opacity-50">
          <Button
            variant="ghost"
            size="sm"
            disabled
            className="p-1.5 hover:bg-gray-100 rounded-lg text-foreground"
          >
            <Minus className="w-4 h-4" />
          </Button>
          <span className="text-xs font-bold w-12 text-center text-foreground">
            100%
          </span>
          <Button
            variant="ghost"
            size="sm"
            disabled
            className="p-1.5 hover:bg-gray-100 rounded-lg text-foreground"
          >
            <Plus className="w-4 h-4" />
          </Button>
          <div className="w-[1px] h-4 bg-border mx-1"></div>
          <Button
            variant="ghost"
            size="sm"
            disabled
            className="flex items-center gap-2 text-xs font-bold text-foreground"
          >
            <Upload className="w-4 h-4" /> Reset
          </Button>
        </div>
      </div>

      {/* Document Viewer */}
      <div className="flex-1 overflow-auto p-24 flex justify-center items-start pt-32">
        <div className="text-center max-w-md">
          <div className="mb-6">
            <div className="w-24 h-24 mx-auto mb-4 bg-muted rounded-lg flex items-center justify-center">
              <svg className="w-12 h-12 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">PDF Viewer Unavailable</h3>
            <p className="text-muted-foreground mb-4">
              {error || "The PDF viewer could not load at this time."}
            </p>
          </div>

          {fileUrl && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">You can still download and view your resume:</p>
              <div className="p-4 bg-muted rounded-lg">
                <p className="font-medium text-foreground mb-2">{fileName || 'Resume.pdf'}</p>
                <Button
                  asChild
                  className="w-full"
                  variant="outline"
                >
                  <a
                    href={fileUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    download={fileName}
                  >
                    Download & View PDF
                  </a>
                </Button>
              </div>
            </div>
          )}

          <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>Tip:</strong> Try refreshing the page or use a different browser if the PDF viewer continues to have issues.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}