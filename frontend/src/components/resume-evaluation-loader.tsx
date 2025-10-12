"use client"

import { motion, AnimatePresence } from "framer-motion"
import { useEffect, useState } from "react"
import { CheckCircle, FileText, Target, Brain, Shield, Users, Building2, Sparkles } from "lucide-react"
import { resumeApi, ResumeFile } from "@/app/lib/api"

interface EvaluationStage {
  id: string
  name: string
  description: string
  icon: React.ComponentType<any>
  color: string
  duration: number
}

interface ResumeEvaluationLoaderProps {
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
    color: "text-green-400",
    duration: 2000
  },
  {
    id: "experience",
    name: "Experience Analysis",
    description: "Evaluating career progression and impact",
    icon: Brain,
    color: "text-purple-400",
    duration: 2000
  },
  {
    id: "skills",
    name: "Skills Assessment",
    description: "Analyzing technical and soft skills alignment",
    icon: Sparkles,
    color: "text-accent-400",
    duration: 2000
  },
  {
    id: "format",
    name: "Format Structure",
    description: "Checking document layout and readability",
    icon: Shield,
    color: "text-indigo-400",
    duration: 2000
  },
  {
    id: "redflags",
    name: "Red Flag Detection",
    description: "Identifying potential concerns and gaps",
    icon: Shield,
    color: "text-red-400",
    duration: 2000
  },
  {
    id: "company",
    name: "Company Fit",
    description: "Assessing alignment with target roles",
    icon: Building2,
    color: "text-gold-400",
    duration: 2000
  },
  {
    id: "detailed",
    name: "Detailed Analysis",
    description: "Generating comprehensive insights and recommendations",
    icon: FileText,
    color: "text-blue-400",
    duration: 2000
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

export function ResumeEvaluationLoader({ isVisible, resumeId, onComplete }: ResumeEvaluationLoaderProps) {
  const [currentStageIndex, setCurrentStageIndex] = useState(0)
  const [stageProgress, setStageProgress] = useState(0)
  const [completedStages, setCompletedStages] = useState<Set<string>>(new Set())
  const [isPolling, setIsPolling] = useState(false)
  const [evaluationComplete, setEvaluationComplete] = useState(false)

  // Poll backend for resume status
  useEffect(() => {
    if (!isVisible || !resumeId || isPolling) return

    setIsPolling(true)
    const pollInterval = setInterval(async () => {
      try {
        const resume = await resumeApi.getResume(resumeId)
        if (resume.evaluation_status === 'completed') {
          setEvaluationComplete(true)
          clearInterval(pollInterval)
          setIsPolling(false)
        } else if (resume.evaluation_status === 'failed') {
          clearInterval(pollInterval)
          setIsPolling(false)
          onComplete?.()
        }
      } catch (error) {
        console.error('Error polling resume status:', error)
      }
    }, 1000) // Poll every second

    return () => {
      clearInterval(pollInterval)
      setIsPolling(false)
    }
  }, [isVisible, resumeId, isPolling, onComplete])

  // Handle realistic stage progression that matches backend behavior
  useEffect(() => {
    if (!isVisible) {
      setCurrentStageIndex(0)
      setStageProgress(0)
      setCompletedStages(new Set())
      setEvaluationComplete(false)
      return
    }

    // Start all stages simultaneously (like the backend)
    // But show them sequentially for better UX
    const simulateStageCompletion = (stageIndex: number, delay: number) => {
      setTimeout(() => {
        if (stageIndex < evaluationStages.length) {
          setCurrentStageIndex(stageIndex)
          setStageProgress(0)

          // Animate progress for this stage
          const progressInterval = setInterval(() => {
            setStageProgress(prev => {
              const increment = 100 / (1500 / 50) // 1.5 seconds
              return Math.min(prev + increment, 100)
            })
          }, 50)

          // Complete this stage
          setTimeout(() => {
            setCompletedStages(prev => new Set([...prev, evaluationStages[stageIndex].id]))
            setStageProgress(100)
            clearInterval(progressInterval)
          }, 1500)
        }
      }, delay)
    }

    // Stagger the visual stages every 1.8 seconds
    evaluationStages.forEach((_, index) => {
      simulateStageCompletion(index, index * 1800)
    })

    // All visual stages complete after ~12.6 seconds (7 stages × 1.8s)
    const allStagesTimer = setTimeout(() => {
      if (evaluationComplete) {
        setTimeout(() => onComplete?.(), 1000)
      }
    }, evaluationStages.length * 1800)

    return () => {
      clearTimeout(allStagesTimer)
    }
  }, [isVisible, evaluationComplete, onComplete])

  // Complete when backend is done and all stages are shown
  useEffect(() => {
    if (evaluationComplete && currentStageIndex >= evaluationStages.length - 1 && stageProgress === 100) {
      setTimeout(() => onComplete?.(), 1000)
    }
  }, [evaluationComplete, currentStageIndex, stageProgress, onComplete])

  if (!isVisible) return null

  const currentStage = evaluationStages[currentStageIndex]
  const totalProgress = ((currentStageIndex * 100) + stageProgress) / evaluationStages.length

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
          <motion.div
            className="mb-8"
            key={currentStage?.id}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -20, opacity: 0 }}
            transition={{ duration: 0.4 }}
          >
            <div className="flex items-center justify-center gap-3 mb-4">
              <motion.div
                className={`w-12 h-12 rounded-full bg-card flex items-center justify-center ${currentStage?.color}`}
                animate={{
                  scale: [1, 1.1, 1],
                  rotate: [0, 5, -5, 0]
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              >
                {currentStage && <currentStage.icon className="w-6 h-6" />}
              </motion.div>
              <div>
                <h3 className="text-2xl font-anton text-foreground">{currentStage?.name}</h3>
                <p className="text-muted-foreground">{currentStage?.description}</p>
              </div>
            </div>

            {/* Stage Progress Bar */}
            <div className="w-full max-w-md mx-auto bg-muted rounded-full h-2 mb-6">
              <motion.div
                className="h-2 bg-gradient-warm rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${stageProgress}%` }}
                transition={{ duration: 0.3, ease: "easeOut" }}
              />
            </div>
          </motion.div>

          {/* Overall Progress */}
          <motion.div
            className="mb-8"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 1, duration: 0.6 }}
          >
            <div className="text-lg font-semibold text-foreground mb-2">
              Overall Progress: {Math.round(totalProgress)}%
            </div>
            <div className="w-full max-w-2xl mx-auto bg-muted rounded-full h-3">
              <motion.div
                className="h-3 bg-gradient-to-r from-accent-500 to-gold-500 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${totalProgress}%` }}
                transition={{ duration: 0.3, ease: "easeOut" }}
              />
            </div>
          </motion.div>

          {/* Stage Indicators */}
          <motion.div
            className="flex justify-center gap-4 flex-wrap"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 1.2, duration: 0.6 }}
          >
            {evaluationStages.map((stage, index) => {
              const isCompleted = completedStages.has(stage.id)
              const isCurrent = index === currentStageIndex
              const isPending = index > currentStageIndex

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

          {/* Backend Status */}
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
              {currentStageIndex >= evaluationStages.length - 1 ?
                (evaluationComplete ?
                  "🎉 Analysis complete! Preparing detailed insights..." :
                  "🔍 Final review and quality assurance in progress...") :
                `${evaluationStages.length - currentStageIndex} evaluation stages remaining`
              }
            </motion.div>
          </motion.div>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}