import {
    ReferralDetailedInfo,
    ReferralDetailedListResponse,
    ReferralFilters,
    ReferralContactInfo,
    ReferralDraftUpdate,
    ReferralPreferencePayload
} from './types';
import { makeAPIRequest, getAuthHeaders, API_BASE_URL } from './config';

export const referralApi = {
    // Get all sent referrals with detailed information
    getSentReferrals: async (filters?: ReferralFilters): Promise<ReferralDetailedListResponse> => {
        const queryParams = new URLSearchParams();

        if (filters?.page) queryParams.append('page', filters.page.toString());
        if (filters?.page_size) queryParams.append('page_size', filters.page_size.toString());
        if (filters?.company_filter) queryParams.append('company_filter', filters.company_filter);
        if (filters?.date_from) queryParams.append('date_from', filters.date_from);
        if (filters?.date_to) queryParams.append('date_to', filters.date_to);

        const url = `/api/v1/referral/sent${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
        return makeAPIRequest<ReferralDetailedListResponse>(url);
    },

    // Get referral analytics
    getAnalytics: async () => {
        const url = '/api/v1/referral/analytics';
        return makeAPIRequest(url);
    },

    // Get referral stats for dashboard
    getStats: async () => {
        const url = '/api/v1/referral/stats';
        return makeAPIRequest(url);
    },

    // Mark response as received
    markResponseReceived: async (sentId: number, responseDate?: string) => {
        const body: { response_date?: string } = {};
        if (responseDate) body.response_date = responseDate;

        const url = `/api/v1/referral/responses/${sentId}/mark-received`;
        return makeAPIRequest(url, {
            method: 'POST',
            body: JSON.stringify(body),
        });
    },

    // Generate referral email (preview only)
    generateEmail: async (jobId: string | number, contactInfo: ReferralContactInfo) => {
        const url = '/api/v1/referral/generate-email';
        return makeAPIRequest(url, {
            method: 'POST',
            body: JSON.stringify({
                job_id: parseInt(String(jobId)),
                contact_info: contactInfo,
            }),
        });
    },

    // Create referral request (save draft and contact)
    createRequest: async (jobId: string | number, contactInfo: ReferralContactInfo) => {
        const url = '/api/v1/referral/create-request';
        return makeAPIRequest(url, {
            method: 'POST',
            body: JSON.stringify({
                job_id: parseInt(String(jobId)),
                contact_info: contactInfo,
            }),
        });
    },

    // Update draft email
    updateDraft: async (draftId: string, updates: ReferralDraftUpdate) => {
        const url = `/api/v1/referral/drafts/${draftId}`;
        return makeAPIRequest(url, {
            method: 'PUT',
            body: JSON.stringify(updates),
        });
    },

    // Send referral email (mark as sent)
    sendEmail: async (draftId: string) => {
        const url = `/api/v1/referral/send/${draftId}`;
        return makeAPIRequest(url, { method: 'POST' });
    },
};

// Referral Templates API
export const referralTemplatesAPI = {
    // Generate a new referral template
    generate: async (data: {
        contact_info: {
            name: string;
            email?: string;
            company: string;
            position?: string;
            company_size?: string;
            linkedin_url?: string;
        };
        job_info: {
            job_id?: string;
            title: string;
            company: string;
            industry?: string;
            level?: string;
            description?: string;
            user_background?: string;
        };
        user_preferences?: {
            preferred_tone?: string;
            preferred_length?: string;
            include_resume?: boolean;
            include_portfolio?: boolean;
        };
    }) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/referral-templates/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeaders()
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                const errorData = await response.text();
                console.error('Referral template API error:', {
                    status: response.status,
                    statusText: response.statusText,
                    body: errorData
                });

                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                if (response.status === 429) {
                    errorMessage = "Rate limit exceeded. Please wait before trying again.";
                } else if (response.status === 401) {
                    errorMessage = "Authentication error. Please refresh the page and try again.";
                } else if (response.status === 500) {
                    errorMessage = "Server error. Our team has been notified.";
                } else if (errorData.includes('Failed to fetch')) {
                    errorMessage = "Network error. Please check your connection and try again.";
                }

                throw new Error(errorMessage);
            }

            return response.json();
        } catch (error) {
            console.error('Referral template generation failed:', error);
            throw error;
        }
    },

    // Get user's templates
    getTemplates: async (limit: number = 20, offset: number = 0) => {
        const url = `/api/v1/referral-templates/?limit=${limit}&offset=${offset}`;
        return makeAPIRequest(url);
    },

    // Get template statistics
    getStats: async () => {
        const url = '/api/v1/referral-templates/stats';
        return makeAPIRequest(url);
    },

    // Get specific template
    getTemplate: async (templateId: string) => {
        const url = `/api/v1/referral-templates/${templateId}`;
        return makeAPIRequest(url);
    },

    // Mark template as sent
    markSent: async (templateId: string) => {
        const url = `/api/v1/referral-templates/${templateId}/mark-sent`;
        return makeAPIRequest(url, { method: 'POST' });
    },

    // Record feedback
    recordFeedback: async (templateId: string, feedback: {
        got_response: boolean;
        response_type?: string;
        response_quality_score?: number;
        user_satisfaction_score?: number;
        feedback_notes?: string;
    }) => {
        const url = `/api/v1/referral-templates/${templateId}/feedback`;
        return makeAPIRequest(url, {
            method: 'POST',
            body: JSON.stringify(feedback),
        });
    },

    // Delete template
    deleteTemplate: async (templateId: string) => {
        const url = `/api/v1/referral-templates/${templateId}`;
        return makeAPIRequest(url, { method: 'DELETE' });
    },

    // Get user preferences
    getPreferences: async () => {
        const url = '/api/v1/referral-templates/preferences/current';
        return makeAPIRequest(url);
    },

    // Update user preferences
    updatePreferences: async (preferences: ReferralPreferencePayload) => {
        const url = '/api/v1/referral-templates/preferences';
        return makeAPIRequest(url, {
            method: 'PUT',
            body: JSON.stringify(preferences),
        });
    },
};