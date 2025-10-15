from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from pydantic import BaseModel
from typing import List
import uvicorn

from database import get_db, Base, engine
from models import User, Video, Vote
from schemas import UserCreate, UserResponse, UserUpdate, VideoCreate, VideoResponse, VideoUpdate, VoteCreate, VoteResponse
from auth import get_password_hash, verify_password

# Create FastAPI app instance
app = FastAPI(
    title="ANB Rising Stars Showcase API",
    description="API for the ANB Rising Stars Showcase application",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    message: str
    service: str = "ANB Rising Stars Showcase API"

# Health Check Routes
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="success", 
        message="ANB Rising Stars Showcase API is running!",
        service="ANB Rising Stars Showcase API"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy", 
        message="API is operational",
        service="ANB Rising Stars Showcase API"
    )

@app.get("/health/ready", response_model=HealthResponse)
async def readiness_check():
    """Readiness check endpoint"""
    return HealthResponse(
        status="ready", 
        message="API is ready to serve requests",
        service="ANB Rising Stars Showcase API"
    )

@app.get("/health/live", response_model=HealthResponse)
async def liveness_check():
    """Liveness check endpoint"""
    return HealthResponse(
        status="alive", 
        message="API is alive and responding",
        service="ANB Rising Stars Showcase API"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
