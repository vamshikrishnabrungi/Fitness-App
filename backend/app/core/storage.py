from __future__ import annotations

from datetime import timedelta

import anyio


async def download_gcs_bytes(*, project_id: str, bucket: str, object_name: str) -> bytes:
    """Read an object without exposing it to an external AI provider by URL."""

    def download() -> bytes:
        from google.cloud import storage

        return (
            storage.Client(project=project_id or None)
            .bucket(bucket)
            .blob(object_name)
            .download_as_bytes()
        )

    return await anyio.to_thread.run_sync(download)


async def signed_gcs_url(
    *,
    project_id: str,
    bucket: str,
    object_name: str,
    method: str,
    content_type: str | None = None,
    expires: timedelta = timedelta(minutes=15),
) -> str:
    """Generate a V4 URL using IAM signBlob when running on Cloud Run."""

    def sign() -> str:
        import google.auth
        from google.auth.transport.requests import Request
        from google.cloud import storage

        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        credentials.refresh(Request())
        service_account_email = getattr(credentials, "service_account_email", None)
        if not service_account_email:
            raise RuntimeError("The runtime credential has no service account identity")
        blob = storage.Client(project=project_id or None).bucket(bucket).blob(object_name)
        return blob.generate_signed_url(
            version="v4",
            expiration=expires,
            method=method,
            content_type=content_type,
            service_account_email=service_account_email,
            access_token=credentials.token,
        )

    return await anyio.to_thread.run_sync(sign)
