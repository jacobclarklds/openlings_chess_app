import chess
from typing import Dict, List
import random


class MaiaService:
    """
    MAIA chess model integration for human-like move predictions

    NOTE: This is a fallback implementation using Stockfish with ELO-adjusted depth
    and randomness since MAIA models are not readily available.

    In production, this should be replaced with actual MAIA model integration.
    """

    def __init__(self):
        from app.services.stockfish_service import StockfishService
        self.stockfish = StockfishService()

    async def get_move_probabilities(
        self,
        fen: str,
        elo: int
    ) -> Dict:
        """
        Get probability distribution of moves for given ELO

        Uses Stockfish with ELO-adjusted depth and adds randomness
        to approximate human-like play.

        Args:
            fen: Position in FEN notation
            elo: Target ELO rating

        Returns:
            Dict with moves and their probabilities
        """
        board = chess.Board(fen)

        # Adjust depth based on ELO (lower ELO = shallower search)
        depth = self._elo_to_depth(elo)

        # Get legal moves
        legal_moves = list(board.legal_moves)

        if not legal_moves:
            return {"moves": [], "elo_model": elo}

        # Evaluate each move
        move_evals = []
        async with self.stockfish as sf:
            for move in legal_moves[:10]:  # Limit to top 10 for performance
                test_board = board.copy()
                test_board.push(move)

                # Quick evaluation
                try:
                    info = await sf.engine.analyse(
                        test_board,
                        chess.engine.Limit(depth=depth)
                    )
                    score = info["score"].relative.score()
                    if score is None:
                        score = 0
                    # Negate because we're evaluating from opponent's perspective
                    eval_score = -score
                except Exception:
                    eval_score = 0

                move_evals.append({
                    "move": move.uci(),
                    "eval": eval_score
                })

        # Convert evaluations to probabilities
        moves_with_probs = self._evals_to_probabilities(move_evals, elo)

        # Sort by probability
        moves_with_probs.sort(key=lambda x: x["probability"], reverse=True)

        return {
            "moves": moves_with_probs[:5],  # Return top 5
            "elo_model": elo
        }

    async def infer_elo_from_move(
        self,
        fen: str,
        move_made: str
    ) -> Dict:
        """
        Estimate player strength from move choice

        Args:
            fen: Position before the move
            move_made: The move that was played (UCI notation)

        Returns:
            Dict with most likely ELO and distribution
        """
        # Get move probabilities at different ELO levels
        elo_levels = [1100, 1300, 1500, 1900]
        elo_distribution = {}

        for elo in elo_levels:
            probs = await self.get_move_probabilities(fen, elo)
            move_prob = next(
                (m["probability"] for m in probs["moves"] if m["move"] == move_made),
                0.01  # Default small probability if move not in top moves
            )
            elo_distribution[str(elo)] = move_prob

        # Find most likely ELO
        most_likely = max(elo_distribution.items(), key=lambda x: x[1])

        return {
            "most_likely_elo": int(most_likely[0]),
            "elo_distribution": elo_distribution,
            "confidence": most_likely[1]
        }

    def _elo_to_depth(self, elo: int) -> int:
        """Convert ELO to appropriate Stockfish search depth"""
        if elo < 1200:
            return 8
        elif elo < 1500:
            return 12
        elif elo < 1800:
            return 16
        else:
            return 20

    def _evals_to_probabilities(self, move_evals: List[Dict], elo: int) -> List[Dict]:
        """
        Convert move evaluations to probability distribution

        Lower ELO = more randomness in move selection
        Higher ELO = strongly prefer best moves
        """
        if not move_evals:
            return []

        # Temperature based on ELO (lower temp = more random)
        # Lower ELO players make more "random" choices
        temperature = max(0.5, (elo - 800) / 1200)  # 0.5 to 1.5

        # Find best eval
        best_eval = max(m["eval"] for m in move_evals)

        # Calculate softmax probabilities with temperature
        import math
        exp_values = []
        for m in move_evals:
            # Normalize eval relative to best
            normalized_eval = (m["eval"] - best_eval) / 100  # Scale to reasonable range
            exp_val = math.exp(normalized_eval / temperature)
            exp_values.append(exp_val)

        total = sum(exp_values)

        # Add some noise for lower ELO
        noise_factor = max(0, (1500 - elo) / 1500) * 0.1  # Up to 10% noise

        moves_with_probs = []
        for i, m in enumerate(move_evals):
            base_prob = exp_values[i] / total if total > 0 else 1.0 / len(move_evals)

            # Add noise
            noise = random.uniform(-noise_factor, noise_factor)
            prob = max(0.01, min(0.99, base_prob + noise))

            moves_with_probs.append({
                "move": m["move"],
                "probability": prob,
                "uci": m["move"]
            })

        # Renormalize
        total_prob = sum(m["probability"] for m in moves_with_probs)
        for m in moves_with_probs:
            m["probability"] = m["probability"] / total_prob

        return moves_with_probs
