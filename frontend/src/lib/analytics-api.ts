/**
 * Analytics Intelligence API Client
 * Handles all communication with the analytics backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const ANALYTICS_BASE = `${API_BASE_URL}/api/v1/analytics-intelligence`;

// Type definitions for API responses
export interface SkillData {
  skill: string;
  count: number;
  percentage: number;
  category?: string;
}

export interface SkillsAnalysis {
  top_skills: SkillData[];
  trending_skills: string[];
  recommended_skills: string[];
  diversity_score?: number;
}

export interface WorkLocationPreference {
  count: number;
  percentage: number;
}

export interface JobTitleDistribution {
  title: string;
  count: number;
  percentage: number;
}

export interface PreferencesAnalysis {
  work_location: Record<string, WorkLocationPreference>;
  job_titles: {
    distribution: JobTitleDistribution[];
    primary_focus?: string;
    diversity_score: number;
  };
  company_sizes: Record<string, WorkLocationPreference>;
  salary_ranges: {
    min?: number;
    max?: number;
    average?: number;
    count: number;
  };
}

export interface BehaviorAnalysis {
  velocity: {
    apps_per_week: number;
    total_period_weeks: number;
  };
  timing_patterns: {
    peak_days: [string, number][];
    day_distribution: Record<string, number>;
  };
  success_metrics: {
    application_rate: number;
    total_applied: number;
    total_viewed: number;
  };
}

export interface AnalyticsInsight {
  type: string;
  priority: string;
  title: string;
  message: string;
  action?: string;
  impact?: string;
}

export interface AnalyticsMetadata {
  user_id: string;
  total_applications: number;
  analysis_period_days: number;
  analysis_date: string;
  generation_time_seconds?: number;
  status?: string;
}

export interface FullAnalytics {
  skills: SkillsAnalysis;
  preferences: PreferencesAnalysis;
  behavior?: BehaviorAnalysis;
  market?: {
    competition_level?: string;
    market_demand_score?: number;
    salary_competitiveness?: string;
  };
  insights: AnalyticsInsight[];
  metadata: AnalyticsMetadata;
}

export interface AnalyticsOverview {
  top_skills_preview: SkillData[];
  primary_job_focus?: string;
  application_velocity?: number;
  success_rate?: number;
  key_insights_count: number;
  last_updated?: string;
}

export interface TrendDataPoint {
  date: string;
  applications: number;
  responses?: number;
}

export interface TrendAnalysis {
  data_points: TrendDataPoint[];
  period_days: number;
  total_applications: number;
  average_per_week: number;
  trend_direction: 'up' | 'down' | 'stable';
}

export interface APIResponse<T> {
  status: 'success' | 'error' | 'warning';
  message?: string;
  data?: T;
  errors?: string[];
}

// Error classes
export class AnalyticsAPIError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: any
  ) {
    super(message);
    this.name = 'AnalyticsAPIError';
  }
}

export class InsufficientDataError extends AnalyticsAPIError {
  constructor(message: string = 'Insufficient application data for analytics') {
    super(message, 400);
    this.name = 'InsufficientDataError';
  }
}

/**
 * Analytics API Client Class
 */
export class AnalyticsAPI {
  private static instance: AnalyticsAPI;
  private baseURL: string;

  private constructor() {
    this.baseURL = ANALYTICS_BASE;
  }

  public static getInstance(): AnalyticsAPI {
    if (!AnalyticsAPI.instance) {
      AnalyticsAPI.instance = new AnalyticsAPI();
    }
    return AnalyticsAPI.instance;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<APIResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;

    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    // Add auth token if available
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (token) {
      defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));

        if (response.status === 400 && errorData.error_code === 'INSUFFICIENT_DATA') {
          throw new InsufficientDataError(errorData.message);
        }

