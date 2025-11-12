from app.services.stockfish_service import StockfishService
from app.services.maia_service import MaiaService
from typing import Dict, List
import asyncio
import chess


class AnalysisCoordinator:
    """
    Coordinates MAIA, Stockfish, and other analysis services
    This is what the AI agent will call to gather information
    """

    def __init__(self):
        self.stockfish = StockfishService()
        self.maia = MaiaService()

    async def analyze_position_full(
        self,
        fen: str,
        user_elo: int
    ) -> Dict:
        """
        Comprehensive analysis of a position

        Args:
            fen: Position in FEN notation
            user_elo: User's ELO rating

        Returns:
            Dict with stockfish eval, MAIA predictions, and position features
        """
        # Run Stockfish and MAIA in parallel
        async with self.stockfish as sf:
            stockfish_task = sf.evaluate_position(fen, depth=20)
            maia_task = self.maia.get_move_probabilities(fen, user_elo)

            stockfish_eval, maia_predictions = await asyncio.gather(
                stockfish_task,
                maia_task
            )

        # Classify position type
        position_type = self._classify_position(fen)

        # Extract key features
        key_features = self._extract_features(fen)

        return {
            "fen": fen,
            "user_elo": user_elo,
            "stockfish": stockfish_eval,
            "maia_predictions": maia_predictions,
            "position_type": position_type,
            "key_features": key_features
        }

    async def analyze_user_move(
        self,
        fen_before: str,
        move: str,
        user_elo: int
    ) -> Dict:
        """
        Analyze a move the user made

        Args:
            fen_before: Position before the move
            move: Move in UCI notation
            user_elo: User's rating

        Returns:
            Dict with comprehensive move analysis
        """
        async with self.stockfish as sf:
            # Get Stockfish evaluation of the move
            stockfish_eval = await sf.analyze_move(fen_before, move, depth=20)

            # Get MAIA probability for this move
            maia_probs = await self.maia.get_move_probabilities(fen_before, user_elo)
            move_prob = next(
                (m["probability"] for m in maia_probs["moves"] if m["move"] == move),
                0.01  # Default small probability
            )

            # Infer ELO strength from this move
            elo_inference = await self.maia.infer_elo_from_move(fen_before, move)

        # Determine if move is typical for user's level
        typical_for_level = move_prob > 0.1  # More than 10% of players at this level play it

        return {
            "move": move,
            "stockfish_eval": stockfish_eval,
            "maia_probability": move_prob,
            "inferred_strength": elo_inference["most_likely_elo"],
            "typical_for_level": typical_for_level,
            "alternatives": maia_probs["moves"][:3]  # Top 3 alternatives
        }

    def _classify_position(self, fen: str) -> str:
        """Classify position phase"""
        board = chess.Board(fen)
        piece_count = len(board.piece_map())

        if board.fullmove_number <= 10:
            return "opening"
        elif piece_count <= 10:
            return "endgame"
        else:
            # Check if it's tactical or positional middlegame
            # Simple heuristic: if many pieces are attacked, it's tactical
            return "middlegame"

    def _extract_features(self, fen: str) -> List[str]:
        """
        Extract tactical/positional features from position

        Returns list of feature strings like "hanging_piece", "fork_opportunity", etc.
        """
        features = []
        board = chess.Board(fen)

        # Check for hanging pieces
        hanging = self._find_hanging_pieces(board)
        if hanging:
            features.append("hanging_pieces")

        # Check for checks
        if board.is_check():
            features.append("check")

        # Check for pieces under attack
        attacked_pieces = self._count_attacked_pieces(board)
        if attacked_pieces > 2:
            features.append("tactical")

        return features

    def _find_hanging_pieces(self, board: chess.Board) -> List[str]:
        """Find undefended pieces (excluding pawns)"""
        hanging = []

        for square, piece in board.piece_map().items():
            # Skip pawns and kings
            if piece.piece_type in [chess.PAWN, chess.KING]:
                continue

            # Check if piece is attacked
            if board.is_attacked_by(not piece.color, square):
                # Check if it's defended
                if not board.is_attacked_by(piece.color, square):
                    hanging.append(chess.square_name(square))

        return hanging

    def _count_attacked_pieces(self, board: chess.Board) -> int:
        """Count how many pieces are under attack"""
        count = 0

        for square, piece in board.piece_map().items():
            if board.is_attacked_by(not piece.color, square):
                count += 1

        return count
