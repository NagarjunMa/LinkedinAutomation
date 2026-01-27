// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper function to get authentication headers
export function getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    };

    // Add authentication if available
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
}

// API Error handling
export class APIError extends Error {
    constructor(
        message: string,
        public status?: number,
        public statusText?: string,
        public data?: any
    ) {
        super(message);
        this.name = 'APIError';
    }
}

// Generic API request handler with error handling
export async function makeAPIRequest<T>(
    url: string,
    options?: RequestInit
): Promise<T> {
    try {
        const response = await fetch(`${API_BASE_URL}${url}`, {
            headers: getAuthHeaders(),
            ...options,
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new APIError(
                `API request failed: ${response.status} ${response.statusText}`,
                response.status,
                response.statusText,
                errorText
            );
        }

        return response.json();
    } catch (error) {
        if (error instanceof APIError) {
            throw error;
        }
        throw new APIError(`Network error: ${error}`);
    }
}

export { API_BASE_URL };