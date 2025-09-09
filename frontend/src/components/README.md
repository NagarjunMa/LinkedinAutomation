# Job Status Modal Component

A smart React modal component that appears after job URL processing, allowing users to quickly assign application statuses with context collection.

## Features

- **4 Status Options**: Applied, Want to Apply, Maybe Later, Not Interested
- **Smart Context Collection**: Auto-fills context based on selected status
- **Date Picker**: For "Applied" status with application date
- **Notes & Context**: Optional fields for additional information
- **Smooth UX**: Appears automatically after job extraction
- **One-Click Assignment**: Quick status updates without interruption

## Components

### 1. JobStatusModal

The main modal component that handles status selection and context collection.

```tsx
import { JobStatusModal, JobAnalysis, StatusUpdate } from './job-status-modal'

interface JobStatusModalProps {
  isOpen: boolean
  onClose: () => void
  job: JobAnalysis | null
  onStatusUpdate: (statusUpdate: StatusUpdate) => void
}
```

### 2. useJobStatusModal Hook

Custom hook for managing modal state and integration.

```tsx
import { useJobStatusModal } from '@/hooks/use-job-status-modal'

const {
  isModalOpen,
  currentJob,
  openModal,
  closeModal,
  handleStatusUpdate
} = useJobStatusModal(onStatusUpdate)
```

## Usage

### Basic Integration

```tsx
import { JobStatusModal } from './job-status-modal'
import { useJobStatusModal } from '@/hooks/use-job-status-modal'

function JobExtractionComponent() {
  const {
    isModalOpen,
    currentJob,
    openModal,
    closeModal,
    handleStatusUpdate
  } = useJobStatusModal(async (jobId, statusUpdate) => {
    // Call your API to update job status
    await api.updateJobStatus(jobId, statusUpdate)
  })

  const handleJobExtracted = (job) => {
    // Automatically open modal after extraction
    openModal(job)
  }

  return (
    <>
      {/* Your job extraction UI */}
      
      <JobStatusModal
        isOpen={isModalOpen}
        onClose={closeModal}
        job={currentJob}
        onStatusUpdate={handleStatusUpdate}
      />
    </>
  )
}
```

### Status Options

The modal provides 4 status options with different behaviors:

1. **Applied** 🟢
   - Requires application date (with date picker)
   - Marks job as applied
   - Updates application tracking

2. **Want to Apply** 🔵
   - Adds to application todo list
   - Schedules for future action
   - Tracks application intent

3. **Maybe Later** 🟡
   - Schedules for future review
   - Adds to review queue
   - Maintains job in system

4. **Not Interested** 🔴
   - Marks as not interested
   - Collects feedback for AI improvement
   - Helps refine future recommendations

### Context Collection

Each status automatically suggests context and allows custom notes:

```tsx
// Auto-filled context examples
const contextExamples = {
  applied: 'Job application submitted successfully',
  want_to_apply: 'Added to application todo list',
  maybe_later: 'Scheduled for future review',
  not_interested: 'Not a good fit for current goals'
}
```

## API Integration

### Backend Endpoint

```typescript
// POST /api/v1/jobs/{job_id}/status
interface StatusUpdateRequest {
  status: 'applied' | 'want_to_apply' | 'maybe_later' | 'not_interested'
  date?: string // ISO date string for applied status
  notes?: string
  context?: string
}
```

### Database Schema

```sql
-- Job applications table
CREATE TABLE job_applications (
  id SERIAL PRIMARY KEY,
  job_id INTEGER REFERENCES job_listings(id),
  user_id VARCHAR(100),
  application_status VARCHAR(50),
  application_date TIMESTAMP,
  notes TEXT,
  context TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Styling & Customization

### Theme Colors

The modal uses semantic colors for each status:

- **Applied**: Green (`bg-green-500`, `text-green-700`)
- **Want to Apply**: Blue (`bg-blue-500`, `text-blue-700`)
- **Maybe Later**: Yellow (`bg-yellow-500`, `text-yellow-700`)
- **Not Interested**: Red (`bg-red-500`, `text-red-700`)

### Responsive Design

- **Mobile**: Single column layout
- **Desktop**: Two-column grid for status options
- **Modal**: Responsive width with scroll for long content

## Accessibility

- **Keyboard Navigation**: Full keyboard support
- **Screen Readers**: Proper ARIA labels and descriptions
- **Focus Management**: Automatic focus on selected status
- **High Contrast**: Clear visual indicators for all states

## Performance

- **Lazy Loading**: Modal content loads only when opened
- **Optimized Rendering**: Minimal re-renders with React hooks
- **Smooth Animations**: CSS transitions for better UX
- **Memory Management**: Proper cleanup on unmount

## Error Handling

```tsx
const handleStatusUpdate = async (statusUpdate: StatusUpdate) => {
  try {
    await onStatusUpdate(currentJob.id, statusUpdate)
    // Success: modal closes automatically
  } catch (error) {
    // Error: modal stays open, show error message
    console.error('Failed to update status:', error)
    // You can add toast notifications here
  }
}
```

## Testing

### Component Testing

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { JobStatusModal } from './job-status-modal'

test('opens modal with job data', () => {
  const mockJob = { /* job data */ }
  render(<JobStatusModal isOpen={true} job={mockJob} />)
  
  expect(screen.getByText(mockJob.title)).toBeInTheDocument()
})

test('calls onStatusUpdate when status is selected', () => {
  const mockOnStatusUpdate = jest.fn()
  render(<JobStatusModal isOpen={true} onStatusUpdate={mockOnStatusUpdate} />)
  
  fireEvent.click(screen.getByText('Applied'))
  fireEvent.click(screen.getByText('Update Status'))
  
  expect(mockOnStatusUpdate).toHaveBeenCalled()
})
```

## Demo

Visit `/demo` to see the modal in action with mock data and sample URLs.

## Dependencies

- **UI Components**: Shadcn/ui components (Dialog, Button, Calendar, etc.)
- **Icons**: Lucide React icons
- **Date Handling**: date-fns for date formatting
- **Styling**: Tailwind CSS with custom utilities
- **State Management**: React hooks for local state

## Future Enhancements

- **Bulk Status Updates**: Handle multiple jobs at once
- **Status Templates**: Pre-defined status configurations
- **Integration Hooks**: Connect with calendar and todo apps
- **Analytics**: Track status change patterns
- **AI Suggestions**: Smart status recommendations based on job data
