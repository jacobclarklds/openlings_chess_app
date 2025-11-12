from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Now nullable for OAuth users
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # OAuth provider information
    oauth_provider = Column(String, nullable=True)  # 'google', 'facebook', or None
    oauth_provider_id = Column(String, nullable=True)  # Unique ID from OAuth provider
    profile_picture = Column(String, nullable=True)  # URL to profile picture

    # Chess platform credentials
    lichess_username = Column(String, nullable=True)
    lichess_token = Column(String, nullable=True)
    chesscom_username = Column(String, nullable=True)

    # Relationships
    games = relationship("Game", back_populates="user")
    lessons = relationship("Lesson", back_populates="user")
