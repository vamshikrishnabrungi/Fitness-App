CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS activity_geometries (
    activity_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ,
    distance_m DOUBLE PRECISION NOT NULL DEFAULT 0,
    computation_version TEXT NOT NULL,
    quality JSONB NOT NULL DEFAULT '{}'::jsonb,
    route GEOMETRY(LineString, 4326),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS activity_geometries_route_gix
    ON activity_geometries USING GIST (route);
CREATE INDEX IF NOT EXISTS activity_geometries_user_started_idx
    ON activity_geometries (user_id, started_at DESC);

CREATE TABLE IF NOT EXISTS route_geometries (
    route_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    visibility TEXT NOT NULL,
    distance_m DOUBLE PRECISION NOT NULL DEFAULT 0,
    route GEOMETRY(LineString, 4326) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS route_geometries_route_gix
    ON route_geometries USING GIST (route);

CREATE TABLE IF NOT EXISTS segment_geometries (
    segment_id UUID PRIMARY KEY,
    status TEXT NOT NULL,
    distance_m DOUBLE PRECISION NOT NULL,
    segment GEOMETRY(LineString, 4326) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS segment_geometries_segment_gix
    ON segment_geometries USING GIST (segment);

CREATE TABLE IF NOT EXISTS street_edges (
    street_edge_id TEXT PRIMARY KEY,
    name TEXT,
    highway TEXT,
    surface TEXT,
    distance_m DOUBLE PRECISION NOT NULL,
    edge GEOMETRY(LineString, 4326) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS street_edges_edge_gix
    ON street_edges USING GIST (edge);

CREATE TABLE IF NOT EXISTS segment_efforts (
    effort_id UUID PRIMARY KEY,
    activity_id UUID NOT NULL,
    segment_id UUID NOT NULL,
    user_id UUID NOT NULL,
    elapsed_time_sec DOUBLE PRECISION NOT NULL,
    quality_score DOUBLE PRECISION,
    leaderboard_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    started_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (activity_id, segment_id)
);
CREATE INDEX IF NOT EXISTS segment_efforts_leaderboard_idx
    ON segment_efforts (segment_id, leaderboard_eligible, elapsed_time_sec);

CREATE TABLE IF NOT EXISTS street_edge_ownership (
    street_edge_id TEXT PRIMARY KEY REFERENCES street_edges(street_edge_id),
    user_id UUID NOT NULL,
    club_id UUID,
    activity_id UUID NOT NULL,
    quality_score DOUBLE PRECISION,
    claimed_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS street_edge_ownership_user_idx
    ON street_edge_ownership (user_id, updated_at DESC);
