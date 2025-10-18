"""
Tests for public endpoints (voting and rankings)
"""
import uuid

from models.db_models import Video
from tests.test_database import client, db_session, another_user

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
