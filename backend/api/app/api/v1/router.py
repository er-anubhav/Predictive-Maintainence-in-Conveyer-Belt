from fastapi import APIRouter
from app.api.v1.mines import router as mines_router
from app.api.v1.conveyors import router as conveyors_router
from app.api.v1.devices import router as devices_router
from app.api.v1.telemetry import router as telemetry_router
from app.api.v1.multimodal import router as multimodal_router

api_v1_router = APIRouter()

api_v1_router.include_router(mines_router)
api_v1_router.include_router(conveyors_router)
api_v1_router.include_router(devices_router)
api_v1_router.include_router(telemetry_router)
api_v1_router.include_router(multimodal_router)

