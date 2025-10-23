from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GameBase(BaseModel):
    platform: str
    game_id: str
    played_at: datetime
    white_player: str
    black_player: str
    result: str
    pgn: str

class GameCreate(GameBase):
    white_rating: Optional[int] = None
    black_rating: Optional[int] = None
    termination: Optional[str] = None
    opening_name: Optional[str] = None
    opening_eco: Optional[str] = None
    time_control: Optional[str] = None

class GameResponse(GameCreate):
    id: int
    user_id: int
    analyzed: bool
    created_at: datetime

    class Config:
        from_attributes = True

class GameImportRequest(BaseModel):
    platform: str  # 'lichess' or 'chesscom'
    username: str
    max_games: Optional[int] = 100