        throw new AnalyticsAPIError(
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      const data = await response.json();
      return data as APIResponse<T>;
    } catch (error) {
      if (error instanceof AnalyticsAPIError) {
        throw error;
      }

      // Network or parsing errors
      throw new AnalyticsAPIError(
        `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        0
      );
    }
  }

  /**
   * Get analytics overview for dashboard cards
   */
  async getOverview(): Promise<AnalyticsOverview> {
    const response = await this.makeRequest<AnalyticsOverview>('/overview');

    if (response.status === 'error') {
      throw new AnalyticsAPIError(response.message || 'Failed to get analytics overview', 500);
    }

    return response.data || {
      top_skills_preview: [],
      key_insights_count: 0
    };
  }

  /**
   * Get full analytics data
   */
  async getFullAnalytics(days: number = 30, forceRefresh: boolean = false): Promise<FullAnalytics> {
    const params = new URLSearchParams({
      days: days.toString(),
      force_refresh: forceRefresh.toString()
    });

    const response = await this.makeRequest<FullAnalytics>(`/full?${params}`);

    if (response.status === 'error') {
      throw new AnalyticsAPIError(response.message || 'Failed to get full analytics', 500);
    }

    if (!response.data) {
      throw new AnalyticsAPIError('No analytics data received', 500);
    }

    return response.data;
  }

  /**
   * Get skills analysis only
   */
  async getSkillsAnalysis(): Promise<SkillsAnalysis> {
    const response = await this.makeRequest<SkillsAnalysis>('/skills');

    if (response.status === 'error') {
      throw new AnalyticsAPIError(response.message || 'Failed to get skills analysis', 500);
    }

    return response.data || {
      top_skills: [],
      trending_skills: [],
      recommended_skills: []
    };
  }

  /**
   * Get application trends for charts
   */
  async getTrends(days: number = 30): Promise<TrendAnalysis> {
    const params = new URLSearchParams({ days: days.toString() });
    const response = await this.makeRequest<TrendAnalysis>(`/trends?${params}`);

    if (response.status === 'error') {
      throw new AnalyticsAPIError(response.message || 'Failed to get trends', 500);
    }

    return response.data || {
      data_points: [],
      period_days: days,
      total_applications: 0,
      average_per_week: 0,
      trend_direction: 'stable'
    };
  }

  /**
   * Trigger analytics refresh
   */
  async refreshAnalytics(days: number = 30): Promise<void> {
    const response = await this.makeRequest('/refresh', {
      method: 'POST',
      body: JSON.stringify({
        days,
        force_refresh: true,
        include_insights: true
      })
    });

    if (response.status === 'error') {
      throw new AnalyticsAPIError(response.message || 'Failed to refresh analytics', 500);
    }
  }

  /**
   * Update user preferences
   */
  async updatePreferences(preferences: {
    weekly_digest: boolean;
    insight_notifications: boolean;
    analysis_period_days: number;
  }): Promise<void> {
    const response = await this.makeRequest('/preferences', {
      method: 'PUT',
      body: JSON.stringify(preferences)
    });

    if (response.status === 'error') {
      throw new AnalyticsAPIError(response.message || 'Failed to update preferences', 500);
    }
  }

  /**
   * Check analytics system health
   */
  async getHealth(): Promise<{
    status: string;
    last_update?: string;
    cache_hit_rate?: number;
    pending_updates: number;
  }> {
    const response = await this.makeRequest<{
      status: string;
      last_update?: string;
      cache_hit_rate?: number;
      pending_updates: number;
    }>('/health');

    if (response.status === 'error') {
      throw new AnalyticsAPIError(response.message || 'Failed to check health', 500);
    }

    return response.data || {
      status: 'unknown',
      pending_updates: 0
    };
  }
}

// Export singleton instance
export const analyticsAPI = AnalyticsAPI.getInstance();

// Utility functions for error handling
export const isInsufficientDataError = (error: any): error is InsufficientDataError => {
  return error instanceof InsufficientDataError;
};

export const isAnalyticsAPIError = (error: any): error is AnalyticsAPIError => {
  return error instanceof AnalyticsAPIError;
};

// React hooks for common analytics operations
export const useAnalyticsErrorHandler = () => {
  const handleError = (error: unknown) => {
    if (isInsufficientDataError(error)) {
      return {
        type: 'insufficient_data' as const,
        message: error.message,
        suggestion: 'Apply to more jobs to unlock detailed analytics insights'
      };
    }

    if (isAnalyticsAPIError(error)) {
      return {
        type: 'api_error' as const,
        message: error.message,
        status: error.status
      };
    }

    return {
      type: 'unknown_error' as const,
      message: 'An unexpected error occurred while loading analytics'
    };
  };

  return { handleError };
};