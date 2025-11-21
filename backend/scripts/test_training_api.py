#!/usr/bin/env python3
"""
Test Training API

Tests the complete training API workflow:
1. Start a training session
2. Create a training game
3. Play moves
4. Complete the game
5. View session stats
"""

import asyncio
import requests
import json
from typing import Optional

# API Base URL
BASE_URL = "http://localhost:8000"

# Test user credentials
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "testpass123"

class TrainingAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token: Optional[str] = None
        self.headers = {}

    def login(self, email: str, password: str) -> bool:
        """Login and get authentication token."""
        print(f"\n{'='*60}")
        print("AUTHENTICATION")
        print(f"{'='*60}")

        print(f"Attempting to login as {email}...")

        # Try to login via OAuth2 password flow
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                data={
                    "username": email,  # OAuth2 uses 'username' field
                    "password": password
                }
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                print(f"✓ Login successful!")
                print(f"  Token: {self.token[:20]}...")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                print("   Please check TEST_PASSWORD or create user with:")
                print("   curl -X POST http://localhost:8000/api/auth/register \\")
                print("        -H 'Content-Type: application/json' \\")
                print(f"        -d '{{\"email\":\"{email}\",\"username\":\"testuser\",\"password\":\"{password}\"}}'")
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def start_session(self) -> Optional[int]:
        """Start a new training session."""
        print(f"\n{'='*60}")
        print("STEP 1: START TRAINING SESSION")
        print(f"{'='*60}")

        response = requests.post(
            f"{self.base_url}/api/training/sessions/start",
            json={"opening_filter": None},
            headers=self.headers
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Session started successfully")
            print(f"  Session ID: {data['session_id']}")
            print(f"  Started at: {data['started_at']}")
            return data['session_id']
        else:
            print(f"❌ Failed to start session: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

    def create_game(self, session_id: int) -> Optional[dict]:
        """Create a new training game."""
        print(f"\n{'='*60}")
        print("STEP 2: CREATE TRAINING GAME")
        print(f"{'='*60}")

        response = requests.post(
            f"{self.base_url}/api/training/games/new",
            json={
                "session_id": session_id,
                "user_plays_white": True  # User plays white
            },
            headers=self.headers
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Game created successfully")
            print(f"  Game ID: {data['game_id']}")
            print(f"  User plays: {'White' if data['user_plays_white'] else 'Black'}")
            print(f"  Starting FEN: {data['fen'][:50]}...")
            print(f"  Is user's turn: {data['is_user_turn']}")
            print(f"  Legal moves ({len(data['legal_moves'])}): {data['legal_moves'][:5]}...")
            return data
        else:
            print(f"❌ Failed to create game: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

    def make_move(self, game_id: int, move: str) -> Optional[dict]:
        """Make a move in the game."""
        response = requests.post(
            f"{self.base_url}/api/training/games/{game_id}/move",
            json={"move": move},
            headers=self.headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to make move: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

    def get_game_state(self, game_id: int) -> Optional[dict]:
        """Get current game state."""
        response = requests.get(
            f"{self.base_url}/api/training/games/{game_id}/state",
            headers=self.headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get game state: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

    def play_game(self, game_id: int, initial_state: dict):
        """Play through a complete training game."""
        print(f"\n{'='*60}")
        print("STEP 3: PLAY TRAINING GAME")
        print(f"{'='*60}")

        # Predefined moves for testing (Italian Game opening)
        user_moves = ['e2e4', 'g1f3', 'f1c4', 'd2d3', 'b1c3']
        move_number = 1

        for user_move in user_moves:
            print(f"\nMove {move_number}:")
            print(f"  User plays: {user_move}")

            result = self.make_move(game_id, user_move)

            if not result:
                print("  ❌ Move failed, ending game")
                break

            print(f"  ✓ Move accepted")

            if result.get('opponent_move'):
                print(f"  Opponent plays: {result['opponent_move']}")

            print(f"  FEN: {result['fen'][:50]}...")
            print(f"  Game over: {result['game_over']}")
            print(f"  Opening ended: {result['opening_ended']}")

            if result['game_over']:
                print(f"\n🏁 GAME OVER!")
                print(f"  Result: {result['result'].upper()}")
                break

            if result['opening_ended']:
                print(f"  📍 Opening phase ended - game will end soon")

            move_number += 1

        # If game didn't end naturally, show final state
        if not result.get('game_over'):
            print(f"\n⚠️  Reached end of predefined moves")
            state = self.get_game_state(game_id)
            if state:
                print(f"  Final position: {state['fen'][:50]}...")
                print(f"  Moves played: {state['move_count']}")

    def get_session_stats(self, session_id: int):
        """Get session statistics."""
        print(f"\n{'='*60}")
        print("STEP 4: SESSION STATISTICS")
        print(f"{'='*60}")

        response = requests.get(
            f"{self.base_url}/api/training/sessions/{session_id}/stats",
            headers=self.headers
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Session stats retrieved")
            print(f"  Games played: {data['games_played']}")
            print(f"  Record: {data['wins']}W - {data['losses']}L - {data['draws']}D")
            print(f"  Total moves: {data['total_moves']}")
            print(f"  Unique positions: {data['positions_practiced']}")
        else:
            print(f"❌ Failed to get stats: {response.status_code}")
            print(f"   Response: {response.text}")

    def end_session(self, session_id: int):
        """End the training session."""
        print(f"\n{'='*60}")
        print("STEP 5: END SESSION")
        print(f"{'='*60}")

        response = requests.post(
            f"{self.base_url}/api/training/sessions/{session_id}/end",
            headers=self.headers
        )

        if response.status_code == 200:
            print(f"✓ Session ended successfully")
        else:
            print(f"❌ Failed to end session: {response.status_code}")

    def run_complete_test(self):
        """Run the complete test workflow."""
        print("\n" + "="*60)
        print("TRAINING API TEST SUITE")
        print("="*60)

        # Step 0: Login
        if not self.login(TEST_EMAIL, TEST_PASSWORD):
            print("\n❌ Authentication failed. Cannot continue tests.")
            return

        # Step 1: Start session
        session_id = self.start_session()
        if not session_id:
            print("\n❌ Failed to start session. Stopping tests.")
            return

        # Step 2: Create game
        game_data = self.create_game(session_id)
        if not game_data:
            print("\n❌ Failed to create game. Stopping tests.")
            return

        # Step 3: Play game
        self.play_game(game_data['game_id'], game_data)

        # Step 4: Get stats
        self.get_session_stats(session_id)

        # Step 5: End session
        self.end_session(session_id)

        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETE!")
        print("="*60)
        print("\nNOTE: If you see authentication errors, you need to:")
        print("1. Create a test user in the database")
        print("2. Update TEST_PASSWORD in this script")
        print("3. Implement proper token-based authentication")


def main():
    """Main entry point."""
    tester = TrainingAPITester()
    tester.run_complete_test()


if __name__ == "__main__":
    main()
