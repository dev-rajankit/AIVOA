from fastapi import APIRouter
from app.api.copilot import router as copilot_router
from app.api.report import router as report_router

api_router = APIRouter()
api_router.include_router(copilot_router, prefix="/copilot", tags=["copilot"])
api_router.include_router(report_router, prefix="/report", tags=["report"])
