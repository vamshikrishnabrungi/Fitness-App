from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GeographicRegion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "geographic_regions"
    __table_args__ = (UniqueConstraint("code", name="uq_geographic_region_code"), {"schema": "activity"})
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    region_type: Mapped[str] = mapped_column(String(24), nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.geographic_regions.id"))
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    boundary: Mapped[Any] = mapped_column(Geometry("MULTIPOLYGON", srid=4326, spatial_index=True), nullable=False)


class OSMRegion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "osm_regions"
    __table_args__ = (UniqueConstraint("code", name="uq_osm_region_code"), {"schema": "activity"})
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    pbf_object: Mapped[str] = mapped_column(String(500), nullable=False)
    replication_sequence: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    boundary: Mapped[Any] = mapped_column(Geometry("MULTIPOLYGON", srid=4326, spatial_index=True), nullable=False)


class OSMGraphVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "osm_graph_versions"
    __table_args__ = (
        UniqueConstraint("region_id", "version_code", name="uq_osm_graph_version"),
        Index("uq_active_osm_graph_per_region", "region_id", unique=True, postgresql_where=text("status = 'active'")),
        {"schema": "activity"},
    )
    region_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.osm_regions.id", ondelete="CASCADE"), nullable=False)
    version_code: Mapped[str] = mapped_column(String(80), nullable=False)
    source_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    graph_object: Mapped[str] = mapped_column(String(500), nullable=False)
    graph_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StreetEdge(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "street_edges"
    __table_args__ = (UniqueConstraint("graph_version_id", "edge_key", name="uq_street_edge_version_key"), {"schema": "activity"})
    region_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.osm_regions.id"), nullable=False, index=True)
    graph_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.osm_graph_versions.id"), nullable=False)
    edge_key: Mapped[str] = mapped_column(String(180), nullable=False)
    osm_way_id: Mapped[int] = mapped_column(nullable=False, index=True)
    from_node_id: Mapped[int] = mapped_column(nullable=False)
    to_node_id: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str | None] = mapped_column(String(240))
    highway_class: Mapped[str] = mapped_column(String(40), nullable=False)
    surface: Mapped[str | None] = mapped_column(String(40))
    length_m: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    running_accessible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    spatial_cell: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    geometry: Mapped[Any] = mapped_column(Geometry("LINESTRING", srid=4326, spatial_index=True), nullable=False)


class StreetEdgeAlias(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "street_edge_aliases"
    __table_args__ = (UniqueConstraint("old_edge_id", "new_edge_id", name="uq_street_edge_alias"), {"schema": "activity"})
    old_edge_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.street_edges.id"), nullable=False)
    new_edge_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.street_edges.id"), nullable=False)
    overlap_ratio: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(20), nullable=False)


class MatchedEdgeTraversal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "matched_edge_traversals"
    __table_args__ = (UniqueConstraint("activity_id", "edge_id", "sequence", "computation_version", name="uq_matched_traversal"), {"schema": "activity"})
    activity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.activities.id", ondelete="CASCADE"), nullable=False, index=True)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    edge_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.street_edges.id"), nullable=False, index=True)
    graph_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.osm_graph_versions.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    coverage: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    elapsed_seconds: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    speed_mps: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    traversed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    local_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    qualifies: Mapped[bool] = mapped_column(Boolean, nullable=False)
    computation_version: Mapped[str] = mapped_column(String(40), nullable=False)


class Route(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "routes"
    __table_args__ = ({"schema": "activity"},)
    owner_athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    visibility: Mapped[str] = mapped_column(String(16), nullable=False)
    distance_m: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    elevation_gain_m: Mapped[float | None] = mapped_column(Numeric(10, 2))
    surface_mix_json: Mapped[dict[str, float]] = mapped_column(JSONB, default=dict, nullable=False)
    geometry: Mapped[Any] = mapped_column(Geometry("LINESTRING", srid=4326, spatial_index=True), nullable=False)
    source_object: Mapped[str | None] = mapped_column(String(500))


class Segment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "segments"
    __table_args__ = (UniqueConstraint("geometry_hash", name="uq_segment_geometry_hash"), {"schema": "activity"})
    creator_athlete_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    visibility: Mapped[str] = mapped_column(String(16), nullable=False)
    distance_m: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    geometry_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    geometry: Mapped[Any] = mapped_column(Geometry("LINESTRING", srid=4326, spatial_index=True), nullable=False)
    quality_votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class SegmentEffort(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "segment_efforts"
    __table_args__ = (UniqueConstraint("activity_id", "segment_id", "attempt_number", name="uq_segment_effort_attempt"), {"schema": "activity"})
    activity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.activities.id", ondelete="CASCADE"), nullable=False)
    segment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("activity.segments.id", ondelete="CASCADE"), nullable=False)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    elapsed_seconds: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    coverage: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    quality_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    achieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class HiddenMapZone(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "hidden_map_zones"
    __table_args__ = ({"schema": "activity"},)
    athlete_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("athlete.profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    radius_m: Mapped[int] = mapped_column(Integer, nullable=False)
    geometry_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    wrapped_dek: Mapped[str] = mapped_column(Text, nullable=False)
    kms_key_version: Mapped[str] = mapped_column(String(300), nullable=False)
