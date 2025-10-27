-- Create referral templates table for Supabase
-- This matches the existing codebase pattern using String(100) for user_id

CREATE TABLE IF NOT EXISTS referral_templates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    contact_name VARCHAR(255),
    contact_email VARCHAR(255),
    contact_company VARCHAR(255),
    contact_position VARCHAR(255),
    subject_line TEXT NOT NULL,
    email_body TEXT NOT NULL,
    template_style VARCHAR(50) DEFAULT 'professional',
    personalization_level VARCHAR(50) DEFAULT 'medium',
    effectiveness_score DECIMAL(3,2) DEFAULT 0.0,
    was_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMPTZ,
    got_response BOOLEAN DEFAULT FALSE,
    response_type VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_referral_templates_user_id ON referral_templates(user_id);
CREATE INDEX IF NOT EXISTS idx_referral_templates_created_at ON referral_templates(created_at);
CREATE INDEX IF NOT EXISTS idx_referral_templates_sent_at ON referral_templates(sent_at);

-- Create user preferences table
CREATE TABLE IF NOT EXISTS user_referral_preferences (
    user_id VARCHAR(100) PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    preferred_tone VARCHAR(50) DEFAULT 'professional',
    preferred_length VARCHAR(50) DEFAULT 'medium',
    include_resume BOOLEAN DEFAULT TRUE,
    include_portfolio BOOLEAN DEFAULT FALSE,
    auto_follow_up BOOLEAN DEFAULT TRUE,
    follow_up_days INTEGER DEFAULT 15,
    max_templates_per_day INTEGER DEFAULT 5,
    learning_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create template feedback table
CREATE TABLE IF NOT EXISTS template_feedback (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    template_id UUID NOT NULL REFERENCES referral_templates(id) ON DELETE CASCADE,
    user_id VARCHAR(100) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    got_response BOOLEAN NOT NULL,
    response_type VARCHAR(100),
    response_quality_score INTEGER CHECK (response_quality_score >= 1 AND response_quality_score <= 5),
    user_satisfaction_score INTEGER CHECK (user_satisfaction_score >= 1 AND user_satisfaction_score <= 5),
    feedback_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for feedback table
CREATE INDEX IF NOT EXISTS idx_template_feedback_template_id ON template_feedback(template_id);
CREATE INDEX IF NOT EXISTS idx_template_feedback_user_id ON template_feedback(user_id);

-- Enable RLS (Row Level Security) for Supabase
ALTER TABLE referral_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_referral_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE template_feedback ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can only access their own templates" ON referral_templates
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can only access their own preferences" ON user_referral_preferences
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can only access their own feedback" ON template_feedback
    FOR ALL USING (auth.uid()::text = user_id);