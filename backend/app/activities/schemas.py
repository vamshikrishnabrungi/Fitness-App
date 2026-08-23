from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ActivityStart(BaseModel):
    started_at: datetime
    visibility: str = Field(default="private", pattern="^(public|club|private)$")
    surface: str = Field(default="road", pattern="^(road|trail|park|track)$")


class ActivityTransition(BaseModel):
    expected_version: int = Field(ge=1)
    ended_at: datetime | None = None
    device_distance_m: float | None = Field(default=None, ge=0, le=300000)


class ActivityView(BaseModel):
    id: UUID
    status: str
    visibility: str
    started_at: datetime
    ended_at: datetime | None
    elapsed_seconds: int | None
    moving_seconds: int | None
    distance_m: float | None
    average_pace_s_per_km: float | None
    competition_eligible: bool | None
    processing_message: str | None
    version: int


class ActivityListPage(BaseModel):
    items: list[ActivityView]
    next_cursor: str | None = None


class ActivitySplitView(BaseModel):
    sequence: int
    distance_m: float
    elapsed_seconds: float
    pace_s_per_km: float | None
    elevation_delta_m: float | None
    average_hr: int | None


class BestEffortView(BaseModel):
    distance_code: str
    distance_m: float
    elapsed_seconds: float
    pace_s_per_km: float
    quality_passed: bool
    is_personal_record: bool


class SegmentEffortView(BaseModel):
    segment_id: UUID
    segment_name: str
    elapsed_seconds: float
    coverage: float
    quality_passed: bool


class ActivityQualityView(BaseModel):
    gps_score: float
    duplicate_status: str
    speed_status: str
    vehicle_status: str
    matcher_confidence: float | None
    competition_eligible: bool
    territory_eligible: bool
    reasons: list[str]


class ActivityDetailView(BaseModel):
    id: UUID
    source: str
    sport_type: str
    surface: str
    distance_source: str
    device_distance_m: float | None
    server_confirmation_delta_m: float | None
    elevation_source: str | None
    status: str
    visibility: str
    title: str | None
    started_at: datetime
    ended_at: datetime | None
    elapsed_seconds: int | None
    moving_seconds: int | None
    paused_seconds: int | None
    distance_m: float | None
    elevation_gain_m: float | None
    average_pace_s_per_km: float | None
    calories_kcal: float | None
    average_hr: int | None
    average_cadence: float | None
    route: list[dict[str, float]]
    splits: list[ActivitySplitView]
    best_efforts: list[BestEffortView]
    segment_efforts: list[SegmentEffortView]
    quality: ActivityQualityView | None
    attributed_club_id: UUID | None
    roads_verified_m: float
    processing_message: str | None
    rejection_code: str | None
    processing_error_code: str | None
    schema_version: int
    computation_version: str | None
    version: int


class ImportUploadRequest(BaseModel):
    filename: str = Field(min_length=3, max_length=240)
    content_type: str = Field(pattern="^(application/(gpx\\+xml|vnd.garmin.tcx\\+xml|octet-stream)|text/xml)$")
    content_hash: str = Field(min_length=64, max_length=64, pattern="^[0-9a-f]{64}$")
    size_bytes: int = Field(gt=0, le=25 * 1024 * 1024)
    visibility: str = Field(default="private", pattern="^(public|club|private)$")


class ImportUploadView(BaseModel):
    id: UUID
    status: str
    object_name: str
    upload_url: str
    expires_at: datetime


class ImportCompleteCommand(BaseModel):
    expected_version: int = Field(ge=1)


class HealthMetricInput(BaseModel):
    provider_record_id: str = Field(min_length=1, max_length=500)
    metric_code: str = Field(pattern="^(sleep_duration_min|resting_hr_bpm|hrv_rmssd_ms|steps|active_energy_kcal|body_mass_kg)$")
    started_at: datetime
    ended_at: datetime
    value: float = Field(ge=0, le=1_000_000)
    unit: str = Field(min_length=1, max_length=30)
    source_name: str | None = Field(default=None, max_length=120)


class HealthBatchCommand(BaseModel):
    provider: str = Field(pattern="^(apple_health|health_connect)$")
    records: list[HealthMetricInput] = Field(min_length=1, max_length=500)


class ActivityFeedbackCommand(BaseModel):
    feeling: str = Field(max_length=30)
    session_rpe: float | None = Field(default=None, ge=0, le=10)
    notes: str | None = Field(default=None, max_length=2000)


class ChunkUploadRequest(BaseModel):
    chunk_number: int = Field(ge=0, le=100000)
    content_hash: str = Field(min_length=64, max_length=64)
    sample_count: int = Field(ge=1, le=100000)
    content_type: str = Field(default="application/json", pattern="^application/(json|octet-stream)$")


class ChunkUploadView(BaseModel):
    chunk_number: int
    object_name: str
    upload_url: str
    expires_at: datetime


class ActivityEditCommand(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    visibility: str | None = Field(default=None, pattern="^(public|club|private)$")
    expected_version: int = Field(ge=1)


class ActivityCropCommand(BaseModel):
    start_offset_seconds: int = Field(default=0, ge=0)
    end_offset_seconds: int = Field(default=0, ge=0)
    expected_version: int = Field(ge=1)


class ManualActivityCreate(BaseModel):
    started_at: datetime
    duration_seconds: int = Field(gt=0, le=172800)
    distance_m: float = Field(ge=0, le=300000)
    title: str | None = Field(default=None, max_length=160)
    treadmill: bool = False
    visibility: str = Field(default="private", pattern="^(public|club|private)$")
