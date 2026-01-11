# Trigger Reload
from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="0.1.0",
    description="Multi-tenant HR Management System with JWT Authentication"
)

# Include API routers
# Include API routers
app.include_router(api_router)

# Mount static files
from fastapi.staticfiles import StaticFiles
import os
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "message": "HR Management System API",
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected"
    }