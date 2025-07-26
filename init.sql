-- Initialize database for Vehicle Program Slack Bot
-- This script runs when the PostgreSQL container starts

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE vehicle_bot'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'vehicle_bot')\gexec

-- Connect to the vehicle_bot database
\c vehicle_bot;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_created_at ON user_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_bot_metrics_user_id ON bot_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_bot_metrics_created_at ON bot_metrics(created_at);
CREATE INDEX IF NOT EXISTS idx_bot_metrics_command ON bot_metrics(command);

-- Create a view for recent activity
CREATE OR REPLACE VIEW recent_activity AS
SELECT 
    user_id,
    command,
    created_at,
    success,
    response_time
FROM bot_metrics 
WHERE created_at >= NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- Create a function to clean up old data
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Delete old sessions (older than 365 days)
    DELETE FROM user_sessions 
    WHERE created_at < NOW() - INTERVAL '365 days';
    
    -- Delete old metrics (older than 90 days)
    DELETE FROM bot_metrics 
    WHERE created_at < NOW() - INTERVAL '90 days';
    
    -- Log the cleanup
    RAISE NOTICE 'Cleanup completed at %', NOW();
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to run cleanup (requires pg_cron extension)
-- Uncomment if pg_cron is available
-- SELECT cron.schedule('cleanup-old-data', '0 2 * * *', 'SELECT cleanup_old_data();');

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE vehicle_bot TO botuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO botuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO botuser;
GRANT EXECUTE ON FUNCTION cleanup_old_data() TO botuser; 