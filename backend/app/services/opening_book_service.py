"""
Opening Book Service

Builds a personalized opening book from user's imported Lichess games.
"""

import chess
from typing import Optional, List, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from collections import defaultdict

from app.models.game import Game


class OpeningBookService:
    """
    Service for generating opening moves from user's game history.

    Builds a frequency-based opening book from imported games.
    """

    def __init__(self, db: Session, user_id: int):
        """
        Initialize opening book service.

        Args:
            db: SQLAlchemy database session
            user_id: ID of the user
        """
        self.db = db
        self.user_id = user_id
        self._cache: Dict[str, List[Tuple[str, int]]] = {}  # FEN -> [(move, count), ...]

    def get_opponent_move(self, fen: str, user_plays_white: bool) -> Optional[str]:
        """
        Get opponent move from user's game history for this position.

        Samples moves weighted by frequency from actual games.

        Args:
            fen: Current position FEN
            user_plays_white: Whether user is playing white

        Returns:
            Move in UCI notation, or None if position not found in games
        """
        # Normalize FEN (remove move counters for matching)
        normalized_fen = self._normalize_fen(fen)

        # Check cache first
        if normalized_fen in self._cache:
            moves_with_counts = self._cache[normalized_fen]
        else:
            # Query games for this position
            moves_with_counts = self._query_moves_from_games(normalized_fen, user_plays_white)
            self._cache[normalized_fen] = moves_with_counts

        if not moves_with_counts:
            return None

        # Sample move weighted by frequency
        moves = []
        weights = []
        for move_uci, count in moves_with_counts:
            moves.append(move_uci)
            weights.append(count)

        total_weight = sum(weights)
        probabilities = [w / total_weight for w in weights]

        # Weighted random choice
        import random
        chosen_move = random.choices(moves, weights=probabilities, k=1)[0]

        return chosen_move

    def _query_moves_from_games(
        self,
        normalized_fen: str,
        user_plays_white: bool
    ) -> List[Tuple[str, int]]:
        """
        Query user's games to find moves played from this position.

        Args:
            normalized_fen: Normalized FEN string
            user_plays_white: Whether user is playing white (opponent plays black)

        Returns:
            List of (move_uci, count) tuples
        """
        # Get all user's games
        games = self.db.query(Game).filter(Game.user_id == self.user_id).all()

        # Track moves from this position
        move_counts = defaultdict(int)

        for game in games:
            # Parse PGN and check if this position appears
            try:
                import chess.pgn
                import io

                pgn = chess.pgn.read_game(io.StringIO(game.pgn))
                if not pgn:
                    continue

                # Determine which color the opponent played in this game
                # We need to find positions where it was the opponent's turn
                game_user_was_white = game.user_was_white

                # We want positions where opponent is to move
                # If user plays white in training, opponent is black, so we want black-to-move positions
                # If user plays black in training, opponent is white, so we want white-to-move positions
                looking_for_white_to_move = not user_plays_white

                # In the imported game, we want moves by the opponent
                # If user was white in the game, opponent was black
                # If user was black in the game, opponent was white
                opponent_was_white_in_game = not game_user_was_white

                # We want positions where:
                # - It matches the opponent's color to move
                # - The color to move matches what we're looking for

                board = pgn.board()
                for node in pgn.mainline():
                    current_fen = board.fen()
                    current_normalized = self._normalize_fen(current_fen)

                    # Check if this is the position we're looking for
                    if current_normalized == normalized_fen:
                        # Check if it's the right player's turn
                        white_to_move = board.turn == chess.WHITE

                        # If we're looking for white-to-move and it is, or black-to-move and it is
                        if white_to_move == looking_for_white_to_move:
                            # This is the opponent's turn in a matching position
                            move_uci = node.move.uci()
                            move_counts[move_uci] += 1

                    # Make the move for next iteration
                    board.push(node.move)

            except Exception as e:
                print(f"Error parsing game {game.id}: {e}")
                continue

        # Convert to list of tuples sorted by frequency
        result = [(move, count) for move, count in move_counts.items()]
        result.sort(key=lambda x: x[1], reverse=True)  # Most frequent first

        return result

    def _normalize_fen(self, fen: str) -> str:
        """
        Normalize FEN by removing move counters.

        Args:
            fen: Full FEN string

        Returns:
            Normalized FEN (board + side + castling + en passant only)
        """
        parts = fen.split(' ')
        if len(parts) >= 4:
            return ' '.join(parts[:4])
        return fen

    def clear_cache(self):
        """Clear the position cache."""
        self._cache.clear()
