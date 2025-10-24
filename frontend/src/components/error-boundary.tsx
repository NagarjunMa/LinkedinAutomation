'use client';

import React from 'react';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ErrorInfo {
  componentStack: string;
  errorBoundary?: string;
  errorBoundaryStack?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<ErrorFallbackProps>;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  isolate?: boolean;
  resetKeys?: Array<string | number>;
  resetOnPropsChange?: boolean;
}

interface ErrorFallbackProps {
  error: Error;
  errorInfo: ErrorInfo;
  resetError: () => void;
  errorId: string;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private resetTimeoutId: number | null = null;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    const errorId = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    return {
      hasError: true,
      error,
      errorId,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const errorId = this.state.errorId;

    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.group(`🚨 Error Boundary Caught Error [${errorId}]`);
      console.error('Error:', error);
      console.error('Error Info:', errorInfo);
      console.error('Component Stack:', errorInfo.componentStack);
      console.groupEnd();
    }

    // Update state with error info
    this.setState({
      errorInfo,
    });

    // Call custom error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log to error reporting service (implement as needed)
    this.logErrorToService(error, errorInfo, errorId);
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps) {
    const { resetKeys, resetOnPropsChange } = this.props;
    const { hasError } = this.state;

    if (hasError && prevProps.resetKeys !== resetKeys) {
      if (resetKeys?.some((key, idx) => prevProps.resetKeys?.[idx] !== key)) {
        this.resetError();
      }
    }

    if (hasError && resetOnPropsChange && prevProps.children !== this.props.children) {
      this.resetError();
    }
  }

  resetError = () => {
    if (this.resetTimeoutId) {
      window.clearTimeout(this.resetTimeoutId);
    }

    this.resetTimeoutId = window.setTimeout(() => {
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: '',
      });
    }, 100);
  };

  private logErrorToService = (error: Error, errorInfo: ErrorInfo, errorId: string) => {
    try {
      // In production, send to error reporting service
      if (process.env.NODE_ENV === 'production') {
        // Example: Sentry, LogRocket, or custom service
        // errorReportingService.captureException(error, {
        //   tags: { errorBoundary: true, errorId },
        //   extra: { errorInfo, userAgent: navigator.userAgent }
        // });
      }

      // Log to local storage for debugging
      const errorLog = {
        timestamp: new Date().toISOString(),
        errorId,
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        url: window.location.href,
        userAgent: navigator.userAgent,
      };

      const logs = JSON.parse(localStorage.getItem('error_logs') || '[]');
      logs.push(errorLog);

      // Keep only last 10 errors
      if (logs.length > 10) {
        logs.splice(0, logs.length - 10);
      }

      localStorage.setItem('error_logs', JSON.stringify(logs));
    } catch (logError) {
      console.error('Failed to log error:', logError);
    }
  };

  render() {
    if (this.state.hasError) {
      const FallbackComponent = this.props.fallback || DefaultErrorFallback;
      return (
        <FallbackComponent
          error={this.state.error!}
          errorInfo={this.state.errorInfo!}
          resetError={this.resetError}
          errorId={this.state.errorId}
        />
      );
    }

    return this.props.children;
  }
}

// Default Error Fallback Component
const DefaultErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetError, errorId }) => {
  const isDevelopment = process.env.NODE_ENV === 'development';

  const handleReportError = () => {
    const subject = encodeURIComponent(`Error Report - ${error.name}`);
    const body = encodeURIComponent(`Error ID: ${errorId}
Error: ${error.message}
URL: ${window.location.href}
Timestamp: ${new Date().toISOString()}
User Agent: ${navigator.userAgent}

Please describe what you were doing when this error occurred:
`);
    window.open(`mailto:support@jobflowpro.com?subject=${subject}&body=${body}`);
  };

  return (
    <div className="min-h-[400px] flex items-center justify-center p-4">
      <Card className="w-full max-w-md mx-auto">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20">
            <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400" />
          </div>
          <CardTitle className="text-xl font-semibold">Something went wrong</CardTitle>
          <CardDescription>
            We encountered an unexpected error. Please try refreshing the page.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isDevelopment && (
            <Alert variant="destructive" className="text-left">
              <Bug className="h-4 w-4" />
              <AlertDescription className="font-mono text-xs">
                <div className="font-semibold mb-1">Error ID: {errorId}</div>
                <div className="break-all">{error.message}</div>
              </AlertDescription>
            </Alert>
          )}

          <div className="flex flex-col sm:flex-row gap-2">
            <Button onClick={resetError} className="flex-1">
              <RefreshCw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
            <Button variant="outline" onClick={() => window.location.href = '/'} className="flex-1">
              <Home className="mr-2 h-4 w-4" />
              Go Home
            </Button>
          </div>

          <Button variant="ghost" onClick={handleReportError} className="w-full text-sm">
            Report this error
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

// Specialized Error Fallbacks
export const PageErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetError, errorId }) => {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <Card className="w-full max-w-lg mx-auto">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20">
            <AlertTriangle className="h-8 w-8 text-red-600 dark:text-red-400" />
          </div>
          <CardTitle className="text-2xl font-bold">Page Error</CardTitle>
          <CardDescription className="text-base">
            This page encountered an error and couldn't load properly.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="text-center text-sm text-muted-foreground">
            Error ID: {errorId}
          </div>

          <div className="flex flex-col gap-3">
            <Button onClick={resetError} size="lg" className="w-full">
              <RefreshCw className="mr-2 h-4 w-4" />
              Reload Page
            </Button>
            <Button variant="outline" onClick={() => window.location.href = '/'} size="lg" className="w-full">
              <Home className="mr-2 h-4 w-4" />
              Return to Dashboard
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export const ComponentErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetError, errorId }) => {
  return (
    <Alert variant="destructive" className="my-4">
      <AlertTriangle className="h-4 w-4" />
      <AlertDescription className="flex items-center justify-between">
        <span>This component failed to load. Error ID: {errorId}</span>
        <Button variant="outline" size="sm" onClick={resetError}>
          <RefreshCw className="h-3 w-3 mr-1" />
          Retry
        </Button>
      </AlertDescription>
    </Alert>
  );
};

// Hook for programmatic error handling
export const useErrorHandler = () => {
  return (error: Error, errorInfo?: any) => {
    if (process.env.NODE_ENV === 'development') {
      console.error('Handled Error:', error, errorInfo);
    }

    // Log to the same service as ErrorBoundary
    const errorId = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const errorLog = {
      timestamp: new Date().toISOString(),
      errorId,
      message: error.message,
      stack: error.stack,
      url: window.location.href,
      userAgent: navigator.userAgent,
      handled: true,
    };

    try {
      const logs = JSON.parse(localStorage.getItem('error_logs') || '[]');
      logs.push(errorLog);
      if (logs.length > 10) {
        logs.splice(0, logs.length - 10);
      }
      localStorage.setItem('error_logs', JSON.stringify(logs));
    } catch (logError) {
      console.error('Failed to log handled error:', logError);
    }
  };
};

export default ErrorBoundary;