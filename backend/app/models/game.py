from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Game metadata
    platform = Column(String, nullable=False)  # 'lichess' or 'chesscom'
    game_id = Column(String, unique=True, index=True, nullable=False)
    played_at = Column(DateTime, nullable=False)

    # Game details
    white_player = Column(String, nullable=False)
    black_player = Column(String, nullable=False)
    white_rating = Column(Integer, nullable=True)
    black_rating = Column(Integer, nullable=True)

    # Result
    result = Column(String, nullable=False)  # '1-0', '0-1', '1/2-1/2'
    termination = Column(String, nullable=True)  # 'Normal', 'Time forfeit', etc.

    # Game content
    pgn = Column(Text, nullable=False)
    opening_name = Column(String, nullable=True)
    opening_eco = Column(String, nullable=True)

    # Analysis flags
    analyzed = Column(Boolean, default=False)

    # Time control
    time_control = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="games")
    lessons = relationship("Lesson", back_populates="game")
