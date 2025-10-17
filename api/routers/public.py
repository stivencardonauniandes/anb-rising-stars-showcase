"""
Public API endpoints for video voting and rankings
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from database import get_db
from dependencies import get_current_user
from models import User
from services.vote_service import vote_service
from services.ranking_service import ranking_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/public", tags=["public"])

@router.post("/videos/{video_id}/vote")
async def vote_for_video(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Vote for a public video
    
    - **Requires authentication (JWT token)**
    - **One vote per user per video**
    - **Cannot vote for own videos**
    
    Returns success message and updated vote count
    """
    try:
        # Validate video_id UUID format
        video_uuid = uuid.UUID(video_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid video ID format"
        )
    
    # Use vote service to handle the voting logic
    result = vote_service.vote_for_video(
        user_id=current_user.id,
        video_id=video_uuid,
        db=db
    )
    
    logger.info(f"Vote registered: user {current_user.id} voted for video {video_id}")
    
    return result

@router.get("/rankings")
async def get_public_rankings(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    sort_by: str = Query("votes", description="Sort field: votes, uploaded_at, title"),
    sort_order: str = Query("desc", description="Sort order: desc, asc"),
    status_filter: Optional[str] = Query(None, description="Filter by video status"),
    min_votes: Optional[int] = Query(None, ge=0, description="Minimum votes threshold"),
    db: Session = Depends(get_db)
):
    """
    Get public video rankings with pagination and filtering
    
    - **No authentication required**
    - **Supports pagination, sorting, and filtering**
    - **Results are cached for performance**
    
    Query Parameters:
    - **page**: Page number (default: 1)
    - **limit**: Items per page, max 100 (default: 20)
    - **sort_by**: Sort field - votes, uploaded_at, title (default: votes)
    - **sort_order**: Sort order - desc, asc (default: desc)
    - **status_filter**: Filter by video status (optional)
    - **min_votes**: Minimum votes threshold (optional)
    
    Returns paginated list of videos with ranking information
    """
    
    result = ranking_service.get_public_videos_ranking(
        db=db,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        status_filter=status_filter,
        min_votes=min_votes
    )
    
    logger.info(f"Rankings requested: page={page}, limit={limit}, sort_by={sort_by}")
    
    return result

@router.get("/rankings/top")
async def get_top_videos(
    limit: int = Query(10, ge=1, le=50, description="Number of top videos to return"),
    db: Session = Depends(get_db)
):
    """
    Get top N videos by votes
    
    - **No authentication required**
    - **Returns only processed videos**
    - **Cached for performance**
    
    Returns list of top videos with ranking positions
    """
    
    result = ranking_service.get_top_videos(db=db, limit=limit)
    
    logger.info(f"Top {limit} videos requested")
    
    return {
        "top_videos": result,
        "count": len(result),
        "limit": limit
    }

@router.get("/rankings/stats")
async def get_ranking_statistics(db: Session = Depends(get_db)):
    """
    Get overall ranking and voting statistics
    
    - **No authentication required**
    - **Cached for performance**
    
    Returns overall stats about videos and votes
    """
    
    result = ranking_service.get_ranking_stats(db=db)
    
    logger.info("Ranking statistics requested")
    
    return result

@router.get("/videos/{video_id}/vote-status")
async def get_vote_status(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if current user has voted for a specific video
    
    - **Requires authentication (JWT token)**
    
    Returns boolean indicating if user has voted for the video
    """
    try:
        video_uuid = uuid.UUID(video_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid video ID format"
        )
    
    has_voted = vote_service.has_user_voted(
        user_id=current_user.id,
        video_id=video_uuid,
        db=db
    )
    
    return {
        "video_id": video_id,
        "has_voted": has_voted,
        "user_id": str(current_user.id)
    }
