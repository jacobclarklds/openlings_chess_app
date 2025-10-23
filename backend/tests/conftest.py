"""
Test configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.models.game import Game

# Use in-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("password123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_oauth_user(db_session):
    """Create a test user with OAuth authentication"""
    user = User(
        email="oauth@example.com",
        username="oauthuser",
        oauth_provider="google",
        oauth_provider_id="google_12345",
        profile_picture="https://example.com/pic.jpg",
        hashed_password=None,  # OAuth users don't have password
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user"""
    response = client.post(
        "/api/auth/login",
        data={"username": test_user.email, "password": "password123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_user_with_lichess(db_session):
    """Create a test user with Lichess account connected"""
    user = User(
        email="lichess@example.com",
        username="lichessuser",
        hashed_password=get_password_hash("password123"),
        lichess_username="jclark982",
        lichess_token=None,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_with_chesscom(db_session):
    """Create a test user with Chess.com account connected"""
    user = User(
        email="chesscom@example.com",
        username="chesscomuser",
        hashed_password=get_password_hash("password123"),
        chesscom_username="jakebyu97",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_game(db_session, test_user):
    """Create a test game"""
    game = Game(
        user_id=test_user.id,
        platform="lichess",
        game_id="lichess_abc123",
        white_player="testuser",
        black_player="opponent",
        result="1-0",
        white_rating=1500,
        black_rating=1450,
        time_control="600+0",
        opening_eco="C50",
        opening_name="Italian Game",
        pgn="[Event \"Test Game\"]\n\n1. e4 e5",
    )
    db_session.add(game)
    db_session.commit()
    db_session.refresh(game)
    return game
