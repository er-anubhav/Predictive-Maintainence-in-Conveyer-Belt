from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class MineBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Name of the mining site")
    location: str = Field(..., min_length=1, max_length=255, description="Geographical or sector location")


class MineCreate(MineBase):
    pass


class MineResponse(MineBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
