from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

import hmac

import anyio
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.activities.service import athlete_id
from backend.app.core.config import get_settings
from backend.app.core.database import get_session
from backend.app.core.ids import uuid7
from backend.app.core.problems import ProblemError
from backend.app.core.security import current_user_id, hash_secret
from backend.app.core.storage import gcs_object_metadata, signed_gcs_url
from backend.app.operations.outbox import enqueue_event
from .models import FoodAnalysis, FoodImage, Meal
from .schemas import AnalyzeCommand, MealConfirm, UploadRequest, UploadView

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


@router.get("/daily-summary")
async def daily_summary(
    local_date: date | None = Query(default=None, alias="date"),
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    from sqlalchemy import select
    athlete = await athlete_id(session, user_id)
    selected_date = local_date or datetime.now(timezone.utc).date()
    starts_at = datetime.combine(selected_date, time.min, timezone.utc)
    ends_at = starts_at + timedelta(days=1)
    rows = (
        await session.scalars(
            select(Meal)
            .where(Meal.athlete_id == athlete, Meal.eaten_at >= starts_at, Meal.eaten_at < ends_at)
            .order_by(Meal.eaten_at, Meal.id)
        )
    ).all()
    return {
        "date": selected_date,
        "calories_kcal": sum(float(row.calories_kcal) for row in rows),
        "protein_g": sum(float(row.protein_g) for row in rows),
        "carbohydrate_g": sum(float(row.carbohydrate_g) for row in rows),
        "fat_g": sum(float(row.fat_g) for row in rows),
        "fibre_g": sum(float(row.fibre_g or 0) for row in rows),
        "meals": [
            {
                "id": row.id,
                "name": row.name,
                "meal_type": row.meal_type,
                "eaten_at": row.eaten_at,
                "calories_kcal": float(row.calories_kcal),
                "protein_g": float(row.protein_g),
                "carbohydrate_g": float(row.carbohydrate_g),
                "fat_g": float(row.fat_g),
                "fibre_g": float(row.fibre_g or 0),
                "analysis_id": row.analysis_id,
                "confirmed_by_user": row.confirmed_by_user,
            }
            for row in rows
        ],
    }


async def _signed_upload(bucket: str, object_name: str, content_type: str) -> str:
    settings = get_settings()
    if not bucket:
        raise ProblemError(503, "storage_unavailable", "Storage unavailable", "Food uploads are not configured.")
    try:
        return await signed_gcs_url(
            project_id=settings.gcp_project_id,
            bucket=bucket,
            object_name=object_name,
            method="PUT",
            content_type=content_type,
        )
    except Exception as exc:
        raise ProblemError(503, "storage_signing_failed", "Upload unavailable", "A signed upload URL could not be created.") from exc


def _local_upload_token(image_id: UUID) -> str:
    return hash_secret(str(image_id), purpose="local-food-image-upload")


@router.post("/food-images/uploads", response_model=UploadView, status_code=201)
async def create_upload(body: UploadRequest, request: Request, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> UploadView:
    athlete = await athlete_id(session, user_id); settings = get_settings(); now = datetime.now(timezone.utc); image_id = uuid7(); bucket = settings.nutrition_image_bucket or "runlete-food-local"; name = f"athletes/{athlete}/{image_id}"
    row = FoodImage(id=image_id, athlete_id=athlete, bucket=bucket, object_name=name, content_type=body.content_type, size_bytes=body.size_bytes, retain=body.retain, expires_at=now + timedelta(days=30 if body.retain else 2))
    session.add(row); await session.commit()
    if settings.environment != "test":
        upload_url = await _signed_upload(bucket, name, body.content_type)
    else:
        upload_url = (
            f"{str(request.base_url).rstrip('/')}/api/v1/nutrition/food-images/{image_id}/content"
            f"?token={_local_upload_token(image_id)}"
        )
    return UploadView(image_id=image_id, upload_url=upload_url, expires_at=now + timedelta(minutes=15))


@router.put("/food-images/{image_id}/content", status_code=204, include_in_schema=False)
async def upload_local_food_image(
    image_id: UUID,
    token: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Development-only upload target matching production's signed-URL flow."""
    settings = get_settings()
    if settings.environment != "test":
        raise ProblemError(404, "not_found", "Not found", "The endpoint does not exist.")
    if not hmac.compare_digest(token, _local_upload_token(image_id)):
        raise ProblemError(403, "invalid_upload_token", "Upload forbidden", "The upload token is invalid.")
    image = await session.get(FoodImage, image_id)
    if image is None:
        raise ProblemError(404, "food_image_not_found", "Image not found", "The food image does not exist.")
    if image.expires_at <= datetime.now(timezone.utc):
        raise ProblemError(410, "upload_expired", "Upload expired", "Request a new food-image upload URL.")
    if request.headers.get("content-type", "").split(";", 1)[0] != image.content_type:
        raise ProblemError(422, "content_type_mismatch", "Invalid image", "The uploaded content type does not match the request.")
    content = await request.body()
    if not content or len(content) > 20 * 1024 * 1024:
        raise ProblemError(422, "invalid_image_size", "Invalid image", "Food images must be between 1 byte and 20 MB.")

    def upload() -> None:
        from google.cloud import storage

        client = storage.Client(project=settings.gcp_project_id or "runlete-local")
        bucket = client.bucket(image.bucket)
        if not bucket.exists():
            bucket = client.create_bucket(image.bucket)
        bucket.blob(image.object_name).upload_from_string(content, content_type=image.content_type)

    await anyio.to_thread.run_sync(upload)
    return Response(status_code=204)


@router.post("/food-analyses", status_code=202)
async def analyze(body: AnalyzeCommand, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    athlete = await athlete_id(session, user_id); image = await session.get(FoodImage, body.image_id)
    if image is None or image.athlete_id != athlete: raise ProblemError(404, "food_image_not_found", "Image not found", "The food image does not exist.")
    settings = get_settings()
    if settings.environment != "test":
        try:
            metadata = await gcs_object_metadata(project_id=settings.gcp_project_id, bucket=image.bucket, object_name=image.object_name)
        except Exception as exc:
            raise ProblemError(422, "food_image_missing", "Image unavailable", "Upload the image before requesting analysis.") from exc
        if metadata["size"] != image.size_bytes or metadata["size"] > 20 * 1024 * 1024 or metadata["content_type"] != image.content_type:
            raise ProblemError(422, "food_image_invalid", "Invalid image", "The uploaded image does not match its manifest.")
        image.object_generation = int(metadata["generation"])
    analysis = FoodAnalysis(image_id=image.id, athlete_id=athlete, status="queued", provider="openai", model_id=settings.openai_food_model, prompt_version="food-openai-v1", schema_version=1, source_object_hash=body.source_object_hash)
    session.add(analysis); await session.flush()
    await enqueue_event(session, topic="nutrition", event_type="nutrition.food_analysis.requested", aggregate_type="food_analysis", aggregate_id=analysis.id, payload={"analysis_id": str(analysis.id)})
    await session.commit()
    if not settings.is_production:
        # Local testing has no always-on Pub/Sub push worker. Execute the same
        # idempotent worker inline; production remains queue-driven.
        from backend.app.operations.worker_router import process_food_analysis

        await process_food_analysis(session, analysis.id)
        await session.refresh(analysis)
    return {"id": analysis.id, "status": analysis.status}


@router.get("/food-analyses/{analysis_id}")
async def analysis_detail(analysis_id: UUID, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    from sqlalchemy import select
    athlete=await athlete_id(session,user_id);row=await session.scalar(select(FoodAnalysis).where(FoodAnalysis.id==analysis_id,FoodAnalysis.athlete_id==athlete))
    if row is None: raise ProblemError(404,"food_analysis_not_found","Analysis not found","The food analysis does not exist.")
    return {"id":row.id,"status":row.status,"result":row.result_json,"confidence":float(row.confidence) if row.confidence is not None else None,"error_code":row.error_code}


@router.post("/meals", status_code=201)
async def confirm_meal(body: MealConfirm, user_id: UUID = Depends(current_user_id), session: AsyncSession = Depends(get_session)) -> dict:
    athlete = await athlete_id(session, user_id)
    if body.analysis_id is not None:
        from sqlalchemy import select
        analysis = await session.scalar(select(FoodAnalysis).where(FoodAnalysis.id == body.analysis_id, FoodAnalysis.athlete_id == athlete, FoodAnalysis.status == "complete"))
        if analysis is None:
            raise ProblemError(404, "food_analysis_not_found", "Analysis not found", "Choose a completed analysis from your account.")
    row = Meal(athlete_id=athlete, analysis_id=body.analysis_id, eaten_at=body.eaten_at, meal_type=body.meal_type, name=body.name, calories_kcal=body.calories_kcal, protein_g=body.protein_g, carbohydrate_g=body.carbohydrate_g, fat_g=body.fat_g, fibre_g=body.fibre_g, confirmed_by_user=True, items_json=body.items)
    session.add(row); await session.commit(); return {"id": row.id, "confirmed": True}
