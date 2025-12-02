"use client"

import { motion, AnimatePresence } from "framer-motion"
import { useEffect, useState } from "react"
import { CheckCircle, FileText, Target, Brain, Shield, Users, Building2, Sparkles, AlertTriangle } from "lucide-react"
import { resumeApi } from "@/app/lib/api"

interface EvaluationStage {
  id: string
  name: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  color: string
}

interface RealTimeResumeLoaderProps {
  isVisible: boolean
  resumeId?: string
  onComplete?: () => void
}

const evaluationStages: EvaluationStage[] = [
  {
    id: "ats",
    name: "ATS Compatibility",
    description: "Optimizing for Applicant Tracking Systems",
    icon: Target,
    color: "text-green-400"
  },
  {
    id: "experience",
    name: "Experience Analysis",
    description: "Evaluating career progression and impact",
    icon: Brain,
    color: "text-purple-400"
  },
  {
    id: "skills",
    name: "Skills Assessment",
    description: "Analyzing technical and soft skills alignment",
    icon: Sparkles,
    color: "text-accent-400"
  },
  {
    id: "format",
    name: "Format Structure",
    description: "Checking document layout and readability",
    icon: Shield,
    color: "text-indigo-400"
  },
  {
    id: "red_flags",
    name: "Red Flag Detection",
    description: "Identifying potential concerns and gaps",
    icon: AlertTriangle,
    color: "text-red-400"
  },
  {
    id: "company_fit",
    name: "Company Fit",
    description: "Assessing alignment with target roles",
    icon: Building2,
    color: "text-gold-400"
  },
  {
    id: "detailed_analysis",
    name: "Detailed Analysis",
    description: "Generating comprehensive insights",
    icon: FileText,
    color: "text-blue-400"
  },
  {
    id: "summary",
    name: "Final Summary",
    description: "Compiling results and recommendations",
    icon: Users,
    color: "text-orange-400"
  }
]

const LoadingText = ({ text, isActive }: { text: string; isActive: boolean }) => {
  return (
    <div className="relative">
      <motion.div
        className="text-6xl lg:text-7xl font-anton text-primary-600"
        initial={{ opacity: 0.3 }}
        animate={{ opacity: isActive ? 0.3 : 0.1 }}
        transition={{ duration: 0.3 }}
      >
        {text}
      </motion.div>
      <motion.div
        className="absolute inset-0 text-6xl lg:text-7xl font-anton bg-gradient-warm bg-clip-text text-transparent overflow-hidden"
        initial={{ clipPath: "inset(0 100% 0 0)" }}
        animate={{
          clipPath: isActive ? "inset(0 0% 0 0)" : "inset(0 100% 0 0)"
        }}
        transition={{
          duration: 1.5,
          ease: "easeInOut",
          delay: isActive ? 0.2 : 0
        }}
      >
        {text}
      </motion.div>
    </div>
  )
}

