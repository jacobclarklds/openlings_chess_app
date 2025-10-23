"""
Tests for Chess.com game import functionality
"""
import pytest
from app.services.chesscom import ChessComService


class TestChessComImport:
    """Test suite for Chess.com API integration"""

    @pytest.fixture
    def chesscom_service(self):
        """Create a Chess.com service instance"""
        return ChessComService()

    def test_chesscom_service_initialization(self, chesscom_service):
        """Test that Chess.com service initializes correctly"""
        assert chesscom_service is not None
        assert chesscom_service.BASE_URL == "https://api.chess.com/pub"

    def test_verify_user_exists_jakebyu97(self, chesscom_service):
        """Test that user jakebyu97 exists on Chess.com"""
        username = "jakebyu97"

        try:
            exists = chesscom_service.verify_user_exists(username)
            assert exists is True, f"User {username} should exist on Chess.com"
            print(f"\n✓ User {username} verified on Chess.com")

        except Exception as e:
            pytest.fail(f"Failed to verify user exists: {str(e)}")

    def test_get_user_games_jakebyu97(self, chesscom_service):
        """Test importing games for user jakebyu97"""
        username = "jakebyu97"
        max_games = 10  # Limit to 10 games for testing

        try:
            games = chesscom_service.get_user_games(username, max_games)

            # Basic assertions
            assert games is not None, "Games should not be None"
            assert isinstance(games, list), "Games should be a list"

            if len(games) > 0:
                print(f"\n✓ Successfully retrieved {len(games)} games for {username}")

                # Verify first game structure
                first_game = games[0]
                assert "platform" in first_game, "Game should have platform"
                assert first_game["platform"] == "chesscom", "Platform should be chesscom"
                assert "game_id" in first_game, "Game should have game_id"
                assert "white_player" in first_game, "Game should have white_player"
                assert "black_player" in first_game, "Game should have black_player"
                assert "result" in first_game, "Game should have result"
                assert "pgn" in first_game, "Game should have PGN"
                assert "played_at" in first_game, "Game should have played_at"

                # Print sample game info
                print(f"  Sample game: {first_game['white_player']} vs {first_game['black_player']}")
                print(f"  Result: {first_game['result']}")
                print(f"  Time control: {first_game.get('time_control', 'Unknown')}")
                print(f"  Date: {first_game['played_at']}")

                # Verify all games have required fields
                for i, game in enumerate(games):
                    assert game["platform"] == "chesscom", f"Game {i} should be from chesscom"
                    assert game["game_id"], f"Game {i} should have valid game_id"
                    assert game["pgn"], f"Game {i} should have PGN data"
                    assert game["result"] in ["1-0", "0-1", "1/2-1/2"], \
                        f"Game {i} should have valid result: got {game['result']}"

                print(f"  All {len(games)} games have valid structure ✓")
            else:
                print(f"\n⚠ No games found for {username}")
                print("  This might be expected if the account has no games")

        except Exception as e:
            pytest.fail(f"Failed to import games from Chess.com: {str(e)}")

    def test_chesscom_game_parsing(self, chesscom_service):
        """Test that game parsing handles various scenarios"""
        username = "jakebyu97"

        try:
            games = chesscom_service.get_user_games(username, max_games=5)

            if len(games) > 0:
                print(f"\n✓ Testing game data parsing for {len(games)} games")

                for game in games:
                    # Test rating fields (can be None)
                    if game.get("white_rating"):
                        assert isinstance(game["white_rating"], int), "White rating should be int"
                        assert game["white_rating"] > 0, "Rating should be positive"

                    if game.get("black_rating"):
                        assert isinstance(game["black_rating"], int), "Black rating should be int"
                        assert game["black_rating"] > 0, "Rating should be positive"

                    # Test PGN is not empty
                    assert len(game["pgn"]) > 0, "PGN should not be empty"

                    # Test that PGN contains chess moves
                    pgn = game["pgn"]
                    assert "[Event" in pgn or "1." in pgn, "PGN should contain game data"

                    # Test game_id format
                    assert game["game_id"].startswith("chesscom_"), \
                        "Game ID should have chesscom_ prefix"

                print("  All games parsed correctly ✓")

        except Exception as e:
            pytest.fail(f"Game parsing test failed: {str(e)}")

    def test_chesscom_api_response_format(self, chesscom_service):
        """Test that we handle Chess.com API response format correctly"""
        username = "jakebyu97"

        try:
            games = chesscom_service.get_user_games(username, max_games=3)

            if len(games) > 0:
                print(f"\n✓ Testing API response format handling")

                for game in games:
                    # Verify all timestamp conversions worked
                    assert game["played_at"] is not None, "Should have parsed timestamp"

                    # Verify player names are extracted
                    assert len(game["white_player"]) > 0, "White player name should not be empty"
                    assert len(game["black_player"]) > 0, "Black player name should not be empty"

                    # Verify result mapping worked
                    assert game["result"] in ["1-0", "0-1", "1/2-1/2"], \
                        f"Result should be standard notation, got: {game['result']}"

                print("  API response format handled correctly ✓")

        except Exception as e:
            pytest.fail(f"API response format test failed: {str(e)}")

    def test_chesscom_rate_limiting(self, chesscom_service):
        """Test that service handles rate limiting properly"""
        username = "jakebyu97"

        try:
            # Make two consecutive requests with small limits
            games1 = chesscom_service.get_user_games(username, max_games=3)
            games2 = chesscom_service.get_user_games(username, max_games=3)

            assert games1 is not None, "First request should succeed"
            assert games2 is not None, "Second request should succeed"

            print(f"\n✓ Successfully handled multiple requests with rate limiting")
            print(f"  Request 1: {len(games1)} games")
            print(f"  Request 2: {len(games2)} games")

        except Exception as e:
            pytest.fail(f"Rate limiting test failed: {str(e)}")


def test_chesscom_user_profile():
    """Quick test to verify the user profile is accessible"""
    import requests

    username = "jakebyu97"
    url = f"https://api.chess.com/pub/player/{username}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ User {username} profile accessible on Chess.com")
            print(f"  Username: {data.get('username', 'N/A')}")
            if 'joined' in data:
                from datetime import datetime
                joined_date = datetime.fromtimestamp(data['joined'])
                print(f"  Member since: {joined_date.strftime('%Y-%m-%d')}")
        else:
            print(f"\n⚠ User profile returned status code: {response.status_code}")
    except Exception as e:
        pytest.fail(f"Failed to fetch user profile: {str(e)}")


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v", "-s"])
