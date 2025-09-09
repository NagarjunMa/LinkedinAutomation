import { useState, useCallback } from 'react'
import { JobAnalysis, StatusUpdate } from '@/components/job-status-modal'

interface UseJobStatusModalReturn {
  isModalOpen: boolean
  currentJob: JobAnalysis | null
  openModal: (job: JobAnalysis) => void
  closeModal: () => void
  handleStatusUpdate: (statusUpdate: StatusUpdate) => Promise<void>
}

export function useJobStatusModal(
  onStatusUpdate?: (jobId: string, statusUpdate: StatusUpdate) => Promise<void>
): UseJobStatusModalReturn {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [currentJob, setCurrentJob] = useState<JobAnalysis | null>(null)

  const openModal = useCallback((job: JobAnalysis) => {
    setCurrentJob(job)
    setIsModalOpen(true)
  }, [])

  const closeModal = useCallback(() => {
    setIsModalOpen(false)
    setCurrentJob(null)
  }, [])

  const handleStatusUpdate = useCallback(async (statusUpdate: StatusUpdate) => {
    if (!currentJob || !onStatusUpdate) return

    try {
      await onStatusUpdate(currentJob.id, statusUpdate)
      
      // You could add success notification here
      console.log(`Status updated for job: ${currentJob.title}`)
    } catch (error) {
      console.error('Failed to update job status:', error)
      // You could add error notification here
      throw error
    }
  }, [currentJob, onStatusUpdate])

  return {
    isModalOpen,
    currentJob,
    openModal,
    closeModal,
    handleStatusUpdate
  }
}
