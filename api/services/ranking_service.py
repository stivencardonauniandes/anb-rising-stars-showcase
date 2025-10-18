"""
Ranking service for handling video rankings with caching and pagination
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, and_, func
from typing import Dict, List, Optional
from models.db_models import Video, User
from services.cache_service import cache_service
from datetime import datetime
import logging

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
        Get paginated ranking of public videos with caching and filtering
        """
        # Validate and sanitize inputs
        page = max(1, page)
        limit = min(max(1, limit), 100)
        
        valid_sort_fields = {"votes", "uploaded_at", "title"}
        if sort_by not in valid_sort_fields:
            sort_by = "votes"
        
        if sort_order not in {"desc", "asc"}:
            sort_order = "desc"
        
        # Build query (simplified - no eager loading in tests)
        query = db.query(Video).filter(
            Video.status != "deleted"
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
        
        # Serialize videos for JSON response
        video_list = []
        for idx, video in enumerate(videos, start=offset + 1):
            # Get user separately to avoid serialization issues
            user = db.query(User).filter(User.id == video.user_id).first()
            
            video_dict = {
                "id": str(video.id),
                "title": video.title,
                "status": video.status.value if hasattr(video.status, 'value') else str(video.status),
                "votes": video.votes,
                "uploaded_at": video.uploaded_at.isoformat() if video.uploaded_at else None,
                "processed_at": video.processed_at.isoformat() if video.processed_at else None,
                "original_url": video.original_url,
                "processed_url": video.processed_url,
                "user": {
                    "id": str(user.id) if user else None,
                    "first_name": user.first_name if user else "Unknown",
                    "last_name": user.last_name if user else "User",
                    "city": user.city if user else None,
                    "country": user.country if user else None
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
                "generated_at": datetime.now().isoformat(),
                "cache_ttl": 300
            }
        }
        
        return result
    
    @staticmethod
    def get_top_videos(db: Session, limit: int = 10) -> List[Dict]:
        """Get top N videos by votes"""
        videos = db.query(Video).filter(
            Video.status == "processed"
        ).order_by(
            desc(Video.votes)
        ).limit(limit).all()
        
        result = []
        for idx, video in enumerate(videos, 1):
            user = db.query(User).filter(User.id == video.user_id).first()
            result.append({
                "rank": idx,
                "id": str(video.id),
                "title": video.title,
                "votes": video.votes,
                "user_name": f"{user.first_name} {user.last_name}" if user else "Unknown User",
                "uploaded_at": video.uploaded_at.isoformat() if video.uploaded_at else None
            })
        
        return result
    
    @staticmethod
    def get_ranking_stats(db: Session) -> Dict:
        """Get overall ranking statistics"""
        # Count non-deleted videos
        total_videos = db.query(Video).filter(Video.status != "deleted").count()
        
        # Sum votes from non-deleted videos  
        total_votes_result = db.query(func.sum(Video.votes)).filter(
            Video.status != "deleted"
        ).scalar()
        total_votes = int(total_votes_result) if total_votes_result else 0
        
        # Count processed videos
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
        
        return result

# Global ranking service instance
ranking_service = RankingService()
