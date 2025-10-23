-- Migration: Add OAuth fields to users table
-- Created: 2025-10-20

-- Add OAuth provider fields
ALTER TABLE users
ADD COLUMN IF NOT EXISTS oauth_provider VARCHAR(50),
ADD COLUMN IF NOT EXISTS oauth_provider_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS profile_picture VARCHAR(500);

-- Make hashed_password nullable for OAuth users
ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;

-- Create index on oauth_provider_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_oauth_provider_id ON users(oauth_provider_id);

-- Add comment to table
COMMENT ON COLUMN users.oauth_provider IS 'OAuth provider name (google, facebook, or NULL for email/password users)';
COMMENT ON COLUMN users.oauth_provider_id IS 'Unique ID from OAuth provider';
COMMENT ON COLUMN users.profile_picture IS 'URL to user profile picture from OAuth provider';