export function RealTimeResumeLoader({ isVisible, resumeId, onComplete }: RealTimeResumeLoaderProps) {
  const [currentStage, setCurrentStage] = useState<string | null>(null)
  const [completedStages, setCompletedStages] = useState<Set<string>>(new Set())
  const [overallProgress, setOverallProgress] = useState(0)
  const [evaluationStatus, setEvaluationStatus] = useState<string>('starting')
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState<string>('')

  // Real-time polling for backend progress
  useEffect(() => {
    if (!isVisible || !resumeId) return

    let pollInterval: NodeJS.Timeout | undefined = undefined

    const pollProgress = async () => {
      try {
        const progressData = await resumeApi.getEvaluationProgress(resumeId)
        const { progress, evaluation_status } = progressData

        console.log('Progress update:', progress)

        // Update overall status
        setEvaluationStatus(evaluation_status)
        setOverallProgress(progress.overall_progress || 0)

        // Update stage statuses
        const completed = new Set<string>()
        let activeStage: string | null = null

        Object.entries(progress.stages || {}).forEach(([stageId, stageData]) => {
          if (stageData.status === 'completed') {
            completed.add(stageId)
          } else if (stageData.status === 'running') {
            activeStage = stageId
          }
        })

        setCompletedStages(completed)
        setCurrentStage(activeStage)

        // Calculate estimated time remaining
        const totalStages = evaluationStages.length
        const completedCount = completed.size
        const avgTimePerStage = 10 // seconds
        const remainingStages = totalStages - completedCount - (activeStage ? 1 : 0)
        const estimatedSeconds = remainingStages * avgTimePerStage

        if (estimatedSeconds > 60) {
          setEstimatedTimeRemaining(`~${Math.ceil(estimatedSeconds / 60)} minutes remaining`)
        } else if (estimatedSeconds > 0) {
          setEstimatedTimeRemaining(`~${estimatedSeconds} seconds remaining`)
        } else {
          setEstimatedTimeRemaining('Finalizing results...')
        }

        // Check if evaluation is complete
        if (evaluation_status === 'completed') {
          clearInterval(pollInterval)
          setTimeout(() => {
            onComplete?.()
          }, 2000) // Wait 2 seconds to show completion
        } else if (evaluation_status === 'failed') {
          clearInterval(pollInterval)
          onComplete?.()
        }

      } catch (error) {
        console.error('Error polling evaluation progress:', error)
      }
    }

    // Start polling immediately, then every 2 seconds
    pollProgress()
    pollInterval = setInterval(pollProgress, 2000)

    return () => {
      if (pollInterval) {
        clearInterval(pollInterval)
      }
    }
  }, [isVisible, resumeId, onComplete])

  if (!isVisible) return null

  const getCurrentStageInfo = () => {
    if (currentStage) {
      return evaluationStages.find(stage => stage.id === currentStage)
    }

    // If no current stage, show the next pending stage
    const nextStage = evaluationStages.find(stage => !completedStages.has(stage.id))
    return nextStage || evaluationStages[evaluationStages.length - 1]
  }

  const currentStageInfo = getCurrentStageInfo()

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 bg-background/95 backdrop-blur-sm z-50 flex items-center justify-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="container mx-auto px-6 text-center">
          {/* Main Loading Text */}
          <motion.div
            className="mb-12"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.6 }}
          >
            <LoadingText text="EVALUATING" isActive={true} />
            <motion.p
              className="text-xl text-muted-foreground mt-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
            >
              Advanced AI agents analyzing your resume
            </motion.p>
          </motion.div>

          {/* Current Stage Information */}
          {currentStageInfo && (
            <motion.div
              className="mb-8"
              key={currentStageInfo.id}
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -20, opacity: 0 }}
              transition={{ duration: 0.4 }}
            >
              <div className="flex items-center justify-center gap-3 mb-4">
                <motion.div
                  className={`w-12 h-12 rounded-full bg-card flex items-center justify-center ${currentStageInfo.color}`}
                  animate={{
                    scale: currentStage === currentStageInfo.id ? [1, 1.1, 1] : 1,
                    rotate: currentStage === currentStageInfo.id ? [0, 5, -5, 0] : 0
                  }}
                  transition={{
                    duration: 2,
                    repeat: currentStage === currentStageInfo.id ? Infinity : 0,
                    ease: "easeInOut"
                  }}
                >
                  <currentStageInfo.icon className="w-6 h-6" />
                </motion.div>
                <div>
                  <h3 className="text-2xl font-anton text-foreground">{currentStageInfo.name}</h3>
                  <p className="text-muted-foreground">{currentStageInfo.description}</p>
                </div>
              </div>
            </motion.div>
          )}

          {/* Overall Progress */}
          <motion.div
            className="mb-8"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 1, duration: 0.6 }}
          >
            <div className="text-lg font-semibold text-foreground mb-2">
              Overall Progress: {overallProgress}%
            </div>
            <div className="w-full max-w-2xl mx-auto bg-muted rounded-full h-3">
              <motion.div
                className="h-3 bg-gradient-to-r from-accent-500 to-gold-500 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${overallProgress}%` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              />
            </div>
          </motion.div>

          {/* Stage Indicators */}
          <motion.div
            className="flex justify-center gap-4 flex-wrap mb-8"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 1.2, duration: 0.6 }}
          >
            {evaluationStages.map((stage, _index) => {
              const isCompleted = completedStages.has(stage.id)
              const isCurrent = currentStage === stage.id
              const _isPending = !isCompleted && !isCurrent

              return (
                <motion.div
                  key={stage.id}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all duration-300 ${
                    isCompleted
                      ? 'bg-green-500/20 text-green-400'
                      : isCurrent
                        ? 'bg-accent-500/20 text-accent-400 scale-105'
                        : 'bg-muted text-muted-foreground'
                  }`}
                  animate={isCurrent ? {
                    scale: [1, 1.05, 1],
                  } : {}}
                  transition={{
                    duration: 2,
                    repeat: isCurrent ? Infinity : 0,
                    ease: "easeInOut"
                  }}
                >
                  {isCompleted ? (
                    <CheckCircle className="w-4 h-4" />
                  ) : (
                    <stage.icon className="w-4 h-4" />
                  )}
                  <span className="text-sm font-medium hidden sm:inline">
                    {stage.name}
                  </span>
                </motion.div>
              )
            })}
          </motion.div>

          {/* Status Information */}
          <motion.div
            className="mt-8 text-sm text-muted-foreground"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.5 }}
          >
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              {evaluationStatus === 'completed' ? (
                "🎉 Analysis complete! Preparing detailed insights..."
              ) : evaluationStatus === 'failed' ? (
                "❌ Evaluation failed. Please try again."
              ) : (
                estimatedTimeRemaining || "Processing your resume with advanced AI..."
              )}
            </motion.div>
          </motion.div>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}