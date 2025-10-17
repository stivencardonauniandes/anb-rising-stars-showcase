"""
Vote service for handling video voting logic
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
from models import Vote, Video, User
from services.cache_service import cache_service
import logging
import uuid

logger = logging.getLogger(__name__)

class VoteService:
    @staticmethod
    def vote_for_video(user_id: uuid.UUID, video_id: uuid.UUID, db: Session) -> dict:
        """
        Vote for a video. Ensures one vote per user per video.
        """
        # Verify video exists and is not deleted
        video = db.query(Video).filter(
            and_(Video.id == video_id, Video.status != "deleted")
        ).first()
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found or has been deleted"
            )
        
        # Check if user already voted for this video
        existing_vote = db.query(Vote).filter(
            and_(Vote.user_id == user_id, Vote.video_id == video_id)
        ).first()
        
        if existing_vote:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already voted for this video"
            )
        
        # Prevent users from voting for their own videos
        if video.user_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot vote for your own video"
            )
        
        try:
            # Create the vote
            new_vote = Vote(user_id=user_id, video_id=video_id)
            db.add(new_vote)
            
            # Update vote count
            video.votes += 1
            
            db.commit()
            db.refresh(video)
            
            # Invalidate rankings cache since vote count changed
            cache_service.invalidate_rankings_cache()
            
            logger.info(f"User {user_id} voted for video {video_id}")
            
            return {
                "message": "Vote registered successfully",
                "video_id": str(video_id),
                "total_votes": video.votes
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error voting for video {video_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register vote"
            )
    
    @staticmethod
    def get_user_votes(user_id: uuid.UUID, db: Session) -> list:
        """Get all videos a user has voted for"""
        votes = db.query(Vote).filter(Vote.user_id == user_id).all()
        return [str(vote.video_id) for vote in votes]
    
    @staticmethod
    def get_video_votes_count(video_id: uuid.UUID, db: Session) -> int:
        """Get total votes for a specific video"""
        video = db.query(Video).filter(Video.id == video_id).first()
        return video.votes if video else 0
    
    @staticmethod
    def has_user_voted(user_id: uuid.UUID, video_id: uuid.UUID, db: Session) -> bool:
        """Check if user has voted for a specific video"""
        vote = db.query(Vote).filter(
            and_(Vote.user_id == user_id, Vote.video_id == video_id)
        ).first()
        return vote is not None

# Global vote service instance
vote_service = VoteService()
