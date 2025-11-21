"""
Training API Routes

Endpoints for adaptive chess opening training.
Manages training sessions and games using the TrainingEngine.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import json
import random

from app.core.database import get_db
from app.models.user import User
from app.api.auth import get_current_user
from app.models.training_session import TrainingSession, TrainingGame
from app.services.training_engine import TrainingEngine

# Redis for session state (we'll add this later)
# For now, we'll use in-memory storage
active_games = {}  # game_id -> TrainingEngine instance

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class StartSessionRequest(BaseModel):
    opening_filter: Optional[str] = None  # Future: filter by opening


class StartSessionResponse(BaseModel):
    session_id: int
    started_at: str


class NewGameRequest(BaseModel):
    session_id: int
    user_plays_white: Optional[bool] = None  # None = random


class NewGameResponse(BaseModel):
    game_id: int
    session_id: int
    user_plays_white: bool
    fen: str
    legal_moves: List[str]
    is_user_turn: bool


class MakeMoveRequest(BaseModel):
    move: str  # UCI notation (e.g., "e2e4")


class MoveResponse(BaseModel):
    success: bool
    fen: str
    legal_moves: List[str]
    is_user_turn: bool
    game_over: bool
    opening_ended: bool
    result: Optional[str]  # 'win', 'loss', 'draw'
    opponent_move: Optional[str]  # If opponent moved


class GameStateResponse(BaseModel):
    game_id: int
    fen: str
    user_plays_white: bool
    is_user_turn: bool
    move_count: int
    opening_ended: bool
    game_over: bool
    result: Optional[str]
    legal_moves: List[str]
    position_count: int


class SessionStatsResponse(BaseModel):
    session_id: int
    games_played: int
    wins: int
    losses: int
    draws: int
    total_moves: int
    positions_practiced: int


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/sessions/start", response_model=StartSessionResponse)
async def start_training_session(
    request: StartSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a new training session.

    A session groups multiple training games together.
    """
    from datetime import datetime

    session = TrainingSession(
        user_id=current_user.id,
        opening_filter=request.opening_filter,
        started_at=datetime.utcnow(),
        game_count=0,
        positions_visited=0
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return StartSessionResponse(
        session_id=session.id,
        started_at=session.started_at.isoformat()
    )


@router.post("/games/new", response_model=NewGameResponse)
async def create_training_game(
    request: NewGameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new training game within a session.

    Returns the initial board state and whose turn it is.
    """
    # Verify session exists and belongs to user
    session = db.query(TrainingSession).filter(
        TrainingSession.id == request.session_id,
        TrainingSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training session not found"
        )

    # Determine color (50/50 if not specified)
    if request.user_plays_white is None:
        user_plays_white = random.choice([True, False])
    else:
        user_plays_white = request.user_plays_white

    # Create training engine
    engine = TrainingEngine(
        db=db,
        user_id=current_user.id,
        session=session,
        user_plays_white=user_plays_white
    )

    # Generate a game ID (in production, this would be from database)
    game_id = id(engine)  # Use object ID as temporary game ID

    # Store engine in memory
    active_games[game_id] = engine

    # If opponent plays first, make their move
    opponent_move = None
    if not engine.is_user_turn():
        result = await engine.make_opponent_move()
        if result['success']:
            opponent_move = result['move']

    # Get current state
    state = engine.get_game_state()

    return NewGameResponse(
        game_id=game_id,
        session_id=request.session_id,
        user_plays_white=user_plays_white,
        fen=state['fen'],
        legal_moves=state['legal_moves'],
        is_user_turn=state['is_user_turn']
    )


@router.post("/games/{game_id}/move", response_model=MoveResponse)
async def make_move(
    game_id: int,
    request: MakeMoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Make a move in an active training game.

    If the move is valid, the opponent will automatically respond
    (unless the game ends).
    """
    # Get active game
    engine = active_games.get(game_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found or expired"
        )

    # Make user's move
    user_result = await engine.make_user_move(request.move)

    if not user_result['success']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=user_result.get('error', 'Invalid move')
        )

    # Check if game ended
    if user_result['game_over']:
        # Finalize and save game
        await engine.finalize_game()

        # Remove from active games
        del active_games[game_id]

        return MoveResponse(
            success=True,
            fen=user_result['fen'],
            legal_moves=[],
            is_user_turn=False,
            game_over=True,
            opening_ended=user_result.get('opening_ended', False),
            result=user_result['result'],
            opponent_move=None
        )

    # Make opponent's move
    opponent_move = None
    if not engine.is_user_turn():
        opp_result = await engine.make_opponent_move()

        if opp_result['success']:
            opponent_move = opp_result['move']

            # Check if opponent's move ended the game
            if opp_result['game_over']:
                # Finalize and save game
                await engine.finalize_game()

                # Remove from active games
                del active_games[game_id]

                return MoveResponse(
                    success=True,
                    fen=opp_result['fen'],
                    legal_moves=[],
                    is_user_turn=False,
                    game_over=True,
                    opening_ended=opp_result.get('opening_ended', False),
                    result=opp_result['result'],
                    opponent_move=opponent_move
                )

    # Get current state
    state = engine.get_game_state()

    return MoveResponse(
        success=True,
        fen=state['fen'],
        legal_moves=state['legal_moves'],
        is_user_turn=state['is_user_turn'],
        game_over=state['game_over'],
        opening_ended=state['opening_ended'],
        result=state['result'],
        opponent_move=opponent_move
    )


@router.get("/games/{game_id}/state", response_model=GameStateResponse)
async def get_game_state(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current state of an active training game.
    """
    engine = active_games.get(game_id)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found or expired"
        )

    state = engine.get_game_state()

    return GameStateResponse(
        game_id=game_id,
        fen=state['fen'],
        user_plays_white=state['user_plays_white'],
        is_user_turn=state['is_user_turn'],
        move_count=state['move_count'],
        opening_ended=state['opening_ended'],
        game_over=state['game_over'],
        result=state['result'],
        legal_moves=state['legal_moves'],
        position_count=state['position_count']
    )


@router.get("/sessions/{session_id}/stats", response_model=SessionStatsResponse)
async def get_session_stats(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics for a training session.
    """
    # Verify session exists and belongs to user
    session = db.query(TrainingSession).filter(
        TrainingSession.id == session_id,
        TrainingSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training session not found"
        )

    # Get all games in this session
    games = db.query(TrainingGame).filter(
        TrainingGame.session_id == session_id
    ).all()

    # Calculate stats
    wins = sum(1 for g in games if g.result == 'win')
    losses = sum(1 for g in games if g.result == 'loss')
    draws = sum(1 for g in games if g.result == 'draw')
    total_moves = sum(g.moves_played for g in games)

    # Count unique positions
    unique_positions = set()
    for game in games:
        if game.positions_visited:
            unique_positions.update(game.positions_visited)

    return SessionStatsResponse(
        session_id=session_id,
        games_played=len(games),
        wins=wins,
        losses=losses,
        draws=draws,
        total_moves=total_moves,
        positions_practiced=len(unique_positions)
    )


@router.post("/sessions/{session_id}/end")
async def end_training_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    End a training session.

    Marks the session as completed.
    """
    from datetime import datetime

    session = db.query(TrainingSession).filter(
        TrainingSession.id == session_id,
        TrainingSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training session not found"
        )

    session.completed_at = datetime.utcnow()
    db.commit()

    return {"success": True, "message": "Session ended"}
