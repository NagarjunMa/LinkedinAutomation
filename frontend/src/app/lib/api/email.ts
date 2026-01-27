import { makeAPIRequest } from './config';

// Email Agent API endpoints
export const emailAgentApi = {
    // Get configuration status
    getConfigStatus: async () => {
        const url = '/api/v1/email-agent/config/status';
        return makeAPIRequest(url);
    },

    // Connect Gmail
    connectGmail: async (userId: string, userEmail?: string) => {
        const url = '/api/v1/email-agent/connect';
        return makeAPIRequest(url, {
            method: 'POST',
            body: JSON.stringify({ user_id: userId, user_email: userEmail })
        });
    },

    // Get Gmail status
    getGmailStatus: async (userId: string) => {
        const url = `/api/v1/email-agent/status/${userId}`;
        return makeAPIRequest(url);
    },

    // Process emails
    processEmails: async (userId: string, userEmail?: string) => {
        const body: Record<string, string> = {};
        if (userEmail) {
            body.user_email = userEmail;
        }

        const url = `/api/v1/email-agent/process/${userId}`;
        return makeAPIRequest(url, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    },

    // Disconnect Gmail
    disconnectGmail: async (userId: string) => {
        const url = `/api/v1/email-agent/disconnect/${userId}`;
        return makeAPIRequest(url, { method: 'DELETE' });
    },

    // Get email summary
    getEmailSummary: async (userId: string) => {
        const url = `/api/v1/email-agent/summary/${userId}`;
        return makeAPIRequest(url);
    },

    // Get email events
    getEmailEvents: async (userId: string, limit = 50, offset = 0, emailType?: string) => {
        const params = new URLSearchParams();
        if (limit) params.append('limit', limit.toString());
        if (offset) params.append('offset', offset.toString());
        if (emailType) params.append('email_type', emailType);

        const url = `/api/v1/email-agent/events/${userId}?${params}`;
        return makeAPIRequest(url);
    },

    // Mark event as reviewed
    markEventReviewed: async (eventId: number) => {
        const url = `/api/v1/email-agent/events/${eventId}/review`;
        return makeAPIRequest(url, { method: 'POST' });
    }
};