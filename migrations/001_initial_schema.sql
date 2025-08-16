-- Initial database schema for ViraLearn ContentBot
-- This script creates all necessary tables for the application

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create workflows table
CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'created',
    content_type VARCHAR(50) NOT NULL,
    platform VARCHAR(50),
    input_data JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create content table
CREATE TABLE IF NOT EXISTS content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL,
    platform VARCHAR(50),
    title TEXT,
    body TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create media table
CREATE TABLE IF NOT EXISTS media (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID NOT NULL REFERENCES content(id) ON DELETE CASCADE,
    media_type VARCHAR(50) NOT NULL, -- 'image', 'audio', 'video'
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create quality_metrics table
CREATE TABLE IF NOT EXISTS quality_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID NOT NULL REFERENCES content(id) ON DELETE CASCADE,
    readability_score DECIMAL(5,2),
    sentiment_score DECIMAL(5,2),
    seo_score DECIMAL(5,2),
    engagement_score DECIMAL(5,2),
    overall_score DECIMAL(5,2),
    feedback JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create api_keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    permissions JSONB DEFAULT '[]',
    last_used TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_workflows_user_id ON workflows(user_id);
CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflows_created_at ON workflows(created_at);
CREATE INDEX IF NOT EXISTS idx_content_workflow_id ON content(workflow_id);
CREATE INDEX IF NOT EXISTS idx_content_content_type ON content(content_type);
CREATE INDEX IF NOT EXISTS idx_media_content_id ON media(content_id);
CREATE INDEX IF NOT EXISTS idx_media_media_type ON media(media_type);
CREATE INDEX IF NOT EXISTS idx_quality_metrics_content_id ON quality_metrics(content_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to generate API key hash
CREATE OR REPLACE FUNCTION generate_api_key_hash()
RETURNS VARCHAR(255) AS $$
BEGIN
    RETURN encode(sha256(random()::text::bytea), 'hex');
END;
$$ LANGUAGE plpgsql;

-- Insert default admin user (password: admin123)
INSERT INTO users (id, email, username, full_name, password_hash, is_active, is_verified)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'admin@viralearn.com',
    'admin',
    'System Administrator',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK8i', -- admin123
    TRUE,
    TRUE
) ON CONFLICT (id) DO NOTHING;

-- Create view for workflow summary
CREATE OR REPLACE VIEW workflow_summary AS
SELECT 
    w.id,
    w.user_id,
    u.username,
    w.status,
    w.content_type,
    w.platform,
    w.created_at,
    w.updated_at,
    COUNT(c.id) as content_count,
    COUNT(m.id) as media_count,
    AVG(qm.overall_score) as avg_quality_score
FROM workflows w
LEFT JOIN users u ON w.user_id = u.id
LEFT JOIN content c ON w.id = c.workflow_id
LEFT JOIN media m ON c.id = m.content_id
LEFT JOIN quality_metrics qm ON c.id = qm.content_id
GROUP BY w.id, w.user_id, u.username, w.status, w.content_type, w.platform, w.created_at, w.updated_at;

-- Create view for content analytics
CREATE OR REPLACE VIEW content_analytics AS
SELECT 
    c.id,
    c.workflow_id,
    c.content_type,
    c.platform,
    c.created_at,
    qm.readability_score,
    qm.sentiment_score,
    qm.seo_score,
    qm.engagement_score,
    qm.overall_score,
    COUNT(m.id) as media_count,
    LENGTH(c.body) as content_length,
    ARRAY_LENGTH(STRING_TO_ARRAY(c.body, ' '), 1) as word_count
FROM content c
LEFT JOIN quality_metrics qm ON c.id = qm.content_id
LEFT JOIN media m ON c.id = m.content_id
GROUP BY c.id, c.workflow_id, c.content_type, c.platform, c.created_at, 
         qm.readability_score, qm.sentiment_score, qm.seo_score, qm.engagement_score, qm.overall_score; 