import { createClient } from '@/lib/supabase';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function getAuthHeaders(): Promise<Record<string, string>> {
    const headers: Record<string, string> = {};

    try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();

        if (session?.access_token) {
            headers['Authorization'] = `Bearer ${session.access_token}`;
        }
    } catch (error) {
        console.warn('Failed to get Supabase session:', error);
    }

    return headers;
}

function isFormDataBody(body: BodyInit | null | undefined): body is FormData {
    return typeof FormData !== 'undefined' && body instanceof FormData;
}

async function buildRequestHeaders(options: RequestInit): Promise<Headers> {
    const headers = new Headers(options.headers);

    // Authorization is owned by the current Supabase session, not individual callers.
    headers.delete('Authorization');
    const authHeaders = await getAuthHeaders();
    if (authHeaders.Authorization) {
        headers.set('Authorization', authHeaders.Authorization);
    }

    if (isFormDataBody(options.body)) {
        // The browser must include the generated multipart boundary.
        headers.delete('Content-Type');
    } else if (typeof options.body === 'string' && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
    }

    return headers;
}

// API Error handling
export class APIError extends Error {
    constructor(
        message: string,
        public status?: number,
        public statusText?: string,
        public data?: unknown
    ) {
        super(message);
        this.name = 'APIError';
    }
}

type ResponseParser<T> = (response: Response) => Promise<T>;

async function parseJsonResponse<T>(response: Response): Promise<T> {
    if (response.status === 204) {
        return undefined as T;
    }
    return response.json() as Promise<T>;
}

export async function makeAPIRequest<T>(
    url: string,
    options: RequestInit = {},
    parseResponse: ResponseParser<T> = parseJsonResponse,
): Promise<T> {
    try {
        const headers = await buildRequestHeaders(options);
        const response = await fetch(`${API_BASE_URL}${url}`, {
            ...options,
            headers,
        });

        if (!response.ok) {
            let detail: unknown = await response.text();
            try {
                const parsed = JSON.parse(String(detail));
                detail = parsed.detail ?? parsed;
            } catch { /* not JSON — keep text */ }
            const msg = typeof detail === 'string' ? detail : JSON.stringify(detail);
            throw new APIError(msg, response.status, response.statusText, detail);
        }

        return parseResponse(response);
    } catch (error) {
        if (error instanceof APIError) {
            throw error;
        }
        throw new APIError(`Network error: ${error}`);
    }
}
