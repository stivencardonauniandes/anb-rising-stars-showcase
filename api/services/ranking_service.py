"""
Ranking service for handling video rankings with caching and pagination
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, and_, or_, func
from typing import Dict, List, Optional
from models import Video, User
from services.cache_service import cache_service
from schemas import VideoResponse
import logging
import uuid

logger = logging.getLogger(__name__)

class RankingService:
    @staticmethod
    def get_public_videos_ranking(
        db: Session,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "votes",
        sort_order: str = "desc",
        status_filter: Optional[str] = None,
        min_votes: Optional[int] = None
    ) -> Dict:
        """
        Get paginated ranking of public videos with caching
        
        Args:
            db: Database session
            page: Page number (1-based)
            limit: Items per page (max 100)
            sort_by: Field to sort by (votes, uploaded_at, title)
            sort_order: Sort order (desc, asc)
            status_filter: Filter by video status
            min_votes: Minimum votes threshold
        
        Returns:
            Dict with videos, pagination info, and metadata
        """
        # Validate and sanitize inputs
        page = max(1, page)
        limit = min(max(1, limit), 100)  # Max 100 items per page
        
        valid_sort_fields = {"votes", "uploaded_at", "title"}
        if sort_by not in valid_sort_fields:
            sort_by = "votes"
        
        if sort_order not in {"desc", "asc"}:
            sort_order = "desc"
        
        # Generate cache key
        cache_key = cache_service.generate_rankings_key(
            page=page,
            limit=limit,
            sort_by=f"{sort_by}_{sort_order}_{status_filter}_{min_votes}"
        )
        
        # Try to get from cache first
        cached_result = cache_service.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for rankings: {cache_key}")
            return cached_result
        
        # Build query
        query = db.query(Video).options(
            joinedload(Video.user)
        ).filter(
            Video.status != "deleted"  # Only show non-deleted videos
        )
        
        # Apply filters
        if status_filter:
            query = query.filter(Video.status == status_filter)
        
        if min_votes is not None:
            query = query.filter(Video.votes >= min_votes)
        
        # Apply sorting
        if sort_by == "votes":
            sort_field = Video.votes
        elif sort_by == "uploaded_at":
            sort_field = Video.uploaded_at
        elif sort_by == "title":
            sort_field = Video.title
        else:
            sort_field = Video.votes
        
        if sort_order == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(asc(sort_field))
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        videos = query.offset(offset).limit(limit).all()
        
        # Calculate pagination metadata
        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        # Serialize videos
        video_list = []
        for idx, video in enumerate(videos, start=offset + 1):
            video_dict = {
                "id": str(video.id),
                "title": video.title,
                "status": video.status,
                "votes": video.votes,
                "uploaded_at": video.uploaded_at.isoformat(),
                "processed_at": video.processed_at.isoformat() if video.processed_at else None,
                "original_url": video.original_url,
                "processed_url": video.processed_url,
                "user": {
                    "id": str(video.user.id),
                    "first_name": video.user.first_name,
                    "last_name": video.user.last_name,
                    "city": video.user.city,
                    "country": video.user.country
                },
                "rank": idx
            }
            video_list.append(video_dict)
        
        result = {
            "videos": video_list,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_count,
                "items_per_page": limit,
                "has_next": has_next,
                "has_prev": has_prev,
                "next_page": page + 1 if has_next else None,
                "prev_page": page - 1 if has_prev else None
            },
            "filters": {
                "sort_by": sort_by,
                "sort_order": sort_order,
                "status_filter": status_filter,
                "min_votes": min_votes
            },
            "metadata": {
                "generated_at": func.now(),
                "cache_ttl": 300  # 5 minutes
            }
        }
        
        # Cache the result for 5 minutes
        cache_service.set(cache_key, result, expire=300)
        logger.info(f"Cached rankings result: {cache_key}")
        
        return result
    
    @staticmethod
    def get_top_videos(db: Session, limit: int = 10) -> List[Dict]:
        """Get top N videos by votes"""
        cache_key = f"top_videos:{limit}"
        
        cached_result = cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        videos = db.query(Video).options(
            joinedload(Video.user)
        ).filter(
            Video.status == "processed"
        ).order_by(
            desc(Video.votes)
        ).limit(limit).all()
        
        result = []
        for idx, video in enumerate(videos, 1):
            result.append({
                "rank": idx,
                "id": str(video.id),
                "title": video.title,
                "votes": video.votes,
                "user_name": f"{video.user.first_name} {video.user.last_name}",
                "uploaded_at": video.uploaded_at.isoformat()
            })
        
        # Cache for 2 minutes (shorter TTL for top videos)
        cache_service.set(cache_key, result, expire=120)
        
        return result
    
    @staticmethod
    def get_ranking_stats(db: Session) -> Dict:
        """Get overall ranking statistics"""
        cache_key = "ranking_stats"
        
        cached_result = cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        total_videos = db.query(Video).filter(Video.status != "deleted").count()
        total_votes = db.query(func.sum(Video.votes)).scalar() or 0
        processed_videos = db.query(Video).filter(Video.status == "processed").count()
        
        # Get top vote count
        top_video = db.query(Video).filter(
            Video.status != "deleted"
        ).order_by(desc(Video.votes)).first()
        
        result = {
            "total_videos": total_videos,
            "total_votes": total_votes,
            "processed_videos": processed_videos,
            "top_votes": top_video.votes if top_video else 0,
            "average_votes": round(total_votes / max(total_videos, 1), 2)
        }
        
        # Cache for 1 minute
        cache_service.set(cache_key, result, expire=60)
        
        return result

# Global ranking service instance
ranking_service = RankingService()
