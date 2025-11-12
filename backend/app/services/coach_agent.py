"""
ChessCoachAgent: AI agent powered by Anthropic Claude.
Generates personalized chess lessons with annotations and questions.
"""

import asyncio
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
import chess
import chess.pgn
import io
from app.core.config import settings
from app.services.agent_tools import AgentToolkit
from app.services.tool_definitions import TOOL_DEFINITIONS


class ChessCoachAgent:
    """
    AI agent that generates personalized chess lessons.
    Uses Claude with tool calling to analyze games and create educational content.
    """

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.toolkit = AgentToolkit()
        self.model = settings.ANTHROPIC_MODEL
        self.max_tokens = settings.ANTHROPIC_MAX_TOKENS

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
            focus_areas: Optional list of areas to focus on (e.g., ["tactics", "endgame"])

        Returns:
            Dictionary with lesson data including comments, annotations, and questions
        """
        # Parse the PGN to extract positions and moves
        game_data = self._parse_pgn(pgn)

        # Build the system prompt
        system_prompt = self._build_system_prompt(user_elo, focus_areas)

        # Build the initial user prompt
        user_prompt = self._build_user_prompt(game_data, user_elo)

        # Run the agentic loop
        lesson_comments = await self._agentic_loop(
            system_prompt,
            user_prompt,
            game_data,
            user_elo
        )

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
        """Build the system prompt for Claude."""
        base_prompt = f"""You are an expert chess coach creating a personalized lesson for a student with ELO rating {user_elo}.

Your goal is to analyze the provided chess game and create educational commentary that:
1. Identifies key moments and critical positions
2. Explains strategic and tactical concepts appropriate for the student's level
3. Uses visual annotations (arrows, circles, highlights) to illustrate ideas
4. Asks interactive questions to test understanding
5. Provides clear, encouraging, and actionable feedback

You have access to chess analysis tools:
- analyze_position: Get engine evaluation and human-like move predictions
- analyze_move: Evaluate move quality and compare to best moves
- classify_opening: Identify the opening played
- get_position_type: Determine if opening/middlegame/endgame
- create_board_annotation: Add visual markers to the board
- create_question: Create interactive questions for the student

Guidelines for creating lessons:
- Focus on 3-5 key moments in the game (don't comment on every move)
- Start with opening overview, then critical moments, then conclusion
- Use markdown formatting for clear structure
- Add 1-2 visual annotations per position to highlight key squares/pieces
- Include 1 question every 2-3 comments to engage the student
- Adapt complexity to the student's ELO level
- Be encouraging and constructive, not critical"""

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

PGN:
{game_data['pgn']}

Student ELO: {user_elo}

Create a lesson with 3-5 coach comments focusing on the most instructive moments.
For each comment:
1. Use tools to analyze the position
2. Write educational commentary in markdown
3. Add visual annotations to highlight key ideas
4. Optionally include an interactive question

Format your response as a series of lesson steps."""

    async def _agentic_loop(
        self,
        system_prompt: str,
        user_prompt: str,
        game_data: Dict[str, Any],
        user_elo: int
    ) -> List[Dict[str, Any]]:
        """
        Run the agentic loop with Claude.
        Handles tool calling and builds lesson comments.
        """
        messages = [{"role": "user", "content": user_prompt}]
        lesson_comments = []
        current_comment_text = ""
        max_iterations = 30  # Prevent infinite loops

        for iteration in range(max_iterations):
            # Call Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                tools=TOOL_DEFINITIONS,
                messages=messages
            )

            # Add assistant response to messages
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # Check stop reason
            if response.stop_reason == "end_turn":
                # Agent is done, save final comment if any
                if current_comment_text.strip():
                    lesson_comments.append(self._finalize_comment(
                        current_comment_text,
                        game_data['positions'][0]['fen']  # Default to start position
                    ))
                break

            # Process tool calls
            if response.stop_reason == "tool_use":
                tool_results = []

                for block in response.content:
                    if block.type == "text":
                        # Accumulate commentary text
                        current_comment_text += block.text

                        # Check if this indicates a new comment section
                        if "---" in block.text or "### " in block.text:
                            # Save previous comment
                            if current_comment_text.strip():
                                lesson_comments.append(self._finalize_comment(
                                    current_comment_text,
                                    game_data['positions'][len(lesson_comments)]['fen']
                                    if len(lesson_comments) < len(game_data['positions'])
                                    else game_data['positions'][-1]['fen']
                                ))
                            # Clear for next comment
                            self.toolkit.clear_context()
                            current_comment_text = ""

                    elif block.type == "tool_use":
                        # Execute tool
                        tool_name = block.name
                        tool_input = block.input

                        try:
                            result = await self.toolkit.execute_tool(tool_name, tool_input)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": str(result)
                            })
                        except Exception as e:
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": f"Error: {str(e)}",
                                "is_error": True
                            })

                # Add tool results to messages
                if tool_results:
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })

        return lesson_comments

    def _finalize_comment(self, text: str, position_fen: str) -> Dict[str, Any]:
        """Finalize a lesson comment with annotations and questions."""
        import time

        return {
            "id": str(time.time()),
            "text": text.strip(),
            "position_fen": position_fen,
            "annotations": self.toolkit.get_current_annotations(),
            "question": self.toolkit.get_current_question(),
            "timestamp": int(time.time() * 1000)
        }

    async def cleanup(self):
        """Clean up resources."""
        await self.toolkit.cleanup()
