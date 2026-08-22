from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Coordinate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    elevation_m: float | None = Field(default=None, ge=-500, le=9000)


class RouteCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    visibility: Literal["public", "private"] = "private"
    surface: str = Field(default="unknown", min_length=2, max_length=40)
    path: list[Coordinate] = Field(min_length=2, max_length=20_000)


class RouteGenerate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    target_distance_km: float = Field(default=5, ge=1, le=100)
    surface: Literal["any", "paved", "trail"] = "any"
    avoid_hills: bool = False


class RouteUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    visibility: Literal["public", "private"] | None = None
    expected_version: int = Field(ge=1)


class SegmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    visibility: Literal["public", "private"] = "public"
    path: list[Coordinate] = Field(min_length=2, max_length=5000)

    @model_validator(mode="after")
    def distinct_endpoints(self) -> "SegmentCreate":
        first, last = self.path[0], self.path[-1]
        if first.latitude == last.latitude and first.longitude == last.longitude:
            raise ValueError("Segment start and end must be different")
        return self
