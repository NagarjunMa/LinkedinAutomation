'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AlertTriangle, Bug, Download, Trash2, RefreshCw } from 'lucide-react';
import { apiErrorHandler } from '@/lib/api-error-handler';

interface ErrorLog {
  timestamp: string;
  errorId?: string;
  message: string;
  stack?: string;
  componentStack?: string;
  url: string;
  userAgent: string;
  handled?: boolean;
  status?: number;
  requestId?: string;
}

export const ErrorLogger: React.FC = () => {
  const [errorLogs, setErrorLogs] = useState<ErrorLog[]>([]);
  const [apiErrorLogs, setApiErrorLogs] = useState<Array<Record<string, unknown>>>([]);

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = () => {
    try {
      // Load error boundary logs
      const errorLogsData = JSON.parse(localStorage.getItem('error_logs') || '[]');
      setErrorLogs(errorLogsData);

      // Load API error logs
      const apiLogsData = apiErrorHandler.getErrorLogs();
      setApiErrorLogs(apiLogsData);
    } catch (error) {
      console.error('Failed to load error logs:', error);
    }
  };

  const clearAllLogs = () => {
    localStorage.removeItem('error_logs');
    apiErrorHandler.clearErrorLogs();
    setErrorLogs([]);
    setApiErrorLogs([]);
  };

  const downloadLogs = () => {
    const allLogs = {
      timestamp: new Date().toISOString(),
      errorBoundaryLogs: errorLogs,
      apiErrorLogs: apiErrorLogs,
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    const blob = new Blob([JSON.stringify(allLogs, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `error-logs-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getErrorSeverity = (log: ErrorLog | Record<string, unknown>) => {
    if (log.status >= 500 || log.message?.includes('Network')) return 'destructive';
    if (log.status >= 400 || log.message?.includes('Error')) return 'secondary';
    return 'outline';
  };

  if (process.env.NODE_ENV !== 'development') {
    return null; // Only show in development
  }

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Bug className="h-5 w-5" />
              Error Logger
            </CardTitle>
            <CardDescription>
              Development tool for monitoring application errors
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={loadLogs}>
              <RefreshCw className="h-4 w-4 mr-1" />
              Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={downloadLogs}>
              <Download className="h-4 w-4 mr-1" />
              Download
            </Button>
            <Button variant="destructive" size="sm" onClick={clearAllLogs}>
              <Trash2 className="h-4 w-4 mr-1" />
              Clear All
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="component-errors" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="component-errors">
              Component Errors ({errorLogs.length})
            </TabsTrigger>
            <TabsTrigger value="api-errors">
              API Errors ({apiErrorLogs.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="component-errors" className="space-y-4">
            {errorLogs.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                No component errors logged
              </div>
            ) : (
              <ScrollArea className="h-[600px]">
                <div className="space-y-4">
                  {errorLogs.map((log, index) => (
                    <Card key={index} className="border-l-4 border-l-red-500">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <AlertTriangle className="h-4 w-4 text-red-500" />
                            <span className="font-semibold text-sm">
                              {formatDate(log.timestamp)}
                            </span>
                            {log.errorId && (
                              <Badge variant="outline" className="text-xs">
                                ID: {log.errorId}
                              </Badge>
                            )}
                          </div>
                          <Badge variant={getErrorSeverity(log)}>
                            Component Error
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="pt-0">
                        <div className="space-y-2">
                          <div className="font-medium text-sm">{log.message}</div>
                          {log.url && (
                            <div className="text-xs text-muted-foreground">
                              URL: {log.url}
                            </div>
                          )}
                          {log.stack && (
                            <details className="mt-2">
                              <summary className="cursor-pointer text-xs text-muted-foreground">
                                View Stack Trace
                              </summary>
                              <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-x-auto">
                                {log.stack}
                              </pre>
                            </details>
                          )}
                          {log.componentStack && (
                            <details className="mt-2">
                              <summary className="cursor-pointer text-xs text-muted-foreground">
                                View Component Stack
                              </summary>
                              <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-x-auto">
                                {log.componentStack}
                              </pre>
                            </details>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            )}
          </TabsContent>

          <TabsContent value="api-errors" className="space-y-4">
            {apiErrorLogs.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                No API errors logged
              </div>
            ) : (
              <ScrollArea className="h-[600px]">
                <div className="space-y-4">
                  {apiErrorLogs.map((log, index) => (
                    <Card key={index} className="border-l-4 border-l-orange-500">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <AlertTriangle className="h-4 w-4 text-orange-500" />
                            <span className="font-semibold text-sm">
                              {formatDate(log.timestamp)}
                            </span>
                            {log.requestId && (
                              <Badge variant="outline" className="text-xs">
                                ID: {log.requestId}
                              </Badge>
                            )}
                            {log.status && (
                              <Badge variant={getErrorSeverity(log)} className="text-xs">
                                {log.status}
                              </Badge>
                            )}
                          </div>
                          <Badge variant={getErrorSeverity(log)}>
                            API Error
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="pt-0">
                        <div className="space-y-2">
                          <div className="font-medium text-sm">{log.message}</div>
                          {log.url && (
                            <div className="text-xs text-muted-foreground">
                              URL: {log.url}
                            </div>
                          )}
                          {log.code && (
                            <div className="text-xs text-muted-foreground">
                              Code: {log.code}
                            </div>
                          )}
                          {log.handled && (
                            <Badge variant="secondary" className="text-xs">
                              Handled
                            </Badge>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

// Global Error Reporter Hook
export const useErrorReporter = () => {
  const reportError = (error: Error, context?: unknown) => {
    // In production, this would send to error reporting service
    if (process.env.NODE_ENV === 'production') {
      // Send to Sentry, LogRocket, or other service
      console.error('Error reported:', error, context);
    } else {
      console.error('Development error:', error, context);
    }

    // Store locally for debugging
    const errorLog = {
      timestamp: new Date().toISOString(),
      message: error.message,
      stack: error.stack,
      url: window.location.href,
      userAgent: navigator.userAgent,
      context,
      handled: true,
    };

    try {
      const logs = JSON.parse(localStorage.getItem('error_logs') || '[]');
      logs.push(errorLog);
      if (logs.length > 50) {
        logs.splice(0, logs.length - 50);
      }
      localStorage.setItem('error_logs', JSON.stringify(logs));
    } catch (storageError) {
      console.error('Failed to store error log:', storageError);
    }
  };

  return { reportError };
};

export default ErrorLogger;