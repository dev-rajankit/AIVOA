"""
AIVOA Backend — FastAPI Application

AI-Powered Customer Complaint Management System.
This is the main application entry point. The FastAPI app is configured
with CORS middleware and exposes a health check endpoint.

Architecture note: This application is built async-first. All endpoints
use async def, and future database/LLM operations will use async drivers
(asyncpg, async Groq client) to avoid blocking the event loop. This is
important because complaint processing involves multiple sequential LLM
calls per request, and blocking would starve concurrent users.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router

app = FastAPI(
    title="AIVOA",
    description="AI-Powered Customer Complaint Management System for Pharma QMS",
    version="0.1.0",
)

# CORS — allow the React dev server during development.
# In production, this should be restricted to the actual frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # Vite dev server ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")



@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    Returns HTTP 200 with a machine-readable status.
    """
    return {"status": "ok"}
