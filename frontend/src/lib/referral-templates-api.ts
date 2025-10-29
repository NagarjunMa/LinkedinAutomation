/**
 * Referral Templates API Client
 * Handles communication with the referral templates backend
 */

import { apiRequest } from './api-error-handler';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Type definitions
export interface TemplateContactInfo {
  name: string;
  email?: string;
  company: string;
  position?: string;
  company_size?: 'startup' | 'medium' | 'enterprise';
  linkedin_url?: string;
}

export interface JobInfo {
  job_id?: string;
  title: string;
  company: string;
  industry?: string;
  level?: 'entry_level' | 'mid_level' | 'senior_level' | 'executive';
  description?: string;
  user_background?: string;
}

export interface UserPreferences {
  preferred_tone?: 'professional' | 'casual' | 'direct' | 'friendly';
  preferred_length?: 'short' | 'medium' | 'long';
  include_resume?: boolean;
  include_portfolio?: boolean;
}

export interface GenerateTemplateRequest {
  contact_info: TemplateContactInfo;
  job_info: JobInfo;
  user_preferences?: UserPreferences;
}

export interface TemplateResponse {
  template_id: string;
  subject_line: string;
  email_body: string;
  style: string;
  personalization_level: string;
  confidence_score: number;
  suggested_follow_up_days: number;
}

export interface TemplateFeedback {
  got_response: boolean;
  response_type?: 'positive_reply' | 'interview_scheduled' | 'referred' | 'no_response' | 'connection_accepted';
  response_quality_score?: number; // 1-5
  user_satisfaction_score?: number; // 1-5
  feedback_notes?: string;
}

export interface TemplateListItem {
  id: string;
  contact_name?: string;
  contact_company?: string;
  subject_line: string;
  email_body?: string;
  template_style: string;
  was_sent: boolean;
  sent_at?: string;
  got_response?: boolean;
  response_type?: string;
  effectiveness_score?: number;
  created_at: string;
  user_feedback?: {
    response_quality_score?: number;
    user_satisfaction_score?: number;
  };
}

export interface TemplateStats {
  total_templates: number;
  sent_count: number;
  response_count: number;
  response_rate: number;
  avg_effectiveness: number;
  draft_count: number;
}

export interface UserReferralPreferences {
  preferred_tone: string;
  preferred_length: string;
  include_resume: boolean;
  include_portfolio: boolean;
  auto_follow_up: boolean;
  follow_up_days: number;
  max_templates_per_day: number;
  learning_enabled: boolean;
}

class ReferralTemplatesAPI {
  private baseURL: string;

  constructor() {
    this.baseURL = `${API_BASE_URL}/api/v1/referral-templates`;
  }

  /**
   * Generate a new referral email template
   */
  async generateTemplate(request: GenerateTemplateRequest): Promise<TemplateResponse> {
    return apiRequest.post<TemplateResponse>(`${this.baseURL}/generate`, request);
  }

