from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass
from typing import Optional


class ObjectStorageError(RuntimeError):
    pass


@dataclass(frozen=True)
class StoredObject:
    bucket: str
    key: str
    size_bytes: int


def object_storage_configured() -> bool:
    return bool(
        os.environ.get('S3_BUCKET')
        and os.environ.get('S3_ACCESS_KEY_ID')
        and os.environ.get('S3_SECRET_ACCESS_KEY')
    )


def _safe_filename(filename: str) -> str:
    base = (filename or 'activity').rsplit('/', 1)[-1].rsplit('\\', 1)[-1]
    cleaned = re.sub(r'[^A-Za-z0-9._-]+', '-', base).strip('.-')
    return (cleaned or 'activity')[:180]


def _store_sync(content: bytes, user_id: str, job_id: str, filename: str) -> StoredObject:
    try:
        import boto3
    except ImportError as exc:  # pragma: no cover - dependency is part of runtime image
        raise ObjectStorageError('boto3 is unavailable') from exc

    bucket = os.environ['S3_BUCKET']
    key = f'activity-imports/{user_id}/{job_id}/{_safe_filename(filename)}'
    client = boto3.client(
        's3',
        region_name=os.environ.get('S3_REGION') or None,
        endpoint_url=os.environ.get('S3_ENDPOINT_URL') or None,
        aws_access_key_id=os.environ.get('S3_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('S3_SECRET_ACCESS_KEY'),
    )
    try:
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=content,
            ContentType='application/octet-stream',
            ServerSideEncryption='AES256',
            Metadata={'runlete-job-id': job_id, 'runlete-user-id': user_id},
        )
    except Exception as exc:  # boto providers expose several client-specific errors
        raise ObjectStorageError(f'Unable to preserve original activity file: {exc}') from exc
    return StoredObject(bucket=bucket, key=key, size_bytes=len(content))


async def store_activity_original(
    content: bytes,
    *,
    user_id: str,
    job_id: str,
    filename: str,
) -> Optional[StoredObject]:
    """Store an immutable import original when S3-compatible storage is configured."""
    if not object_storage_configured():
        return None
    return await asyncio.to_thread(_store_sync, content, user_id, job_id, filename)


def _delete_sync(bucket: str, key: str) -> None:
    import boto3

    client = boto3.client(
        's3',
        region_name=os.environ.get('S3_REGION') or None,
        endpoint_url=os.environ.get('S3_ENDPOINT_URL') or None,
        aws_access_key_id=os.environ.get('S3_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('S3_SECRET_ACCESS_KEY'),
    )
    client.delete_object(Bucket=bucket, Key=key)


async def delete_stored_object(bucket: Optional[str], key: Optional[str]) -> bool:
    if not bucket or not key or not object_storage_configured():
        return False
    try:
        await asyncio.to_thread(_delete_sync, bucket, key)
    except Exception as exc:
        raise ObjectStorageError(f'Unable to delete stored object: {exc}') from exc
    return True
