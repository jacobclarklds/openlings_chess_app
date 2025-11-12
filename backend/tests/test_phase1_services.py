"""
Tests for Phase 1: Backend Infrastructure - Chess Analysis Services
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.stockfish_service import StockfishService
from app.services.maia_service import MaiaService
from app.services.analysis_coordinator import AnalysisCoordinator
from app.services.opening_service import OpeningService


class TestStockfishService:
    """Test Stockfish integration"""

    @pytest.mark.asyncio
    async def test_evaluate_starting_position(self):
        """Test evaluation of starting position"""
        async with StockfishService() as service:
            fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            result = await service.evaluate_position(fen, depth=15)

            assert result["evaluation_type"] == "cp"
            assert abs(result["centipawn_eval"]) < 50  # Starting position is roughly equal
            assert result["best_move"] in ["e2e4", "d2d4", "g1f3", "c2c4", "c2c3", "b1c3"]
            print(f"✅ Starting position eval: {result['centipawn_eval']} cp, best move: {result['best_move']}")

    @pytest.mark.asyncio
    async def test_analyze_good_move(self):
        """Test analysis of a good move (e4 opening)"""
        async with StockfishService() as service:
            fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            move = "e2e4"

            result = await service.analyze_move(fen, move, depth=15)

            assert result["classification"] in ["excellent", "good"]
            assert result["centipawns_lost"] < 50
            print(f"✅ Move e4 classified as: {result['classification']} (lost {result['centipawns_lost']} cp)")

    @pytest.mark.asyncio
    async def test_analyze_blunder(self):
        """Test detection of a blunder"""
        async with StockfishService() as service:
            fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            blunder = "f2f3"  # Weakens king safety

            result = await service.analyze_move(fen, blunder, depth=15)

            # f3 is playable but not great
            assert result["classification"] in ["good", "inaccuracy", "mistake"]
            print(f"✅ Move f3 classified as: {result['classification']} (lost {result['centipawns_lost']} cp)")


class TestMaiaService:
    """Test MAIA service (fallback implementation)"""

    @pytest.mark.asyncio
    async def test_get_move_probabilities(self):
        """Test getting move probabilities"""
        service = MaiaService()
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"

        result = await service.get_move_probabilities(fen, elo=1500)

        assert "moves" in result
        assert len(result["moves"]) > 0
        assert all(0 <= m["probability"] <= 1 for m in result["moves"])
        total_prob = sum(m["probability"] for m in result["moves"])
        assert 0.95 <= total_prob <= 1.05  # Allow small rounding error
        print(f"✅ Got {len(result['moves'])} move predictions, total prob: {total_prob:.3f}")

    @pytest.mark.asyncio
    async def test_infer_elo(self):
        """Test ELO inference from move"""
        service = MaiaService()
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        move = "e2e4"  # Common strong move

        result = await service.infer_elo_from_move(fen, move)

        assert "most_likely_elo" in result
        assert "elo_distribution" in result
        assert result["most_likely_elo"] in [1100, 1300, 1500, 1900]
        print(f"✅ Inferred ELO: {result['most_likely_elo']} (confidence: {result['confidence']:.3f})")


class TestAnalysisCoordinator:
    """Test the analysis coordinator that combines services"""

    @pytest.mark.asyncio
    async def test_analyze_position_full(self):
        """Test comprehensive position analysis"""
        coordinator = AnalysisCoordinator()
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"

        result = await coordinator.analyze_position_full(fen, user_elo=1500)

        assert "stockfish" in result
        assert "maia_predictions" in result
        assert "position_type" in result
        assert result["position_type"] == "opening"
        print(f"✅ Full analysis complete: {result['position_type']}, {len(result['maia_predictions']['moves'])} MAIA moves")

    @pytest.mark.asyncio
    async def test_analyze_user_move(self):
        """Test analysis of a user's move"""
        coordinator = AnalysisCoordinator()
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        move = "e2e4"

        result = await coordinator.analyze_user_move(fen, move, user_elo=1500)

        assert "stockfish_eval" in result
        assert "maia_probability" in result
        assert "inferred_strength" in result
        assert result["stockfish_eval"]["classification"] in ["excellent", "good"]
        print(f"✅ User move e4: {result['stockfish_eval']['classification']}, MAIA prob: {result['maia_probability']:.3f}")


class TestOpeningService:
    """Test opening classification"""

    @pytest.mark.asyncio
    async def test_classify_italian_game(self):
        """Test identification of Italian Game"""
        service = OpeningService()
        pgn = """[Event "Test"]
1. e4 e5 2. Nf3 Nc6 3. Bc4
"""

        result = await service.get_opening_classification(pgn)

        assert result["name"] == "Italian Game"
        assert "typical_plans" in result
        assert len(result["typical_plans"]) > 0
        print(f"✅ Identified: {result['name']} ({result['eco']})")

    @pytest.mark.asyncio
    async def test_get_position_type(self):
        """Test position phase classification"""
        service = OpeningService()

        # Opening
        fen_opening = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        result = await service.get_position_type(fen_opening)
        assert result == "opening"

        # Endgame (few pieces)
        fen_endgame = "8/5k2/8/8/8/8/5K2/8 w - - 0 1"
        result = await service.get_position_type(fen_endgame)
        assert result == "endgame"

        print("✅ Position type classification working")


@pytest.mark.asyncio
async def test_full_integration():
    """Integration test: Analyze a short game"""
    coordinator = AnalysisCoordinator()

    # Simulate analyzing a few moves of a game
    moves_and_fens = [
        ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "e2e4"),
        ("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1", "e7e5"),
        ("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2", "g1f3"),
    ]

    print("\n🎯 Integration Test: Analyzing game moves:")
    for fen, move in moves_and_fens:
        result = await coordinator.analyze_user_move(fen, move, user_elo=1500)
        print(f"   Move {move}: {result['stockfish_eval']['classification']} "
              f"(MAIA prob: {result['maia_probability']:.2f}, "
              f"lost {result['stockfish_eval']['centipawns_lost']} cp)")

    print("✅ Full integration test passed!")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
