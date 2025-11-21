"""
Chess Compute Microservice

Handles CPU-intensive chess operations:
- Stockfish position evaluation
- Blunder detection (centipawn loss)
- Opening phase detection
- MAIA-2 move probability generation

Runs as separate service to avoid blocking main API.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import chess
import chess.engine
import asyncio
from contextlib import asynccontextmanager

# MAIA-2 imports
from maia2 import model, inference

# Concurrency limiter (max 4 concurrent operations)
compute_semaphore = asyncio.Semaphore(4)

# Global engines
stockfish_engine = None
maia2_model = None
maia2_prepared = None

STOCKFISH_PATH = "/opt/homebrew/bin/stockfish"  # Default Mac path

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage engine lifecycle."""
    global stockfish_engine, maia2_model, maia2_prepared

    # Startup: Initialize Stockfish
    try:
        stockfish_engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
        print(f"✓ Stockfish initialized at {STOCKFISH_PATH}")
    except FileNotFoundError:
        print(f"⚠️  Stockfish not found at {STOCKFISH_PATH}")
        print("   Service will run but Stockfish endpoints will fail")
        stockfish_engine = None

    # Startup: Initialize MAIA-2
    try:
        print("Loading MAIA-2 model (this may take a few seconds)...")
        maia2_model = model.from_pretrained(type="rapid", device="cpu")
        maia2_prepared = inference.prepare()
        print("✓ MAIA-2 model loaded successfully")
    except Exception as e:
        print(f"⚠️  MAIA-2 failed to load: {e}")
        print("   Service will run but MAIA endpoints will use fallback")
        maia2_model = None
        maia2_prepared = None

    yield

    # Shutdown: Close engines
    if stockfish_engine:
        stockfish_engine.quit()
        print("✓ Stockfish engine closed")

    if maia2_model:
        print("✓ MAIA-2 model released")


app = FastAPI(
    title="Chess Compute Service",
    description="Microservice for MAIA and Stockfish chess computations",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class EvaluateRequest(BaseModel):
    fen: str
    depth: int = 20


class EvaluateResponse(BaseModel):
    fen: str
    centipawns: Optional[int]
    mate_in: Optional[int]
    depth: int


class BlunderDetectionRequest(BaseModel):
    before_fen: str
    after_fen: str
    depth: int = 20


class BlunderDetectionResponse(BaseModel):
    is_blunder: bool
    centipawn_loss: int
    eval_before: int
    eval_after: int


class OpeningDetectionRequest(BaseModel):
    fen: str
    move_number: int


class OpeningDetectionResponse(BaseModel):
    opening_ended: bool
    reason: str


class MaiaRequest(BaseModel):
    fen: str
    user_elo: int


class MaiaMove(BaseModel):
    move: str
    probability: float


class MaiaResponse(BaseModel):
    fen: str
    model_used: str
    moves: List[MaiaMove]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_stockfish_eval(board: chess.Board, depth: int = 20) -> Dict:
    """
    Evaluate position with Stockfish.

    Returns:
        Dict with 'centipawns' and 'mate_in' keys
    """
    if not stockfish_engine:
        raise HTTPException(status_code=503, detail="Stockfish engine not available")

    info = stockfish_engine.analyse(board, chess.engine.Limit(depth=depth))
    score = info["score"].white()

    if score.is_mate():
        return {
            "centipawns": None,
            "mate_in": score.mate()
        }
    else:
        return {
            "centipawns": score.score(),
            "mate_in": None
        }


def check_piece_development(board: chess.Board) -> Dict[str, int]:
    """Check how many pieces have been developed."""
    piece_map = board.piece_map()

    # Count developed minor pieces (off back rank)
    white_developed = sum(
        1 for sq, piece in piece_map.items()
        if piece.color == chess.WHITE
        and piece.piece_type in [chess.KNIGHT, chess.BISHOP]
        and chess.square_rank(sq) > 0
    )

    black_developed = sum(
        1 for sq, piece in piece_map.items()
        if piece.color == chess.BLACK
        and piece.piece_type in [chess.KNIGHT, chess.BISHOP]
        and chess.square_rank(sq) < 7
    )

    return {
        "white": white_developed,
        "black": black_developed
    }


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "stockfish_available": stockfish_engine is not None,
        "maia_available": maia2_model is not None,
        "maia_version": "maia2-rapid"
    }


