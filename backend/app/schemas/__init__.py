"""Pydantic schemas for API validation."""
from .lesson import (
    LessonCreate,
    LessonResponse,
    LessonCommentResponse,
    LessonListResponse,
    UserLessonProgressUpdate,
    UserLessonProgressResponse
)

__all__ = [
    "LessonCreate",
    "LessonResponse",
    "LessonCommentResponse",
    "LessonListResponse",
    "UserLessonProgressUpdate",
    "UserLessonProgressResponse"
]
