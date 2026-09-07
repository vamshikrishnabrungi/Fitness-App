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
    test_database_url: str
    cloud_sql_instance: str
    cloud_sql_ip_type: str
    database_user: str
    database_password: str
    database_name: str
    database_pool_size: int
    database_max_overflow: int
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
    dem_provider_url: str
    valhalla_url: str
    valhalla_urls: tuple[tuple[str, str], ...]
    resend_api_key: str
    resend_from: str
    email_provider: str
    smtp_host: str
    smtp_port: int
    smtp_secure: bool
    smtp_user: str
    smtp_password: str
    smtp_from_name: str
    sentry_dsn: str
    expo_access_token: str
    kms_key_name: str
    generation_enabled: bool
    admin_studio_open_access: bool
    admin_iap_audience: str
    otp_debug_enabled: bool

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
    environment = os.getenv("ENVIRONMENT", "development").strip().lower()
    if environment not in {"development", "staging", "production", "test"}:
        raise RuntimeError("ENVIRONMENT must be development, staging, production, or test")
    cloud_sql_instance = os.getenv("CLOUD_SQL_INSTANCE", "").strip()
    test_database_url = os.getenv("TEST_DATABASE_URL", "").strip()
    if environment == "test":
        if not test_database_url:
            raise RuntimeError("TEST_DATABASE_URL is required in the test environment")
    elif not cloud_sql_instance:
        raise RuntimeError("CLOUD_SQL_INSTANCE is required outside the test environment")
    cloud_sql_ip_type = os.getenv(
        "CLOUD_SQL_IP_TYPE", "PRIVATE" if environment in {"staging", "production"} else "PUBLIC"
    ).strip().upper()
    if cloud_sql_ip_type not in {"PRIVATE", "PUBLIC"}:
        raise RuntimeError("CLOUD_SQL_IP_TYPE must be PRIVATE or PUBLIC")
    secret = os.getenv("JWT_SECRET", "")
    otp_pepper = os.getenv("OTP_PEPPER", "")
    if environment == "production" and (len(secret) < 32 or len(otp_pepper) < 32):
        raise RuntimeError("JWT_SECRET and OTP_PEPPER must each contain at least 32 characters")
    if environment != "test" and not os.getenv("DATABASE_PASSWORD"):
        raise RuntimeError("DATABASE_PASSWORD is required for Cloud SQL")
    redis_url = os.getenv("REDIS_URL", "").strip()
    if environment != "test" and not redis_url:
        raise RuntimeError("REDIS_URL is required outside the test environment")
    if environment != "test":
        required_gcp = {
            "GOOGLE_CLOUD_PROJECT": os.getenv("GOOGLE_CLOUD_PROJECT", ""),
            "KMS_KEY_NAME": os.getenv("KMS_KEY_NAME", ""),
            "RAW_ACTIVITY_BUCKET": os.getenv("RAW_ACTIVITY_BUCKET", ""),
            "IMPORT_BUCKET": os.getenv("IMPORT_BUCKET", ""),
            "EXERCISE_MEDIA_BUCKET": os.getenv("EXERCISE_MEDIA_BUCKET", ""),
            "NUTRITION_IMAGE_BUCKET": os.getenv("NUTRITION_IMAGE_BUCKET", ""),
            "EXPORT_BUCKET": os.getenv("EXPORT_BUCKET", ""),
            "VALHALLA_GRAPH_BUCKET": os.getenv("VALHALLA_GRAPH_BUCKET", ""),
        }
        missing = sorted(name for name, value in required_gcp.items() if not value.strip())
        if missing:
            raise RuntimeError(f"Managed GCP configuration is incomplete: {', '.join(missing)}")
        if not os.getenv("VALHALLA_URL", "").strip() and not os.getenv("VALHALLA_URLS_JSON", "").strip():
            raise RuntimeError("VALHALLA_URL or VALHALLA_URLS_JSON is required outside tests")
    admin_studio_open_access = os.getenv(
        "ADMIN_STUDIO_OPEN_ACCESS",
        "false",
    ).lower() == "true"
    otp_debug_enabled = os.getenv("OTP_DEBUG_ENABLED", "false").lower() == "true"
    if environment in {"staging", "production"} and (admin_studio_open_access or otp_debug_enabled):
        raise RuntimeError("Admin open access and OTP debugging are forbidden in staging and production")
    email_provider = os.getenv("EMAIL_PROVIDER", "resend").strip().lower()
    if email_provider not in {"resend", "smtp"}:
        raise RuntimeError("EMAIL_PROVIDER must be resend or smtp")
    admin_iap_audience = os.getenv("ADMIN_IAP_AUDIENCE", "").strip()
    if environment in {"staging", "production"} and not admin_iap_audience:
        raise RuntimeError("ADMIN_IAP_AUDIENCE is required in staging and production")
    database_pool_size = int(os.getenv("DATABASE_POOL_SIZE", "5"))
    database_max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "5"))
    if not 1 <= database_pool_size <= 20 or not 0 <= database_max_overflow <= 20:
        raise RuntimeError("Database pool settings exceed the supported per-instance bounds")
    return Settings(
        environment=environment,
        test_database_url=test_database_url,
        cloud_sql_instance=cloud_sql_instance,
        cloud_sql_ip_type=cloud_sql_ip_type,
        database_user=os.getenv("DATABASE_USER", "runlete"),
        database_password=os.getenv("DATABASE_PASSWORD", ""),
        database_name=os.getenv("DATABASE_NAME", "runlete"),
        database_pool_size=database_pool_size,
        database_max_overflow=database_max_overflow,
        redis_url=redis_url,
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
        dem_provider_url=os.getenv("DEM_PROVIDER_URL", ""),
        valhalla_url=os.getenv("VALHALLA_URL", ""),
        valhalla_urls=_url_map("VALHALLA_URLS_JSON"),
        resend_api_key=os.getenv("RESEND_API_KEY", ""),
        resend_from=os.getenv("RESEND_FROM", "Runlete <noreply@runlete.com>"),
        email_provider=email_provider,
        smtp_host=os.getenv("SMTP_HOST", ""),
        smtp_port=int(os.getenv("SMTP_PORT", "465")),
        smtp_secure=os.getenv("SMTP_SECURE", "true").lower() == "true",
        smtp_user=os.getenv("INFO_EMAIL_USER", ""),
        smtp_password=os.getenv("INFO_EMAIL_PASS", ""),
        smtp_from_name=os.getenv("SMTP_FROM_NAME", "Runlete"),
        sentry_dsn=os.getenv("SENTRY_DSN", ""),
        expo_access_token=os.getenv("EXPO_ACCESS_TOKEN", ""),
        kms_key_name=os.getenv("KMS_KEY_NAME", ""),
        generation_enabled=os.getenv("TRAINING_GENERATION_ENABLED", "false").lower() == "true",
        admin_studio_open_access=admin_studio_open_access,
        admin_iap_audience=admin_iap_audience,
        otp_debug_enabled=otp_debug_enabled,
    )
