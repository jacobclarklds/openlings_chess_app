"""
Tests for games endpoints
"""
import pytest
from fastapi import status
from unittest.mock import patch, MagicMock


class TestGetGames:
    """Test getting user games"""

    def test_get_user_games(self, client, test_user, test_game, auth_headers):
        """Test getting games for authenticated user"""
        response = client.get("/api/games", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["game_id"] == test_game.game_id
        assert data[0]["platform"] == "lichess"

    def test_get_games_unauthenticated(self, client):
        """Test that unauthenticated users cannot get games"""
        response = client.get("/api/games")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_games_empty_list(self, client, auth_headers):
        """Test getting games when user has no games"""
        response = client.get("/api/games", headers=auth_headers)
        # User has no games in this fixture
        assert response.status_code == status.HTTP_200_OK

    def test_get_games_pagination(self, client, test_user, auth_headers, db_session):
        """Test pagination of games"""
        from app.models.game import Game

        # Create multiple games
        for i in range(15):
            game = Game(
                user_id=test_user.id,
                platform="lichess",
                game_id=f"lichess_game_{i}",
                white_player="player1",
                black_player="player2",
                result="1-0",
                pgn=f"[Event \"Game {i}\"]\n\n1. e4",
            )
            db_session.add(game)
        db_session.commit()

        # Test pagination
        response = client.get("/api/games?skip=0&limit=10", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 10

        response = client.get("/api/games?skip=10&limit=10", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 5

    def test_get_games_only_user_games(self, client, test_user, test_game, auth_headers, db_session):
        """Test that users only see their own games"""
        from app.models.user import User
        from app.models.game import Game
        from app.core.security import get_password_hash

        # Create another user with games
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(other_user)
        db_session.commit()

        other_game = Game(
            user_id=other_user.id,
            platform="lichess",
            game_id="lichess_other",
            white_player="other",
            black_player="opponent",
            result="0-1",
            pgn="[Event \"Other Game\"]\n\n1. d4",
        )
        db_session.add(other_game)
        db_session.commit()

        # Test user should only see their own games
        response = client.get("/api/games", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        games = response.json()
        assert len(games) == 1
        assert games[0]["game_id"] == test_game.game_id


class TestGetGameById:
    """Test getting a specific game"""

    def test_get_game_by_id(self, client, test_game, auth_headers):
        """Test getting a specific game by ID"""
        response = client.get(f"/api/games/{test_game.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["game_id"] == test_game.game_id
        assert data["platform"] == "lichess"
        assert data["white_player"] == "testuser"

    def test_get_game_not_found(self, client, auth_headers):
        """Test getting nonexistent game returns 404"""
        response = client.get("/api/games/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_other_user_game(self, client, test_game, auth_headers, db_session):
        """Test that users cannot access other users' games"""
        from app.models.user import User
        from app.models.game import Game
        from app.core.security import get_password_hash, create_access_token

        # Create another user
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password=get_password_hash("password123"),
        )
        db_session.add(other_user)
        db_session.commit()

        # Create game for other user
        other_game = Game(
            user_id=other_user.id,
            platform="lichess",
            game_id="lichess_other",
            white_player="other",
            black_player="opponent",
            result="0-1",
            pgn="[Event \"Other Game\"]\n\n1. d4",
        )
        db_session.add(other_game)
        db_session.commit()

        # Try to access other user's game with test user's auth
        response = client.get(f"/api/games/{other_game.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestConnectPlatform:
    """Test connecting chess platforms"""

    def test_connect_lichess_without_token(self, client, auth_headers):
        """Test connecting Lichess account without token"""
        response = client.post(
            "/api/games/connect-platform",
            json={
                "platform": "lichess",
                "username": "testuser123",
                "token": None,
            },
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "successfully connected" in data["message"].lower()

    def test_connect_chesscom(self, client, auth_headers):
        """Test connecting Chess.com account"""
        with patch('app.services.chesscom.ChessComService.verify_user_exists') as mock_verify:
            mock_verify.return_value = True

            response = client.post(
                "/api/games/connect-platform",
                json={
                    "platform": "chesscom",
                    "username": "testuser123",
                },
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

    def test_connect_chesscom_invalid_user(self, client, auth_headers):
        """Test connecting nonexistent Chess.com user fails"""
        with patch('app.services.chesscom.ChessComService.verify_user_exists') as mock_verify:
            mock_verify.return_value = False

            response = client.post(
                "/api/games/connect-platform",
                json={
                    "platform": "chesscom",
                    "username": "nonexistent",
                },
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "not found" in response.json()["detail"].lower()

    def test_connect_invalid_platform(self, client, auth_headers):
        """Test connecting invalid platform fails"""
        response = client.post(
            "/api/games/connect-platform",
            json={
                "platform": "invalid",
                "username": "testuser",
            },
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid platform" in response.json()["detail"].lower()

    def test_connect_platform_unauthenticated(self, client):
        """Test that unauthenticated users cannot connect platforms"""
        response = client.post(
            "/api/games/connect-platform",
            json={
                "platform": "lichess",
                "username": "testuser",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestImportGames:
    """Test importing games from platforms"""

    def test_import_lichess_games(self, client, test_user_with_lichess, db_session):
        """Test importing games from Lichess"""
        from app.core.security import create_access_token

        token = create_access_token(data={"sub": test_user_with_lichess.email})
        headers = {"Authorization": f"Bearer {token}"}

        with patch('app.services.lichess.LichessService.get_user_games') as mock_get:
            mock_get.return_value = [
                {
                    "platform": "lichess",
                    "game_id": "lichess_test1",
                    "white_player": "player1",
                    "black_player": "player2",
                    "result": "1-0",
                    "pgn": "[Event \"Test\"]\n\n1. e4",
                }
            ]

            response = client.post(
                "/api/games/import",
                json={
                    "platform": "lichess",
                    "max_games": 10,
                },
                headers=headers,
            )

            assert response.status_code == status.HTTP_202_ACCEPTED
            data = response.json()
            assert "importing" in data["message"].lower()

    def test_import_chesscom_games(self, client, test_user_with_chesscom, db_session):
        """Test importing games from Chess.com"""
        from app.core.security import create_access_token

        token = create_access_token(data={"sub": test_user_with_chesscom.email})
        headers = {"Authorization": f"Bearer {token}"}

        with patch('app.services.chesscom.ChessComService.get_user_games') as mock_get:
            mock_get.return_value = [
                {
                    "platform": "chesscom",
                    "game_id": "chesscom_test1",
                    "white_player": "player1",
                    "black_player": "player2",
                    "result": "1-0",
                    "pgn": "[Event \"Test\"]\n\n1. e4",
                }
            ]

            response = client.post(
                "/api/games/import",
                json={
                    "platform": "chesscom",
                    "max_games": 10,
                },
                headers=headers,
            )

            assert response.status_code == status.HTTP_202_ACCEPTED

    def test_import_without_connected_account(self, client, auth_headers):
        """Test importing without connected account fails"""
        response = client.post(
            "/api/games/import",
            json={
                "platform": "lichess",
                "max_games": 10,
            },
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not connected" in response.json()["detail"].lower()

    def test_import_invalid_platform(self, client, auth_headers):
        """Test importing from invalid platform fails"""
        response = client.post(
            "/api/games/import",
            json={
                "platform": "invalid",
                "max_games": 10,
            },
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_import_unauthenticated(self, client):
        """Test that unauthenticated users cannot import games"""
        response = client.post(
            "/api/games/import",
            json={
                "platform": "lichess",
                "max_games": 10,
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
