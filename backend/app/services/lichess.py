import requests
from typing import List, Dict, Optional
import chess.pgn
from io import StringIO
from datetime import datetime

class LichessService:
    BASE_URL = "https://lichess.org/api"

    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.headers = {}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def get_user_games(
        self, username: str, max_games: int = 100
    ) -> List[Dict]:
        """
        Fetch games for a user from Lichess.
        """
        url = f"{self.BASE_URL}/games/user/{username}"
        params = {
            "max": max_games,
            "opening": "true",
        }

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        # Parse PGN format
        games = []
        pgn_text = response.text

        # Use chess.pgn to parse games
        pgn_io = StringIO(pgn_text)

        while len(games) < max_games:
            game = chess.pgn.read_game(pgn_io)
            if game is None:
                break

            parsed_game = self._parse_pgn_game(game)
            if parsed_game:
                games.append(parsed_game)

        return games

    def _parse_pgn_game(self, game: chess.pgn.Game) -> Optional[Dict]:
        """
        Parse a python-chess game object into our standard format.
        """
        try:
            headers = game.headers

            # Extract game info
            game_id = headers.get("Site", "").split("/")[-1] or headers.get("GameId", "unknown")
            white_player = headers.get("White", "Unknown")
            black_player = headers.get("Black", "Unknown")
            result = headers.get("Result", "*")

            # Parse date
            date_str = headers.get("UTCDate", headers.get("Date", ""))
            time_str = headers.get("UTCTime", "00:00:00")
            try:
                played_at = datetime.strptime(f"{date_str} {time_str}", "%Y.%m.%d %H:%M:%S")
            except:
                played_at = datetime.utcnow()

            # Extract ratings
            try:
                white_rating = int(headers.get("WhiteElo", 0)) or None
            except:
                white_rating = None

            try:
                black_rating = int(headers.get("BlackElo", 0)) or None
            except:
                black_rating = None

            # Get opening info
            opening_eco = headers.get("ECO")
            opening_name = headers.get("Opening")

            # Get full PGN
            exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
            pgn_str = game.accept(exporter)

            return {
                "platform": "lichess",
                "game_id": game_id,
                "played_at": played_at,
                "white_player": white_player,
                "black_player": black_player,
                "white_rating": white_rating,
                "black_rating": black_rating,
                "result": result,
                "termination": headers.get("Termination"),
                "pgn": pgn_str,
                "opening_name": opening_name,
                "opening_eco": opening_eco,
                "time_control": headers.get("TimeControl"),
            }
        except Exception as e:
            print(f"Error parsing Lichess game: {e}")
            return None

    def verify_token(self) -> bool:
        """
        Verify if the API token is valid.
        """
        if not self.token:
            return False

        try:
            url = f"{self.BASE_URL}/account"
            response = requests.get(url, headers=self.headers)
            return response.status_code == 200
        except:
            return False
