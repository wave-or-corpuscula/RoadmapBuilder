from fastapi import APIRouter

from backend.api.v1.plans import router as plans_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(plans_router)