@app.post("/stockfish/evaluate", response_model=EvaluateResponse)
async def evaluate_position(request: EvaluateRequest):
    """
    Evaluate a chess position using Stockfish.

    Returns centipawn evaluation or mate-in-N.
    """
    async with compute_semaphore:
        try:
            board = chess.Board(request.fen)
            eval_result = get_stockfish_eval(board, request.depth)

            return EvaluateResponse(
                fen=request.fen,
                centipawns=eval_result["centipawns"],
                mate_in=eval_result["mate_in"],
                depth=request.depth
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid FEN: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@app.post("/stockfish/detect-blunder", response_model=BlunderDetectionResponse)
async def detect_blunder(request: BlunderDetectionRequest):
    """
    Detect if a move was a blunder based on centipawn loss.

    A blunder is defined as >100 centipawn loss.
    """
    async with compute_semaphore:
        try:
            before_board = chess.Board(request.before_fen)
            after_board = chess.Board(request.after_fen)

            # Evaluate both positions
            eval_before = get_stockfish_eval(before_board, request.depth)
            eval_after = get_stockfish_eval(after_board, request.depth)

            # Handle mate scores (treat as very high/low centipawns)
            if eval_before["mate_in"] is not None:
                cp_before = 10000 if eval_before["mate_in"] > 0 else -10000
            else:
                cp_before = eval_before["centipawns"]

            if eval_after["mate_in"] is not None:
                cp_after = 10000 if eval_after["mate_in"] > 0 else -10000
            else:
                cp_after = eval_after["centipawns"]

            # Calculate centipawn loss from player's perspective
            # After move, it's opponent's turn, so flip the sign
            cp_loss = cp_before - (-cp_after)

            return BlunderDetectionResponse(
                is_blunder=cp_loss > 100,
                centipawn_loss=cp_loss,
                eval_before=cp_before,
                eval_after=-cp_after
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid FEN: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Blunder detection failed: {str(e)}")


@app.post("/stockfish/detect-opening-end", response_model=OpeningDetectionResponse)
async def detect_opening_end(request: OpeningDetectionRequest):
    """
    Detect if the opening phase has ended.

    Uses heuristics:
    1. Move number > 15
    2. Both sides developed 2+ minor pieces
    3. High evaluation swing (tactical position = middlegame)
    """
    async with compute_semaphore:
        try:
            board = chess.Board(request.fen)

            # Heuristic 1: Move number
            if request.move_number < 15:
                return OpeningDetectionResponse(
                    opening_ended=False,
                    reason="early_game"
                )

            # Heuristic 2: Piece development
            development = check_piece_development(board)

            if development["white"] < 2 or development["black"] < 2:
                return OpeningDetectionResponse(
                    opening_ended=False,
                    reason="underdeveloped"
                )

            # Heuristic 3: Check for tactical complexity using Stockfish
            eval_result = get_stockfish_eval(board, depth=15)

            if eval_result["centipawns"] is not None:
                abs_eval = abs(eval_result["centipawns"])

                # High evaluation = tactical middlegame
                if abs_eval > 150:
                    return OpeningDetectionResponse(
                        opening_ended=True,
                        reason="tactical_position"
                    )

            # All criteria met - opening has ended
            return OpeningDetectionResponse(
                opening_ended=True,
                reason="development_complete"
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid FEN: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Opening detection failed: {str(e)}")


@app.post("/maia/move-probabilities", response_model=MaiaResponse)
async def get_maia_move_probabilities(request: MaiaRequest):
    """
    Get MAIA-2 move probabilities for a position.

    Uses MAIA-2 neural network trained on human games.
    """
    async with compute_semaphore:
        try:
            board = chess.Board(request.fen)
            legal_moves = list(board.legal_moves)

            if not legal_moves:
                return MaiaResponse(
                    fen=request.fen,
                    model_used="maia2-rapid",
                    moves=[]
                )

            # Use real MAIA-2 if available
            if maia2_model is not None and maia2_prepared is not None:
                try:
                    # Clamp user ELO to valid range (1100-1900)
                    elo_clamped = max(1100, min(1900, request.user_elo))

                    # Get move probabilities from MAIA-2
                    # Using same ELO for both sides (single-player perspective)
                    move_probs, win_prob = inference.inference_each(
                        maia2_model,
                        maia2_prepared,
                        request.fen,
                        elo_clamped,  # User's ELO
                        elo_clamped   # Opponent ELO (same for balanced play)
                    )

                    # Convert to API response format
                    moves = [
                        MaiaMove(
                            move=move_uci,
                            probability=prob
                        )
                        for move_uci, prob in sorted(
                            move_probs.items(),
                            key=lambda x: x[1],
                            reverse=True
                        )
                    ]

                    return MaiaResponse(
                        fen=request.fen,
                        model_used=f"maia2-rapid (ELO {elo_clamped})",
                        moves=moves
                    )

                except Exception as maia_error:
                    print(f"MAIA-2 inference failed: {maia_error}, falling back to random")
                    # Fall through to fallback below

            # Fallback: Generate random probabilities if MAIA not available
            import random
            random.seed(hash(request.fen))  # Deterministic for same position

            raw_probs = [random.random() for _ in legal_moves]
            total = sum(raw_probs)
            normalized_probs = [p / total for p in raw_probs]

            moves = [
                MaiaMove(
                    move=move.uci(),
                    probability=prob
                )
                for move, prob in sorted(
                    zip(legal_moves, normalized_probs),
                    key=lambda x: x[1],
                    reverse=True
                )
            ]

            return MaiaResponse(
                fen=request.fen,
                model_used="random-fallback",
                moves=moves
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid FEN: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"MAIA probability generation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
