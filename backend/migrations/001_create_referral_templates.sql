-- Migration: Create Referral Templates with Learning System
-- Date: 2025-10-26
-- Description: Create tables for referral template generation, tracking, and effectiveness learning

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create referral templates table
CREATE TABLE IF NOT EXISTS referral_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    job_id UUID,
    contact_name VARCHAR(255),
    contact_email VARCHAR(255),
    contact_company VARCHAR(255),
    contact_position VARCHAR(255),
    subject_line VARCHAR(500),
    email_body TEXT,
    template_version INTEGER DEFAULT 1,
    parent_template_id UUID REFERENCES referral_templates(id) ON DELETE SET NULL,
    was_sent BOOLEAN DEFAULT false,
    sent_at TIMESTAMP,
    got_response BOOLEAN DEFAULT false,
    response_received_at TIMESTAMP,
    response_type VARCHAR(50), -- positive_reply, interview_scheduled, referred, no_response
    effectiveness_score FLOAT DEFAULT 0.0, -- 0.0 to 1.0 based on user feedback
    template_style VARCHAR(50) DEFAULT 'professional', -- professional, casual, direct, creative
    personalization_level VARCHAR(50) DEFAULT 'medium', -- low, medium, high
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Add foreign key constraints (assuming users and jobs tables exist)
    CONSTRAINT fk_referral_templates_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    -- Note: job_id constraint will be added if jobs table exists
);

