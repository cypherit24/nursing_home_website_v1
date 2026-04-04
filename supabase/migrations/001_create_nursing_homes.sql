-- T04: Create nursing_homes table with RLS policy
-- This table stores nursing home facility information collected from public data portal
-- S4 Security: representative_name is stored in DB but MUST NOT be rendered on frontend
-- S2 Security: RLS is enabled with anon=SELECT only, service_role=ALL

-- Create the nursing_homes table
CREATE TABLE IF NOT EXISTS nursing_homes (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

  -- Basic facility information from step 1 (공공데이터 수집)
  facility_code TEXT NOT NULL,
  name TEXT NOT NULL,
  sido TEXT NOT NULL,
  sigungu TEXT NOT NULL,
  address TEXT,
  representative_name TEXT,  -- S4: Store in DB only, never render on frontend
  phone TEXT,

  -- Detail information collected in step 2 (API 수집)
  capacity INTEGER,
  current_occupancy INTEGER,
  caregiver_count INTEGER,
  meal_cost_per_day INTEGER,       -- 1인 기준 원 단위
  room_cost_1person INTEGER,       -- 1인실 원 단위
  room_cost_2person INTEGER,       -- 2인실 원 단위
  detail_fetched_at TIMESTAMPTZ,   -- step2 완료 시점

  -- SEO content generated in step 3 (SEO 콘텐츠 생성)
  seo_content JSONB,               -- MUST be JSONB, not TEXT (for efficiency & indexing)
  seo_generated_at TIMESTAMPTZ,    -- step3 완료 시점

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create UNIQUE constraint on facility_code
ALTER TABLE nursing_homes ADD CONSTRAINT nursing_homes_facility_code_unique UNIQUE (facility_code);

-- Create composite index on sido, sigungu for location-based queries
CREATE INDEX idx_nursing_homes_location ON nursing_homes(sido, sigungu);

-- Enable RLS (Row Level Security) - S2 보안 규칙
ALTER TABLE nursing_homes ENABLE ROW LEVEL SECURITY;

-- RLS Policy 1: Allow anon role to SELECT only (read-only access)
CREATE POLICY "anon_select_nursing_homes" ON nursing_homes
  FOR SELECT
  USING (true);

-- RLS Policy 2: Allow service_role to perform ALL operations (INSERT, UPDATE, DELETE, SELECT)
CREATE POLICY "service_role_all_nursing_homes" ON nursing_homes
  FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- Comment: parameterized queries pattern
-- All external inputs (facility_code, name, etc.) must be validated for format before insertion.
-- Python pipeline (step1, step2, step3) handles parameterized queries via psycopg2 or SQLAlchemy ORM.
-- Example: cursor.execute("INSERT INTO nursing_homes(facility_code, name, ...) VALUES(%s, %s, ...)", params)
