import chess
import chess.pgn
from typing import Dict
import io


class OpeningService:
    """Service for classifying chess openings"""

    def __init__(self):
        # In a full implementation, this would load an ECO database
        # For MVP, we'll use simple classification
        pass

    async def get_opening_classification(self, pgn: str) -> Dict:
        """
        Get ECO code, opening name, and typical plans

        Args:
            pgn: Game in PGN format

        Returns:
            Dict with opening classification info
        """
        try:
            game = chess.pgn.read_game(io.StringIO(pgn))

            if not game:
                return {
                    "eco": "Unknown",
                    "name": "Unknown Opening",
                    "variation": "",
                    "typical_plans": []
                }

            # Get first few moves to identify opening
            board = game.board()
            moves = []
            for move in list(game.mainline_moves())[:6]:  # First 6 moves
                moves.append(board.san(move))
                board.push(move)

            # Simple pattern matching for common openings
            opening_info = self._identify_opening(moves)

            return opening_info

        except Exception:
            return {
                "eco": "Unknown",
                "name": "Unknown Opening",
                "variation": "",
                "typical_plans": []
            }

    async def get_position_type(self, fen: str) -> str:
        """
        Classify position phase

        Args:
            fen: Position in FEN notation

        Returns:
            Position type: "opening", "middlegame", or "endgame"
        """
        board = chess.Board(fen)
        piece_count = len(board.piece_map())

        if board.fullmove_number <= 10:
            return "opening"
        elif piece_count <= 10:
            return "endgame"
        else:
            return "middlegame"

    def _identify_opening(self, moves: list) -> Dict:
        """
        Simple opening identification based on first moves

        In production, this should use a comprehensive ECO database
        """
        if not moves:
            return {
                "eco": "A00",
                "name": "Start Position",
                "variation": "",
                "typical_plans": ["Develop pieces", "Control center"]
            }

        first_move = moves[0] if moves else ""

        # Italian Game
        if len(moves) >= 4 and moves[:4] == ["e4", "e5", "Nf3", "Nc6"]:
            if len(moves) >= 5 and moves[4] == "Bc4":
                return {
                    "eco": "C50",
                    "name": "Italian Game",
                    "variation": "",
                    "typical_plans": [
                        "Control center with d4",
                        "Develop pieces quickly",
                        "Castle kingside",
                        "Attack on f7"
                    ]
                }

        # Sicilian Defense
        if len(moves) >= 2 and moves[:2] == ["e4", "c5"]:
            return {
                "eco": "B20",
                "name": "Sicilian Defense",
                "variation": "",
                "typical_plans": [
                    "Fight for d4 square",
                    "Create pawn asymmetry",
                    "Black plays for counterplay on queenside"
                ]
            }

        # French Defense
        if len(moves) >= 2 and moves[:2] == ["e4", "e6"]:
            return {
                "eco": "C00",
                "name": "French Defense",
                "variation": "",
                "typical_plans": [
                    "Build pawn chain",
                    "Black plays c5 break",
                    "White plays for space advantage"
                ]
            }

        # Queen's Gambit
        if len(moves) >= 2 and moves[:2] == ["d4", "d5"]:
            if len(moves) >= 3 and moves[2] == "c4":
                return {
                    "eco": "D06",
                    "name": "Queen's Gambit",
                    "variation": "",
                    "typical_plans": [
                        "Challenge black's center",
                        "Develop pieces to natural squares",
                        "Fight for central control"
                    ]
                }

        # Default classification based on first move
        if first_move == "e4":
            return {
                "eco": "B00",
                "name": "King's Pawn Opening",
                "variation": "",
                "typical_plans": ["Control center", "Develop pieces", "Castle"]
            }
        elif first_move == "d4":
            return {
                "eco": "A40",
                "name": "Queen's Pawn Opening",
                "variation": "",
                "typical_plans": ["Control center", "Develop pieces", "Build solid structure"]
            }
        elif first_move in ["Nf3", "c4"]:
            return {
                "eco": "A00",
                "name": "Flank Opening",
                "variation": "",
                "typical_plans": ["Flexible piece development", "Control from distance"]
            }
        else:
            return {
                "eco": "A00",
                "name": "Uncommon Opening",
                "variation": "",
                "typical_plans": ["Develop pieces", "Control center"]
            }
