// Enhanced API Error Handling with Retry Logic and User-Friendly Messages

export interface ApiError extends Error {
  status?: number;
  code?: string;
  details?: unknown;
  timestamp?: string;
  requestId?: string;
  retryable?: boolean;
}

export interface ApiErrorResponse {
  error: string;
  message: string;
  status_code: number;
  detail?: unknown;
  request_id?: string;
}

export interface RetryConfig {
  maxRetries: number;
  initialDelay: number;
  maxDelay: number;
  backoffFactor: number;
  retryCondition?: (error: ApiError) => boolean;
}

export interface RequestConfig {
  timeout?: number;
  retries?: Partial<RetryConfig>;
  showErrorToast?: boolean;
  silentErrors?: number[];
  headers?: Record<string, string>;
}

type ErrorLogEntry = {
  timestamp?: string;
  message: string;
  status?: number;
  code?: string;
  url?: string;
  userAgent: string;
  requestId?: string;
};

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  initialDelay: 1000,
  maxDelay: 10000,
  backoffFactor: 2,
  retryCondition: (error: ApiError) => {
    // Retry on network errors, 5xx errors, and 429 (rate limit)
    return !error.status || error.status >= 500 || error.status === 429;
  }
};

export class ApiErrorHandler {
  private static instance: ApiErrorHandler;
  private errorListeners: Array<(error: ApiError) => void> = [];

  static getInstance(): ApiErrorHandler {
    if (!ApiErrorHandler.instance) {
      ApiErrorHandler.instance = new ApiErrorHandler();
    }
    return ApiErrorHandler.instance;
  }

  // Add error listener for global error handling
  addErrorListener(listener: (error: ApiError) => void): () => void {
    this.errorListeners.push(listener);
    return () => {
      const index = this.errorListeners.indexOf(listener);
      if (index > -1) {
        this.errorListeners.splice(index, 1);
      }
    };
  }

  // Create enhanced API error from response
  async createApiError(response: Response, requestUrl?: string): Promise<ApiError> {
    let errorData: ApiErrorResponse;

    try {
      errorData = await response.json();
    } catch {
      errorData = {
        error: 'Network Error',
        message: 'Failed to connect to the server',
        status_code: response.status || 0
      };
    }

    const error = new Error(this.getUserFriendlyMessage(errorData)) as ApiError;
    error.name = 'ApiError';
    error.status = response.status;
    error.code = errorData.error;
    error.details = errorData.detail;
    error.timestamp = new Date().toISOString();
    error.requestId = errorData.request_id;
    error.retryable = this.isRetryableError(error);

    // Log error details
    this.logError(error, requestUrl);

    // Notify listeners
    this.errorListeners.forEach(listener => {
      try {
        listener(error);
      } catch (listenerError) {
        console.error('Error in error listener:', listenerError);
      }
    });

    return error;
  }

  // Get user-friendly error messages
  private getUserFriendlyMessage(errorData: ApiErrorResponse): string {
    const status = errorData.status_code;
    const defaultMessage = errorData.message || 'An unexpected error occurred';

    // Handle specific error codes/statuses
    switch (status) {
      case 400:
        return 'Invalid request. Please check your input and try again.';
      case 401:
        return 'Authentication required. Please log in and try again.';
      case 403:
        return 'You don\'t have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 409:
        return errorData.message || 'This action conflicts with the current state. Please refresh and try again.';
      case 422:
        return 'Invalid data provided. Please check your input.';
      case 429:
        return 'Too many requests. Please wait a moment and try again.';
      case 500:
        return 'Server error. Please try again later.';
      case 502:
      case 503:
      case 504:
        return 'Service temporarily unavailable. Please try again later.';
      default:
        if (status >= 500) {
          return 'Server error. Please try again later.';
        }
        return defaultMessage;
    }
  }

  // Check if error is retryable
  private isRetryableError(error: ApiError): boolean {
    if (!error.status) return true; // Network errors are retryable

    // Retryable status codes
    const retryableStatuses = [429, 500, 502, 503, 504];
    return retryableStatuses.includes(error.status);
  }

