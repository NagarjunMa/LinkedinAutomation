import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const { getSession } = vi.hoisted(() => ({
  getSession: vi.fn(),
}));

vi.mock('@/lib/supabase', () => ({
  createClient: () => ({
    auth: { getSession },
  }),
}));

import { APIError, getAuthHeaders, makeAPIRequest } from '@/app/lib/api/config';

async function rejectedRequest(url: string, options?: RequestInit): Promise<APIError> {
  try {
    await makeAPIRequest(url, options);
  } catch (error) {
    if (error instanceof APIError) return error;
    throw error;
  }
  throw new Error('Expected APIError');
}

describe('frontend API authentication boundary', () => {
  beforeEach(() => {
    getSession.mockResolvedValue({
      data: { session: { access_token: 'session-token' } },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it('returns only the bearer token from the current Supabase session', async () => {
    await expect(getAuthHeaders()).resolves.toEqual({
      Authorization: 'Bearer session-token',
    });
  });

  it('preserves caller headers while keeping session authorization authoritative', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    await makeAPIRequest<{ ok: boolean }>('/api/v1/test', {
      method: 'POST',
      headers: {
        authorization: 'Bearer caller-token',
        'X-Request-ID': 'request-123',
      },
      body: JSON.stringify({ value: 1 }),
    });

    const options = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = new Headers(options.headers);
    expect(headers.get('Authorization')).toBe('Bearer session-token');
    expect(headers.get('X-Request-ID')).toBe('request-123');
    expect(headers.get('Content-Type')).toBe('application/json');
  });

  it('lets the browser create the multipart content type boundary', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ resume_document_id: 'resume-1' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);
    const body = new FormData();
    body.append('file', new File(['resume'], 'resume.pdf', { type: 'application/pdf' }));

    await makeAPIRequest('/api/v1/resumes/upload', {
      method: 'POST',
      headers: {
        'Content-Type': 'multipart/form-data',
        'X-Upload-ID': 'upload-123',
      },
      body,
    });

    const options = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = new Headers(options.headers);
    expect(headers.has('Content-Type')).toBe(false);
    expect(headers.get('Authorization')).toBe('Bearer session-token');
    expect(headers.get('X-Upload-ID')).toBe('upload-123');
    expect(options.body).toBe(body);
  });

  it('does not invent authorization when there is no session', async () => {
    getSession.mockResolvedValueOnce({ data: { session: null } });
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    await makeAPIRequest('/api/v1/public');

    const options = fetchMock.mock.calls[0][1] as RequestInit;
    expect(new Headers(options.headers).has('Authorization')).toBe(false);
  });

  it('supports authenticated binary responses through the same client', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response('%PDF-test', {
        status: 200,
        headers: { 'Content-Type': 'application/pdf' },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    const result = await makeAPIRequest<Blob>(
      '/api/v1/exports/export-1/download',
      { method: 'GET' },
      (response) => response.blob(),
    );

    expect(result.type).toBe('application/pdf');
    const options = fetchMock.mock.calls[0][1] as RequestInit;
    expect(new Headers(options.headers).get('Authorization')).toBe('Bearer session-token');
  });

  it('retains structured API error details', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: 'insufficient credits' }), {
          status: 402,
          statusText: 'Payment Required',
        }),
      ),
    );

    const request = makeAPIRequest('/api/v1/exports', {
      method: 'POST',
      body: JSON.stringify({ resume_version_id: 'version-1' }),
    });

    await expect(request).rejects.toMatchObject({
      name: 'APIError',
      message: 'insufficient credits',
      status: 402,
      data: 'insufficient credits',
    } satisfies Partial<APIError>);
  });

  it('retains validated correlation metadata without retaining the error payload or retrying', async () => {
    const requestId = '7018a0a3-9431-4bc4-b4ce-719a579588a1';
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      code: 'resource_not_found', message: 'Resource not found.', detail: 'Resource not found.',
      request_id: requestId, retryable: false, private: 'private-sentinel',
    }), { status: 404, headers: { 'X-Request-ID': requestId } }));
    vi.stubGlobal('fetch', fetchMock);
    const error = await rejectedRequest('/api/v1/resumes/doc');
    expect(error).toMatchObject({ code: 'resource_not_found', requestId, retryable: false, status: 404, message: 'Resource not found.' });
    expect(error.data).toBeUndefined();
    expect(JSON.stringify(error)).not.toContain('private-sentinel');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it.each(['private-sentinel', JSON.stringify({detail: {input: 'private-sentinel'}}), JSON.stringify({code: 'internal_error', message: 'private-sentinel', request_id: 'bad', retryable: 'yes'})])('sanitizes malformed private-workflow errors: %s', async body => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(body, { status: 500 })));
    const error = await rejectedRequest('/api/v1/jd/analyze', {method: 'POST'});
    expect(error).toBeInstanceOf(APIError);
    expect(error.message).toBe('Request failed. Please try again when ready.');
    expect(error.data).toBeUndefined();
    expect(JSON.stringify(error)).not.toContain('private-sentinel');
  });

  it('does not render arbitrary text even in a structurally valid envelope', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      code: 'internal_error', message: 'private-sentinel', detail: 'private-sentinel',
      request_id: '7018a0a3-9431-4bc4-b4ce-719a579588a1', retryable: false,
    }), {status: 500})));
    const error = await rejectedRequest('/api/v1/jd/analyze');
    expect(error.message).toBe('Request failed. Please try again when ready.');
    expect(JSON.stringify(error)).not.toContain('private-sentinel');
  });

  it('bounds error reads and retains only a valid header request ID', async () => {
    const cancel = vi.fn();
    const requestId = '7018a0a3-9431-4bc4-b4ce-719a579588a1';
    const stream = new ReadableStream({start(controller) {controller.enqueue(new Uint8Array(8193));}, cancel});
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(stream, {status: 500, headers: {'X-Request-ID': requestId}})));
    const error = await rejectedRequest('/api/v1/resumes');
    expect(error.requestId).toBe(requestId);
    expect(error.code).toBeUndefined();
    expect(cancel).toHaveBeenCalledOnce();
  });

  it('does not expose network exception details for private workflows', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('private-sentinel')));
    const error = await rejectedRequest('/api/v1/jd/analyze');
    expect(error.message).toBe('Network request failed. Please try again when ready.');
    expect(error.data).toBeUndefined();
  });

  it('rejects conflicting header/body correlation IDs', async () => {
    const requestId = '7018a0a3-9431-4bc4-b4ce-719a579588a1';
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      code: 'internal_error', message: 'Failure', detail: 'Failure',
      request_id: 'a1b525d3-7920-4bf3-a62f-359460913dcd', retryable: false,
    }), {status: 500, headers: {'X-Request-ID': requestId}})));
    const error = await rejectedRequest('/api/v1/resumes/doc');
    expect(error.requestId).toBe(requestId);
    expect(error.code).toBeUndefined();
  });
});
