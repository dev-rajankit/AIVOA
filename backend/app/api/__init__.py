from fastapi import APIRouter
from app.api.copilot import router as copilot_router

api_router = APIRouter()
api_router.include_router(copilot_router, prefix="/copilot", tags=["copilot"])
