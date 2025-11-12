"""
Pydantic schemas for lesson API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# Board Annotation Schema
class BoardAnnotation(BaseModel):
    """Visual annotation on the chess board."""
    id: str
    type: str = Field(..., pattern="^(arrow|circle|highlight)$")
    color: str = Field(..., pattern="^(red|green|blue|yellow|orange)$")
    from_square: Optional[str] = Field(None, alias="from")
    to_square: Optional[str] = Field(None, alias="to")
    square: Optional[str] = None

    class Config:
        populate_by_name = True


# AI Question Schema
class AIQuestion(BaseModel):
    """Interactive question for the user."""
    type: str = Field(..., pattern="^(multiple_choice|move_selection)$")
    question: str
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: Optional[str] = None


# Lesson Comment Schemas
class LessonCommentResponse(BaseModel):
    """Response schema for a lesson comment."""
    id: int
    step_number: int
    position_fen: str
    move_to_make: Optional[str] = None
    text: str
    annotations: List[Dict[str, Any]] = []
    question: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Lesson Create Schema
class LessonCreate(BaseModel):
    """Schema for creating a new lesson."""
    game_id: Optional[int] = None
    pgn: str = Field(..., description="PGN of the game to analyze")
    title: Optional[str] = Field(None, description="Custom title for the lesson")
    focus_areas: Optional[List[str]] = Field(
        None,
        description="Areas to focus on (e.g., ['tactics', 'endgame'])"
    )


# Lesson Response Schema
class LessonResponse(BaseModel):
    """Response schema for a complete lesson."""
    id: int
    user_id: int
    game_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    focus_areas: Optional[List[str]] = []
    user_elo_at_creation: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    comments: List[LessonCommentResponse] = []

    class Config:
        from_attributes = True


# Lesson List Response (without comments for efficiency)
class LessonListResponse(BaseModel):
    """Response schema for lesson in list view."""
    id: int
    title: str
    description: Optional[str] = None
    focus_areas: Optional[List[str]] = []
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    comment_count: int = 0

    class Config:
        from_attributes = True


# User Lesson Progress Schemas
class UserLessonProgressUpdate(BaseModel):
    """Schema for updating user progress."""
    current_step: Optional[int] = None
    completed: Optional[bool] = None
    answer: Optional[Dict[str, Any]] = Field(
        None,
        description="Answer to question: {step_number: answer}"
    )


class UserLessonProgressResponse(BaseModel):
    """Response schema for user lesson progress."""
    id: int
    user_id: int
    lesson_id: int
    current_step: int
    completed: bool
    answers: Dict[str, Any] = {}
    started_at: datetime
    completed_at: Optional[datetime] = None
    last_accessed: datetime

    class Config:
        from_attributes = True
