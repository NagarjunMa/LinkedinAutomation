"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { ResumeEvaluationLoader } from "@/components/resume-evaluation-loader"

export default function TestLoaderPage() {
  const [showLoader, setShowLoader] = useState(false)

  const handleStartEvaluation = () => {
    setShowLoader(true)
  }

  const handleEvaluationComplete = () => {
    setShowLoader(false)
    alert("Evaluation completed!")
  }

  return (
    <div className="container mx-auto py-20 text-center">
      <h1 className="text-4xl font-anton mb-8">Resume Evaluation Loader Test</h1>
      <p className="text-lg text-muted-foreground mb-8">
        Click the button below to test the new Framer Motion loading animation
      </p>

      <Button
        onClick={handleStartEvaluation}
        className="bg-gradient-warm hover:bg-gradient-gold text-white px-8 py-4 text-lg"
        disabled={showLoader}
      >
        {showLoader ? "Evaluation Running..." : "Start Resume Evaluation"}
      </Button>

      <ResumeEvaluationLoader
        isVisible={showLoader}
        onComplete={handleEvaluationComplete}
      />
    </div>
  )
}