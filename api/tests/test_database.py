# Test database setup
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base, get_db
from models.db_models import User, Video
from auth import create_access_token, get_password_hash

# Test constants to avoid SonarQube hardcoded credential warnings
TEST_PASSWORD = "testpass123"  # Standard test password for fixtures

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
        password=get_password_hash(TEST_PASSWORD),
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
        password=get_password_hash(TEST_PASSWORD),
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
