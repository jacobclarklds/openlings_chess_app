"""
ChessCoachAgent using Ollama instead of Anthropic.
Generates personalized chess lessons using local LLM.
"""

import asyncio
import json
import logging
import time
from typing import List, Dict, Any, Optional
import chess
import chess.pgn
import io
import ollama
from app.core.config import settings
from app.services.agent_tools import AgentToolkit

logger = logging.getLogger(__name__)


class OllamaChessCoachAgent:
    """
    AI agent that generates personalized chess lessons using Ollama.
    """

    def __init__(self):
        self.toolkit = AgentToolkit()
        self.model = settings.OLLAMA_MODEL
        self.base_url = settings.OLLAMA_BASE_URL

    async def generate_lesson(
        self,
        pgn: str,
        user_elo: int,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete lesson from a chess game.

        Args:
            pgn: The game in PGN format
            user_elo: User's ELO rating for personalized analysis
            focus_areas: Optional list of areas to focus on

        Returns:
            Dictionary with lesson data including comments, annotations, and questions
        """
        logger.info("  📖 Parsing PGN...")
        parse_start = time.time()
        # Parse the PGN to extract positions and moves
        game_data = self._parse_pgn(pgn)
        parse_time = time.time() - parse_start
        logger.info(f"  ✓ PGN parsed in {parse_time:.2f}s - Found {len(game_data['moves'])} moves, {len(game_data['positions'])} positions")

        # Build the prompt
        logger.info("  📝 Building prompts...")
        prompt_start = time.time()
        system_prompt = self._build_system_prompt(user_elo, focus_areas)
        user_prompt = self._build_user_prompt(game_data, user_elo)
        prompt_time = time.time() - prompt_start
        logger.info(f"  ✓ Prompts built in {prompt_time:.2f}s")

        # Generate lesson using Ollama with function calling
        logger.info("  🤖 Generating lesson with Ollama...")
        generation_start = time.time()
        lesson_comments = await self._generate_with_ollama(
            system_prompt,
            user_prompt,
            game_data,
            user_elo
        )
        generation_time = time.time() - generation_start
        logger.info(f"  ✓ Lesson generation completed in {generation_time:.2f}s")

        return {
            "comments": lesson_comments,
            "total_steps": len(lesson_comments),
            "focus_areas": focus_areas or []
        }

    def _parse_pgn(self, pgn: str) -> Dict[str, Any]:
        """Parse PGN and extract positions and moves."""
        pgn_io = io.StringIO(pgn)
        game = chess.pgn.read_game(pgn_io)

        if not game:
            raise ValueError("Invalid PGN format")

        positions = []
        moves = []
        board = game.board()

        # Store initial position
        positions.append({
            "fen": board.fen(),
            "move_number": 0,
            "move": None
        })

        # Iterate through moves
        for move_number, move in enumerate(game.mainline_moves(), start=1):
            uci_move = move.uci()
            moves.append(uci_move)
            board.push(move)
            positions.append({
                "fen": board.fen(),
                "move_number": move_number,
                "move": uci_move
            })

        return {
            "pgn": pgn,
            "positions": positions,
            "moves": moves,
            "result": game.headers.get("Result", "*"),
            "white": game.headers.get("White", "Unknown"),
            "black": game.headers.get("Black", "Unknown")
        }

    def _build_system_prompt(self, user_elo: int, focus_areas: Optional[List[str]]) -> str:
        """Build the system prompt for the LLM."""
        base_prompt = f"""You are an expert chess coach creating a personalized lesson for a student with ELO rating {user_elo}.

Your goal is to analyze the provided chess game and create educational commentary that:
1. Identifies 3-5 key moments in the game
2. Explains strategic and tactical concepts appropriate for the student's level
3. Uses visual annotations (arrows, circles, highlights) to illustrate ideas
4. Includes interactive questions to test understanding
5. Provides clear, encouraging, and actionable feedback

You have access to the following tools:
- analyze_position: Get engine evaluation and move predictions
- analyze_move: Evaluate move quality
- classify_opening: Identify the opening played
- get_position_type: Determine if opening/middlegame/endgame
- create_board_annotation: Add visual markers (arrows, circles, highlights)
- create_question: Create interactive questions

Guidelines:
- Focus on 3-5 key moments, don't comment on every move
- Start with opening overview, then critical moments, then conclusion
- Add 1-2 visual annotations per position
- Include 1 question every 2-3 comments
- Adapt complexity to the student's ELO level
- Be encouraging and constructive"""

        if focus_areas:
            base_prompt += f"\n- Pay special attention to: {', '.join(focus_areas)}"

        return base_prompt

    def _build_user_prompt(self, game_data: Dict[str, Any], user_elo: int) -> str:
        """Build the initial user prompt."""
        return f"""Please analyze this chess game and create a lesson:

Game Details:
- White: {game_data['white']}
- Black: {game_data['black']}
- Result: {game_data['result']}
- Total Moves: {len(game_data['moves'])}

Student ELO: {user_elo}

Create a lesson with 3-5 coach comments focusing on the most instructive moments.

For each comment, you should:
1. Select an important position from the game
2. Write educational commentary explaining what's happening (use markdown formatting)
3. Use the tools to analyze the position if needed
4. Add 1-2 visual annotations using create_board_annotation
5. Optionally include a question using create_question

Format your response as JSON with this structure:
{{
  "comments": [
    {{
      "position_index": 0,
      "text": "## Opening Principles\\n\\nYour markdown commentary here...",
      "annotations_created": true,
      "question_created": false
    }},
    ...
  ]
}}

After creating each comment, I'll provide you with the current annotations and questions that were saved."""

    async def _generate_with_ollama(
        self,
        system_prompt: str,
        user_prompt: str,
        game_data: Dict[str, Any],
        user_elo: int
    ) -> List[Dict[str, Any]]:
        """
        Generate lesson using Ollama.
        Since Ollama doesn't have native function calling, we'll use a simpler approach.
        """
        lesson_comments = []

        # For now, generate a simple lesson without tool calling
        # We'll create comments for each move

        positions = game_data['positions']
        total_moves = len(game_data['moves'])

        # For short games (< 10 moves), show every position
        # For longer games, show key positions
        if total_moves <= 10:
            # Show all positions for short games
            key_indices = list(range(len(positions)))
            logger.info(f"    Short game: showing all {len(key_indices)} positions")
        else:
            # Select key positions to analyze for longer games
            key_indices = [
                0,  # Opening position
                min(5, total_moves // 4),  # Early game
                total_moves // 2,  # Middle game
                3 * total_moves // 4,  # Late game
                total_moves  # Final position
            ]
            logger.info(f"    Long game: selected {len(key_indices)} key positions to analyze")

        # Track if we've added an interactive move yet
        has_interactive_move = False
        interactive_position_index = None

        # Choose a middle position for the interactive move (not first or last)
        if len(key_indices) >= 3:
            interactive_position_index = len(key_indices) // 2

        for idx, position_idx in enumerate(key_indices):  # Generate comment for each selected position
            if position_idx >= len(positions):
                logger.warning(f"    ⚠️  Position index {position_idx} out of range, skipping")
                continue

            position = positions[position_idx]
            comment_start = time.time()
            logger.info(f"    📍 Generating comment {idx + 1}/{len(key_indices)} for position {position_idx} (move {position['move_number']})...")

            # Determine if this should be an interactive move
            is_interactive = (not has_interactive_move and
                            idx == interactive_position_index and
                            position_idx < len(positions) - 1)  # Not the last position

            if is_interactive:
                has_interactive_move = True
                logger.info(f"    🎮 Making position {idx + 1} interactive - user will need to make a move")

            # Generate comment using Ollama
            comment_text = await self._generate_comment_for_position(
                position,
                game_data,
                user_elo,
                idx,
                is_interactive
            )

            # Create some basic annotations
            annotations = self._create_default_annotations(position['fen'], idx)

            # Get the expected move if this is interactive
            expected_move = None
            if is_interactive and position_idx + 1 < len(positions):
                next_move = positions[position_idx + 1].get('move')
                if next_move and len(next_move) >= 4:
                    expected_move = {
                        'from': next_move[:2],
                        'to': next_move[2:4]
                    }

            lesson_comments.append({
                "id": str(idx),
                "text": comment_text,
                "position_fen": position['fen'],
                "annotations": annotations,
                "question": None if idx % 2 == 0 else self._create_default_question(idx),
                "timestamp": int(asyncio.get_event_loop().time() * 1000),
                "move_to_make": position.get('move'),
                "requires_move": is_interactive,
                "expected_move": expected_move
            })

            comment_time = time.time() - comment_start
            logger.info(f"    ✓ Comment {idx + 1} generated in {comment_time:.2f}s ({len(comment_text)} characters)")

        logger.info(f"  ✓ Generated {len(lesson_comments)} total comments")
        return lesson_comments

    async def _generate_comment_for_position(
        self,
        position: Dict[str, Any],
        game_data: Dict[str, Any],
        user_elo: int,
        comment_index: int,
        is_interactive: bool = False
    ) -> str:
        """Generate commentary for a specific position using Ollama."""

        # Analyze the position
        logger.info(f"      🔍 Analyzing position {position['move_number']}...")
        analysis_start = time.time()
        try:
            analysis = await self.toolkit.analyze_position(
                position['fen'],
                user_elo
            )
            analysis_time = time.time() - analysis_start
            logger.info(f"      ✓ Position analysis completed in {analysis_time:.2f}s")
        except Exception as e:
            logger.warning(f"      ⚠️  Analysis failed: {e}")
            analysis = None

        # Determine stage
        move_num = position['move_number']
        total_moves = len(game_data['moves'])

        if move_num == 0:
            stage = "opening"
            stage_title = "Opening Position"
        elif move_num < 10:
            stage = "early_game"
            stage_title = "Early Game"
        elif move_num < total_moves * 0.7:
            stage = "middle_game"
            stage_title = "Middle Game"
        else:
            stage = "endgame"
            stage_title = "Endgame"

        # Build context for Ollama
        if is_interactive:
            context = f"""You are a chess coach. This is an INTERACTIVE position where the student will make a move.

Position FEN: {position['fen']}
Move Number: {move_num}
Game Stage: {stage_title}
Student ELO: {user_elo}
White: {game_data['white']}
Black: {game_data['black']}
"""
            if analysis:
                context += f"\nEngine Evaluation: {analysis.get('stockfish_eval', {}).get('evaluation', 'N/A')}"
                context += f"\nBest Move: {analysis.get('stockfish_eval', {}).get('best_move', 'N/A')}"

            context += f"\n\nWrite a BRIEF (3-5 sentences) challenge for the student. Use markdown heading for the title. Ask them to find the best move in this position. Explain why this moment is important and what they should look for. End with 'Make your move on the board.' Be encouraging!"
        else:
            context = f"""You are a chess coach. Analyze this position and create educational commentary.

Position FEN: {position['fen']}
Move Number: {move_num}
Game Stage: {stage_title}
Student ELO: {user_elo}
White: {game_data['white']}
Black: {game_data['black']}
"""

            if analysis:
                context += f"\nEngine Evaluation: {analysis.get('stockfish_eval', {}).get('evaluation', 'N/A')}"
                context += f"\nBest Move: {analysis.get('stockfish_eval', {}).get('best_move', 'N/A')}"

            context += f"\n\nWrite a VERY BRIEF (3-5 sentences max) educational comment about this position. Use markdown heading for the title. Be concise and focused. Teach ONE key concept appropriate for a {user_elo} ELO player."

        # Call Ollama
        logger.info(f"      🤖 Calling Ollama API (model: {self.model})...")
        ollama_start = time.time()
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an expert chess coach. Provide clear, educational commentary using markdown formatting.'
                    },
                    {
                        'role': 'user',
                        'content': context
                    }
                ],
                options={
                    'temperature': 0.7,
                    'num_predict': 500,
                }
            )
            
            ollama_time = time.time() - ollama_start
            content = response['message']['content']
            logger.info(f"      ✓ Ollama response received in {ollama_time:.2f}s ({len(content)} characters)")
            return content
        except Exception as e:
            ollama_time = time.time() - ollama_start
            logger.error(f"      ❌ Ollama generation failed after {ollama_time:.2f}s: {e}")
            # Fallback commentary
            return f"## {stage_title}\n\nThis is an important position in the game. {self._get_generic_advice(stage, user_elo)}"

    def _get_generic_advice(self, stage: str, elo: int) -> str:
        """Get generic advice based on game stage."""
        advice = {
            "opening": "Focus on controlling the center, developing your pieces quickly, and castling early to keep your king safe.",
            "early_game": "Continue developing your pieces and look for tactical opportunities. Make sure all your pieces are contributing to the game.",
            "middle_game": "Look for weaknesses in your opponent's position. Consider pawn breaks, piece placement, and king safety.",
            "endgame": "Activate your king, create passed pawns, and use your pieces efficiently. Every move counts in the endgame!"
        }
        return advice.get(stage, "Analyze the position carefully and find the best plan.")

    def _create_default_annotations(self, fen: str, comment_index: int) -> List[Dict[str, Any]]:
        """Create meaningful annotations based on position analysis."""
        annotations = []

        try:
            board = chess.Board(fen)

            # For opening positions (index 0)
            if comment_index == 0:
                # Highlight center squares
                for square in ['e4', 'd4', 'e5', 'd5']:
                    annotations.append({
                        'id': f'ann_{square}',
                        'type': 'highlight',
                        'color': 'green',
                        'square': square
                    })
                # Add arrows showing ideal piece development
                annotations.append({
                    'id': 'ann_arrow_1',
                    'type': 'arrow',
                    'color': 'blue',
                    'from': 'g1',
                    'to': 'f3'
                })
                annotations.append({
                    'id': 'ann_arrow_2',
                    'type': 'arrow',
                    'color': 'blue',
                    'from': 'b1',
                    'to': 'c3'
                })
            else:
                # For other positions, highlight pieces that moved recently or are under attack
                # Find pieces and create circles/highlights
                piece_map = board.piece_map()
                annotation_count = 0

                # Highlight pieces in the center
                for square in [chess.E4, chess.D4, chess.E5, chess.D5]:
                    if square in piece_map:
                        annotations.append({
                            'id': f'ann_center_{annotation_count}',
                            'type': 'circle',
                            'color': 'yellow',
                            'square': chess.square_name(square)
                        })
                        annotation_count += 1

                # Find attackers and defenders (limited to avoid clutter)
                if len(annotations) < 3:
                    # Find king square and highlight it
                    for square, piece in piece_map.items():
                        if piece.piece_type == chess.KING:
                            annotations.append({
                                'id': f'ann_king_{annotation_count}',
                                'type': 'circle',
                                'color': 'red' if board.is_check() else 'blue',
                                'square': chess.square_name(square)
                            })
                            annotation_count += 1
                            if annotation_count >= 2:
                                break

                # Add at least one arrow if we haven't added many annotations
                if len(annotations) < 3 and len(list(board.legal_moves)) > 0:
                    # Pick a random good-looking move to show
                    moves = list(board.legal_moves)
                    for move in moves[:3]:
                        if move.promotion is None:  # Avoid complex promotion moves
                            annotations.append({
                                'id': f'ann_move_arrow_{annotation_count}',
                                'type': 'arrow',
                                'color': 'green',
                                'from': chess.square_name(move.from_square),
                                'to': chess.square_name(move.to_square)
                            })
                            break

        except Exception as e:
            logger.warning(f"Failed to create annotations for position: {e}")
            # Fallback to simple center highlights
            for square in ['e4', 'd4']:
                annotations.append({
                    'id': f'ann_fallback_{square}',
                    'type': 'highlight',
                    'color': 'green',
                    'square': square
                })

        return annotations

    def _create_default_question(self, comment_index: int) -> Dict[str, Any]:
        """Create a default question."""
        questions = [
            {
                'type': 'multiple_choice',
                'question': 'What is the most important principle in this position?',
                'options': [
                    'Control the center',
                    'Attack the king immediately',
                    'Trade all pieces',
                    'Move the same piece twice'
                ],
                'correct_answer': 'Control the center',
                'explanation': 'Controlling the center gives your pieces more mobility and influence over the board.'
            },
            {
                'type': 'multiple_choice',
                'question': 'What should be your main focus here?',
                'options': [
                    'Piece development',
                    'Immediate attack',
                    'Passive defense',
                    'Random moves'
                ],
                'correct_answer': 'Piece development',
                'explanation': 'Developing your pieces efficiently is crucial in the opening and early middlegame.'
            }
        ]
        
        return questions[comment_index % len(questions)]

    async def cleanup(self):
        """Clean up resources."""
        await self.toolkit.cleanup()
