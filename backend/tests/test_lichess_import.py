"""
Tests for Lichess game import functionality
"""
import pytest
from app.services.lichess import LichessService


class TestLichessImport:
    """Test suite for Lichess API integration"""

    @pytest.fixture
    def lichess_service(self):
        """Create a Lichess service instance without token (public access)"""
        return LichessService()

    def test_lichess_service_initialization(self, lichess_service):
        """Test that Lichess service initializes correctly"""
        assert lichess_service is not None
        assert lichess_service.BASE_URL == "https://lichess.org/api"

    def test_get_user_games_jclark982(self, lichess_service):
        """Test importing games for user jclark982"""
        username = "jclark982"
        max_games = 10  # Limit to 10 games for testing

        try:
            games = lichess_service.get_user_games(username, max_games)

            # Basic assertions
            assert games is not None, "Games should not be None"
            assert isinstance(games, list), "Games should be a list"

            if len(games) > 0:
                print(f"\n✓ Successfully retrieved {len(games)} games for {username}")

                # Verify first game structure
                first_game = games[0]
                assert "platform" in first_game, "Game should have platform"
                assert first_game["platform"] == "lichess", "Platform should be lichess"
                assert "game_id" in first_game, "Game should have game_id"
                assert "white_player" in first_game, "Game should have white_player"
                assert "black_player" in first_game, "Game should have black_player"
                assert "result" in first_game, "Game should have result"
                assert "pgn" in first_game, "Game should have PGN"
                assert "played_at" in first_game, "Game should have played_at"

                # Print sample game info
                print(f"  Sample game: {first_game['white_player']} vs {first_game['black_player']}")
                print(f"  Result: {first_game['result']}")
                print(f"  Opening: {first_game.get('opening_name', 'Unknown')}")
                print(f"  Date: {first_game['played_at']}")

                # Verify all games have required fields
                for i, game in enumerate(games):
                    assert game["platform"] == "lichess", f"Game {i} should be from lichess"
                    assert game["game_id"], f"Game {i} should have valid game_id"
                    assert game["pgn"], f"Game {i} should have PGN data"
                    assert game["result"] in ["1-0", "0-1", "1/2-1/2"], \
                        f"Game {i} should have valid result"

                print(f"  All {len(games)} games have valid structure ✓")
            else:
                print(f"\n⚠ No games found for {username}")
                print("  This might be expected if the account has no public games")

        except Exception as e:
            pytest.fail(f"Failed to import games from Lichess: {str(e)}")

    def test_lichess_game_parsing(self, lichess_service):
        """Test that game parsing handles various scenarios"""
        username = "jclark982"

        try:
            games = lichess_service.get_user_games(username, max_games=5)

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

                    # Test opening data (can be None)
                    if game.get("opening_eco"):
                        assert isinstance(game["opening_eco"], str), "ECO should be string"
                        assert len(game["opening_eco"]) >= 3, "ECO should have at least 3 chars"

                    # Test PGN is not empty
                    assert len(game["pgn"]) > 0, "PGN should not be empty"

                print("  All games parsed correctly ✓")

        except Exception as e:
            pytest.fail(f"Game parsing test failed: {str(e)}")

    def test_lichess_rate_limiting(self, lichess_service):
        """Test that service handles multiple requests properly"""
        username = "jclark982"

        try:
            # Make two consecutive requests
            games1 = lichess_service.get_user_games(username, max_games=5)
            games2 = lichess_service.get_user_games(username, max_games=5)

            assert games1 is not None, "First request should succeed"
            assert games2 is not None, "Second request should succeed"

            print(f"\n✓ Successfully handled multiple requests")
            print(f"  Request 1: {len(games1)} games")
            print(f"  Request 2: {len(games2)} games")

        except Exception as e:
            pytest.fail(f"Rate limiting test failed: {str(e)}")


def test_lichess_user_exists():
    """Quick test to verify the user exists on Lichess"""
    import requests

    username = "jclark982"
    url = f"https://lichess.org/@/{username}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"\n✓ User {username} exists on Lichess")
        else:
            print(f"\n⚠ User {username} returned status code: {response.status_code}")
    except Exception as e:
        pytest.fail(f"Failed to verify user exists: {str(e)}")


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v", "-s"])