-- Create template feedback tracking table
CREATE TABLE IF NOT EXISTS template_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES referral_templates(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    got_response BOOLEAN,
    response_type VARCHAR(50), -- positive_reply, interview_scheduled, referred, no_response, connection_accepted
    response_quality_score INTEGER CHECK (response_quality_score >= 1 AND response_quality_score <= 5),
    user_satisfaction_score INTEGER CHECK (user_satisfaction_score >= 1 AND user_satisfaction_score <= 5),
    feedback_notes TEXT,
    feedback_date TIMESTAMP DEFAULT NOW(),
    follow_up_scheduled TIMESTAMP, -- 15 days after template sent
    follow_up_completed BOOLEAN DEFAULT false,
    follow_up_response BOOLEAN DEFAULT false,

    -- Add foreign key constraint
    CONSTRAINT fk_template_feedback_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create template performance analytics table
CREATE TABLE IF NOT EXISTS template_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES referral_templates(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    generation_context JSONB, -- Store context data used for generation
    ai_confidence_score FLOAT DEFAULT 0.0,
    user_editing_time_seconds INTEGER DEFAULT 0,
    user_made_edits BOOLEAN DEFAULT false,
    edit_types JSONB, -- Track what types of edits user made
    usage_timestamp TIMESTAMP DEFAULT NOW(),

    -- Add foreign key constraint
    CONSTRAINT fk_template_analytics_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create template success patterns table for learning
CREATE TABLE IF NOT EXISTS template_success_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_name VARCHAR(255) NOT NULL,
    pattern_description TEXT,
    success_rate FLOAT DEFAULT 0.0,
    total_uses INTEGER DEFAULT 0,
    successful_uses INTEGER DEFAULT 0,
    pattern_data JSONB, -- Store pattern characteristics
    industry_tags TEXT[], -- Industries where this pattern works
    job_level_tags TEXT[], -- Job levels where this pattern works
    company_size_tags TEXT[], -- Company sizes where this pattern works
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create user referral preferences table
CREATE TABLE IF NOT EXISTS user_referral_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,
    preferred_tone VARCHAR(50) DEFAULT 'professional', -- professional, casual, direct, friendly
    preferred_length VARCHAR(50) DEFAULT 'medium', -- short, medium, long
    include_resume BOOLEAN DEFAULT true,
    include_portfolio BOOLEAN DEFAULT false,
    auto_follow_up BOOLEAN DEFAULT true,
    follow_up_days INTEGER DEFAULT 15,
    max_templates_per_day INTEGER DEFAULT 5,
    learning_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Add foreign key constraint
    CONSTRAINT fk_user_referral_preferences_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_referral_templates_user_id ON referral_templates(user_id);
CREATE INDEX IF NOT EXISTS idx_referral_templates_job_id ON referral_templates(job_id);
CREATE INDEX IF NOT EXISTS idx_referral_templates_created_at ON referral_templates(created_at);
CREATE INDEX IF NOT EXISTS idx_referral_templates_effectiveness_score ON referral_templates(effectiveness_score);
CREATE INDEX IF NOT EXISTS idx_referral_templates_response_type ON referral_templates(response_type);

CREATE INDEX IF NOT EXISTS idx_template_feedback_template_id ON template_feedback(template_id);
CREATE INDEX IF NOT EXISTS idx_template_feedback_user_id ON template_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_template_feedback_response_type ON template_feedback(response_type);
CREATE INDEX IF NOT EXISTS idx_template_feedback_date ON template_feedback(feedback_date);

CREATE INDEX IF NOT EXISTS idx_template_analytics_template_id ON template_analytics(template_id);
CREATE INDEX IF NOT EXISTS idx_template_analytics_user_id ON template_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_template_analytics_usage_timestamp ON template_analytics(usage_timestamp);

CREATE INDEX IF NOT EXISTS idx_template_success_patterns_success_rate ON template_success_patterns(success_rate);
CREATE INDEX IF NOT EXISTS idx_template_success_patterns_industry_tags ON template_success_patterns USING GIN(industry_tags);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at
CREATE TRIGGER update_referral_templates_updated_at BEFORE UPDATE ON referral_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_template_success_patterns_updated_at BEFORE UPDATE ON template_success_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_referral_preferences_updated_at BEFORE UPDATE ON user_referral_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default success patterns for initial learning
INSERT INTO template_success_patterns (pattern_name, pattern_description, pattern_data, industry_tags, job_level_tags, company_size_tags) VALUES
(
    'Professional Introduction',
    'Standard professional introduction with mutual connection mention',
    '{"opening": "professional_greeting", "connection_mention": true, "value_proposition": "experience_based", "call_to_action": "informational_interview"}',
    ARRAY['technology', 'finance', 'consulting'],
    ARRAY['entry_level', 'mid_level'],
    ARRAY['startup', 'medium', 'enterprise']
),
(
    'Mutual Interest Approach',
    'Emphasizes shared interests or company admiration',
    '{"opening": "company_admiration", "connection_mention": false, "value_proposition": "interest_based", "call_to_action": "coffee_chat"}',
    ARRAY['technology', 'media', 'creative'],
    ARRAY['mid_level', 'senior_level'],
    ARRAY['startup', 'medium']
),
(
    'Value-First Approach',
    'Leads with specific value or insight for the recipient',
    '{"opening": "value_proposition", "connection_mention": false, "value_proposition": "insight_based", "call_to_action": "quick_call"}',
    ARRAY['consulting', 'sales', 'marketing'],
    ARRAY['senior_level', 'executive'],
    ARRAY['medium', 'enterprise']
),
(
    'Casual Connection',
    'Friendly, less formal approach for creative industries',
    '{"opening": "casual_greeting", "connection_mention": true, "value_proposition": "personality_based", "call_to_action": "informal_meet"}',
    ARRAY['creative', 'media', 'entertainment'],
    ARRAY['entry_level', 'mid_level'],
    ARRAY['startup', 'medium']
);

-- Add comments for table documentation
COMMENT ON TABLE referral_templates IS 'Stores generated referral email templates with effectiveness tracking';
COMMENT ON TABLE template_feedback IS 'Tracks user feedback and response data for template effectiveness learning';
COMMENT ON TABLE template_analytics IS 'Analytics data for template generation and usage patterns';
COMMENT ON TABLE template_success_patterns IS 'ML patterns for improving template effectiveness';
COMMENT ON TABLE user_referral_preferences IS 'User preferences for referral template generation';

COMMENT ON COLUMN referral_templates.effectiveness_score IS 'Calculated score (0.0-1.0) based on response rate and user feedback';
COMMENT ON COLUMN template_feedback.response_quality_score IS 'User rating of response quality (1-5 scale)';
COMMENT ON COLUMN template_feedback.user_satisfaction_score IS 'User satisfaction with generated template (1-5 scale)';
COMMENT ON COLUMN template_analytics.generation_context IS 'JSON context data used for AI template generation';
COMMENT ON COLUMN template_success_patterns.pattern_data IS 'JSON structure defining the successful pattern characteristics';