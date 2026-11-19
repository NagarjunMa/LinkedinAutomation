import { UserProfile, UserSettings, ProfileChangeHistory } from './types';
import { APIError, makeAPIRequest } from './config';
import type { components } from '@/generated/api/types';

type JobPreferencesUpdate = components['schemas']['JobPreferencesUpdate'];
type JobPreferencesResponse = components['schemas']['JobPreferencesResponse'];

function isMissingSettings(error: unknown): boolean {
    return error instanceof APIError && error.status === 404 && error.data === 'Settings not found';
}

export const profileApi = {
    // Get user profile with statistics
    getProfile: async (userId: string): Promise<UserProfile> => {
        const url = `/api/v1/user-profiles/${userId}`;
        return makeAPIRequest<UserProfile>(url, { expectedUserId: userId, cache: 'no-store' });
    },

    // Create user profile
    createProfile: async (userId: string, profileData: Partial<UserProfile>): Promise<UserProfile> => {
        const url = `/api/v1/user-profiles/${userId}`;
        return makeAPIRequest<UserProfile>(url, {
            method: 'POST',
            body: JSON.stringify(profileData),
        });
    },

    // Update user profile
    updateProfile: async (userId: string, profileData: Partial<UserProfile>): Promise<UserProfile> => {
        const url = `/api/v1/user-profiles/${userId}`;
        return makeAPIRequest<UserProfile>(url, {
            method: 'PUT',
            body: JSON.stringify(profileData),
        });
    },

    savePreferences: (userId: string, preferences: JobPreferencesUpdate): Promise<JobPreferencesResponse> =>
        makeAPIRequest(`/api/v1/user-profiles/${userId}/preferences`, {
            method: 'PUT',
            body: JSON.stringify(preferences),
            expectedUserId: userId,
        }),

    getSettings: async (userId: string, signal?: AbortSignal): Promise<UserSettings | null> => {
        const url = `/api/v1/user-profiles/${userId}/settings`;
        try {
            return await makeAPIRequest<UserSettings>(url, { expectedUserId: userId, cache: 'no-store', signal });
        } catch (error) {
            if (isMissingSettings(error)) return null;
            throw error;
        }
    },

    saveAnalytics: async (userId: string, value: 'enabled' | 'disabled'): Promise<UserSettings> => {
        const url = `/api/v1/user-profiles/${userId}/settings`;
        const body = JSON.stringify({ analytics_enabled: value });
        const update = () => makeAPIRequest<UserSettings>(`${url}/privacy`, {
            method: 'PUT', body, expectedUserId: userId,
        });
        try {
            return await update();
        } catch (error) {
            if (!isMissingSettings(error)) throw error;
        }
        try {
            return await makeAPIRequest<UserSettings>(url, { method: 'POST', body, expectedUserId: userId });
        } catch (error) {
            // Another tab may have created settings since the initial update.
            if (!(error instanceof APIError && error.status === 409 && error.data === 'Settings already exist')) throw error;
            return update();
        }
    },

    // Update user settings
    updateSettings: async (userId: string, settingsData: Partial<UserSettings>): Promise<UserSettings> => {
        const url = `/api/v1/user-profiles/${userId}/settings`;
        return makeAPIRequest<UserSettings>(url, {
            method: 'PUT',
            body: JSON.stringify(settingsData),
        });
    },

    // Update notification settings
    updateNotifications: async (userId: string, notifications: Partial<UserSettings['email_notifications']>): Promise<UserSettings> => {
        const url = `/api/v1/user-profiles/${userId}/settings/notifications`;
        return makeAPIRequest<UserSettings>(url, {
            method: 'PUT',
            body: JSON.stringify(notifications),
        });
    },

    // Update email tracking settings
    updateEmailTracking: async (userId: string, emailSettings: {
        email_forwarding_enabled?: string;
        forwarding_address?: string;
        notification_frequency?: string
    }): Promise<UserSettings> => {
        const url = `/api/v1/user-profiles/${userId}/settings/email-tracking`;
        return makeAPIRequest<UserSettings>(url, {
            method: 'PUT',
            body: JSON.stringify(emailSettings),
        });
    },

    // Update privacy settings
    updatePrivacy: async (userId: string, privacySettings: {
        data_retention_days?: number;
        analytics_enabled?: string
    }): Promise<UserSettings> => {
        const url = `/api/v1/user-profiles/${userId}/settings/privacy`;
        return makeAPIRequest<UserSettings>(url, {
            method: 'PUT',
            body: JSON.stringify(privacySettings),
        });
    },

    // Get profile change history
    getChangeHistory: async (userId: string, limit: number = 50): Promise<ProfileChangeHistory[]> => {
        const url = `/api/v1/user-profiles/${userId}/change-history?limit=${limit}`;
        return makeAPIRequest<ProfileChangeHistory[]>(url);
    },
};
