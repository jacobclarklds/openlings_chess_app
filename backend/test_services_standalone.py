"""
Standalone tests for Phase 1 services - NO DATABASE REQUIRED
Run with: python test_services_standalone.py
"""
import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.stockfish_service import StockfishService
from app.services.maia_service import MaiaService
from app.services.analysis_coordinator import AnalysisCoordinator
from app.services.opening_service import OpeningService


async def test_stockfish():
    """Test Stockfish service"""
    print("\n🧪 Testing Stockfish Service...")

    async with StockfishService() as service:
        # Test 1: Evaluate starting position
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        result = await service.evaluate_position(fen, depth=15)

        print(f"   ✅ Starting position: {result['centipawn_eval']} cp, best move: {result['best_move']}")
        assert result["evaluation_type"] == "cp"
        assert abs(result["centipawn_eval"]) < 50

        # Test 2: Analyze good move
        move = "e2e4"
        result = await service.analyze_move(fen, move, depth=15)
        print(f"   ✅ Move e4: {result['classification']} (lost {result['centipawns_lost']} cp)")
        assert result["classification"] in ["excellent", "good"]

    print("   ✅ Stockfish tests passed!")


async def test_maia():
    """Test MAIA service"""
    print("\n🧪 Testing MAIA Service (Fallback)...")

    service = MaiaService()

    # Test 1: Get move probabilities
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    result = await service.get_move_probabilities(fen, elo=1500)

    print(f"   ✅ Got {len(result['moves'])} move predictions")
    assert len(result["moves"]) > 0

    # Test 2: Infer ELO
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    move = "e2e4"
    result = await service.infer_elo_from_move(fen, move)

    print(f"   ✅ Inferred ELO: {result['most_likely_elo']} (confidence: {result['confidence']:.3f})")
    assert result["most_likely_elo"] in [1100, 1300, 1500, 1900]

    print("   ✅ MAIA tests passed!")


async def test_coordinator():
    """Test Analysis Coordinator"""
    print("\n🧪 Testing Analysis Coordinator...")

    coordinator = AnalysisCoordinator()

    # Test 1: Full position analysis
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    result = await coordinator.analyze_position_full(fen, user_elo=1500)

    print(f"   ✅ Full analysis: {result['position_type']}, {len(result['maia_predictions']['moves'])} MAIA moves")
    assert "stockfish" in result
    assert "maia_predictions" in result

    # Test 2: Analyze user move
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    move = "e2e4"
    result = await coordinator.analyze_user_move(fen, move, user_elo=1500)

    print(f"   ✅ User move e4: {result['stockfish_eval']['classification']}, "
          f"MAIA prob: {result['maia_probability']:.3f}")

    print("   ✅ Coordinator tests passed!")


async def test_opening_service():
    """Test Opening Service"""
    print("\n🧪 Testing Opening Service...")

    service = OpeningService()

    # Test 1: Classify Italian Game
    pgn = """[Event "Test"]
1. e4 e5 2. Nf3 Nc6 3. Bc4
"""
    result = await service.get_opening_classification(pgn)
    print(f"   ✅ Identified: {result['name']} ({result['eco']})")
    assert result["name"] == "Italian Game"

    # Test 2: Position type
    fen_opening = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    result = await service.get_position_type(fen_opening)
    print(f"   ✅ Position type: {result}")
    assert result == "opening"

    print("   ✅ Opening service tests passed!")


async def test_integration():
    """Full integration test"""
    print("\n🎯 Integration Test: Analyzing a short game...")

    coordinator = AnalysisCoordinator()

    moves_and_fens = [
        ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "e2e4"),
        ("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1", "e7e5"),
        ("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2", "g1f3"),
    ]

    for i, (fen, move) in enumerate(moves_and_fens, 1):
        result = await coordinator.analyze_user_move(fen, move, user_elo=1500)
        print(f"   Move {i} ({move}): {result['stockfish_eval']['classification']} "
              f"(MAIA: {result['maia_probability']:.2f}, "
              f"lost {result['stockfish_eval']['centipawns_lost']} cp)")

    print("   ✅ Integration test passed!")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 PHASE 1: Backend Infrastructure - Chess Analysis Services")
    print("=" * 60)

    try:
        await test_stockfish()
        await test_maia()
        await test_coordinator()
        await test_opening_service()
        await test_integration()

        print("\n" + "=" * 60)
        print("✅ ALL PHASE 1 TESTS PASSED!")
        print("=" * 60)
        print("\n📋 Services Implemented:")
        print("   ✓ Stockfish Service - Position evaluation and move analysis")
        print("   ✓ MAIA Service - Human-like move predictions (fallback)")
        print("   ✓ Analysis Coordinator - Combined analysis")
        print("   ✓ Opening Service - Opening classification")
        print("\n🎉 Phase 1 Complete - Ready for Phase 2!")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
