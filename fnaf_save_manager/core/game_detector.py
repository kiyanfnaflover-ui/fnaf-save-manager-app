from dataclasses import dataclass
from typing import List, Optional

@dataclass
class GameProfile:
    id: str
    title: str
    save_filename: str
    icon_name: str

# Fixed save filenames based on engine outputs (e.g., fn4 instead of fnaf4)
GAMES = [
    GameProfile("fnaf1", "Five Nights at Freddy's", "freddy", "fnaf.png"),
    GameProfile("fnaf2", "Five Nights at Freddy's 2", "freddy2", "fnaf2.png"),
    GameProfile("fnaf3", "Five Nights at Freddy's 3", "freddy3", "fnaf3.png"),
    GameProfile("fnaf4", "Five Nights at Freddy's 4", "fn4", "fnaf4.png"),
    GameProfile("fnaf5", "Sister Location", "sl", "fnaf5.png"),
    GameProfile("fnaf6", "Pizzeria Simulator", "FNAF6", "fnaf6.png"),
    GameProfile("ucn", "Ultimate Custom Night", "CN", "ucn.png")
]

def get_all_profiles() -> List[GameProfile]:
    return GAMES

def get_profile_by_id(game_id: str) -> Optional[GameProfile]:
    for game in GAMES:
        if game.id == game_id:
            return game
    return None