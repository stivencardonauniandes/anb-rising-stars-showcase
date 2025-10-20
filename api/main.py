import logging
import uvicorn
from config import config

from pydantic import BaseModel
from routers import auth, public, videos
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate configuration at startup
try:
    config.validate_config()
    logger.info(f"Configuration loaded successfully for {config.ENVIRONMENT} environment")
except ValueError as e:
    logger.error(f"Configuration validation failed: {e}")
    raise

# Constants
API_TITLE = "ANB Rising Stars Showcase API"

# Create FastAPI app instance
app = FastAPI(
    title=API_TITLE,
    description="API for the ANB Rising Stars Showcase application",
    version="1.0.0",
)

Instrumentator().instrument(app).expose(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(public.router)
app.include_router(videos.router)

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    message: str
    service: str = API_TITLE

# Health Check Routes
@app.get("/api/health", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="success", 
        message=f"{API_TITLE} is running!",
        service=API_TITLE
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
