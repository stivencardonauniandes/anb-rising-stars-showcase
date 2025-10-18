"""
Tests for vote endpoints
"""
import uuid

from models.db_models import Video, Vote
from tests.test_database import client, db_session, test_user, test_video, auth_headers, another_user

class TestVoteEndpoint:
    """Tests for POST /api/public/videos/{video_id}/vote"""
    
    def test_vote_for_video_success(self, db_session, test_user, test_video, auth_headers):
        """Test successful voting for a video"""
        response = client.post(
            f"/api/public/videos/{test_video.id}/vote",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Vote registered successfully"
        assert data["video_id"] == str(test_video.id)
        assert data["total_votes"] == 1
        
        # Refresh session to see committed changes
        db_session.commit()
        db_session.expire_all()
        
        # Verify vote was created in database
        vote = db_session.query(Vote).filter(
            Vote.user_id == test_user.id,
            Vote.video_id == test_video.id
        ).first()
        assert vote is not None
        
        # Verify video vote count was updated
        updated_video = db_session.query(Video).filter(Video.id == test_video.id).first()
        assert updated_video.votes == 1
    
    def test_vote_without_auth_fails(self, test_video):
        """Test voting without authentication fails"""
        response = client.post(f"/api/public/videos/{test_video.id}/vote")
        # FastAPI returns 403 when HTTPBearer is missing, 401 when token is invalid
        assert response.status_code in [401, 403]
    
    def test_vote_invalid_video_id_format(self, auth_headers):
        """Test voting with invalid video ID format"""
        response = client.post(
            "/api/public/videos/invalid-id/vote",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Invalid video ID format" in response.json()["detail"]
    
    def test_vote_nonexistent_video(self, auth_headers):
        """Test voting for non-existent video"""
        fake_video_id = uuid.uuid4()
        response = client.post(
            f"/api/public/videos/{fake_video_id}/vote",
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "Video not found" in response.json()["detail"]
    
    def test_vote_twice_fails(self, db_session, test_user, test_video, auth_headers):
        """Test voting twice for the same video fails"""
        # First vote
        response1 = client.post(
            f"/api/public/videos/{test_video.id}/vote",
            headers=auth_headers
        )
        assert response1.status_code == 200
        
        # Second vote should fail
        response2 = client.post(
            f"/api/public/videos/{test_video.id}/vote",
            headers=auth_headers
        )
        assert response2.status_code == 400
        assert "already voted" in response2.json()["detail"]
    
    def test_vote_own_video_fails(self, db_session, test_user, auth_headers):
        """Test voting for own video fails"""
        # Create video owned by test_user
        own_video = Video(
            id=uuid.uuid4(),
            user_id=test_user.id,
            raw_video_id=uuid.uuid4(),
            title="Own Video",
            status="processed",
            original_url="https://example.com/own.mp4",
            votes=0
        )
        db_session.add(own_video)
        db_session.commit()
        
        response = client.post(
            f"/api/public/videos/{own_video.id}/vote",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "cannot vote for your own video" in response.json()["detail"]

class TestVoteStatusEndpoint:
    """Tests for GET /api/public/videos/{video_id}/vote-status"""
    
    def test_vote_status_not_voted(self, test_user, test_video, auth_headers):
        """Test vote status when user hasn't voted"""
        response = client.get(
            f"/api/public/videos/{test_video.id}/vote-status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == str(test_video.id)
        assert data["has_voted"] is False
        assert data["user_id"] == str(test_user.id)
    
    def test_vote_status_has_voted(self, db_session, test_user, test_video, auth_headers):
        """Test vote status when user has voted"""
        # Create a vote
        vote = Vote(user_id=test_user.id, video_id=test_video.id)
        db_session.add(vote)
        db_session.commit()
        
        response = client.get(
            f"/api/public/videos/{test_video.id}/vote-status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_voted"] is True
    
    def test_vote_status_without_auth_fails(self, test_video):
        """Test vote status without authentication fails"""
        response = client.get(f"/api/public/videos/{test_video.id}/vote-status")
        # FastAPI returns 403 when HTTPBearer is missing
        assert response.status_code in [401, 403]
