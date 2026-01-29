/**
 * Frontend Remote Logger Service
 * Sends frontend errors to centralized backend logging system
 */

interface LogEntry {
  errorId: string;
  message: string;
  stack?: string;
  componentStack?: string;
  url: string;
  userAgent: string;
  userId?: string;
  sessionId?: string;
  level: 'error' | 'warn' | 'info' | 'debug';
  metadata?: Record<string, unknown>;
  timestamp: string;
}

interface LogResponse {
  success: boolean;
  message: string;
  processed: number;
  errors?: string[];
}

class RemoteLogger {
  private baseUrl: string;
  private queue: LogEntry[] = [];
  private isProcessing = false;
  private batchSize = 5;
  private flushInterval = 5000; // 5 seconds
  private maxRetries = 3;
  private retryDelay = 1000; // 1 second
  private flushTimer?: NodeJS.Timeout;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    // Start periodic flush
    this.startPeriodicFlush();

    // Flush on page unload
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        this.flushSync();
      });
    }
  }

  /**
   * Log an error to the remote service
   */
  async logError(
    error: Error,
    errorId: string,
    componentStack?: string,
    userId?: string,
    metadata?: Record<string, unknown>
  ): Promise<void> {
    if (typeof window === 'undefined') return;

    const logEntry: LogEntry = {
      errorId,
      message: error.message,
      stack: error.stack,
      componentStack,
      url: window.location.href,
      userAgent: navigator.userAgent,
      userId,
      sessionId: this.getSessionId(),
      level: 'error',
      metadata: {
        ...metadata,
        errorType: error.constructor.name,
        timestamp_client: Date.now()
      },
      timestamp: new Date().toISOString()
    };

    this.addToQueue(logEntry);
  }

  /**
   * Log a warning message
   */
  async logWarn(
    message: string,
    errorId: string,
    userId?: string,
    metadata?: Record<string, unknown>
  ): Promise<void> {
    if (typeof window === 'undefined') return;

    const logEntry: LogEntry = {
      errorId,
      message,
      url: window.location.href,
      userAgent: navigator.userAgent,
      userId,
      sessionId: this.getSessionId(),
      level: 'warn',
      metadata,
      timestamp: new Date().toISOString()
    };

    this.addToQueue(logEntry);
  }

  /**
   * Log an info message
   */
  async logInfo(
    message: string,
    errorId: string,
    userId?: string,
    metadata?: Record<string, unknown>
  ): Promise<void> {
    if (typeof window === 'undefined') return;

    const logEntry: LogEntry = {
      errorId,
      message,
      url: window.location.href,
      userAgent: navigator.userAgent,
      userId,
      sessionId: this.getSessionId(),
      level: 'info',
      metadata,
      timestamp: new Date().toISOString()
    };

    this.addToQueue(logEntry);
  }

  /**
   * Add log entry to queue and potentially trigger flush
   */
  private addToQueue(logEntry: LogEntry): void {
    this.queue.push(logEntry);

    // Auto-flush on critical errors or when queue is full
    if (logEntry.level === 'error' || this.queue.length >= this.batchSize) {
      this.flush();
    }
  }

  /**
   * Flush queued logs to backend (async)
   */
  private async flush(): Promise<void> {
    if (this.isProcessing || this.queue.length === 0) return;

    this.isProcessing = true;
    const logsToSend = this.queue.splice(0, this.batchSize);

    try {
      if (logsToSend.length === 1) {
        // Single log entry
        await this.sendSingleLog(logsToSend[0]);
      } else {
        // Batch send
        await this.sendBatchLogs(logsToSend);
      }
    } catch (error) {
      // On failure, put logs back in queue for retry (up to max retries)
      logsToSend.forEach(log => {
        const retryCount = (log.metadata?.retryCount as number || 0) + 1;
        if (retryCount <= this.maxRetries) {
          log.metadata = { ...log.metadata, retryCount };
          this.queue.unshift(log); // Add to front for priority
        } else {
          // Max retries reached, log to localStorage as fallback
          this.logToLocalStorage(log, 'max_retries_exceeded');
        }
      });

      console.warn('Failed to send logs to remote service:', error);
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * Synchronous flush for page unload
   */
  private flushSync(): void {
    if (this.queue.length === 0) return;

    try {
      // Use sendBeacon for reliable delivery on page unload
      if (navigator.sendBeacon) {
        const payload = JSON.stringify({
          logs: this.queue.splice(0, this.batchSize)
        });

        navigator.sendBeacon(
          `${this.baseUrl}/api/v1/logs/frontend/batch`,
          new Blob([payload], { type: 'application/json' })
        );
      }
    } catch (error) {
      console.warn('Failed to send logs on page unload:', error);
    }
  }

  /**
   * Send single log entry
   */
  private async sendSingleLog(logEntry: LogEntry): Promise<LogResponse> {
    const response = await this.makeRequest('/api/v1/logs/frontend', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(logEntry)
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Send batch of log entries
   */
  private async sendBatchLogs(logs: LogEntry[]): Promise<LogResponse> {
    const response = await this.makeRequest('/api/v1/logs/frontend/batch', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ logs })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Make HTTP request with timeout and error handling
   */
  private async makeRequest(endpoint: string, options: RequestInit): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new Error('Request timeout');
      }

      throw error;
    }
  }

  /**
   * Get or create session ID
   */
  private getSessionId(): string {
    if (typeof window === 'undefined') return 'server';

    let sessionId = sessionStorage.getItem('logging_session_id');
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      sessionStorage.setItem('logging_session_id', sessionId);
    }
    return sessionId;
  }

  /**
   * Fallback logging to localStorage
   */
  private logToLocalStorage(logEntry: LogEntry, reason: string): void {
    try {
      const logs = JSON.parse(localStorage.getItem('failed_remote_logs') || '[]');
      logs.push({
        ...logEntry,
        failureReason: reason,
        failedAt: new Date().toISOString()
      });

      // Keep only last 20 failed logs
      if (logs.length > 20) {
        logs.splice(0, logs.length - 20);
      }

      localStorage.setItem('failed_remote_logs', JSON.stringify(logs));
    } catch (error) {
      console.error('Failed to log to localStorage:', error);
    }
  }

  /**
   * Start periodic flush timer
   */
  private startPeriodicFlush(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }

    this.flushTimer = setInterval(() => {
      this.flush();
    }, this.flushInterval);
  }

  /**
   * Stop the logger and flush remaining logs
   */
  public async stop(): Promise<void> {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = undefined;
    }

    // Flush any remaining logs
    await this.flush();
  }

  /**
   * Get failed logs from localStorage for debugging
   */
  public getFailedLogs(): unknown[] {
    try {
      return JSON.parse(localStorage.getItem('failed_remote_logs') || '[]');
    } catch {
      return [];
    }
  }

  /**
   * Clear failed logs from localStorage
   */
  public clearFailedLogs(): void {
    localStorage.removeItem('failed_remote_logs');
  }

  /**
   * Health check - test if remote logging is working
   */
  public async healthCheck(): Promise<boolean> {
    try {
      const response = await this.makeRequest('/api/v1/logs/frontend/health', {
        method: 'GET'
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

// Global instance
const remoteLogger = new RemoteLogger();

// Export both class and instance
export { RemoteLogger, remoteLogger };
export default remoteLogger;