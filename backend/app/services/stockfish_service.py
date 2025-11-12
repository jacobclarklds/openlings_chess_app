import chess
import chess.engine
from typing import Dict, Optional
import asyncio
import os


class StockfishService:
    """Service for integrating Stockfish chess engine"""

    def __init__(self, engine_path: str = None):
        if engine_path is None:
            # Try common paths
            possible_paths = [
                "/opt/homebrew/bin/stockfish",
                "/usr/local/bin/stockfish",
                "/usr/bin/stockfish",
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    engine_path = path
                    break

            if engine_path is None:
                raise FileNotFoundError("Stockfish engine not found. Please install Stockfish.")

        self.engine_path = engine_path
        self.default_depth = 20
        self.engine = None
        self.transport = None

    async def __aenter__(self):
        """Async context manager - start engine"""
        self.transport, self.engine = await chess.engine.popen_uci(self.engine_path)
        await self.engine.configure({
            "Threads": 4,
            "Hash": 512
        })
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Stop engine"""
        if self.engine:
            await self.engine.quit()

    async def evaluate_position(
        self,
        fen: str,
        depth: int = 20
    ) -> Dict:
        """
        Get centipawn evaluation and best moves

        Args:
            fen: Position in FEN notation
            depth: Search depth (higher = more accurate but slower)

        Returns:
            Dict with evaluation, best move, and best line
        """
        board = chess.Board(fen)

        info = await self.engine.analyse(
            board,
            chess.engine.Limit(depth=depth)
        )

        score = info["score"].relative
        best_move = info.get("pv", [None])[0]

        if score.is_mate():
            return {
                "evaluation_type": "mate",
                "mate_in": score.mate(),
                "centipawn_eval": None,
                "best_move": best_move.uci() if best_move else None,
                "best_line": [m.uci() for m in info.get("pv", [])],
                "depth": depth
            }
        else:
            return {
                "evaluation_type": "cp",
                "centipawn_eval": score.score(),
                "mate_in": None,
                "best_move": best_move.uci() if best_move else None,
                "best_line": [m.uci() for m in info.get("pv", [])],
                "depth": depth
            }

    async def analyze_move(
        self,
        fen: str,
        move: str,
        depth: int = 20
    ) -> Dict:
        """
        Analyze quality of a specific move

        Args:
            fen: Position before the move
            move: Move in UCI notation (e.g., "e2e4")
            depth: Search depth

        Returns:
            Dict with move classification and evaluation data
        """
        board = chess.Board(fen)

        # Evaluate before move
        info_before = await self.engine.analyse(
            board,
            chess.engine.Limit(depth=depth)
        )
        eval_before = info_before["score"].relative.score() or 0

        # Make move
        move_obj = chess.Move.from_uci(move)
        board.push(move_obj)

        # Evaluate after move (negate for same perspective)
        info_after = await self.engine.analyse(
            board,
            chess.engine.Limit(depth=depth)
        )
        eval_after = -(info_after["score"].relative.score() or 0)

        # Get best move from original position
        board = chess.Board(fen)
        info_best = await self.engine.analyse(
            board,
            chess.engine.Limit(depth=depth)
        )
        best_move = info_best.get("pv", [None])[0]
        best_eval = info_best["score"].relative.score() or 0

        # Calculate centipawns lost
        centipawns_lost = max(0, best_eval - eval_after)

        # Classify move
        classification = self._classify_move(centipawns_lost)

        return {
            "move": move,
            "eval_before": eval_before,
            "eval_after": eval_after,
            "eval_diff": eval_after - eval_before,
            "classification": classification,
            "best_move": best_move.uci() if best_move else None,
            "best_eval": best_eval,
            "centipawns_lost": int(centipawns_lost)
        }

    def _classify_move(self, centipawns_lost: int) -> str:
        """Classify move quality based on centipawns lost"""
        if centipawns_lost <= 15:
            return "excellent"
        elif centipawns_lost <= 50:
            return "good"
        elif centipawns_lost <= 100:
            return "inaccuracy"
        elif centipawns_lost <= 300:
            return "mistake"
        else:
            return "blunder"