  /**
   * Get user's referral templates with pagination
   */
  async getTemplates(limit: number = 20, offset: number = 0): Promise<TemplateListItem[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString()
    });

    return apiRequest.get<TemplateListItem[]>(`${this.baseURL}/?${params}`);
  }

  /**
   * Get a specific template by ID
   */
  async getTemplate(templateId: string): Promise<TemplateListItem> {
    return apiRequest.get<TemplateListItem>(`${this.baseURL}/${templateId}`);
  }

  /**
   * Get user's template statistics
   */
  async getTemplateStats(): Promise<TemplateStats> {
    return apiRequest.get<TemplateStats>(`${this.baseURL}/stats`);
  }

  /**
   * Record feedback about a template's effectiveness
   */
  async recordFeedback(templateId: string, feedback: TemplateFeedback): Promise<{ message: string }> {
    return apiRequest.post<{ message: string }>(`${this.baseURL}/${templateId}/feedback`, feedback);
  }

  /**
   * Mark a template as sent
   */
  async markTemplateAsSent(templateId: string): Promise<{ message: string }> {
    return apiRequest.post<{ message: string }>(`${this.baseURL}/${templateId}/mark-sent`, {});
  }

  /**
   * Delete a template
   */
  async deleteTemplate(templateId: string): Promise<{ message: string }> {
    return apiRequest.delete<{ message: string }>(`${this.baseURL}/${templateId}`);
  }

  /**
   * Get user's referral preferences
   */
  async getUserPreferences(): Promise<UserReferralPreferences> {
    return apiRequest.get<UserReferralPreferences>(`${this.baseURL}/preferences/current`);
  }

  /**
   * Update user's referral preferences
   */
  async updateUserPreferences(preferences: Partial<UserReferralPreferences>): Promise<{ message: string }> {
    return apiRequest.put<{ message: string }>(`${this.baseURL}/preferences`, preferences);
  }

  /**
   * Get templates filtered by status
   */
  async getTemplatesByStatus(status: 'draft' | 'sent' | 'responded', limit: number = 20): Promise<TemplateListItem[]> {
    const allTemplates = await this.getTemplates(100); // Get more to filter
    return allTemplates.filter(template => {
      switch (status) {
        case 'draft':
          return !template.was_sent;
        case 'sent':
          return template.was_sent && !template.got_response;
        case 'responded':
          return template.was_sent && template.got_response;
        default:
          return true;
      }
    }).slice(0, limit);
  }

  /**
   * Get recent template activity
   */
  async getRecentActivity(limit: number = 5): Promise<TemplateListItem[]> {
    const templates = await this.getTemplates(limit);
    return templates.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  }

  /**
   * Get template analytics for charts
   */
  async getTemplateAnalytics(days: number = 30): Promise<{
    daily_counts: Array<{ date: string; templates_generated: number; templates_sent: number; responses: number }>;
    style_distribution: Array<{ style: string; count: number; response_rate: number }>;
    effectiveness_trends: Array<{ date: string; avg_effectiveness: number }>;
  }> {
    // This would be implemented if the backend provides analytics endpoints
    // For now, return mock data structure
    const templates = await this.getTemplates(100);

    // Process templates for analytics
    const now = new Date();
    const daysArray = Array.from({ length: days }, (_, i) => {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      return date.toISOString().split('T')[0];
    }).reverse();

    const daily_counts = daysArray.map(date => {
      const dayTemplates = templates.filter(t => t.created_at.startsWith(date));
      return {
        date,
        templates_generated: dayTemplates.length,
        templates_sent: dayTemplates.filter(t => t.was_sent).length,
        responses: dayTemplates.filter(t => t.got_response).length
      };
    });

    const styleGroups = templates.reduce((acc, template) => {
      const style = template.template_style;
      if (!acc[style]) {
        acc[style] = { total: 0, sent: 0, responses: 0 };
      }
      acc[style].total++;
      if (template.was_sent) acc[style].sent++;
      if (template.got_response) acc[style].responses++;
      return acc;
    }, {} as Record<string, { total: number; sent: number; responses: number }>);

    const style_distribution = Object.entries(styleGroups).map(([style, data]) => ({
      style,
      count: data.total,
      response_rate: data.sent > 0 ? (data.responses / data.sent) * 100 : 0
    }));

    const effectiveness_trends = daysArray.map(date => {
      const dayTemplates = templates.filter(t => t.created_at.startsWith(date) && t.effectiveness_score);
      const avgEffectiveness = dayTemplates.length > 0
        ? dayTemplates.reduce((sum, t) => sum + (t.effectiveness_score || 0), 0) / dayTemplates.length
        : 0;

      return {
        date,
        avg_effectiveness: avgEffectiveness
      };
    });

    return {
      daily_counts,
      style_distribution,
      effectiveness_trends
    };
  }
}

// Export singleton instance
export const referralTemplatesAPI = new ReferralTemplatesAPI();

// Export types for use in components
export type {
  JobInfo,
  UserPreferences,
  GenerateTemplateRequest,
  TemplateResponse,
  TemplateFeedback,
  TemplateListItem,
  TemplateStats,
  UserReferralPreferences
};