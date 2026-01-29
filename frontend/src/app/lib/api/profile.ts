import { UserProfile, UserSettings, ProfileChangeHistory } from './types';
import { makeAPIRequest } from './config';

export const profileApi = {
    // Get user profile with statistics
    getProfile: async (userId: string): Promise<UserProfile> => {
        const url = `/api/v1/user-profiles/${userId}`;
        return makeAPIRequest<UserProfile>(url);
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

    // Get user settings
    getSettings: async (userId: string): Promise<UserSettings> => {
        const url = `/api/v1/user-profiles/${userId}/settings`;
        return makeAPIRequest<UserSettings>(url);
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