from fastapi import APIRouter

from backend.api.v1.graph import router as graph_router
from backend.api.v1.plans import router as plans_router
from backend.api.v1.skills import router as skills_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(plans_router)
api_router.include_router(skills_router)
api_router.include_router(graph_router)
