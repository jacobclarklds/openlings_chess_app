"""
Compute Service Client

Client for communicating with the Chess Compute Microservice.
Handles all MAIA and Stockfish operations.
"""

import httpx
from typing import Dict, List, Optional
import os


# Get compute service URL from environment or default to localhost
COMPUTE_SERVICE_URL = os.getenv("COMPUTE_SERVICE_URL", "http://localhost:8001")


class ComputeServiceClient:
    """Client for Chess Compute Service."""

    def __init__(self, base_url: str = COMPUTE_SERVICE_URL):
        """
        Initialize compute service client.

        Args:
            base_url: Base URL of compute service
        """
        self.base_url = base_url

    async def health_check(self) -> Dict:
        """
        Check if compute service is healthy.

        Returns:
            Health status dict
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()

    async def evaluate_position(self, fen: str, depth: int = 20) -> Dict:
        """
        Evaluate a chess position using Stockfish.

        Args:
            fen: Position FEN
            depth: Search depth (default: 20)

        Returns:
            Dict with 'centipawns', 'mate_in', 'fen', 'depth'
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/stockfish/evaluate",
                json={"fen": fen, "depth": depth}
            )
            response.raise_for_status()
            return response.json()

    async def detect_blunder(
        self,
        before_fen: str,
        after_fen: str,
        depth: int = 20
    ) -> Dict:
        """
        Detect if a move was a blunder.

        Args:
            before_fen: FEN before the move
            after_fen: FEN after the move
            depth: Search depth (default: 20)

        Returns:
            Dict with 'is_blunder', 'centipawn_loss', 'eval_before', 'eval_after'
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/stockfish/detect-blunder",
                json={
                    "before_fen": before_fen,
                    "after_fen": after_fen,
                    "depth": depth
                }
            )
            response.raise_for_status()
            return response.json()

    async def detect_opening_end(self, fen: str, move_number: int) -> Dict:
        """
        Detect if the opening phase has ended.

        Args:
            fen: Current position FEN
            move_number: Current move number

        Returns:
            Dict with 'opening_ended' (bool) and 'reason' (str)
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/stockfish/detect-opening-end",
                json={"fen": fen, "move_number": move_number}
            )
            response.raise_for_status()
            return response.json()

    async def get_maia_probabilities(self, fen: str, user_elo: int) -> Dict:
        """
        Get MAIA move probabilities for a position.

        Args:
            fen: Position FEN
            user_elo: User's ELO rating (determines which MAIA model to use)

        Returns:
            Dict with 'fen', 'model_used', and 'moves' (list of {move, probability})
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/maia/move-probabilities",
                json={"fen": fen, "user_elo": user_elo}
            )
            response.raise_for_status()
            return response.json()


# Global client instance
compute_client = ComputeServiceClient()
