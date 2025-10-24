/**
 * Referral API Client
 * Handles all referral-related API communication
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const REFERRAL_BASE = `${API_BASE_URL}/api/v1/referral`;

// Types for referral system
export interface ContactInfo {
  contact_name: string;
  contact_email: string;
  company: string;
  position?: string;
  relationship?: string;
}

export interface ReferralContact extends ContactInfo {
  id: string;
  user_id: string;
  created_at: string;
}

export interface EmailDraft {
  id: string;
  user_id: string;
  job_id?: string;
  contact_id: string;
  subject?: string;
  email_body?: string;
  version: number;
  is_primary: boolean;
  template_used?: string;
  created_at: string;
}

export interface GeneratedEmail {
  subject: string;
  body: string;
  template_used: string;
}

export interface ReferralAnalytics {
  this_week: number;
  total_sent: number;
  response_rate: number;
  trend_data: Array<{ date: string; count: number }>;
}

export interface ReferralStats {
  total_contacts: number;
  emails_sent_this_month: number;
  response_rate: number;
  pending_responses: number;
}

// API Error handling
export class ReferralAPIError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ReferralAPIError';
    this.status = status;
  }
}

// Helper function for API calls
async function apiCall<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${REFERRAL_BASE}${endpoint}`;

  console.log('🌐 API Call:', url)
  console.log('🌐 Options:', options)

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  console.log('🌐 Response status:', response.status)

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    console.error('🌐 API Error:', errorData)
    throw new ReferralAPIError(
      errorData.detail || `HTTP ${response.status}`,
      response.status
    );
  }

  const result = await response.json();
  console.log('🌐 API Success:', result)
  return result;
}

export const referralAPI = {
  // Generate email without saving
  generateEmail: async (
    jobId: string | null,
    contactInfo: ContactInfo
  ): Promise<GeneratedEmail> => {
    console.log('🔥 referralAPI.generateEmail called with:', { jobId, contactInfo })

    // Convert jobId to integer if it's not null and not "sample-job-id"
    let processedJobId = null
    if (jobId && jobId !== 'sample-job-id') {
      processedJobId = parseInt(jobId)
      if (isNaN(processedJobId)) {
        console.warn('Invalid job ID, using default')
        processedJobId = 1 // Default fallback
      }
    } else {
      processedJobId = 1 // Default fallback for sample
    }

    console.log('🔥 Processed job ID:', processedJobId)

    // Map frontend field names to backend expected names
    const backendContactInfo = {
      name: contactInfo.contact_name,
      contact_email: contactInfo.contact_email,
      company: contactInfo.company,
      position: contactInfo.position,
      relationship: contactInfo.relationship
    }

    console.log('🔥 Mapped contact info for backend:', backendContactInfo)

    return apiCall<GeneratedEmail>('/generate-email', {
      method: 'POST',
      body: JSON.stringify({
        job_id: processedJobId,
        contact_info: backendContactInfo
      }),
    });
  },

  // Create complete referral request
  createReferralRequest: async (
    jobId: string,
    contactInfo: ContactInfo
  ): Promise<{ draft: EmailDraft; contact: ReferralContact }> => {
    // Convert jobId to integer if it's not null and not "sample-job-id"
    let processedJobId = null
    if (jobId && jobId !== 'sample-job-id') {
      processedJobId = parseInt(jobId)
      if (isNaN(processedJobId)) {
        console.warn('Invalid job ID, setting to null')
        processedJobId = null
      }
    } else {
      // For sample jobs, don't reference a job ID to avoid foreign key constraint
      processedJobId = null
    }

    // Map frontend field names to backend expected names
    const backendContactInfo = {
      name: contactInfo.contact_name,
      contact_email: contactInfo.contact_email,
      company: contactInfo.company,
      position: contactInfo.position,
      relationship: contactInfo.relationship
    }

    console.log('🔥 createReferralRequest - Processed job ID:', processedJobId)
    console.log('🔥 createReferralRequest - Mapped contact info:', backendContactInfo)

    return apiCall('/create-request', {
      method: 'POST',
      body: JSON.stringify({
        job_id: processedJobId,
        contact_info: backendContactInfo
      }),
    });
  },

  // Update draft
  updateDraft: async (
    draftId: string,
    updates: { subject?: string; email_body?: string }
  ): Promise<EmailDraft> => {
    return apiCall(`/drafts/${draftId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  },

  // Send email (mark as sent)
  sendEmail: async (draftId: string): Promise<{ success: boolean; message: string; sent_id: string }> => {
    return apiCall(`/send/${draftId}`, {
      method: 'POST',
    });
  },

  // Get user contacts
  getContacts: async (
    limit = 50,
    offset = 0
  ): Promise<{ contacts: ReferralContact[]; total_count: number }> => {
    return apiCall(`/contacts?limit=${limit}&offset=${offset}`);
  },

  // Get user drafts
  getDrafts: async (
    jobId: string | null = null,
    limit = 20,
    offset = 0
  ): Promise<{ drafts: EmailDraft[]; total_count: number }> => {
    const jobParam = jobId ? `&job_id=${jobId}` : '';
    return apiCall(`/drafts?limit=${limit}&offset=${offset}${jobParam}`);
  },

  // Get analytics
  getAnalytics: async (): Promise<ReferralAnalytics> => {
    return apiCall('/analytics');
  },

  // Get quick stats
  getStats: async (): Promise<ReferralStats> => {
    return apiCall('/stats');
  },

  // Mark response received
  markResponseReceived: async (
    sentId: string,
    responseDate?: string
  ): Promise<{ success: boolean; message: string }> => {
    return apiCall(`/responses/${sentId}/mark-received`, {
      method: 'POST',
      body: JSON.stringify({
        response_date: responseDate
      }),
    });
  },

  // Get available templates
  getTemplates: async (): Promise<{
    templates: Record<string, {
      name: string;
      focus: string;
      value_prop: string;
      keywords: string[];
    }>;
    default: string;
  }> => {
    return apiCall('/templates');
  },

  // Delete contact
  deleteContact: async (contactId: string): Promise<{ success: boolean; message: string }> => {
    return apiCall(`/contacts/${contactId}`, {
      method: 'DELETE',
    });
  },

  // Delete draft
  deleteDraft: async (draftId: string): Promise<{ success: boolean; message: string }> => {
    return apiCall(`/drafts/${draftId}`, {
      method: 'DELETE',
    });
  },
};

// React hooks for error handling
export const isReferralAPIError = (error: unknown): error is ReferralAPIError => {
  return error instanceof ReferralAPIError;
};

export const isInsufficientDataError = (error: unknown): boolean => {
  return isReferralAPIError(error) && error.message.includes('Insufficient');
};