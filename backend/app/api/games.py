from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.user import User
from app.models.game import Game
from app.schemas.game import GameResponse, GameImportRequest
from app.schemas.user import ChessPlatformCredentials
from app.services.lichess import LichessService
from app.services.chesscom import ChessComService
from app.api.auth import get_current_user

router = APIRouter(prefix="/games", tags=["games"])

@router.get("", response_model=List[GameResponse])
def get_user_games(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all games for the current user.
    """
    games = (
        db.query(Game)
        .filter(Game.user_id == current_user.id)
        .order_by(Game.played_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return games

@router.post("/import", status_code=status.HTTP_202_ACCEPTED)
def import_games(
    import_request: GameImportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Import games from Lichess or Chess.com.
    """
    if import_request.platform == "lichess":
        # Check if user has Lichess credentials
        if not current_user.lichess_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lichess account not connected. Please connect your Lichess account first.",
            )

        service = LichessService(token=current_user.lichess_token)
        username = current_user.lichess_username

    elif import_request.platform == "chesscom":
        # Check if user has Chess.com credentials
        if not current_user.chesscom_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chess.com account not connected. Please connect your Chess.com account first.",
            )

        service = ChessComService()
        username = current_user.chesscom_username

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid platform. Must be 'lichess' or 'chesscom'.",
        )

    # Import games in background
    background_tasks.add_task(
        import_games_task,
        service,
        username,
        current_user.id,
        import_request.max_games or 100,
        db,
    )

    return {
        "message": f"Importing games from {import_request.platform}. This may take a few moments."
    }

def import_games_task(
    service,
    username: str,
    user_id: int,
    max_games: int,
    db: Session,
):
    """
    Background task to import games.
    """
    try:
        games_data = service.get_user_games(username, max_games)

        for game_data in games_data:
            # Check if game already exists
            existing_game = db.query(Game).filter(
                Game.game_id == game_data["game_id"]
            ).first()

            if existing_game:
                continue

            # Create new game
            new_game = Game(
                user_id=user_id,
                **game_data
            )
            db.add(new_game)

        db.commit()
        print(f"Successfully imported {len(games_data)} games for user {user_id}")

    except Exception as e:
        print(f"Error importing games: {e}")
        db.rollback()

@router.post("/connect-platform", status_code=status.HTTP_200_OK)
def connect_chess_platform(
    credentials: ChessPlatformCredentials,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Connect a Lichess or Chess.com account.
    """
    if credentials.platform == "lichess":
        # Verify token if provided
        if credentials.token:
            service = LichessService(token=credentials.token)
            if not service.verify_token():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Lichess API token",
                )

        current_user.lichess_username = credentials.username
        current_user.lichess_token = credentials.token

    elif credentials.platform == "chesscom":
        # Verify user exists
        service = ChessComService()
        if not service.verify_user_exists(credentials.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chess.com user not found",
            )

        current_user.chesscom_username = credentials.username

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid platform. Must be 'lichess' or 'chesscom'.",
        )

    db.commit()
    db.refresh(current_user)

    return {
        "message": f"Successfully connected {credentials.platform} account",
        "username": credentials.username,
    }

@router.get("/{game_id}", response_model=GameResponse)
def get_game(
    game_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific game by ID.
    """
    game = db.query(Game).filter(
        Game.id == game_id,
        Game.user_id == current_user.id
    ).first()

    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found",
        )

    return game