  // Enhanced fetch with retry logic
  async fetchWithRetry<T>(
    url: string,
    options: RequestInit & RequestConfig = {}
  ): Promise<T> {
    const {
      timeout = 30000,
      retries = {},
      silentErrors = [],
      ...fetchOptions
    } = options;

    const retryConfig = { ...DEFAULT_RETRY_CONFIG, ...retries };

    // Add timeout to fetch
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    const fetchWithTimeout = async (): Promise<Response> => {
      try {
        const response = await fetch(url, {
          ...fetchOptions,
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        return response;
      } catch (error) {
        clearTimeout(timeoutId);
        throw error;
      }
    };

    let lastError: ApiError = new Error('Unknown error') as ApiError;

    for (let attempt = 0; attempt <= retryConfig.maxRetries; attempt++) {
      try {
        const response = await fetchWithTimeout();

        if (!response.ok) {
          const apiError = await this.createApiError(response, url);

          // Don't show toast for silent errors
          if (silentErrors.includes(response.status)) {
            apiError.retryable = false;
          }

          // Check if we should retry
          if (attempt < retryConfig.maxRetries &&
              retryConfig.retryCondition &&
              retryConfig.retryCondition(apiError)) {
            lastError = apiError;

            // Calculate delay with exponential backoff
            const delay = Math.min(
              retryConfig.initialDelay * Math.pow(retryConfig.backoffFactor, attempt),
              retryConfig.maxDelay
            );

            console.warn(`API request failed (attempt ${attempt + 1}/${retryConfig.maxRetries + 1}), retrying in ${delay}ms:`, apiError.message);
            await this.delay(delay);
            continue;
          }

          throw apiError;
        }

        // Success - parse response
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          return await response.json();
        } else {
          return await response.text() as unknown as T;
        }

      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          lastError = new Error('Request timeout') as ApiError;
          lastError.name = 'ApiError';
          lastError.status = 408;
          lastError.retryable = true;
        } else if (error instanceof Error && error.name === 'ApiError') {
          lastError = error as ApiError;
        } else {
          lastError = new Error('Network error') as ApiError;
          lastError.name = 'ApiError';
          lastError.retryable = true;
        }

        // Check if we should retry
        if (attempt < retryConfig.maxRetries &&
            retryConfig.retryCondition &&
            retryConfig.retryCondition(lastError)) {

          const delay = Math.min(
            retryConfig.initialDelay * Math.pow(retryConfig.backoffFactor, attempt),
            retryConfig.maxDelay
          );

          console.warn(`API request failed (attempt ${attempt + 1}/${retryConfig.maxRetries + 1}), retrying in ${delay}ms:`, lastError.message);
          await this.delay(delay);
          continue;
        }

        // All retries exhausted
        break;
      }
    }

    throw lastError;
  }

  // Utility methods
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private logError(error: ApiError, requestUrl?: string): void {
    const logData = {
      timestamp: error.timestamp,
      message: error.message,
      status: error.status,
      code: error.code,
      url: requestUrl,
      userAgent: navigator.userAgent,
      requestId: error.requestId,
    };

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('API Error:', logData);
    }

    // Store in localStorage for debugging
    try {
      const errorLogs = JSON.parse(localStorage.getItem('api_error_logs') || '[]');
      errorLogs.push(logData);

      // Keep only last 20 errors
      if (errorLogs.length > 20) {
        errorLogs.splice(0, errorLogs.length - 20);
      }

      localStorage.setItem('api_error_logs', JSON.stringify(errorLogs));
    } catch (storageError) {
      console.error('Failed to store error log:', storageError);
    }
  }

  // Get error logs for debugging
  getErrorLogs(): ErrorLogEntry[] {
    try {
      return JSON.parse(localStorage.getItem('api_error_logs') || '[]');
    } catch {
      return [];
    }
  }

  // Clear error logs
  clearErrorLogs(): void {
    localStorage.removeItem('api_error_logs');
  }
}

// Singleton instance
export const apiErrorHandler = ApiErrorHandler.getInstance();

// React hook for error handling
export const useApiErrorHandler = () => {
  const handleError = (error: ApiError) => {
    // This can be used to show toast notifications or handle errors globally
    console.error('API Error handled:', error);
  };

  return {
    handleError,
    clearLogs: () => apiErrorHandler.clearErrorLogs(),
    getLogs: () => apiErrorHandler.getErrorLogs(),
  };
};

// Enhanced API wrapper functions
export const apiRequest = {
  get: <T>(url: string, config?: RequestConfig) =>
    apiErrorHandler.fetchWithRetry<T>(url, { ...config, method: 'GET' }),

  post: <T>(url: string, data?: Record<string, unknown>, config?: RequestConfig) =>
    apiErrorHandler.fetchWithRetry<T>(url, {
      ...config,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...config?.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
    }),

  put: <T>(url: string, data?: Record<string, unknown>, config?: RequestConfig) =>
    apiErrorHandler.fetchWithRetry<T>(url, {
      ...config,
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...config?.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
    }),

  delete: <T>(url: string, config?: RequestConfig) =>
    apiErrorHandler.fetchWithRetry<T>(url, { ...config, method: 'DELETE' }),

  patch: <T>(url: string, data?: Record<string, unknown>, config?: RequestConfig) =>
    apiErrorHandler.fetchWithRetry<T>(url, {
      ...config,
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...config?.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
    }),
};