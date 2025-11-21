#!/usr/bin/env python3
"""Test script for Chess Compute Service"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_health():
    print("Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"✓ Health: {response.json()}\n")

def test_evaluate():
    print("Testing /stockfish/evaluate...")
    response = requests.post(
        f"{BASE_URL}/stockfish/evaluate",
        json={
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "depth": 15
        }
    )
    result = response.json()
    print(f"✓ Starting position evaluation: {result['centipawns']} centipawns\n")

def test_blunder_detection():
    print("Testing /stockfish/detect-blunder...")
    # Test with h3 (poor move)
    response = requests.post(
        f"{BASE_URL}/stockfish/detect-blunder",
        json={
            "before_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "after_fen": "rnbqkbnr/pppppppp/8/8/8/7P/PPPPPPP1/RNBQKBNR b KQkq - 0 1",
            "depth": 15
        }
    )
    result = response.json()
    print(f"✓ h3 move analysis:")
    print(f"  Is blunder: {result['is_blunder']}")
    print(f"  Centipawn loss: {result['centipawn_loss']}\n")

def test_opening_detection():
    print("Testing /stockfish/detect-opening-end...")
    # Early position
    response = requests.post(
        f"{BASE_URL}/stockfish/detect-opening-end",
        json={
            "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 5",
            "move_number": 5
        }
    )
    result = response.json()
    print(f"✓ Move 5 position:")
    print(f"  Opening ended: {result['opening_ended']}")
    print(f"  Reason: {result['reason']}\n")

    # Later position
    response = requests.post(
        f"{BASE_URL}/stockfish/detect-opening-end",
        json={
            "fen": "r2q1rk1/ppp2ppp/2n1bn2/3p4/3P4/2NBP3/PPP2PPP/R1BQ1RK1 w - - 8 10",
            "move_number": 20
        }
    )
    result = response.json()
    print(f"✓ Move 20 position:")
    print(f"  Opening ended: {result['opening_ended']}")
    print(f"  Reason: {result['reason']}\n")

def test_maia():
    print("Testing /maia/move-probabilities (placeholder)...")
    response = requests.post(
        f"{BASE_URL}/maia/move-probabilities",
        json={
            "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
            "user_elo": 1484
        }
    )
    result = response.json()
    print(f"✓ MAIA model: {result['model_used']}")
    print(f"  Top 3 moves:")
    for i, move in enumerate(result['moves'][:3], 1):
        print(f"    {i}. {move['move']} ({move['probability']:.1%})")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("CHESS COMPUTE SERVICE TEST SUITE")
    print("=" * 60)
    print()

    try:
        test_health()
        test_evaluate()
        test_blunder_detection()
        test_opening_detection()
        test_maia()

        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
