CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE IF NOT EXISTS province (
 name text PRIMARY KEY,
 geom geometry(MultiPolygon,4326) NOT NULL,
 result jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS province_geom ON province USING gist(geom);

-- Additive v2 schema. Existing province table is retained for rollback/archive.
CREATE TABLE IF NOT EXISTS lst_release (
 id text PRIMARY KEY,
 created_at timestamptz NOT NULL DEFAULT now(),
 metadata jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS lst_release_province (
 release_id text NOT NULL REFERENCES lst_release(id),
 name text NOT NULL,
 geom geometry(MultiPolygon,4326) NOT NULL,
 result jsonb NOT NULL,
 PRIMARY KEY(release_id,name)
);
CREATE INDEX IF NOT EXISTS lst_release_province_geom ON lst_release_province USING gist(geom);
CREATE TABLE IF NOT EXISTS lst_active_release (
 singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton),
 release_id text NOT NULL REFERENCES lst_release(id)
);
