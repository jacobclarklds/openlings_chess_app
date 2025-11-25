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
from app.services.opening_book_service import OpeningBookService


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
        self.opening_book = OpeningBookService(db, user_id)

        # Game state
        self.is_opening_ended = False
        self.game_over = False
        self.result: Optional[str] = None  # 'win', 'loss', 'draw'

        # Move generation strategy
        # First 4-5 moves use opening book from user's games, then switch to MAIA
        self.use_opening_book = True  # Start with opening book
        self.opening_book_threshold = self._calculate_opening_threshold()
        self.opponent_move_number = 0  # Track opponent moves

        # Debug info (for development/debugging)
        self.last_maia_moves: List[Dict] = []  # Top MAIA moves with probabilities
        self.last_evaluation: Optional[float] = None  # Stockfish centipawns
        self.last_mate_in: Optional[int] = None  # Mate in N moves
        self.last_win_probability: Optional[float] = None  # MAIA win probability

    def _calculate_opening_threshold(self) -> int:
        """
        Calculate when to switch from opening book to MAIA.

        Randomly switch on move 4 or 5 (average of 4.5).

        Returns:
            Move number to switch at (4 or 5)
        """
        # 50% chance of switching on move 4, 50% on move 5
        return random.randint(4, 5)

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

            print(f"DEBUG: User making move: {move.uci()} on board with FEN: {self.board.fen()}")
            self.board.push(move)
            self.move_count += 1
            self.positions.append(self.board.fen())
            print(f"DEBUG: After user move, FEN is now: {self.board.fen()}")

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

        # Clear MAIA moves since user just moved (they're no longer relevant)
        self.last_maia_moves = []

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
        print(f"DEBUG: Opponent making move: {move.uci()} on board with FEN: {self.board.fen()}")
        self.board.push(move)
        self.move_count += 1
        self.opponent_move_number += 1
        self.positions.append(self.board.fen())
        print(f"DEBUG: After opponent move, FEN is now: {self.board.fen()}")

        # Check if we should switch from opening book to MAIA
        if self.use_opening_book and self.opponent_move_number >= self.opening_book_threshold:
            self.use_opening_book = False
            print(f"DEBUG: Switching from opening book to MAIA after move {self.opponent_move_number}")

        # Check if opening phase ended
        if not self.is_opening_ended:
            await self._check_opening_end()

        # Check game end conditions
        await self._check_game_over()

        # Get Stockfish evaluation for debugging
        await self._update_evaluation()

        # After opponent moves, get MAIA moves for the NEW position (user's turn)
        # This way the debug panel shows moves the user might consider
        if not self.game_over and self.is_user_turn():
            try:
                user_elo = self.trie_service.get_user_baseline_elo()
                maia_result = await compute_client.get_maia_probabilities(
                    fen=self.board.fen(),
                    user_elo=user_elo
                )
                moves = maia_result.get('moves', [])
                if moves:
                    legal_move_set = {move.uci() for move in self.board.legal_moves}
                    legal_moves = [
                        m for m in moves
                        if m.get('move') in legal_move_set
                    ]
                    self.last_maia_moves = legal_moves[:5] if legal_moves else []
                else:
                    self.last_maia_moves = []
            except Exception as e:
                print(f"Error getting MAIA moves for user: {e}")
                self.last_maia_moves = []

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
        Select opponent move using opening book or MAIA based on move number.

        First 4-5 moves use opening book from user's games.
        Then switches to MAIA with tactical punishment for blunders.

        Returns:
            Selected move in UCI notation, or None if error
        """
        try:
            # Choose move generation strategy
            if self.use_opening_book:
                print(f"DEBUG: Using opening book for move {self.opponent_move_number + 1}")
                return await self._select_opening_book_move()
            else:
                print(f"DEBUG: Using MAIA for move {self.opponent_move_number + 1}")
                return await self._select_maia_move()

        except Exception as e:
            print(f"Error selecting opponent move: {e}")
            return None

    async def _select_opening_book_move(self) -> Optional[str]:
        """
        Select move from user's opening repertoire (from imported games).

        Samples moves weighted by frequency from actual games.
        Falls back to MAIA if position not found in repertoire.

        Returns:
            Selected move in UCI notation, or None if error
        """
        try:
            # Try to get move from opening book
            move_uci = self.opening_book.get_opponent_move(
                self.board.fen(),
                self.user_plays_white
            )

            if move_uci:
                # Validate the move is legal
                try:
                    move_obj = chess.Move.from_uci(move_uci)
                    if move_obj in self.board.legal_moves:
                        print(f"DEBUG: Found opening book move: {move_uci}")
                        return move_uci
                    else:
                        print(f"WARNING: Opening book move {move_uci} is not legal!")
                except Exception as e:
                    print(f"ERROR: Invalid opening book move {move_uci}: {e}")

            # Fallback to MAIA if no opening book move found
            print(f"DEBUG: Position not in opening book, falling back to MAIA")
            return await self._select_maia_move()

        except Exception as e:
            print(f"Error selecting opening book move: {e}")
            # Fallback to MAIA on error
            return await self._select_maia_move()

    async def _select_maia_move(self) -> Optional[str]:
        """
        Select move using MAIA with tactical punishment for blunders.

        Checks if user hung a piece (≥100cp gain). If so, punishes 80% of the time.
        Otherwise uses MAIA probabilities with blunder filtering.

        Returns:
            Selected move in UCI notation, or None if error
        """
        try:
            # FIRST: Check for tactical punishments (hanging pieces)
            punishment_move = await self._check_tactical_punishment()
            if punishment_move:
                # 80% chance to punish
                if random.random() < 0.8:
                    print(f"DEBUG: PUNISHING hung piece with move {punishment_move}")
                    return punishment_move
                else:
                    print(f"DEBUG: Mercy! Not punishing hung piece (20% chance)")

            # Get user's baseline ELO for MAIA model selection
            user_elo = self.trie_service.get_user_baseline_elo()

            # Get MAIA move probabilities
            maia_result = await compute_client.get_maia_probabilities(
                fen=self.board.fen(),
                user_elo=user_elo
            )

            moves = maia_result.get('moves', [])
            win_prob = maia_result.get('win_probability')

            # Store win probability for debugging
            if win_prob is not None:
                self.last_win_probability = win_prob

            if not moves:
                return None

            # Filter to only legal moves and validate
            legal_move_set = {move.uci() for move in self.board.legal_moves}
            legal_moves = [
                m for m in moves
                if m.get('move') in legal_move_set
            ]

            if not legal_moves:
                print(f"WARNING: MAIA returned {len(moves)} moves but none are legal!")
                print(f"Legal moves: {list(legal_move_set)[:10]}")
                return None

            print(f"DEBUG: MAIA returned {len(moves)} moves, {len(legal_moves)} are legal")
            print(f"DEBUG: Top 3 legal MAIA moves: {[(m['move'], m['probability']) for m in legal_moves[:3]]}")

            # Store top 5 legal MAIA moves for debugging (for the current position)
            self.last_maia_moves = legal_moves[:5]

            # Filter out obvious blunders (e.g., knight retreats with 66% probability)
            print(f"DEBUG: Before blunder filtering, {len(legal_moves)} moves")
            filtered_moves = await self._filter_blunders(legal_moves)
            print(f"DEBUG: After blunder filtering, {len(filtered_moves)} moves")
            if filtered_moves:
                print(f"DEBUG: Top 3 filtered moves: {[(m['move'], m['probability']) for m in sorted(filtered_moves, key=lambda x: x['probability'], reverse=True)[:3]]}")

            # NOTE: Weakness adjustment is disabled - using raw MAIA probabilities
            # adjusted_moves = await self._apply_weakness_adjustment(filtered_moves)

            if not filtered_moves:
                return None

            # Select move based on MAIA probabilities (without weakness adjustment)
            move_uci = self._weighted_random_choice(filtered_moves)

            # Validate the selected move is legal before returning
            if move_uci:
                try:
                    move_obj = chess.Move.from_uci(move_uci)
                    if move_obj in self.board.legal_moves:
                        return move_uci
                    else:
                        print(f"WARNING: Selected move {move_uci} is not legal! Legal moves: {[m.uci() for m in self.board.legal_moves][:10]}")
                        return None
                except Exception as e:
                    print(f"ERROR: Invalid UCI move {move_uci}: {e}")
                    return None

            return None

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

                # Make temporary move - use try/finally to ensure pop happens
                self.board.push(move)
                try:
                    resulting_fen = self.board.fen()

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
                finally:
                    # Always pop the move, even if there's an exception
                    self.board.pop()

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

    async def _check_tactical_punishment(self) -> Optional[str]:
        """
        Check if user hung a piece (≥100cp material gain).

        Returns the move that wins material, or None if no such move exists.

        Returns:
            Move in UCI notation that wins ≥100cp, or None
        """
        try:
            # Get current evaluation
            current_eval = await compute_client.evaluate_position(
                fen=self.board.fen(),
                depth=15
            )
            current_cp = current_eval.get('centipawns', 0)

            # Remember whose turn it is (opponent's turn)
            side_to_move = self.board.turn

            # Check each legal move for material gain
            best_gain = 0
            best_move = None

            for move in self.board.legal_moves:
                self.board.push(move)
                try:
                    # Evaluate after the move
                    result_eval = await compute_client.evaluate_position(
                        fen=self.board.fen(),
                        depth=15
                    )
                    result_cp = result_eval.get('centipawns', 0)

                    # Calculate gain from opponent's perspective
                    if side_to_move == chess.WHITE:
                        # White to move: gain = how much better for white
                        gain = result_cp - current_cp
                    else:
                        # Black to move: gain = how much better for black (more negative)
                        gain = current_cp - result_cp

                    # Check if this wins material (≥100cp)
                    if gain >= 100 and gain > best_gain:
                        best_gain = gain
                        best_move = move.uci()

                finally:
                    self.board.pop()

            if best_move:
                print(f"DEBUG: Found tactical punishment! Move {best_move} wins {best_gain}cp")
                return best_move

            return None

        except Exception as e:
            print(f"Error checking tactical punishment: {e}")
            return None

    async def _filter_blunders(self, moves: List[Dict]) -> List[Dict]:
        """
        Filter out obvious blunders from MAIA's move distribution.

        Only evaluates moves with >5% probability (efficiency optimization).
        Blunders (>150 centipawn loss) are reduced to ≤2.5% after normalization
        using a 0.1x multiplier.

        Args:
            moves: List of {move, probability} from MAIA

        Returns:
            List of {move, probability} with blunders filtered/reduced
        """
        print(f"DEBUG: _filter_blunders called with {len(moves) if moves else 0} moves")

        if not moves:
            return moves

        # Threshold for evaluation (only check moves that are likely to be played)
        EVAL_THRESHOLD = 0.05  # 5%
        BLUNDER_MULTIPLIER = 0.1  # Reduce blunder probability by 10x
        MAX_BLUNDER_PROB = 0.025  # 2.5% max for blunders after normalization

        # Probability-weighted blunder threshold with smooth linear taper
        # High probability moves must be much better quality
        # 50%+ probability: 40cp threshold (very strict)
        # 5% probability: 150cp threshold (more tolerant)
        # Linear interpolation between these points
        def get_blunder_threshold(prob: float) -> int:
            """
            Get centipawn threshold based on move probability.
            Uses linear interpolation from 40cp at 50% to 150cp at 5%.
            """
            if prob >= 0.50:
                return 40  # Very high probability = very strict
            elif prob <= 0.05:
                return 150  # Low probability = more tolerant
            else:
                # Linear interpolation between 50% (40cp) and 5% (150cp)
                # Formula: threshold = 40 + (150-40) * (0.50-prob) / (0.50-0.05)
                return int(40 + 110 * (0.50 - prob) / 0.45)

        print(f"DEBUG: Filtering blunders with threshold {EVAL_THRESHOLD*100}% probability")

        # Get current position evaluation (before any move)
        try:
            current_eval = await compute_client.evaluate_position(
                fen=self.board.fen(),
                depth=15
            )
            current_centipawns = current_eval.get('centipawns', 0)
            current_mate = current_eval.get('mate_in')

            # If we're already in a mate situation, don't filter
            if current_mate is not None:
                return moves

        except Exception as e:
            print(f"Error getting current evaluation for blunder filtering: {e}")
            return moves  # Don't filter if we can't evaluate

        filtered = []

        for move_data in moves:
            move_uci = move_data['move']
            probability = move_data['probability']

            # Only evaluate moves with significant probability
            if probability < EVAL_THRESHOLD:
                # Keep low-probability moves as-is (not worth evaluating)
                filtered.append({
                    'move': move_uci,
                    'probability': probability,
                    'is_blunder': False
                })
                continue

            print(f"DEBUG: Evaluating move {move_uci} with probability {probability*100:.1f}%")

            # Evaluate the move
            try:
                move = chess.Move.from_uci(move_uci)
                if move not in self.board.legal_moves:
                    continue

                # Remember whose turn it is BEFORE making the move
                side_to_move = self.board.turn

                # Make temporary move
                self.board.push(move)
                try:
                    # Evaluate resulting position
                    result_eval = await compute_client.evaluate_position(
                        fen=self.board.fen(),
                        depth=15
                    )
                    result_centipawns = result_eval.get('centipawns', 0)
                    result_mate = result_eval.get('mate_in')

                    # Calculate centipawn loss from the moving side's perspective
                    # The evaluation is always from White's perspective
                    # Centipawn loss = how much worse is the position for the side that just moved
                    if result_mate is not None:
                        # Moving into mate is definitely a blunder
                        # If we just moved and now we're getting mated, that's bad
                        if (side_to_move == chess.WHITE and result_mate < 0) or \
                           (side_to_move == chess.BLACK and result_mate > 0):
                            # We're getting mated after this move
                            centipawn_loss = 999999
                        else:
                            # We're delivering mate after this move (good!)
                            centipawn_loss = -999999
                    else:
                        # Normal centipawn calculation
                        # Stockfish evals are from White's perspective
                        # If White moved: loss = (current_eval - result_eval)
                        # If Black moved: loss = (result_eval - current_eval) (because Black wants negative evals)
                        if side_to_move == chess.WHITE:
                            centipawn_loss = current_centipawns - result_centipawns
                        else:
                            # Black wants the evaluation to go down (more negative)
                            # So loss is when eval goes up (becomes less negative/more positive)
                            centipawn_loss = result_centipawns - current_centipawns

                    # Check if it's a blunder using probability-weighted threshold
                    blunder_threshold = get_blunder_threshold(probability)
                    is_blunder = centipawn_loss > blunder_threshold

                    print(f"DEBUG: Move {move_uci}: prob={probability*100:.1f}%, threshold={blunder_threshold}cp, loss={centipawn_loss:.0f}cp, is_blunder={is_blunder}")

                    if is_blunder:
                        # Reduce blunder probability
                        adjusted_prob = probability * BLUNDER_MULTIPLIER
                        print(f"DEBUG: Blunder detected! Move {move_uci} loses {centipawn_loss:.0f}cp, "
                              f"reducing probability from {probability*100:.1f}% to {adjusted_prob*100:.1f}%")

                        filtered.append({
                            'move': move_uci,
                            'probability': adjusted_prob,
                            'is_blunder': True,
                            'centipawn_loss': centipawn_loss
                        })
                    else:
                        # Keep non-blunders as-is
                        filtered.append({
                            'move': move_uci,
                            'probability': probability,
                            'is_blunder': False,
                            'centipawn_loss': centipawn_loss
                        })

                finally:
                    self.board.pop()

            except Exception as e:
                print(f"Error evaluating move {move_uci}: {e}")
                # Keep move as-is if we can't evaluate it
                filtered.append({
                    'move': move_uci,
                    'probability': probability,
                    'is_blunder': False
                })

        # Normalize probabilities
        if filtered:
            total_prob = sum(m['probability'] for m in filtered)
            if total_prob > 0:
                for m in filtered:
                    m['probability'] /= total_prob

                # Enforce max blunder probability after normalization
                for m in filtered:
                    if m.get('is_blunder') and m['probability'] > MAX_BLUNDER_PROB:
                        print(f"DEBUG: Capping blunder {m['move']} from {m['probability']*100:.1f}% to {MAX_BLUNDER_PROB*100:.1f}%")
                        m['probability'] = MAX_BLUNDER_PROB

                # Renormalize after capping
                total_prob = sum(m['probability'] for m in filtered)
                if total_prob > 0:
                    for m in filtered:
                        m['probability'] /= total_prob

        return filtered

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

    async def _update_evaluation(self) -> None:
        """Update Stockfish evaluation for current position (for debugging)."""
        try:
            eval_result = await compute_client.evaluate_position(
                fen=self.board.fen(),
                depth=15  # Lighter depth for real-time evaluation
            )

            self.last_evaluation = eval_result.get('centipawns')
            self.last_mate_in = eval_result.get('mate_in')

        except Exception as e:
            print(f"Error updating evaluation: {e}")
            # Don't fail the move if evaluation fails
            self.last_evaluation = None
            self.last_mate_in = None

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
            # In opening training, even small advantages matter
            # 30cp (~1/3 pawn) is a meaningful edge out of the opening
            if user_eval > 30:
                self.result = 'win'
            elif user_eval < -30:
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
