from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


# Local commands load the same development configuration as the deployed
# service. Real Cloud Run variables still win because override is disabled.
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


def _csv(name: str, default: str = "") -> tuple[str, ...]:
    return tuple(item.strip() for item in os.getenv(name, default).split(",") if item.strip())


def _url_map(name: str) -> tuple[tuple[str, str], ...]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return ()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{name} must be a JSON object") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{name} must be a JSON object")
    result: list[tuple[str, str]] = []
    for key, url in value.items():
        if not isinstance(key, str) or not isinstance(url, str) or not url.startswith(("http://", "https://")):
            raise RuntimeError(f"{name} contains an invalid region or URL")
        result.append((key.lower(), url.rstrip("/")))
    return tuple(sorted(result))


@dataclass(frozen=True)
class Settings:
    environment: str
    database_url: str
    cloud_sql_instance: str
    database_user: str
    database_password: str
    database_name: str
    redis_url: str
    jwt_secret: str
    jwt_issuer: str
    jwt_audience: str
    access_token_minutes: int
    refresh_token_days: int
    otp_pepper: str
    allowed_origins: tuple[str, ...]
    gcp_project_id: str
    gcp_region: str
    raw_activity_bucket: str
    import_bucket: str
    exercise_media_bucket: str
    nutrition_image_bucket: str
    export_bucket: str
    valhalla_graph_bucket: str
    openai_api_key: str
    openai_workout_model: str
    openai_food_model: str
    mapbox_public_token: str
    valhalla_url: str
    valhalla_urls: tuple[tuple[str, str], ...]
    resend_api_key: str
    resend_from: str
    sentry_dsn: str
    expo_access_token: str
    kms_key_name: str
    local_envelope_key: str
    generation_enabled: bool
    admin_studio_open_access: bool

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    def valhalla_url_for_region(self, region_code: str) -> str:
        urls = dict(self.valhalla_urls)
        if urls:
            return urls.get(region_code.lower(), "")
        return self.valhalla_url.rstrip("/")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    environment = os.getenv("ENVIRONMENT", "development")
    secret = os.getenv("JWT_SECRET", "")
    otp_pepper = os.getenv("OTP_PEPPER", "")
    if environment == "production" and (len(secret) < 32 or len(otp_pepper) < 32):
        raise RuntimeError("JWT_SECRET and OTP_PEPPER must each contain at least 32 characters")
    if environment == "production" and os.getenv("CLOUD_SQL_INSTANCE") and not os.getenv("DATABASE_PASSWORD"):
        raise RuntimeError("DATABASE_PASSWORD is required when Cloud SQL connector mode is enabled")
    admin_studio_open_access = os.getenv(
        "ADMIN_STUDIO_OPEN_ACCESS",
        "true" if environment.lower() == "development" else "false",
    ).lower() == "true"
    if environment.lower() == "production" and admin_studio_open_access:
        raise RuntimeError("ADMIN_STUDIO_OPEN_ACCESS cannot be enabled in production")
    return Settings(
        environment=environment,
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://runlete:runlete@localhost:5432/runlete",
        ),
        cloud_sql_instance=os.getenv("CLOUD_SQL_INSTANCE", ""),
        database_user=os.getenv("DATABASE_USER", "runlete"),
        database_password=os.getenv("DATABASE_PASSWORD", ""),
        database_name=os.getenv("DATABASE_NAME", "runlete"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        jwt_secret=secret or "development-only-change-me-development-only",
        jwt_issuer=os.getenv("JWT_ISSUER", "runlete-api"),
        jwt_audience=os.getenv("JWT_AUDIENCE", "runlete-mobile"),
        access_token_minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "15")),
        refresh_token_days=int(os.getenv("REFRESH_TOKEN_DAYS", "30")),
        otp_pepper=otp_pepper or "development-only-otp-pepper-change-me",
        allowed_origins=_csv("ALLOWED_ORIGINS", "http://localhost:8081,http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"),
        gcp_project_id=os.getenv("GOOGLE_CLOUD_PROJECT", ""),
        gcp_region=os.getenv("GOOGLE_CLOUD_REGION", "europe-west1"),
        raw_activity_bucket=os.getenv("RAW_ACTIVITY_BUCKET", ""),
        import_bucket=os.getenv("IMPORT_BUCKET", ""),
        exercise_media_bucket=os.getenv("EXERCISE_MEDIA_BUCKET", ""),
        nutrition_image_bucket=os.getenv("NUTRITION_IMAGE_BUCKET", ""),
        export_bucket=os.getenv("EXPORT_BUCKET", ""),
        valhalla_graph_bucket=os.getenv("VALHALLA_GRAPH_BUCKET", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_workout_model=os.getenv("OPENAI_WORKOUT_MODEL", "gpt-4o"),
        openai_food_model=os.getenv("OPENAI_FOOD_MODEL", "gpt-4o"),
        mapbox_public_token=os.getenv("MAPBOX_PUBLIC_TOKEN", ""),
        valhalla_url=os.getenv("VALHALLA_URL", "http://localhost:8002"),
        valhalla_urls=_url_map("VALHALLA_URLS_JSON"),
        resend_api_key=os.getenv("RESEND_API_KEY", ""),
        resend_from=os.getenv("RESEND_FROM", "Runlete <noreply@runlete.com>"),
        sentry_dsn=os.getenv("SENTRY_DSN", ""),
        expo_access_token=os.getenv("EXPO_ACCESS_TOKEN", ""),
        kms_key_name=os.getenv("KMS_KEY_NAME", ""),
        local_envelope_key=os.getenv("LOCAL_ENVELOPE_KEY", "development-envelope-key-change-me"),
        generation_enabled=os.getenv("TRAINING_GENERATION_ENABLED", "false").lower() == "true",
        admin_studio_open_access=admin_studio_open_access,
    )
