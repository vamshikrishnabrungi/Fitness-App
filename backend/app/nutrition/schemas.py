from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NutrientRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    minimum: float = Field(ge=0)
    likely: float = Field(ge=0)
    maximum: float = Field(ge=0)
    unit: str

    @model_validator(mode="after")
    def ordered(self):
        if not self.minimum <= self.likely <= self.maximum: raise ValueError("nutrient range must be ordered")
        return self


class FoodCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    portion_description: str
    confidence: float = Field(ge=0, le=1)
    calories: NutrientRange
    protein: NutrientRange
    carbohydrate: NutrientRange
    fat: NutrientRange
    fibre: NutrientRange


class FoodAnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidates: list[FoodCandidate] = Field(min_length=1, max_length=20)
    overall_confidence: float = Field(ge=0, le=1)
    needs_user_review: bool


class UploadRequest(BaseModel):
    content_type: str = Field(pattern="^image/(jpeg|png|webp)$")
    size_bytes: int = Field(gt=0, le=20 * 1024 * 1024)
    retain: bool = False


class UploadView(BaseModel):
    image_id: UUID
    upload_url: str
    expires_at: datetime


class AnalyzeCommand(BaseModel):
    image_id: UUID
    source_object_hash: str = Field(min_length=64, max_length=64)


class MealConfirm(BaseModel):
    analysis_id: UUID | None = None
    eaten_at: datetime
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    name: str = Field(min_length=1, max_length=160)
    calories_kcal: float = Field(ge=0, le=10000)
    protein_g: float = Field(ge=0, le=1000)
    carbohydrate_g: float = Field(ge=0, le=2000)
    fat_g: float = Field(ge=0, le=1000)
    fibre_g: float | None = Field(default=None, ge=0, le=300)
    items: list[dict] = Field(default_factory=list)
