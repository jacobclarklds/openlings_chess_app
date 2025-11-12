"""
Tool definitions for the Chess Coach AI Agent.
Defines the tools available to Claude for analyzing chess positions and creating lessons.
"""

from typing import List, Dict, Any

# Tool definitions in Anthropic's format
TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "analyze_position",
        "description": "Analyze a chess position using Stockfish and MAIA engines. Returns comprehensive analysis including evaluation, best moves, and human-like move predictions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fen": {
                    "type": "string",
                    "description": "The position in FEN (Forsyth-Edwards Notation) format"
                },
                "user_elo": {
                    "type": "integer",
                    "description": "The user's ELO rating for personalized analysis",
                    "minimum": 800,
                    "maximum": 2800
                }
            },
            "required": ["fen", "user_elo"]
        }
    },
    {
        "name": "analyze_move",
        "description": "Analyze a specific move made in a position. Classifies move quality (excellent/good/inaccuracy/mistake/blunder) and compares to engine recommendations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fen_before": {
                    "type": "string",
                    "description": "The position before the move in FEN format"
                },
                "move": {
                    "type": "string",
                    "description": "The move in UCI format (e.g., 'e2e4', 'e7e8q')"
                },
                "user_elo": {
                    "type": "integer",
                    "description": "The user's ELO rating",
                    "minimum": 800,
                    "maximum": 2800
                }
            },
            "required": ["fen_before", "move", "user_elo"]
        }
    },
    {
        "name": "classify_opening",
        "description": "Identify the chess opening from a PGN string. Returns ECO code, opening name, variation, and typical plans.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pgn": {
                    "type": "string",
                    "description": "The game in PGN format"
                }
            },
            "required": ["pgn"]
        }
    },
    {
        "name": "get_position_type",
        "description": "Classify a position as opening, middlegame, or endgame based on piece count and structure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fen": {
                    "type": "string",
                    "description": "The position in FEN format"
                }
            },
            "required": ["fen"]
        }
    },
    {
        "name": "create_board_annotation",
        "description": "Create visual annotations for the chess board (arrows, circles, highlights) to illustrate concepts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "annotation_type": {
                    "type": "string",
                    "enum": ["arrow", "circle", "highlight"],
                    "description": "Type of annotation to create"
                },
                "color": {
                    "type": "string",
                    "enum": ["red", "green", "blue", "yellow", "orange"],
                    "description": "Color for the annotation"
                },
                "from_square": {
                    "type": "string",
                    "description": "Starting square for arrows (e.g., 'e2'). Optional for circles/highlights."
                },
                "to_square": {
                    "type": "string",
                    "description": "Ending square for arrows (e.g., 'e4'). Optional for circles/highlights."
                },
                "square": {
                    "type": "string",
                    "description": "Square to annotate for circles and highlights (e.g., 'd5')"
                }
            },
            "required": ["annotation_type", "color"]
        }
    },
    {
        "name": "create_question",
        "description": "Create an interactive question for the user to test understanding.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question_type": {
                    "type": "string",
                    "enum": ["multiple_choice", "move_selection"],
                    "description": "Type of question to create"
                },
                "question_text": {
                    "type": "string",
                    "description": "The question to ask the user"
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Answer options for multiple choice questions"
                },
                "correct_answer": {
                    "type": "string",
                    "description": "The correct answer"
                },
                "explanation": {
                    "type": "string",
                    "description": "Explanation of why the answer is correct"
                }
            },
            "required": ["question_type", "question_text", "correct_answer"]
        }
    }
]
