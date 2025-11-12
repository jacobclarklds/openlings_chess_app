"""
AgentToolkit: Provides tools for the Chess Coach AI Agent.
Bridges between Claude's tool calls and our chess analysis services.
"""

import asyncio
from typing import Dict, Any, List
import uuid
from app.services.stockfish_service import StockfishService
from app.services.maia_service import MaiaService
from app.services.analysis_coordinator import AnalysisCoordinator
from app.services.opening_service import OpeningService


class AgentToolkit:
    """
    Toolkit that provides chess analysis tools to the AI agent.
    Each method corresponds to a tool that Claude can call.
    """

    def __init__(self):
        self.stockfish = StockfishService()
        self.maia = MaiaService(self.stockfish)
        self.coordinator = AnalysisCoordinator(self.stockfish, self.maia)
        self.opening_service = OpeningService()
        
        # Store annotations and questions created during lesson generation
        self.current_annotations: List[Dict[str, Any]] = []
        self.current_question: Dict[str, Any] = None

    async def analyze_position(self, fen: str, user_elo: int) -> Dict[str, Any]:
        """
        Analyze a chess position comprehensively.
        
        Args:
            fen: Position in FEN format
            user_elo: User's ELO rating
            
        Returns:
            Dictionary with stockfish_eval and maia_predictions
        """
        result = await self.coordinator.analyze_position_full(fen, user_elo)
        return result

    async def analyze_move(self, fen_before: str, move: str, user_elo: int) -> Dict[str, Any]:
        """
        Analyze a specific move made in a position.
        
        Args:
            fen_before: Position before the move
            move: Move in UCI format
            user_elo: User's ELO rating
            
        Returns:
            Dictionary with move classification and analysis
        """
        result = await self.coordinator.analyze_user_move(fen_before, move, user_elo)
        return result

    async def classify_opening(self, pgn: str) -> Dict[str, Any]:
        """
        Identify the chess opening from PGN.
        
        Args:
            pgn: Game in PGN format
            
        Returns:
            Dictionary with opening classification
        """
        result = await self.opening_service.get_opening_classification(pgn)
        return result

    async def get_position_type(self, fen: str) -> str:
        """
        Classify position as opening/middlegame/endgame.
        
        Args:
            fen: Position in FEN format
            
        Returns:
            Position type string
        """
        result = await self.opening_service.get_position_type(fen)
        return result

    def create_board_annotation(
        self,
        annotation_type: str,
        color: str,
        from_square: str = None,
        to_square: str = None,
        square: str = None
    ) -> Dict[str, Any]:
        """
        Create a visual board annotation.
        
        Args:
            annotation_type: 'arrow', 'circle', or 'highlight'
            color: Color for the annotation
            from_square: Start square for arrows
            to_square: End square for arrows
            square: Square for circles/highlights
            
        Returns:
            Annotation dictionary
        """
        annotation = {
            "id": str(uuid.uuid4()),
            "type": annotation_type,
            "color": color
        }

        if annotation_type == "arrow":
            if not from_square or not to_square:
                raise ValueError("Arrows require both from_square and to_square")
            annotation["from"] = from_square
            annotation["to"] = to_square
        else:  # circle or highlight
            if not square:
                raise ValueError(f"{annotation_type} requires a square parameter")
            annotation["square"] = square

        self.current_annotations.append(annotation)
        return annotation

    def create_question(
        self,
        question_type: str,
        question_text: str,
        correct_answer: str,
        options: List[str] = None,
        explanation: str = None
    ) -> Dict[str, Any]:
        """
        Create an interactive question for the user.
        
        Args:
            question_type: 'multiple_choice' or 'move_selection'
            question_text: The question to ask
            correct_answer: The correct answer
            options: Answer options (for multiple choice)
            explanation: Explanation of the answer
            
        Returns:
            Question dictionary
        """
        question = {
            "type": question_type,
            "question": question_text,
            "correct_answer": correct_answer
        }

        if question_type == "multiple_choice":
            if not options or len(options) < 2:
                raise ValueError("Multiple choice questions require at least 2 options")
            question["options"] = options

        if explanation:
            question["explanation"] = explanation

        self.current_question = question
        return question

    def get_current_annotations(self) -> List[Dict[str, Any]]:
        """Get all annotations created in current context."""
        return self.current_annotations

    def get_current_question(self) -> Dict[str, Any]:
        """Get the current question if one was created."""
        return self.current_question

    def clear_context(self):
        """Clear annotations and questions for next comment."""
        self.current_annotations = []
        self.current_question = None

    async def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """
        Execute a tool by name with given input.
        
        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool
            
        Returns:
            Tool execution result
        """
        if tool_name == "analyze_position":
            return await self.analyze_position(
                tool_input["fen"],
                tool_input["user_elo"]
            )
        elif tool_name == "analyze_move":
            return await self.analyze_move(
                tool_input["fen_before"],
                tool_input["move"],
                tool_input["user_elo"]
            )
        elif tool_name == "classify_opening":
            return await self.classify_opening(tool_input["pgn"])
        elif tool_name == "get_position_type":
            return await self.get_position_type(tool_input["fen"])
        elif tool_name == "create_board_annotation":
            return self.create_board_annotation(
                tool_input["annotation_type"],
                tool_input["color"],
                tool_input.get("from_square"),
                tool_input.get("to_square"),
                tool_input.get("square")
            )
        elif tool_name == "create_question":
            return self.create_question(
                tool_input["question_type"],
                tool_input["question_text"],
                tool_input["correct_answer"],
                tool_input.get("options"),
                tool_input.get("explanation")
            )
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def cleanup(self):
        """Clean up resources."""
        await self.stockfish.cleanup()
