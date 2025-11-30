# Frontend Integration - Next.js Implementation

## Overview

The browser extension frontend integration involves adding three new pages to the existing Next.js dashboard and implementing real-time synchronization between the extension and web application.

## New Pages Structure

```
frontend/src/app/dashboard/
├── documents/
│   ├── page.tsx              # Document management interface
│   ├── components/
│   │   ├── DocumentUploader.tsx
│   │   ├── DocumentGrid.tsx
│   │   ├── DocumentViewer.tsx
│   │   └── KnowledgeBaseSearch.tsx
│   └── loading.tsx
├── extension/
│   ├── page.tsx              # Extension dashboard
│   ├── components/
│   │   ├── ExtensionStatus.tsx
│   │   ├── ActivityFeed.tsx
│   │   ├── AnalysisHistory.tsx
│   │   └── StatsOverview.tsx
│   └── loading.tsx
└── extension-settings/
    ├── page.tsx              # Extension configuration
    ├── components/
    │   ├── AuthTokenManager.tsx
    │   ├── SyncPreferences.tsx
    │   ├── PlatformSettings.tsx
    │   └── AIModelSettings.tsx
    └── loading.tsx
```

## State Management

### Extension Store (Zustand)

```typescript
// stores/extension-store.ts
import { create } from 'zustand'
import { immer } from 'zustand/middleware/immer'
import { subscribeWithSelector } from 'zustand/middleware'

interface ExtensionDocument {
  id: string;
  name: string;
  type: 'resume' | 'portfolio' | 'project' | 'certificate' | 'other';
  file_path: string;
  file_size: number;
  file_type: string;
  upload_date: string;
  processed_status: 'pending' | 'processing' | 'completed' | 'error';
  vector_status: 'not_indexed' | 'indexing' | 'indexed' | 'failed';
  content_preview: string;
  metadata: {
    title?: string;
    description?: string;
    tags?: string[];
    category?: string;
    skills?: string[];
  };
}

interface ExtensionActivity {
  id: string;
  type: 'job_analysis' | 'application_response' | 'document_upload';
  title: string;
  description: string;
  url?: string;
  result?: any;
  created_at: string;
  status: 'success' | 'error' | 'pending';
}

interface ExtensionSettings {
  auto_sync: boolean;
  notifications_enabled: boolean;
  response_style: 'professional' | 'friendly' | 'custom';
  max_applications_per_day: number;
  supported_platforms: string[];
  ai_model_preference: string;
  custom_response_template?: string;
  sync_frequency: 'real-time' | 'hourly' | 'daily' | 'manual';
}

interface ExtensionState {
  // Connection status
  isConnected: boolean;
  lastSync: Date | null;
  syncStatus: 'idle' | 'syncing' | 'error';

  // Documents
  documents: ExtensionDocument[];
  uploadingDocuments: string[];

  // Activity
  activities: ExtensionActivity[];

  // Settings
  settings: ExtensionSettings;

  // Stats
  stats: {
    totalAnalyzed: number;
    responsesGenerated: number;
    documentsProcessed: number;
    avgCompatibilityScore: number;
  };

  // Actions
  setConnectionStatus: (connected: boolean) => void;
  updateSyncStatus: (status: 'idle' | 'syncing' | 'error') => void;
  addDocument: (document: ExtensionDocument) => void;
  updateDocument: (id: string, updates: Partial<ExtensionDocument>) => void;
  removeDocument: (id: string) => void;
  addActivity: (activity: ExtensionActivity) => void;
  updateSettings: (settings: Partial<ExtensionSettings>) => void;
  updateStats: (stats: Partial<ExtensionState['stats']>) => void;
}

export const useExtensionStore = create<ExtensionState>()(
  subscribeWithSelector(
    immer((set, get) => ({
      // Initial state
      isConnected: false,
      lastSync: null,
      syncStatus: 'idle',
      documents: [],
      uploadingDocuments: [],
      activities: [],
      settings: {
        auto_sync: true,
        notifications_enabled: true,
        response_style: 'professional',
        max_applications_per_day: 10,
        supported_platforms: ['linkedin', 'indeed', 'glassdoor'],
        ai_model_preference: 'gpt-4o-mini',
        sync_frequency: 'real-time'
      },
      stats: {
        totalAnalyzed: 0,
        responsesGenerated: 0,
        documentsProcessed: 0,
        avgCompatibilityScore: 0
      },

      // Actions
      setConnectionStatus: (connected) => set((state) => {
        state.isConnected = connected;
        if (connected) {
          state.lastSync = new Date();
        }
      }),

      updateSyncStatus: (status) => set((state) => {
        state.syncStatus = status;
        if (status === 'idle') {
          state.lastSync = new Date();
        }
      }),

      addDocument: (document) => set((state) => {
        state.documents.push(document);
      }),

      updateDocument: (id, updates) => set((state) => {
        const index = state.documents.findIndex(doc => doc.id === id);
        if (index !== -1) {
          Object.assign(state.documents[index], updates);
        }
      }),

      removeDocument: (id) => set((state) => {
        state.documents = state.documents.filter(doc => doc.id !== id);
      }),

      addActivity: (activity) => set((state) => {
        state.activities.unshift(activity);
        // Keep only last 100 activities
        if (state.activities.length > 100) {
          state.activities = state.activities.slice(0, 100);
        }
      }),

      updateSettings: (newSettings) => set((state) => {
        Object.assign(state.settings, newSettings);
      }),

      updateStats: (newStats) => set((state) => {
        Object.assign(state.stats, newStats);
      })
    }))
  )
);
```

