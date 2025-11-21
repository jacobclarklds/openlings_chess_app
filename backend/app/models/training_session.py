from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base


class TrainingSession(Base):
    """
    Represents a training session where a user plays multiple training games.

    Sessions can optionally filter for specific openings (future feature).
    """
    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    opening_filter = Column(String, nullable=True)  # Future: filter by opening name/ECO
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    game_count = Column(Integer, default=0)
    positions_visited = Column(Integer, default=0)

    # Relationships
    games = relationship("TrainingGame", back_populates="session", cascade="all, delete-orphan")


class TrainingGame(Base):
    """
    Represents a single training game within a session.

    Training games focus on opening practice and auto-end after the opening phase.
    Results are determined by Stockfish evaluation at the end of the opening.
    """
    __tablename__ = "training_games"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("training_sessions.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pgn = Column(Text, nullable=False)
    result = Column(String(10), nullable=False)  # User perspective: 'win', 'loss', 'draw'
    user_color = Column(String(5), nullable=False)  # 'white' or 'black'
    moves_played = Column(Integer, nullable=False)
    positions_visited = Column(JSONB, nullable=True)  # List of normalized FENs
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("TrainingSession", back_populates="games")
