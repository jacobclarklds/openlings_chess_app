"""
API routes for chess lessons.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models import User, Lesson, LessonComment, UserLessonProgress, Game
from app.schemas.lesson import (
    LessonCreate,
    LessonResponse,
    LessonListResponse,
    UserLessonProgressUpdate,
    UserLessonProgressResponse
)
from app.api.auth import get_current_user
from app.services.coach_agent import ChessCoachAgent
import asyncio
from datetime import datetime


router = APIRouter()


async def generate_lesson_background(
    lesson_id: int,
    pgn: str,
    user_elo: int,
    focus_areas: Optional[List[str]],
    db: Session
):
    """
    Background task to generate a lesson using the AI agent.
    Updates the lesson in the database when complete.
    """
    agent = ChessCoachAgent()
    
    try:
        # Generate the lesson
        result = await agent.generate_lesson(
            pgn=pgn,
            user_elo=user_elo,
            focus_areas=focus_areas
        )
        
        # Get the lesson from database
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            return
        
        # Update lesson status
        lesson.status = "completed"
        lesson.completed_at = datetime.utcnow()
        
        # Save comments
        for idx, comment_data in enumerate(result['comments'], start=1):
            comment = LessonComment(
                lesson_id=lesson_id,
                step_number=idx,
                position_fen=comment_data['position_fen'],
                move_to_make=comment_data.get('move_to_make'),
                text=comment_data['text'],
                annotations=comment_data.get('annotations', []),
                question=comment_data.get('question')
            )
            db.add(comment)
        
        db.commit()
        
    except Exception as e:
        # Update lesson with error
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if lesson:
            lesson.status = "failed"
            lesson.error_message = str(e)
            db.commit()
    
    finally:
        await agent.cleanup()


@router.post("/", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    lesson_data: LessonCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new lesson from a game.
    Lesson generation happens in the background.
    """
    # Get user's current ELO (we'll use an average from their recent games)
    user_elo = 1500  # Default
    recent_games = db.query(Game).filter(
        Game.user_id == current_user.id
    ).order_by(Game.played_at.desc()).limit(10).all()
    
    if recent_games:
        ratings = []
        for game in recent_games:
            if game.white_player == current_user.username and game.white_rating:
                ratings.append(game.white_rating)
            elif game.black_player == current_user.username and game.black_rating:
                ratings.append(game.black_rating)
        if ratings:
            user_elo = sum(ratings) // len(ratings)
    
    # Create lesson record
    lesson = Lesson(
        user_id=current_user.id,
        game_id=lesson_data.game_id,
        title=lesson_data.title or "AI Generated Lesson",
        focus_areas=lesson_data.focus_areas or [],
        user_elo_at_creation=user_elo,
        status="generating"
    )
    
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    
    # Start background task to generate lesson
    background_tasks.add_task(
        generate_lesson_background,
        lesson.id,
        lesson_data.pgn,
        user_elo,
        lesson_data.focus_areas,
        db
    )
    
    return lesson


@router.get("/", response_model=List[LessonListResponse])
def get_user_lessons(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all lessons for the current user.
    """
    query = db.query(Lesson).filter(Lesson.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(Lesson.status == status_filter)
    
    lessons = query.order_by(Lesson.created_at.desc()).offset(skip).limit(limit).all()
    
    # Add comment count to each lesson
    result = []
    for lesson in lessons:
        comment_count = db.query(LessonComment).filter(
            LessonComment.lesson_id == lesson.id
        ).count()
        
        lesson_dict = {
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description,
            "focus_areas": lesson.focus_areas,
            "status": lesson.status,
            "created_at": lesson.created_at,
            "completed_at": lesson.completed_at,
            "comment_count": comment_count
        }
        result.append(LessonListResponse(**lesson_dict))
    
    return result


@router.get("/{lesson_id}", response_model=LessonResponse)
def get_lesson(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific lesson with all comments.
    """
    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id,
        Lesson.user_id == current_user.id
    ).first()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    return lesson


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a lesson.
    """
    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id,
        Lesson.user_id == current_user.id
    ).first()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    db.delete(lesson)
    db.commit()
    
    return None


@router.get("/{lesson_id}/progress", response_model=UserLessonProgressResponse)
def get_lesson_progress(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's progress for a lesson.
    """
    progress = db.query(UserLessonProgress).filter(
        UserLessonProgress.lesson_id == lesson_id,
        UserLessonProgress.user_id == current_user.id
    ).first()
    
    # Create progress if doesn't exist
    if not progress:
        progress = UserLessonProgress(
            user_id=current_user.id,
            lesson_id=lesson_id
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
    
    return progress


@router.put("/{lesson_id}/progress", response_model=UserLessonProgressResponse)
def update_lesson_progress(
    lesson_id: int,
    progress_update: UserLessonProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's progress for a lesson.
    """
    progress = db.query(UserLessonProgress).filter(
        UserLessonProgress.lesson_id == lesson_id,
        UserLessonProgress.user_id == current_user.id
    ).first()
    
    if not progress:
        progress = UserLessonProgress(
            user_id=current_user.id,
            lesson_id=lesson_id
        )
        db.add(progress)
    
    # Update fields
    if progress_update.current_step is not None:
        progress.current_step = progress_update.current_step
    
    if progress_update.completed is not None:
        progress.completed = progress_update.completed
        if progress_update.completed:
            progress.completed_at = datetime.utcnow()
    
    if progress_update.answer:
        # Merge answer into answers dict
        if not progress.answers:
            progress.answers = {}
        progress.answers.update(progress_update.answer)
    
    progress.last_accessed = datetime.utcnow()
    
    db.commit()
    db.refresh(progress)
    
    return progress
