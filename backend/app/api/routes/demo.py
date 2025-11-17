"""
Demo API routes - No authentication required
"""

import logging
import time
from fastapi import APIRouter, BackgroundTasks, status, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import SessionLocal
from app.schemas.lesson import LessonCreate
from app.services.ollama_coach_agent import OllamaChessCoachAgent
from app.core.config import settings
from pydantic import BaseModel

logger = logging.getLogger(__name__)


router = APIRouter()


class DemoLessonRequest(BaseModel):
    pgn: str
    user_elo: int = 1200
    focus_areas: Optional[List[str]] = None


class DemoLessonResponse(BaseModel):
    comments: List[dict]
    total_steps: int
    focus_areas: List[str]


@router.post("/generate-lesson", response_model=DemoLessonResponse)
async def generate_demo_lesson(request: DemoLessonRequest):
    """
    Generate a chess lesson without authentication (for demo purposes).
    This endpoint generates lessons on-the-fly without saving to database.
    """
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("🚀 Starting lesson generation request")
    logger.info(f"   PGN length: {len(request.pgn)} characters")
    logger.info(f"   User ELO: {request.user_elo}")
    logger.info(f"   Focus areas: {request.focus_areas}")
    logger.info(f"   AI Provider: {settings.AI_PROVIDER}")
    
    # Choose agent based on configuration
    if settings.AI_PROVIDER == "ollama":
        logger.info(f"   Using Ollama agent with model: {settings.OLLAMA_MODEL}")
        agent = OllamaChessCoachAgent()
    else:
        try:
            from app.services.coach_agent import ChessCoachAgent
            logger.info("   Using Anthropic agent")
            agent = ChessCoachAgent()
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Anthropic provider not available. Please set AI_PROVIDER=ollama in .env"
            )

    try:
        logger.info("   Calling agent.generate_lesson()...")
        lesson_start = time.time()
        
        # Generate the lesson
        result = await agent.generate_lesson(
            pgn=request.pgn,
            user_elo=request.user_elo,
            focus_areas=request.focus_areas
        )
        
        lesson_time = time.time() - lesson_start
        total_time = time.time() - start_time
        
        logger.info(f"✅ Lesson generation completed!")
        logger.info(f"   Generated {result.get('total_steps', 0)} comments")
        logger.info(f"   Lesson generation took: {lesson_time:.2f}s")
        logger.info(f"   Total request time: {total_time:.2f}s")
        logger.info("=" * 60)

        return result

    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"❌ Error generating lesson after {total_time:.2f}s: {str(e)}", exc_info=True)
        raise
    finally:
        logger.info("   Cleaning up agent resources...")
        await agent.cleanup()
        logger.info("   Cleanup complete")


@router.get("/sample-game")
async def get_sample_game():
    """
    Get a sample game for testing.
    """
    return {
        "pgn": """[Event "Casual Game"]
[Site "Online"]
[Date "2024.01.15"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. c3 Nf6 5. d4 exd4 6. cxd4 Bb4+
7. Bd2 Bxd2+ 8. Nbxd2 d5 9. exd5 Nxd5 10. Qb3 Nce7 11. O-O O-O
12. Rfe1 c6 13. a3 Bf5 14. Rac1 Qd6 15. Ne4 Bxe4 16. Rxe4 Rfe8
17. Rce1 Nf6 18. R4e2 Ned5 19. Bd3 h6 20. Ne5 Re7 21. Qc2 Rae8
22. h3 Nh7 23. Nf3 Nhf6 24. Rxe7 Rxe7 25. Rxe7 Qxe7 26. Qe2 Qxe2
27. Bxe2 Ne4 28. Kf1 Kf8 29. Ke1 Ke7 30. Kd1 Kd6 31. Nd2 Nxd2
32. Kxd2 f6 33. f3 Kd7 34. Kd3 b5 35. Bf1 a6 36. Bh3+ Kd6
37. Bf1 Kd7 38. Bh3+ Kd6 39. Bf5 g6 40. Bh3 h5 41. Bf1 a5
42. Bh3 b4 43. axb4 axb4 44. Bf1 Kd7 45. Kc4 Nb6+ 46. Kb3 Nd5
47. Bh3+ Kd6 48. Bf1 Kd7 49. Bh3+ 1/2-1/2""",
        "title": "Italian Game Sample",
        "description": "A classic Italian Game with instructive moments"
    }


@router.get("/health")
async def demo_health():
    """Check if demo endpoints are working."""
    return {
        "status": "healthy",
        "ai_provider": settings.AI_PROVIDER,
        "model": settings.OLLAMA_MODEL if settings.AI_PROVIDER == "ollama" else settings.ANTHROPIC_MODEL
    }
