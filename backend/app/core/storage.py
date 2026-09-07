from __future__ import annotations

from datetime import timedelta

import anyio


async def gcs_object_metadata(*, project_id: str, bucket: str, object_name: str) -> dict[str, object]:
    """Load trusted object metadata before allocating memory for its contents."""

    def load() -> dict[str, object]:
        from google.cloud import storage

        blob = storage.Client(project=project_id or None).bucket(bucket).blob(object_name)
        blob.reload()
        return {"size": int(blob.size or 0), "content_type": blob.content_type or "", "generation": int(blob.generation or 0)}

    return await anyio.to_thread.run_sync(load)


async def download_gcs_bytes(*, project_id: str, bucket: str, object_name: str, max_bytes: int, generation: int | None = None) -> bytes:
    """Read an object without exposing it to an external AI provider by URL."""

    def download() -> bytes:
        from google.cloud import storage

        blob = storage.Client(project=project_id or None).bucket(bucket).blob(object_name)
        blob.reload()
        if int(blob.size or 0) <= 0 or int(blob.size or 0) > max_bytes:
            raise ValueError("object size is outside the permitted range")
        if generation is not None and int(blob.generation or 0) != generation:
            raise ValueError("object generation changed after validation")
        content = blob.download_as_bytes(end=max_bytes - 1, if_generation_match=generation)
        if len(content) > max_bytes:
            raise ValueError("object exceeds the permitted size")
        return content

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
