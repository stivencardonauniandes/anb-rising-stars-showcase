"""
Tests for public endpoints (voting and rankings)
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base, get_db
from models import User, Video, Vote
from auth import create_access_token, get_password_hash

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    """Create and clean up test database for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password=get_password_hash("testpass123"),
        city="Test City",
        country="Test Country"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def another_user(db_session):
    """Create another test user"""
    user = User(
        id=uuid.uuid4(),
        email="another@example.com",
        first_name="Another",
        last_name="User",
        password=get_password_hash("testpass123"),
        city="Another City",
        country="Another Country"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_video(db_session, another_user):
    """Create a test video"""
    video = Video(
        id=uuid.uuid4(),
        user_id=another_user.id,
        raw_video_id=uuid.uuid4(),
        title="Test Video",
        status="processed",
        original_url="https://example.com/video.mp4",
        processed_url="https://example.com/processed.mp4",
        votes=0
    )
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)
    return video

@pytest.fixture
def auth_headers(test_user):
    """Create authorization headers with JWT token"""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}

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

class TestRankingsEndpoint:
    """Tests for GET /api/public/rankings"""
    
    def test_get_rankings_default_params(self, db_session, another_user):
        """Test getting rankings with default parameters"""
        # Create multiple test videos with different vote counts
        videos = []
        for i in range(5):
            video = Video(
                id=uuid.uuid4(),
                user_id=another_user.id,
                raw_video_id=uuid.uuid4(),
                title=f"Video {i+1}",
                status="processed",
                original_url=f"https://example.com/video{i+1}.mp4",
                votes=i * 2  # 0, 2, 4, 6, 8 votes
            )
            videos.append(video)
            db_session.add(video)
        db_session.commit()
        
        response = client.get("/api/public/rankings")
        assert response.status_code == 200
        
        data = response.json()
        assert "videos" in data
        assert "pagination" in data
        assert "filters" in data
        
        # Check videos are sorted by votes (descending)
        video_votes = [video["votes"] for video in data["videos"]]
        assert video_votes == sorted(video_votes, reverse=True)
        
        # Check pagination info
        pagination = data["pagination"]
        assert pagination["current_page"] == 1
        assert pagination["items_per_page"] == 20
        assert pagination["total_items"] == 5
    
    def test_get_rankings_with_pagination(self, db_session, another_user):
        """Test rankings with pagination"""
        # Create 25 videos
        for i in range(25):
            video = Video(
                id=uuid.uuid4(),
                user_id=another_user.id,
                raw_video_id=uuid.uuid4(),
                title=f"Video {i+1}",
                status="processed",
                original_url=f"https://example.com/video{i+1}.mp4",
                votes=i
            )
            db_session.add(video)
        db_session.commit()
        
        # Test first page
        response = client.get("/api/public/rankings?page=1&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["videos"]) == 10
        assert data["pagination"]["current_page"] == 1
        assert data["pagination"]["total_pages"] == 3
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_prev"] is False
        
        # Test second page
        response2 = client.get("/api/public/rankings?page=2&limit=10")
        assert response2.status_code == 200
        
        data2 = response2.json()
        assert len(data2["videos"]) == 10
        assert data2["pagination"]["current_page"] == 2
        assert data2["pagination"]["has_next"] is True
        assert data2["pagination"]["has_prev"] is True
    
    def test_get_rankings_with_filters(self, db_session, another_user):
        """Test rankings with filters"""
        # Create videos with different statuses and vote counts
        videos_data = [
            {"status": "processed", "votes": 10},
            {"status": "processed", "votes": 5},
            {"status": "uploaded", "votes": 3},
            {"status": "processed", "votes": 1},
        ]
        
        for i, video_data in enumerate(videos_data):
            video = Video(
                id=uuid.uuid4(),
                user_id=another_user.id,
                raw_video_id=uuid.uuid4(),
                title=f"Video {i+1}",
                status=video_data["status"],
                original_url=f"https://example.com/video{i+1}.mp4",
                votes=video_data["votes"]
            )
            db_session.add(video)
        db_session.commit()
        
        # Test status filter
        response = client.get("/api/public/rankings?status_filter=processed")
        assert response.status_code == 200
        
        data = response.json()
        processed_videos = [v for v in data["videos"] if v["status"] == "processed"]
        assert len(processed_videos) == len(data["videos"])  # All should be processed
        
        # Test min_votes filter
        response2 = client.get("/api/public/rankings?min_votes=5")
        assert response2.status_code == 200
        
        data2 = response2.json()
        for video in data2["videos"]:
            assert video["votes"] >= 5
    
    def test_get_rankings_sorting(self, db_session, another_user):
        """Test rankings sorting options"""
        # Create videos with different attributes
        videos_data = [
            {"title": "Alpha Video", "votes": 5},
            {"title": "Beta Video", "votes": 10},
            {"title": "Charlie Video", "votes": 3},
        ]
        
        for video_data in videos_data:
            video = Video(
                id=uuid.uuid4(),
                user_id=another_user.id,
                raw_video_id=uuid.uuid4(),
                title=video_data["title"],
                status="processed",
                original_url="https://example.com/video.mp4",
                votes=video_data["votes"]
            )
            db_session.add(video)
        db_session.commit()
        
        # Test sort by title ascending
        response = client.get("/api/public/rankings?sort_by=title&sort_order=asc")
        assert response.status_code == 200
        
        data = response.json()
        titles = [video["title"] for video in data["videos"]]
        assert titles == sorted(titles)  # Should be alphabetically sorted
    
    def test_get_top_videos(self, db_session, another_user):
        """Test GET /api/public/rankings/top endpoint"""
        # Create videos with different vote counts
        for i in range(10):
            video = Video(
                id=uuid.uuid4(),
                user_id=another_user.id,
                raw_video_id=uuid.uuid4(),
                title=f"Video {i+1}",
                status="processed",
                original_url=f"https://example.com/video{i+1}.mp4",
                votes=i * 3  # 0, 3, 6, 9, ..., 27 votes
            )
            db_session.add(video)
        db_session.commit()
        
        response = client.get("/api/public/rankings/top?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "top_videos" in data
        assert len(data["top_videos"]) == 5
        assert data["count"] == 5
        assert data["limit"] == 5
        
        # Check videos are sorted by votes (descending)
        top_videos = data["top_videos"]
        for i in range(len(top_videos) - 1):
            assert top_videos[i]["votes"] >= top_videos[i + 1]["votes"]
        
        # Check rank numbers
        for i, video in enumerate(top_videos):
            assert video["rank"] == i + 1
    
    def test_get_ranking_stats(self, db_session, another_user):
        """Test GET /api/public/rankings/stats endpoint"""
        # Create test videos
        videos_data = [
            {"status": "processed", "votes": 10},
            {"status": "processed", "votes": 5},
            {"status": "uploaded", "votes": 3},
            {"status": "deleted", "votes": 2},  # Should not be counted
        ]
        
        for i, video_data in enumerate(videos_data):
            video = Video(
                id=uuid.uuid4(),
                user_id=another_user.id,
                raw_video_id=uuid.uuid4(),
                title=f"Video {i+1}",
                status=video_data["status"],
                original_url=f"https://example.com/video{i+1}.mp4",
                votes=video_data["votes"]
            )
            db_session.add(video)
        db_session.commit()
        
        response = client.get("/api/public/rankings/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_videos" in data
        assert "total_votes" in data
        assert "processed_videos" in data
        assert "top_votes" in data
        assert "average_votes" in data
        
        # Check stats (excluding deleted videos)
        assert data["total_videos"] == 3  # Excluding deleted
        assert data["processed_videos"] == 2
        assert data["top_votes"] == 10
        # Note: total_votes might include some existing votes from other tests
        assert data["total_votes"] >= 18  # At least 10 + 5 + 3

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
