"""
API v1 router - aggregates all endpoint routers.
"""
from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.companies import router as companies_router

# Main API v1 router
api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(auth_router)
api_router.include_router(companies_router)
