CREATE EXTENSION IF NOT EXISTS postgis;

DO $$
BEGIN
    CREATE TYPE club_visibility AS ENUM ('public', 'private');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$
BEGIN
    CREATE TYPE club_status AS ENUM ('active', 'archived');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$
BEGIN
    CREATE TYPE club_role AS ENUM ('owner', 'admin', 'member');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$
BEGIN
    CREATE TYPE membership_status AS ENUM ('pending', 'active', 'rejected', 'removed', 'banned');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$
BEGIN
    CREATE TYPE activity_visibility AS ENUM ('public', 'club', 'private');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$
BEGIN
    CREATE TYPE verification_status AS ENUM ('provisional', 'verified', 'rejected');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$
BEGIN
    CREATE TYPE controller_type AS ENUM ('athlete', 'club');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS regions (
    id UUID PRIMARY KEY,
    parent_id UUID REFERENCES regions(id),
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('country', 'state', 'city', 'osm_shard')),
    timezone TEXT NOT NULL DEFAULT 'UTC',
    boundary GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS regions_boundary_gix ON regions USING GIST (boundary);

CREATE TABLE IF NOT EXISTS clubs (
    id UUID PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL CHECK (char_length(name) BETWEEN 1 AND 120),
    description TEXT,
    rules TEXT,
    visibility club_visibility NOT NULL DEFAULT 'public',
    status club_status NOT NULL DEFAULT 'active',
    owner_user_id UUID NOT NULL,
    home_region_id UUID REFERENCES regions(id),
    timezone TEXT NOT NULL DEFAULT 'UTC',
    home_location GEOMETRY(Point, 4326),
    primary_color TEXT NOT NULL DEFAULT '#FF4F2E',
    emoji TEXT NOT NULL DEFAULT '🏃',
    avatar_url TEXT,
    banner_url TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS clubs_discovery_idx
    ON clubs (status, visibility, home_region_id, created_at DESC);
CREATE INDEX IF NOT EXISTS clubs_home_location_gix ON clubs USING GIST (home_location);

CREATE TABLE IF NOT EXISTS club_memberships (
    id UUID PRIMARY KEY,
    club_id UUID NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    role club_role NOT NULL DEFAULT 'member',
    status membership_status NOT NULL,
    requested_at TIMESTAMPTZ,
    joined_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    reviewed_by_user_id UUID,
    review_reason TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (club_id, user_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS club_one_active_owner_idx
    ON club_memberships (club_id)
    WHERE role = 'owner' AND status = 'active';
CREATE INDEX IF NOT EXISTS club_memberships_user_idx
    ON club_memberships (user_id, status, joined_at DESC);
CREATE INDEX IF NOT EXISTS club_memberships_admin_queue_idx
    ON club_memberships (club_id, status, requested_at)
    WHERE status = 'pending';

CREATE OR REPLACE FUNCTION enforce_active_club_owner()
RETURNS TRIGGER AS $$
DECLARE
    affected_club_id UUID;
    canonical_owner UUID;
    active_owner_count INTEGER;
    membership_owner UUID;
BEGIN
    IF TG_TABLE_NAME = 'clubs' THEN
        affected_club_id := COALESCE(NEW.id, OLD.id);
    ELSE
        affected_club_id := COALESCE(NEW.club_id, OLD.club_id);
    END IF;

    SELECT owner_user_id
      INTO canonical_owner
      FROM clubs
     WHERE id = affected_club_id
       AND status = 'active';

    IF canonical_owner IS NULL THEN
        RETURN COALESCE(NEW, OLD);
    END IF;

    SELECT COUNT(*), MAX(user_id::text)::uuid
      INTO active_owner_count, membership_owner
      FROM club_memberships
     WHERE club_id = affected_club_id
       AND role = 'owner'
       AND status = 'active';

    IF active_owner_count <> 1 OR membership_owner <> canonical_owner THEN
        RAISE EXCEPTION
          'active club % must have exactly one canonical active owner',
          affected_club_id
          USING ERRCODE = '23514';
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS clubs_require_owner ON clubs;
CREATE CONSTRAINT TRIGGER clubs_require_owner
AFTER INSERT OR UPDATE OF status, owner_user_id ON clubs
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION enforce_active_club_owner();

DROP TRIGGER IF EXISTS memberships_preserve_owner ON club_memberships;
CREATE CONSTRAINT TRIGGER memberships_preserve_owner
AFTER INSERT OR UPDATE OR DELETE ON club_memberships
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION enforce_active_club_owner();

CREATE TABLE IF NOT EXISTS athlete_competitive_profiles (
    user_id UUID PRIMARY KEY,
    primary_club_id UUID REFERENCES clubs(id),
    primary_selected_at TIMESTAMPTZ,
    primary_switch_available_at TIMESTAMPTZ,
    public_competition_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS athlete_primary_club_history (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    club_id UUID NOT NULL REFERENCES clubs(id),
    effective_from TIMESTAMPTZ NOT NULL,
    effective_to TIMESTAMPTZ,
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (effective_to IS NULL OR effective_to > effective_from)
);
CREATE UNIQUE INDEX IF NOT EXISTS athlete_one_open_primary_history_idx
    ON athlete_primary_club_history (user_id)
    WHERE effective_to IS NULL;
CREATE INDEX IF NOT EXISTS athlete_primary_history_lookup_idx
    ON athlete_primary_club_history (user_id, effective_from DESC, effective_to);

CREATE TABLE IF NOT EXISTS club_invitations (
    id UUID PRIMARY KEY,
    club_id UUID NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    invited_user_id UUID,
    invited_email_hash TEXT,
    role club_role NOT NULL DEFAULT 'member',
    created_by_user_id UUID NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    accepted_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS club_invitations_club_idx
    ON club_invitations (club_id, expires_at DESC);

CREATE TABLE IF NOT EXISTS club_bans (
    id UUID PRIMARY KEY,
    club_id UUID NOT NULL REFERENCES clubs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    reason TEXT,
    created_by_user_id UUID NOT NULL,
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS club_active_ban_idx
    ON club_bans (club_id, user_id)
    WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS activities (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    source TEXT NOT NULL,
    source_activity_id TEXT,
    idempotency_key TEXT,
    status TEXT NOT NULL,
    verification verification_status NOT NULL DEFAULT 'provisional',
    visibility activity_visibility NOT NULL DEFAULT 'club',
    started_at TIMESTAMPTZ NOT NULL,
    local_timezone TEXT NOT NULL DEFAULT 'UTC',
    ended_at TIMESTAMPTZ,
    elapsed_time_sec INTEGER NOT NULL DEFAULT 0,
    moving_time_sec INTEGER NOT NULL DEFAULT 0,
    distance_m DOUBLE PRECISION NOT NULL DEFAULT 0,
    elevation_gain_m DOUBLE PRECISION NOT NULL DEFAULT 0,
    quality_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    quality JSONB NOT NULL DEFAULT '{}'::jsonb,
    computation_version TEXT NOT NULL,
    hide_start_end_m INTEGER NOT NULL DEFAULT 0 CHECK (hide_start_end_m >= 0),
    public_competition_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    route GEOMETRY(LineString, 4326),
    public_route GEOMETRY(MultiLineString, 4326),
    raw_stream_object_key TEXT,
    duplicate_of_activity_id UUID REFERENCES activities(id),
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    UNIQUE (user_id, idempotency_key)
);
CREATE UNIQUE INDEX IF NOT EXISTS activities_source_identity_idx
    ON activities (user_id, source, source_activity_id)
    WHERE source_activity_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS activities_user_started_idx
    ON activities (user_id, started_at DESC);
CREATE INDEX IF NOT EXISTS activities_competition_idx
    ON activities (verification, visibility, started_at DESC)
    WHERE status = 'complete' AND deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS activities_route_gix ON activities USING GIST (route);
CREATE INDEX IF NOT EXISTS activities_public_route_gix ON activities USING GIST (public_route);

CREATE TABLE IF NOT EXISTS activity_stream_objects (
    activity_id UUID PRIMARY KEY REFERENCES activities(id) ON DELETE CASCADE,
    object_key TEXT NOT NULL UNIQUE,
    sha256 TEXT NOT NULL,
    sample_count INTEGER NOT NULL,
    byte_size BIGINT NOT NULL,
    schema_version INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS activity_club_attributions (
    activity_id UUID PRIMARY KEY REFERENCES activities(id) ON DELETE CASCADE,
    club_id UUID NOT NULL REFERENCES clubs(id),
    user_id UUID NOT NULL,
    visibility activity_visibility NOT NULL,
    attributed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS activity_club_attributions_club_idx
    ON activity_club_attributions (club_id, attributed_at DESC);

CREATE TABLE IF NOT EXISTS osm_regions (
    id UUID PRIMARY KEY,
    region_id UUID REFERENCES regions(id),
    code TEXT NOT NULL UNIQUE,
    pbf_source_url TEXT NOT NULL,
    replication_url TEXT,
    source_timestamp TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (status IN ('pending', 'building', 'active', 'failed', 'retired')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS osm_graph_versions (
    id UUID PRIMARY KEY,
    osm_region_id UUID NOT NULL REFERENCES osm_regions(id),
    version TEXT NOT NULL,
    source_timestamp TIMESTAMPTZ NOT NULL,
    valhalla_object_key TEXT,
    status TEXT NOT NULL CHECK (status IN ('building', 'validating', 'active', 'failed', 'retired')),
    activated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (osm_region_id, version)
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_graph_per_region_idx
    ON osm_graph_versions (osm_region_id)
    WHERE status = 'active';

ALTER TABLE street_edges ADD COLUMN IF NOT EXISTS id UUID;
ALTER TABLE street_edges ADD COLUMN IF NOT EXISTS osm_region_id UUID REFERENCES osm_regions(id);
ALTER TABLE street_edges ADD COLUMN IF NOT EXISTS graph_version_id UUID REFERENCES osm_graph_versions(id);
ALTER TABLE street_edges ADD COLUMN IF NOT EXISTS osm_way_id BIGINT;
ALTER TABLE street_edges ADD COLUMN IF NOT EXISTS osm_from_node_id BIGINT;
ALTER TABLE street_edges ADD COLUMN IF NOT EXISTS osm_to_node_id BIGINT;
ALTER TABLE street_edges ADD COLUMN IF NOT EXISTS spatial_cell TEXT;
ALTER TABLE street_edges ADD COLUMN IF NOT EXISTS access JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE street_edges ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';
UPDATE street_edges SET id = gen_random_uuid() WHERE id IS NULL;
ALTER TABLE street_edges ALTER COLUMN id SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS street_edges_uuid_idx ON street_edges (id);
CREATE UNIQUE INDEX IF NOT EXISTS street_edges_legacy_key_uidx
    ON street_edges (street_edge_id);
ALTER TABLE street_edge_ownership
    DROP CONSTRAINT IF EXISTS street_edge_ownership_street_edge_id_fkey;
DO $$
DECLARE
    current_primary_key TEXT;
    primary_key_uses_id BOOLEAN;
BEGIN
    SELECT constraint_name
      INTO current_primary_key
      FROM information_schema.table_constraints
     WHERE table_schema = current_schema()
       AND table_name = 'street_edges'
       AND constraint_type = 'PRIMARY KEY'
     LIMIT 1;

    SELECT EXISTS (
      SELECT 1
      FROM information_schema.key_column_usage
      WHERE table_schema = current_schema()
        AND table_name = 'street_edges'
        AND constraint_name = current_primary_key
        AND column_name = 'id'
    ) INTO primary_key_uses_id;

    IF current_primary_key IS NOT NULL AND NOT primary_key_uses_id THEN
        EXECUTE format(
          'ALTER TABLE street_edges DROP CONSTRAINT %I',
          current_primary_key
        );
        current_primary_key := NULL;
    END IF;
    IF current_primary_key IS NULL THEN
        ALTER TABLE street_edges
          ADD CONSTRAINT street_edges_pkey PRIMARY KEY (id);
    END IF;
END $$;
DO $$
BEGIN
    IF NOT EXISTS (
      SELECT 1
      FROM information_schema.table_constraints
      WHERE table_schema=current_schema()
        AND table_name='street_edge_ownership'
        AND constraint_name='street_edge_ownership_street_edge_id_fkey'
    ) THEN
        ALTER TABLE street_edge_ownership
          ADD CONSTRAINT street_edge_ownership_street_edge_id_fkey
          FOREIGN KEY (street_edge_id)
          REFERENCES street_edges(street_edge_id);
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS street_edges_region_cell_idx
    ON street_edges (osm_region_id, spatial_cell, status);

DO $$
BEGIN
    IF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema=current_schema()
        AND table_name='segment_efforts'
        AND column_name='effort_id'
    ) AND NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema=current_schema()
        AND table_name='segment_efforts'
        AND column_name='id'
    ) THEN
        ALTER TABLE segment_efforts RENAME COLUMN effort_id TO id;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS street_edge_aliases (
    id UUID PRIMARY KEY,
    old_street_edge_id UUID NOT NULL,
    new_street_edge_id UUID NOT NULL,
    old_graph_version_id UUID REFERENCES osm_graph_versions(id),
    new_graph_version_id UUID REFERENCES osm_graph_versions(id),
    overlap_ratio DOUBLE PRECISION NOT NULL CHECK (overlap_ratio BETWEEN 0 AND 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (old_street_edge_id, new_street_edge_id, new_graph_version_id)
);

CREATE TABLE IF NOT EXISTS matched_edge_traversals (
    id UUID PRIMARY KEY,
    activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    street_edge_id UUID NOT NULL REFERENCES street_edges(id),
    user_id UUID NOT NULL,
    club_id UUID REFERENCES clubs(id),
    graph_version_id UUID REFERENCES osm_graph_versions(id),
    local_activity_date DATE NOT NULL,
    coverage DOUBLE PRECISION NOT NULL CHECK (coverage BETWEEN 0 AND 1),
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    elapsed_time_sec DOUBLE PRECISION,
    speed_mps DOUBLE PRECISION,
    qualified BOOLEAN NOT NULL,
    rejection_reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
    matched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (activity_id, street_edge_id)
);
CREATE INDEX IF NOT EXISTS matched_traversals_scoring_idx
    ON matched_edge_traversals (street_edge_id, local_activity_date DESC, qualified);
CREATE INDEX IF NOT EXISTS matched_traversals_user_idx
    ON matched_edge_traversals (user_id, local_activity_date DESC);
CREATE INDEX IF NOT EXISTS matched_traversals_club_idx
    ON matched_edge_traversals (club_id, local_activity_date DESC)
    WHERE club_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS territory_scores (
    id UUID PRIMARY KEY,
    street_edge_id UUID NOT NULL REFERENCES street_edges(id),
    controller_type controller_type NOT NULL,
    controller_id UUID NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    fastest_time_sec DOUBLE PRECISION,
    score_reached_at TIMESTAMPTZ,
    scoring_days INTEGER NOT NULL,
    window_started_at TIMESTAMPTZ NOT NULL,
    window_ends_at TIMESTAMPTZ NOT NULL,
    computation_version TEXT NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (street_edge_id, controller_type, controller_id)
);
CREATE INDEX IF NOT EXISTS territory_scores_edge_rank_idx
    ON territory_scores (street_edge_id, controller_type, score DESC);
CREATE INDEX IF NOT EXISTS territory_scores_controller_idx
    ON territory_scores (controller_type, controller_id, score DESC);

CREATE TABLE IF NOT EXISTS territory_current_control (
    street_edge_id UUID NOT NULL REFERENCES street_edges(id),
    controller_type controller_type NOT NULL,
    controller_id UUID NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    fastest_time_sec DOUBLE PRECISION,
    score_reached_at TIMESTAMPTZ,
    controlled_since TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (street_edge_id, controller_type)
);
CREATE INDEX IF NOT EXISTS territory_control_controller_idx
    ON territory_current_control (controller_type, controller_id, expires_at DESC);

CREATE TABLE IF NOT EXISTS territory_control_history (
    id UUID PRIMARY KEY,
    street_edge_id UUID NOT NULL REFERENCES street_edges(id),
    controller_type controller_type NOT NULL,
    previous_controller_id UUID,
    controller_id UUID,
    event_type TEXT NOT NULL CHECK (event_type IN ('claim', 'defence', 'loss', 'expiry', 'disputed')),
    previous_score DOUBLE PRECISION,
    score DOUBLE PRECISION,
    source_activity_id UUID REFERENCES activities(id),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS territory_history_edge_idx
    ON territory_control_history (street_edge_id, occurred_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS territory_history_source_identity_idx
    ON territory_control_history (
        street_edge_id, controller_type, source_activity_id, event_type,
        COALESCE(previous_controller_id, '00000000-0000-0000-0000-000000000000'::uuid),
        COALESCE(controller_id, '00000000-0000-0000-0000-000000000000'::uuid)
    )
    WHERE source_activity_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS seasons (
    id UUID PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('scheduled', 'active', 'closed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (ends_at > starts_at)
);

CREATE TABLE IF NOT EXISTS challenges (
    id UUID PRIMARY KEY,
    club_id UUID REFERENCES clubs(id) ON DELETE CASCADE,
    season_id UUID REFERENCES seasons(id),
    created_by_user_id UUID NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    metric TEXT NOT NULL CHECK (metric IN (
        'distance_m', 'moving_time_sec', 'run_count', 'consistency_days',
        'territory_gain_m', 'fastest_segment_sec'
    )),
    target DOUBLE PRECISION,
    segment_id UUID,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft', 'scheduled', 'active', 'completed', 'cancelled')),
    visibility activity_visibility NOT NULL DEFAULT 'club',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (ends_at > starts_at)
);
CREATE INDEX IF NOT EXISTS challenges_club_time_idx
    ON challenges (club_id, starts_at DESC);

CREATE TABLE IF NOT EXISTS challenge_entries (
    id UUID PRIMARY KEY,
    challenge_id UUID NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    score DOUBLE PRECISION NOT NULL DEFAULT 0,
    progress JSONB NOT NULL DEFAULT '{}'::jsonb,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (challenge_id, user_id)
);

CREATE TABLE IF NOT EXISTS races (
    id UUID PRIMARY KEY,
    club_id UUID REFERENCES clubs(id) ON DELETE CASCADE,
    season_id UUID REFERENCES seasons(id),
    created_by_user_id UUID NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    timezone TEXT NOT NULL,
    starts_at TIMESTAMPTZ NOT NULL,
    start_window_minutes INTEGER NOT NULL CHECK (start_window_minutes BETWEEN 5 AND 180),
    result_cutoff_at TIMESTAMPTZ NOT NULL,
    participant_capacity INTEGER CHECK (participant_capacity > 0),
    route GEOMETRY(LineString, 4326) NOT NULL,
    route_distance_m DOUBLE PRECISION NOT NULL,
    start_radius_m DOUBLE PRECISION NOT NULL DEFAULT 50,
    end_radius_m DOUBLE PRECISION NOT NULL DEFAULT 50,
    minimum_route_coverage DOUBLE PRECISION NOT NULL DEFAULT 0.9,
    status TEXT NOT NULL CHECK (status IN ('draft', 'scheduled', 'active', 'completed', 'cancelled')),
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS races_club_time_idx ON races (club_id, starts_at DESC);
CREATE INDEX IF NOT EXISTS races_route_gix ON races USING GIST (route);

CREATE TABLE IF NOT EXISTS race_entries (
    id UUID PRIMARY KEY,
    race_id UUID NOT NULL REFERENCES races(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (race_id, user_id)
);

CREATE TABLE IF NOT EXISTS race_results (
    id UUID PRIMARY KEY,
    race_id UUID NOT NULL REFERENCES races(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    activity_id UUID NOT NULL REFERENCES activities(id),
    elapsed_time_sec DOUBLE PRECISION,
    route_coverage DOUBLE PRECISION,
    verification verification_status NOT NULL DEFAULT 'provisional',
    rejection_reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    verified_at TIMESTAMPTZ,
    UNIQUE (race_id, user_id),
    UNIQUE (race_id, activity_id)
);

CREATE TABLE IF NOT EXISTS achievements (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    club_id UUID REFERENCES clubs(id),
    activity_id UUID REFERENCES activities(id),
    achievement_type TEXT NOT NULL,
    key TEXT NOT NULL,
    title TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    awarded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, key)
);

CREATE TABLE IF NOT EXISTS leaderboard_facts (
    id UUID PRIMARY KEY,
    subject_type TEXT NOT NULL CHECK (subject_type IN ('athlete', 'club', 'city', 'country')),
    subject_id UUID NOT NULL,
    club_id UUID REFERENCES clubs(id),
    region_id UUID REFERENCES regions(id),
    activity_id UUID REFERENCES activities(id) ON DELETE CASCADE,
    visibility activity_visibility NOT NULL DEFAULT 'club',
    occurred_at TIMESTAMPTZ NOT NULL,
    distance_m DOUBLE PRECISION NOT NULL DEFAULT 0,
    moving_time_sec INTEGER NOT NULL DEFAULT 0,
    run_count INTEGER NOT NULL DEFAULT 0,
    consistency_date DATE,
    territory_gain_m DOUBLE PRECISION NOT NULL DEFAULT 0,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (subject_type, subject_id, activity_id)
);
CREATE INDEX IF NOT EXISTS leaderboard_facts_period_idx
    ON leaderboard_facts (subject_type, occurred_at DESC, subject_id);
CREATE INDEX IF NOT EXISTS leaderboard_facts_public_idx
    ON leaderboard_facts (occurred_at DESC, subject_type, subject_id)
    WHERE visibility = 'public';

CREATE TABLE IF NOT EXISTS leaderboard_snapshots (
    id UUID PRIMARY KEY,
    leaderboard_key TEXT NOT NULL,
    period_key TEXT NOT NULL,
    version INTEGER NOT NULL,
    rows JSONB NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    immutable BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (leaderboard_key, period_key, version)
);

CREATE TABLE IF NOT EXISTS system_activity_events (
    id UUID PRIMARY KEY,
    club_id UUID REFERENCES clubs(id) ON DELETE CASCADE,
    actor_user_id UUID,
    event_type TEXT NOT NULL,
    visibility activity_visibility NOT NULL DEFAULT 'club',
    source_type TEXT NOT NULL,
    source_id UUID,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    idempotency_key TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS system_events_club_idx
    ON system_activity_events (club_id, occurred_at DESC);

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    event_id UUID REFERENCES system_activity_events(id) ON DELETE SET NULL,
    notification_type TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    read_at TIMESTAMPTZ,
    push_status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS notifications_user_idx
    ON notifications (user_id, read_at, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS notifications_event_recipient_idx
    ON notifications (user_id, event_id, notification_type)
    WHERE event_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS push_tokens (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    encrypted_token TEXT NOT NULL,
    platform TEXT NOT NULL CHECK (platform IN ('ios', 'android')),
    disabled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS competition_flags (
    id UUID PRIMARY KEY,
    activity_id UUID REFERENCES activities(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    reported_by_user_id UUID,
    reason_code TEXT NOT NULL,
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL CHECK (status IN ('open', 'reviewing', 'upheld', 'dismissed', 'appealed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS competition_flags_queue_idx
    ON competition_flags (status, created_at);

CREATE TABLE IF NOT EXISTS moderation_decisions (
    id UUID PRIMARY KEY,
    flag_id UUID NOT NULL REFERENCES competition_flags(id) ON DELETE CASCADE,
    moderator_user_id UUID NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('uphold', 'dismiss', 'reopen')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS moderation_appeals (
    id UUID PRIMARY KEY,
    flag_id UUID NOT NULL REFERENCES competition_flags(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'accepted', 'rejected')),
    resolved_by_user_id UUID,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (flag_id, user_id)
);
CREATE INDEX IF NOT EXISTS moderation_appeals_queue_idx
    ON moderation_appeals (status, created_at);

CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY,
    actor_user_id UUID,
    club_id UUID REFERENCES clubs(id),
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id UUID,
    request_id TEXT,
    before_state JSONB,
    after_state JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS audit_events_club_idx
    ON audit_events (club_id, occurred_at DESC);

CREATE TABLE IF NOT EXISTS outbox_events (
    id UUID PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    aggregate_type TEXT NOT NULL,
    aggregate_id UUID NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'retry', 'completed', 'dead_letter')),
    attempts INTEGER NOT NULL DEFAULT 0,
    available_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    lease_expires_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS outbox_pending_idx
    ON outbox_events (available_at, created_at)
    WHERE status IN ('pending', 'retry');
ALTER TABLE notifications
    ADD COLUMN IF NOT EXISTS outbox_event_id UUID REFERENCES outbox_events(id);
CREATE UNIQUE INDEX IF NOT EXISTS notifications_outbox_recipient_idx
    ON notifications (user_id, outbox_event_id, notification_type)
    WHERE outbox_event_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS idempotency_records (
    user_id UUID NOT NULL,
    scope TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    response_status INTEGER NOT NULL,
    response_body JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '24 hours',
    PRIMARY KEY (user_id, scope, idempotency_key)
);
CREATE INDEX IF NOT EXISTS idempotency_expiry_idx ON idempotency_records (expires_at);
