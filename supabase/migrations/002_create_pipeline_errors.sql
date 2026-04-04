-- T04-b: Create pipeline_errors table with RLS policy
-- This table logs errors encountered during the data pipeline execution (step1, step2, step3)
-- S2 Security: RLS is enabled with anon=SELECT only, service_role=ALL
-- WARNING: error_message must never contain API keys, secrets, or credentials

-- Create the pipeline_errors table
CREATE TABLE IF NOT EXISTS pipeline_errors (
  id SERIAL PRIMARY KEY,
  facility_code TEXT,
  step TEXT,                       -- e.g., 'step1', 'step2', 'step3'
  error_message TEXT,              -- IMPORTANT: Must NOT contain API keys, secrets, or tokens
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on facility_code for faster error lookup
CREATE INDEX idx_pipeline_errors_facility_code ON pipeline_errors(facility_code);

-- Create index on step for filtering errors by pipeline stage
CREATE INDEX idx_pipeline_errors_step ON pipeline_errors(step);

-- Enable RLS (Row Level Security) - S2 보안 규칙
ALTER TABLE pipeline_errors ENABLE ROW LEVEL SECURITY;

-- RLS Policy 1: Allow anon role to SELECT only (read-only access)
CREATE POLICY "anon_select_pipeline_errors" ON pipeline_errors
  FOR SELECT
  USING (true);

-- RLS Policy 2: Allow service_role to perform ALL operations (INSERT, UPDATE, DELETE, SELECT)
CREATE POLICY "service_role_all_pipeline_errors" ON pipeline_errors
  FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- Comment: Security notes for pipeline implementation
-- 1. error_message should be sanitized before insertion - remove/redact API keys, OAuth tokens, credentials
-- 2. Use parameterized queries to prevent SQL injection
-- 3. Example: cursor.execute("INSERT INTO pipeline_errors(facility_code, step, error_message) VALUES(%s, %s, %s)", (code, step, msg))
-- 4. Sensitive data (API response body containing secrets) should be logged separately to secure logs, not this table
