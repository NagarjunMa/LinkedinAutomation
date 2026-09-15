import { createClient } from '@/lib/supabase';
import { z } from 'zod';
import type { components } from '@/generated/api/types';

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
    code?: ErrorEnvelope['code'];
    requestId?: string;
    retryable?: boolean;
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

type ErrorEnvelope = components['schemas']['APIErrorEnvelope'];
// UI-owned copy deliberately ignores server prose, even for valid JSON.
const errorMessages = {
    invalid_request: 'Check the request and try again.',
    authentication_required: 'Sign in to continue.',
    insufficient_credits: 'Insufficient credits.',
    access_denied: 'Access is unavailable for this request.',
    resource_not_found: 'Resource not found.',
    method_not_allowed: 'Request method not allowed.',
    resource_conflict: 'The request conflicts with the current state.',
    request_too_large: 'The uploaded file or request is too large.',
    unsupported_media_type: 'This file or content type is not supported.',
    rate_limited: 'Request limit reached. Please wait before trying again.',
    service_unavailable: 'The service is currently unavailable.',
    internal_error: 'Request failed. Please try again when ready.',
} satisfies Record<ErrorEnvelope['code'], string>;
const uuid = z.string().uuid();
const errorEnvelope = z.object({
    code: z.enum(['invalid_request', 'authentication_required', 'insufficient_credits',
        'access_denied', 'resource_not_found', 'method_not_allowed', 'resource_conflict',
        'request_too_large', 'unsupported_media_type', 'rate_limited', 'service_unavailable', 'internal_error']),
    message: z.string().min(1).max(200),
    detail: z.string().max(200),
    request_id: uuid,
    retryable: z.boolean(),
}) satisfies z.ZodType<ErrorEnvelope>;

function isWorkflowPath(url: string): boolean {
    return /^\/api\/v1\/(resumes|jd)(?:\/|\?|$)/.test(url);
}

async function workflowError(response: Response): Promise<APIError> {
    const fallback = new APIError('Request failed. Please try again when ready.', response.status);
    const headerId = uuid.safeParse(response.headers.get('X-Request-ID'));
    if (headerId.success) fallback.requestId = headerId.data;
    // Bound diagnostic reads independently from potentially large success payloads.
    const reader = response.body?.getReader();
    if (!reader) return fallback;
    let text = '';
    let bytes = 0;
    const decoder = new TextDecoder();
    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            bytes += value.byteLength;
            if (bytes > 8192) return fallback;
            text += decoder.decode(value, { stream: true });
        }
        const parsed = errorEnvelope.safeParse(JSON.parse(text + decoder.decode()));
        if (!parsed.success || (headerId.success && headerId.data !== parsed.data.request_id)) return fallback;
        const data = parsed.data;
        const error = new APIError(errorMessages[data.code], response.status);
        error.code = data.code;
        error.requestId = data.request_id;
        error.retryable = data.retryable;
        return error;
    } catch {
        return fallback;
    } finally {
        await reader.cancel().catch(() => undefined);
        reader.releaseLock();
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
            if (isWorkflowPath(url)) throw await workflowError(response);
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
        if (isWorkflowPath(url)) throw new APIError('Network request failed. Please try again when ready.');
        throw new APIError(`Network error: ${error}`);
    }
}
