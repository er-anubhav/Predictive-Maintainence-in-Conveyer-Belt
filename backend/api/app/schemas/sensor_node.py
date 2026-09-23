from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SensorNodeBase(BaseModel):
    conveyor_id: int = Field(..., description="ID of the parent conveyor")
    node_code: str = Field(..., min_length=1, max_length=100, description="Unique node hardware code, e.g. NODE-001")
    location: str = Field(..., min_length=1, max_length=255, description="Physical installation point, e.g. Head Pulley")
    firmware_version: str = Field(default="v1.0.0", max_length=50)
    status: str = Field(default="ONLINE", max_length=50)


class SensorNodeCreate(SensorNodeBase):
    pass


class SensorNodeResponse(SensorNodeBase):
    id: int
    last_seen: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
