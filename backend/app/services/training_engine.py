"""
Training Engine

Core logic for running adaptive opening training games.
Manages board state, move generation, and game lifecycle.
"""

import chess
import random
from typing import Optional, List, Dict, Tuple
from sqlalchemy.orm import Session

from app.models.training_session import TrainingSession, TrainingGame
from app.services.position_trie_service import PositionTrieService
from app.services.compute_client import compute_client


class TrainingEngine:
    """
    Training game engine with adaptive opponent move generation.

    Uses MAIA for human-like moves, biased toward user's weak positions.
    """

    def __init__(
        self,
        db: Session,
        user_id: int,
        session: TrainingSession,
        user_plays_white: bool
    ):
        """
        Initialize training engine.

        Args:
            db: SQLAlchemy database session
            user_id: User ID
            session: Active training session
            user_plays_white: Whether user plays white
        """
        self.db = db
        self.user_id = user_id
        self.session = session
        self.user_plays_white = user_plays_white

        # Initialize board and tracking
        self.board = chess.Board()
        self.positions: List[str] = [self.board.fen()]
        self.move_count = 0

        # Services
        self.trie_service = PositionTrieService(db, user_id)

        # Game state
        self.is_opening_ended = False
        self.game_over = False
        self.result: Optional[str] = None  # 'win', 'loss', 'draw'

    def get_current_fen(self) -> str:
        """Get current board position as FEN."""
        return self.board.fen()

    def get_legal_moves(self) -> List[str]:
        """Get list of legal moves in UCI notation."""
        return [move.uci() for move in self.board.legal_moves]

    def is_user_turn(self) -> bool:
        """Check if it's the user's turn to move."""
        return (self.board.turn == chess.WHITE and self.user_plays_white) or \
               (self.board.turn == chess.BLACK and not self.user_plays_white)

    async def make_user_move(self, move_uci: str) -> Dict:
        """
        Process user's move.

        Args:
            move_uci: Move in UCI notation (e.g., 'e2e4')

        Returns:
            Dict with move result and game state
        """
        if self.game_over:
            return {
                "success": False,
                "error": "Game is already over",
                "game_over": True
            }

        if not self.is_user_turn():
            return {
                "success": False,
                "error": "Not user's turn",
                "game_over": False
            }

        # Validate and make move
        try:
            move = chess.Move.from_uci(move_uci)
            if move not in self.board.legal_moves:
                return {
                    "success": False,
                    "error": "Illegal move",
                    "game_over": False
                }

            self.board.push(move)
            self.move_count += 1
            self.positions.append(self.board.fen())

        except Exception as e:
            return {
                "success": False,
                "error": f"Invalid move: {str(e)}",
                "game_over": False
            }

        # Check if opening phase ended
        if not self.is_opening_ended:
            await self._check_opening_end()

        # Check game end conditions
        await self._check_game_over()

        return {
            "success": True,
            "fen": self.get_current_fen(),
            "game_over": self.game_over,
            "result": self.result,
            "opening_ended": self.is_opening_ended
        }

    async def make_opponent_move(self) -> Dict:
        """
        Generate and make opponent's move using MAIA with weakness adjustment.

        Returns:
            Dict with move made and game state
        """
        if self.game_over:
            return {
                "success": False,
                "error": "Game is already over",
                "game_over": True
            }

        if self.is_user_turn():
            return {
                "success": False,
                "error": "Not opponent's turn",
                "game_over": False
            }

        # Generate opponent move
        move_uci = await self._select_opponent_move()

        if not move_uci:
            # Fallback to random legal move
            legal_moves = list(self.board.legal_moves)
            if not legal_moves:
                self.game_over = True
                return {
                    "success": False,
                    "error": "No legal moves",
                    "game_over": True
                }
            move = random.choice(legal_moves)
        else:
            move = chess.Move.from_uci(move_uci)

        # Make move
        self.board.push(move)
        self.move_count += 1
        self.positions.append(self.board.fen())

        # Check if opening phase ended
        if not self.is_opening_ended:
            await self._check_opening_end()

        # Check game end conditions
        await self._check_game_over()

        return {
            "success": True,
            "move": move.uci(),
            "fen": self.get_current_fen(),
            "game_over": self.game_over,
            "result": self.result,
            "opening_ended": self.is_opening_ended
        }

    async def _select_opponent_move(self) -> Optional[str]:
        """
        Select opponent move using MAIA with weakness-adjusted probabilities.

        Returns:
            Selected move in UCI notation, or None if error
        """
        try:
            # Get user's baseline ELO for MAIA model selection
            user_elo = self.trie_service.get_user_baseline_elo()

            # Get MAIA move probabilities
            maia_result = await compute_client.get_maia_probabilities(
                fen=self.board.fen(),
                user_elo=user_elo
            )

            moves = maia_result.get('moves', [])
            if not moves:
                return None

            # Apply weakness adjustment to probabilities
            adjusted_moves = await self._apply_weakness_adjustment(moves)

            if not adjusted_moves:
                return None

            # Select move based on adjusted probabilities
            move = self._weighted_random_choice(adjusted_moves)
            return move

        except Exception as e:
            print(f"Error selecting opponent move: {e}")
            return None

    async def _apply_weakness_adjustment(
        self,
        moves: List[Dict]
    ) -> List[Dict]:
        """
        Adjust move probabilities based on user's position weaknesses.

        Positions where user struggles get 2x probability boost.

        Args:
            moves: List of {move, probability} from MAIA

        Returns:
            List of {move, probability} with adjusted probabilities
        """
        adjusted = []

        for move_data in moves:
            move_uci = move_data['move']
            base_prob = move_data['probability']

            # Simulate move to get resulting position
            try:
                move = chess.Move.from_uci(move_uci)
                if move not in self.board.legal_moves:
                    continue

                # Make temporary move
                self.board.push(move)
                resulting_fen = self.board.fen()
                self.board.pop()

                # Get position node for this resulting position
                # User's perspective after opponent moves
                user_color = 'white' if self.user_plays_white else 'black'
                node = self.trie_service.get_node(resulting_fen, user_color)

                # Calculate weakness factor
                if node:
                    weakness = self.trie_service.get_weakness_factor(node)
                else:
                    weakness = 1.0  # Unknown position = neutral

                # Apply weakness multiplier
                adjusted_prob = base_prob * weakness

                adjusted.append({
                    'move': move_uci,
                    'probability': adjusted_prob,
                    'weakness_factor': weakness
                })

            except Exception as e:
                print(f"Error processing move {move_uci}: {e}")
                continue

        # Normalize probabilities
        if adjusted:
            total_prob = sum(m['probability'] for m in adjusted)
            if total_prob > 0:
                for m in adjusted:
                    m['probability'] /= total_prob

        return adjusted

    def _weighted_random_choice(self, moves: List[Dict]) -> Optional[str]:
        """
        Select move based on probability distribution.

        Args:
            moves: List of {move, probability}

        Returns:
            Selected move UCI, or None
        """
        if not moves:
            return None

        move_list = [m['move'] for m in moves]
        prob_list = [m['probability'] for m in moves]

        return random.choices(move_list, weights=prob_list, k=1)[0]

    async def _check_opening_end(self) -> None:
        """Check if opening phase has ended using compute service."""
        try:
            result = await compute_client.detect_opening_end(
                fen=self.board.fen(),
                move_number=self.move_count
            )

            if result.get('opening_ended', False):
                self.is_opening_ended = True

        except Exception as e:
            print(f"Error checking opening end: {e}")

    async def _check_game_over(self) -> None:
        """Check if game should end and determine result."""
        # Check standard chess game over conditions
        if self.board.is_checkmate():
            self.game_over = True
            # Winner is the side that just moved (delivered checkmate)
            winner_is_white = not self.board.turn
            if (winner_is_white and self.user_plays_white) or \
               (not winner_is_white and not self.user_plays_white):
                self.result = 'win'
            else:
                self.result = 'loss'
            return

        if self.board.is_stalemate() or self.board.is_insufficient_material() or \
           self.board.is_fifty_moves() or self.board.is_repetition():
            self.game_over = True
            self.result = 'draw'
            return

        # End training game when opening phase ends
        if self.is_opening_ended:
            self.game_over = True
            await self._determine_result_by_evaluation()

    async def _determine_result_by_evaluation(self) -> None:
        """
        Determine game result based on Stockfish evaluation.

        Uses centipawn evaluation to decide winner when opening ends.
        """
        try:
            eval_result = await compute_client.evaluate_position(
                fen=self.board.fen(),
                depth=20
            )

            centipawns = eval_result.get('centipawns', 0)
            mate_in = eval_result.get('mate_in')

            # Handle mate scenarios
            if mate_in is not None:
                if mate_in > 0:
                    # White is winning
                    self.result = 'win' if self.user_plays_white else 'loss'
                else:
                    # Black is winning
                    self.result = 'loss' if self.user_plays_white else 'win'
                return

            # Determine winner by centipawn evaluation
            # Adjust for user's perspective
            if self.user_plays_white:
                user_eval = centipawns
            else:
                user_eval = -centipawns

            # Thresholds for win/loss/draw
            if user_eval > 150:
                self.result = 'win'
            elif user_eval < -150:
                self.result = 'loss'
            else:
                self.result = 'draw'

        except Exception as e:
            print(f"Error evaluating position: {e}")
            # Default to draw on error
            self.result = 'draw'

    async def finalize_game(self) -> TrainingGame:
        """
        Finalize the game and save to database.

        Backpropagates result to position trie and creates TrainingGame record.

        Returns:
            Created TrainingGame instance
        """
        if not self.game_over:
            raise ValueError("Cannot finalize game that is not over")

        # Detect blunders in the game
        blunder_positions = await self.trie_service.detect_blunders_in_game(
            positions=self.positions,
            user_was_white=self.user_plays_white,
            depth=15  # Lighter depth for training games
        )

        # Backpropagate result to trie
        self.trie_service.backpropagate_game_result(
            positions=self.positions,
            result=self.result,
            is_real_game=False,  # This is a training game
            user_was_white=self.user_plays_white,
            blunder_positions=blunder_positions
        )

        # Generate PGN from moves
        pgn_board = chess.Board()
        moves_san = []
        for i in range(len(self.positions) - 1):
            # Get the move that was made
            if i < len(self.positions) - 1:
                # We can't reconstruct exact moves from FENs, so we'll store a simple notation
                moves_san.append(f"move{i+1}")

        # Simple PGN-like format
        pgn_text = f"[Result \"{self.result}\"]\n\n" + " ".join(moves_san)

        # Create training game record
        training_game = TrainingGame(
            session_id=self.session.id,
            user_id=self.user_id,
            user_color='white' if self.user_plays_white else 'black',
            result=self.result,
            pgn=pgn_text,
            moves_played=self.move_count,
            positions_visited=self.positions
        )

        self.db.add(training_game)
        self.db.commit()
        self.db.refresh(training_game)

        return training_game

    def get_game_state(self) -> Dict:
        """
        Get current game state summary.

        Returns:
            Dict with all relevant game state information
        """
        return {
            'fen': self.get_current_fen(),
            'user_plays_white': self.user_plays_white,
            'is_user_turn': self.is_user_turn(),
            'move_count': self.move_count,
            'opening_ended': self.is_opening_ended,
            'game_over': self.game_over,
            'result': self.result,
            'legal_moves': self.get_legal_moves(),
            'position_count': len(self.positions)
        }
