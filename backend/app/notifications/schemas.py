from typing import Literal

from pydantic import BaseModel, Field


class PushTokenRegister(BaseModel):
    platform: Literal["ios", "android"]
    token: str = Field(min_length=20, max_length=2000)

