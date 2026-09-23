from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.sensor_node import SensorNodeResponse


class ConveyorBase(BaseModel):
    mine_id: int = Field(..., description="ID of the mine where this conveyor is installed")
    name: str = Field(..., min_length=1, max_length=255, description="Conveyor designation or name")
    belt_type: str = Field(..., min_length=1, max_length=100, description="Belt composition, e.g. Steel Cord")
    length: float = Field(..., gt=0, description="Total conveyor length in meters")
    width: float = Field(..., gt=0, description="Belt width in meters")
    status: str = Field(default="OPERATIONAL", max_length=50, description="Operational status")


class ConveyorCreate(ConveyorBase):
    pass


class ConveyorResponse(ConveyorBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConveyorDetailResponse(ConveyorResponse):
    sensor_nodes: List[SensorNodeResponse] = []

    model_config = ConfigDict(from_attributes=True)