## Document Management Page

```typescript
// app/dashboard/documents/page.tsx
"use client";

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
  Upload, FileText, Trash2, Eye, Download, Search,
  Filter, RefreshCw, CheckCircle, Clock, AlertTriangle,
  FileImage, FileVideo, Archive, Brain, Zap
} from 'lucide-react';
import { useExtensionStore } from '@/stores/extension-store';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import filesize from 'filesize';

export default function DocumentsPage() {
  const {
    documents,
    uploadingDocuments,
    addDocument,
    updateDocument,
    removeDocument
  } = useExtensionStore();

  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [selectedDocument, setSelectedDocument] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      try {
        // Validate file
        if (file.size > 10 * 1024 * 1024) {
          toast({
            title: "File too large",
            description: `${file.name} exceeds 10MB limit.`,
            variant: "destructive"
          });
          continue;
        }

        // Upload file
        const formData = new FormData();
        formData.append('file', file);
        formData.append('category', 'document');

        const response = await fetch('/api/v1/extension/documents/upload', {
          method: 'POST',
          body: formData
        });

        if (response.ok) {
          const newDocument = await response.json();
          addDocument(newDocument);

          toast({
            title: "Document uploaded",
            description: `${file.name} has been uploaded and is being processed.`
          });
        } else {
          throw new Error('Upload failed');
        }
      } catch (error) {
        toast({
          title: "Upload failed",
          description: `Failed to upload ${file.name}. Please try again.`,
          variant: "destructive"
        });
      }
    }
  }, [addDocument, toast]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'image/*': ['.jpeg', '.jpg', '.png']
    },
    multiple: true
  });

  const handleVectorizeDocument = async (documentId: string) => {
    try {
      updateDocument(documentId, { vector_status: 'indexing' });

      const response = await fetch(`/api/v1/extension/documents/${documentId}/vectorize`, {
        method: 'POST'
      });

      if (response.ok) {
        updateDocument(documentId, { vector_status: 'indexed' });
        toast({
          title: "Document indexed",
          description: "Document has been added to knowledge base."
        });
      } else {
        throw new Error('Vectorization failed');
      }
    } catch (error) {
      updateDocument(documentId, { vector_status: 'failed' });
      toast({
        title: "Indexing failed",
        description: "Failed to add document to knowledge base.",
        variant: "destructive"
      });
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    try {
      const response = await fetch(`/api/v1/extension/documents/${documentId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        removeDocument(documentId);
        toast({
          title: "Document deleted",
          description: "Document has been removed successfully."
        });
      } else {
        throw new Error('Delete failed');
      }
    } catch (error) {
      toast({
        title: "Delete failed",
        description: "Failed to delete document. Please try again.",
        variant: "destructive"
      });
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'processing': return <Clock className="h-4 w-4 text-yellow-500 animate-spin" />;
      case 'error': return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default: return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getVectorStatusBadge = (status: string) => {
    const variants = {
      'indexed': 'default',
      'indexing': 'secondary',
      'failed': 'destructive',
      'not_indexed': 'outline'
    } as const;

    return (
      <Badge variant={variants[status as keyof typeof variants]}>
        {status === 'indexing' && <Brain className="h-3 w-3 mr-1 animate-pulse" />}
        {status === 'indexed' && <Zap className="h-3 w-3 mr-1" />}
        {status.replace('_', ' ')}
      </Badge>
    );
  };

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         doc.metadata.title?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterType === 'all' || doc.type === filterType;

    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Document Management
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Upload and manage your professional documents for AI-powered job applications
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Badge variant="outline" className="text-green-600">
            {documents.length} Documents
          </Badge>
        </div>
      </div>

      <Tabs defaultValue="upload" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="upload">Upload Documents</TabsTrigger>
          <TabsTrigger value="manage">Manage Documents</TabsTrigger>
          <TabsTrigger value="knowledge">Knowledge Base</TabsTrigger>
        </TabsList>

        <TabsContent value="upload" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Upload New Documents</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Upload Zone */}
              <div
                {...getRootProps()}
                className={cn(
                  "border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-8 text-center transition-colors cursor-pointer",
                  isDragActive && "border-orange-500 bg-orange-50 dark:bg-orange-950/20"
                )}
              >
                <input {...getInputProps()} />
                <div className="flex flex-col items-center space-y-4">
                  <div className="p-4 rounded-full bg-orange-100 dark:bg-orange-950/30">
                    <Upload className="h-8 w-8 text-orange-600 dark:text-orange-400" />
                  </div>

                  {isDragActive ? (
                    <p className="text-lg font-medium text-orange-600 dark:text-orange-400">
                      Drop files here to upload
                    </p>
                  ) : (
                    <>
                      <div>
                        <p className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">
                          Upload your documents
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Drag & drop files or click to browse
                        </p>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-500">
                        Supports PDF, DOC, DOCX, TXT, and images up to 10MB
                      </p>
                    </>
                  )}
                </div>
              </div>

              {/* Document Categories */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { name: 'Resume', desc: 'Upload your current resume', icon: FileText },
                  { name: 'Portfolio', desc: 'Upload portfolio documents', icon: FileImage },
                  { name: 'Certificates', desc: 'Upload certifications', icon: Archive },
                  { name: 'Projects', desc: 'Upload project descriptions', icon: FileVideo }
                ].map((category) => (
                  <Card key={category.name} className="text-center p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer">
                    <category.icon className="h-8 w-8 mx-auto mb-2 text-orange-500" />
                    <h3 className="font-medium">{category.name}</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {category.desc}
                    </p>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="manage" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Document Library
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      placeholder="Search documents..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 w-64"
                    />
                  </div>
                  <Select value={filterType} onValueChange={setFilterType}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="resume">Resume</SelectItem>
                      <SelectItem value="portfolio">Portfolio</SelectItem>
                      <SelectItem value="project">Projects</SelectItem>
                      <SelectItem value="certificate">Certificates</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Document</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Knowledge Base</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredDocuments.map((doc) => (
                    <TableRow key={doc.id}>
                      <TableCell className="flex items-center gap-3">
                        <FileText className="h-4 w-4 text-blue-500" />
                        <div>
                          <p className="font-medium">{doc.name}</p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {doc.metadata.title || 'No title'}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{doc.type}</Badge>
                      </TableCell>
                      <TableCell>{filesize(doc.file_size)}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(doc.processed_status)}
                          <span className="capitalize">{doc.processed_status}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {getVectorStatusBadge(doc.vector_status)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleVectorizeDocument(doc.id)}
                            disabled={doc.vector_status === 'indexing'}
                          >
                            <Brain className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteDocument(doc.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="knowledge" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Knowledge Base Search</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search through your documents using AI..."
                    className="pl-10"
                  />
                </div>
                <div className="text-center py-12 text-gray-500">
                  <Brain className="h-12 w-12 mx-auto mb-4 text-orange-500" />
                  <p>Knowledge base search will appear here</p>
                  <p className="text-sm">Upload and index documents to enable AI-powered search</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

## Real-time Sync Implementation

### WebSocket Provider

```typescript
// components/extension-sync-provider.tsx
"use client";

import { createContext, useContext, useEffect, ReactNode } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { useExtensionStore } from '@/stores/extension-store';
import { useToast } from '@/hooks/use-toast';

interface ExtensionSyncContextType {
  isConnected: boolean;
  lastSync: Date | null;
  forceSync: () => Promise<void>;
}

const ExtensionSyncContext = createContext<ExtensionSyncContextType | null>(null);

export function useExtensionSync() {
  const context = useContext(ExtensionSyncContext);
  if (!context) {
    throw new Error('useExtensionSync must be used within ExtensionSyncProvider');
  }
  return context;
}

interface ExtensionSyncProviderProps {
  children: ReactNode;
}

export function ExtensionSyncProvider({ children }: ExtensionSyncProviderProps) {
  const { user } = useAuth();
  const { toast } = useToast();
  const {
    setConnectionStatus,
    updateSyncStatus,
    addActivity,
    isConnected,
    lastSync,
    settings
  } = useExtensionStore();

  useEffect(() => {
    if (!user || !settings.auto_sync) return;

    let ws: WebSocket;
    let reconnectTimeout: NodeJS.Timeout;

    const connectWebSocket = () => {
      const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/extension/${user.id}`;
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setConnectionStatus(true);
        updateSyncStatus('idle');
        console.log('Extension WebSocket connected');
      };

      ws.onclose = () => {
        setConnectionStatus(false);
        console.log('Extension WebSocket disconnected');

        // Attempt to reconnect after 5 seconds
        reconnectTimeout = setTimeout(() => {
          if (user && settings.auto_sync) {
            connectWebSocket();
          }
        }, 5000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          switch (data.type) {
            case 'job_analyzed':
              addActivity({
                id: data.payload.id,
                type: 'job_analysis',
                title: `Job analyzed: ${data.payload.title}`,
                description: `Compatibility score: ${data.payload.compatibility_score}%`,
                url: data.payload.url,
                result: data.payload,
                created_at: new Date().toISOString(),
                status: 'success'
              });

              if (settings.notifications_enabled) {
                toast({
                  title: "Job analyzed",
                  description: `${data.payload.title} - ${data.payload.compatibility_score}% match`
                });
              }
              break;

            case 'application_response_generated':
              addActivity({
                id: data.payload.id,
                type: 'application_response',
                title: 'Application response generated',
                description: data.payload.question,
                result: data.payload,
                created_at: new Date().toISOString(),
                status: 'success'
              });

              if (settings.notifications_enabled) {
                toast({
                  title: "Response generated",
                  description: "AI generated response for application question"
                });
              }
              break;

            case 'sync_complete':
              updateSyncStatus('idle');
              break;

            case 'extension_error':
              addActivity({
                id: Date.now().toString(),
                type: 'job_analysis',
                title: 'Extension error',
                description: data.payload.message,
                created_at: new Date().toISOString(),
                status: 'error'
              });

              toast({
                title: "Extension Error",
                description: data.payload.message,
                variant: "destructive"
              });
              break;
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('Extension WebSocket error:', error);
        updateSyncStatus('error');
      };
    };

    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
    };
  }, [user, settings.auto_sync, settings.notifications_enabled]);

  const forceSync = async () => {
    updateSyncStatus('syncing');

    try {
      const response = await fetch('/api/v1/extension/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        updateSyncStatus('idle');
        toast({
          title: "Sync completed",
          description: "Extension data has been synchronized"
        });
      } else {
        throw new Error('Sync failed');
      }
    } catch (error) {
      updateSyncStatus('error');
      toast({
        title: "Sync failed",
        description: "Failed to sync extension data. Please try again.",
        variant: "destructive"
      });
    }
  };

  return (
    <ExtensionSyncContext.Provider value={{
      isConnected,
      lastSync,
      forceSync
    }}>
      {children}
    </ExtensionSyncContext.Provider>
  );
}
```

## Navigation Integration

### Update Sidebar Navigation

```typescript
// Update in sophisticated-sidebar.tsx
const mainNavigation = [
  // ... existing items
  {
    name: "Extension",
    href: "/dashboard/extension",
    icon: Chrome,
    current: false,
    badge: isConnected ? "Connected" : "Offline"
  },
  {
    name: "Documents",
    href: "/dashboard/documents",
    icon: FileText,
    current: false,
    badge: documents.length > 0 ? documents.length.toString() : undefined
  },
  {
    name: "Settings",
    href: "/dashboard/extension-settings",
    icon: Settings,
    current: false
  }
];
```

## Performance Optimizations

### Lazy Loading and Code Splitting

```typescript
// app/dashboard/documents/page.tsx
import dynamic from 'next/dynamic';

