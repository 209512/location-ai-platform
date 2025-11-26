-- PostGIS 확장 생성
CREATE EXTENSION IF NOT EXISTS postgis;

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_locations_geom ON locations USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_locations_category ON locations (category);