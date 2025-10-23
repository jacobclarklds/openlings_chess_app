import requests
from typing import List, Dict, Optional
from datetime import datetime
import time

class ChessComService:
    BASE_URL = "https://api.chess.com/pub"

    def __init__(self):
        self.headers = {
            "User-Agent": "Chess Training App"
        }

    def get_user_games(
        self, username: str, max_games: int = 100
    ) -> List[Dict]:
        """
        Fetch recent games for a user from Chess.com.
        """
        # First get the user's archives
        archives_url = f"{self.BASE_URL}/player/{username}/games/archives"
        response = requests.get(archives_url, headers=self.headers)
        response.raise_for_status()

        archives = response.json().get("archives", [])

        # Get games from most recent archives
        games = []
        for archive_url in reversed(archives):
            if len(games) >= max_games:
                break

            try:
                archive_response = requests.get(archive_url, headers=self.headers)
                archive_response.raise_for_status()
                archive_games = archive_response.json().get("games", [])

                for game_data in archive_games:
                    if len(games) >= max_games:
                        break

                    parsed_game = self._parse_chesscom_game(game_data)
                    if parsed_game:
                        games.append(parsed_game)

                # Rate limiting
                time.sleep(0.1)
            except Exception as e:
                print(f"Error fetching archive {archive_url}: {e}")
                continue

        return games

    def _parse_chesscom_game(self, game_data: Dict) -> Optional[Dict]:
        """
        Parse a Chess.com game JSON into our standard format.
        """
        try:
            # Extract basic info
            game_url = game_data.get("url", "")
            game_id = game_url.split("/")[-1] if game_url else str(game_data.get("end_time"))

            white = game_data.get("white", {})
            black = game_data.get("black", {})

            # Determine result based on who won
            white_result = white.get("result")
            if white_result == "win":
                result = "1-0"
            elif white_result in ["checkmated", "resigned", "timeout", "abandoned"]:
                result = "0-1"
            else:
                result = "1/2-1/2"

            # Parse timestamp
            end_time = game_data.get("end_time")
            played_at = datetime.fromtimestamp(end_time) if end_time else datetime.utcnow()

            # Get PGN
            pgn = game_data.get("pgn", "")

            # Extract opening from PGN headers
            opening_name = None
            opening_eco = None
            if pgn:
                for line in pgn.split("\n"):
                    if "[ECOUrl" in line or "[ECO " in line:
                        # Extract ECO code
                        parts = line.split('"')
                        if len(parts) > 1:
                            eco_part = parts[1]
                            if "/" in eco_part:
                                opening_eco = eco_part.split("/")[-1]
                            else:
                                opening_eco = eco_part

            return {
                "platform": "chesscom",
                "game_id": f"chesscom_{game_id}",
                "played_at": played_at,
                "white_player": white.get("username", "Unknown"),
                "black_player": black.get("username", "Unknown"),
                "white_rating": white.get("rating"),
                "black_rating": black.get("rating"),
                "result": result,
                "termination": game_data.get("time_class"),
                "pgn": pgn,
                "opening_name": opening_name,
                "opening_eco": opening_eco,
                "time_control": game_data.get("time_control"),
            }
        except Exception as e:
            print(f"Error parsing Chess.com game: {e}")
            return None

    def verify_user_exists(self, username: str) -> bool:
        """
        Verify if a user exists on Chess.com.
        """
        try:
            url = f"{self.BASE_URL}/player/{username}"
            response = requests.get(url, headers=self.headers)
            return response.status_code == 200
        except:
            return False