const DocumentUploader = dynamic(() => import('./components/DocumentUploader'), {
  loading: () => <div>Loading uploader...</div>,
  ssr: false
});

const KnowledgeBaseSearch = dynamic(() => import('./components/KnowledgeBaseSearch'), {
  loading: () => <div>Loading search...</div>,
  ssr: false
});
```

### Optimistic Updates

```typescript
// hooks/use-extension-api.ts
export function useExtensionDocuments() {
  const { addDocument, updateDocument, removeDocument } = useExtensionStore();

  const uploadDocument = async (file: File) => {
    // Optimistic update
    const tempId = Date.now().toString();
    const tempDocument = {
      id: tempId,
      name: file.name,
      type: 'document' as const,
      processed_status: 'processing' as const,
      vector_status: 'not_indexed' as const,
      // ... other fields
    };

    addDocument(tempDocument);

    try {
      const response = await uploadDocumentAPI(file);
      // Replace temp document with real one
      removeDocument(tempId);
      addDocument(response.data);
    } catch (error) {
      // Remove temp document on error
      removeDocument(tempId);
      throw error;
    }
  };

  return { uploadDocument };
}
```

This frontend integration provides a seamless user experience that bridges the gap between the browser extension and the main JobFlow Pro dashboard, ensuring real-time synchronization and efficient document management.