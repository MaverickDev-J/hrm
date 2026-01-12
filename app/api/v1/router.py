"""
API v1 router - aggregates all endpoint routers.
"""
from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.clients import router as clients_router
from app.api.v1.endpoints.companies import router as companies_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.invoices import router as invoices_router

# Main API v1 router
api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(auth_router)
api_router.include_router(clients_router)
api_router.include_router(companies_router)
api_router.include_router(users_router)
api_router.include_router(invoices_router)
