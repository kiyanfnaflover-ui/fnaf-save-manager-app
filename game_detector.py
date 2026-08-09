from dataclasses import dataclass, field
from typing import List, Optional

# ---------------------------------------------------------------- field configs

@dataclass
class FieldConfig:
    """Config-driven editor field.

    kind:
      int        -> QSpinBox over an ini key
      bool       -> QCheckBox over an ini key
      gvas_int   -> QSpinBox over a Help Wanted GVAS int property
      gvas_bool  -> QCheckBox over a Help Wanted GVAS bool property
      gvas_set   -> QSpinBox "how many collected" over a Help Wanted int set
      cert_bool  -> QCheckBox over the FNAF6 CERT file
    """
    kind: str
    label: str
    key: str = ""            # ini key, or gvas property name when gvas_*
    lo: int = 0
    hi: int = 100
    step: int = 1
    note: str = ""

# ---------------------------------------------------------------- profiles

@dataclass
class GameProfile:
    id: str
    title: str
    engine: str              # 'ini' | 'gvas'
    root: str                # 'APPDATA_MMF' | 'LOCALAPPDATA'
    save_name: str           # ini: filename inside MMFApplications; gvas: relative path from root
    icon_name: str
    banner_name: str = ""
    fields: List[FieldConfig] = field(default_factory=list)


# FNAF 1 - 6 common star/night unlock keys
F13_FIELDS = [
    FieldConfig("int", "Current night", "level", 1, 7),
    FieldConfig("bool", "Star 1 (beat the game / night 5)", "beatgame"),
    FieldConfig("bool", "Star 2 (beat night 6)", "beat6"),
]
F13_FIELDS += [
    FieldConfig("bool", "Star 3 (beat 4/20 mode)", "beat7"),
]
F2_FIELDS = F13_FIELDS[:-1] + [
    FieldConfig("bool", "Star 3 (custom night 10/20)", "beat7"),
    FieldConfig("bool", "Unlock all custom night desk plushies (c1-c10)", "c1"),
]
F3_FIELDS = F13_FIELDS + [
    FieldConfig("bool", "Good ending (souls rested)", "goodending"),
]
F4_FIELDS = [
    FieldConfig("int", "Current night", "night", 1, 8),
    FieldConfig("bool", "Star 1 (beat the game)", "beatgame"),
    FieldConfig("bool", "Star 2 (beat night 6)", "beat6"),
    FieldConfig("bool", "Star 3 (beat nightmare / night 7)", "beat7"),
    FieldConfig("bool", "Star 4 (beat 20/20/20/20 / night 8)", "beat8"),
]
SL_FIELDS = [
    FieldConfig("int", "Current night", "current", 1, 5),
    FieldConfig("bool", "Star 1 (real ending / night 5)", "beat1"),
    FieldConfig("bool", "Star 2 (keycard / Baby's death minigame)", "keycard"),
    FieldConfig("bool", "Star 3 (fake ending / Ennard private room)", "beat3"),
    FieldConfig("bool", "Star 4 (beat 10/20 Golden Freddy)", "beat4"),
]
F6_FIELDS = [
    FieldConfig("int", "Current day", "day", 1, 5),
    FieldConfig("int", "Money ($)", "money", 0, 9999999),
    FieldConfig("int", "Play tokens", "play", 0, 999),
]
F6_CERT_FIELDS = [
    FieldConfig("cert_bool", "Cert 1 + Star (completion / good ending)", "6th"),
    FieldConfig("cert_bool", "Cert 2 + Star (mediocrity)", "med"),
    FieldConfig("cert_bool", "Cert 3 (insanity)", "ins"),
    FieldConfig("cert_bool", "Cert 4 + Star (blacklisted)", "bla"),
    FieldConfig("cert_bool", "Cert 5 + Star (bankruptcy)", "ban"),
    FieldConfig("cert_bool", "Cert 6 (lorekeeper / alternate)", "com"),
]
UCN_FIELDS = [
    FieldConfig("int", "Best high score", "hs", 0, 10600, step=50),
    FieldConfig("int", "Faz-Coins", "coins", 0, 99),
    FieldConfig("int", "Frigid (AC)", "fridge", 0, 99),
    FieldConfig("int", "Plush coins", "battery", 0, 99),
    FieldConfig("int", "DD repel", "dd", 0, 99),
]
HW_FIELDS = [
    FieldConfig("gvas_int", "Games won", "NumberOfGamesWon", 0, 9999),
    FieldConfig("gvas_int", "Games lost", "NumberOfGamesLost", 0, 9999),
    FieldConfig("gvas_int", "Dark Ride high score", "DarkRideHighScore", 0, 99999),
    FieldConfig("gvas_set", "Coins collected (1-50)", "CollectedCoins", 0, 50),
    FieldConfig("gvas_set", "Glitch tapes collected (1-16)", "CollectedGlitches", 0, 16),
    FieldConfig("gvas_set", "HUB VOs listened to (1-16)", "HUBUpdateVOListenedTo", 0, 16),
    FieldConfig("gvas_set", "HUB VOs collected (1-16)", "HUBUpdateVOCollected", 0, 16),
    FieldConfig("gvas_bool", "Played menu instructions", "HasPlayedMenuInstructions"),
    FieldConfig("gvas_bool", "EULA agreed", "EULAAgreed"),
    FieldConfig("gvas_bool", "Seen Help Wanted title", "Has_Seen_H_Title"),
]

GAMES = [
    GameProfile("fnaf1", "Five Nights at Freddy's", "ini", "APPDATA_MMF", "freddy",
                "fnaf.png", "fnaf 1 banner.jpg", F13_FIELDS),
    GameProfile("fnaf2", "Five Nights at Freddy's 2", "ini", "APPDATA_MMF", "freddy2",
                "fnaf2.png", "fnaf 2 banner.jpg", F2_FIELDS),
    GameProfile("fnaf3", "Five Nights at Freddy's 3", "ini", "APPDATA_MMF", "freddy3",
                "fnaf3.png", "fnaf 3 banner.jpg", F3_FIELDS),
    GameProfile("fnaf4", "Five Nights at Freddy's 4", "ini", "APPDATA_MMF", "fn4",
                "fnaf4.png", "fnaf 4 banner.jpg", F4_FIELDS),
    GameProfile("fnaf5", "Sister Location", "ini", "APPDATA_MMF", "sl",
                "fnaf5.png", "fnaf 5 banner.jpg", SL_FIELDS),
    GameProfile("fnaf6", "Pizzeria Simulator", "ini", "APPDATA_MMF", "FNAF6",
                "fnaf6.png", "fnaf 6 banner.jpg", F6_FIELDS + F6_CERT_FIELDS),
    GameProfile("ucn", "Ultimate Custom Night", "ini", "APPDATA_MMF", "CN",
                "ucn.png", "fnaf ucn.jpg", UCN_FIELDS),
    GameProfile("hw", "Help Wanted", "gvas", "LOCALAPPDATA",
                "freddys/Saved/SaveGames/Player00.sav",
                "fnaf hw.png", "fnaf hw banner.jpg", HW_FIELDS),
    GameProfile("world", "FNAF World", "ini", "APPDATA_MMF", "fnafw1",
                "fnaf world.png", "fnaf world banner.jpg", [
                    FieldConfig("bool", "Save slot started", "started"),
                    FieldConfig("int", "Mode", "mode", 0, 2),
                    FieldConfig("int", "Difficulty", "diff", 0, 5),
                ]),
    GameProfile("fury", "Fury's Rage", "ini", "APPDATA_MMF", "furysrage",
                "fnaf furys rage.png", "Security_Breach-Fury_Rage_ banner.jpg", []),
    GameProfile("fnac", "Five Nights at Candy's", "ini", "APPDATA_MMF", "fivecandys",
                "fnac.png", "fnac banner.jpg", [
                    FieldConfig("int", "Current night", "level", 1, 8),
                    FieldConfig("bool", "Star 1 (beat the game)", "beatgame"),
                    FieldConfig("bool", "Star 2 (beat night 6)", "beat6"),
                    FieldConfig("bool", "Star 3 (beat night 7)", "beat7"),
                    FieldConfig("bool", "Star 4 (beat night 8)", "beat8"),
                    FieldConfig("bool", "All extras unlocked", "allunlock"),
                    FieldConfig("int", "Stars", "stars", 0, 3),
                ]),
    GameProfile("fnac2", "Five Nights at Candy's 2", "ini", "APPDATA_MMF", "fnac2",
                "fnac 2.png", "fnac 2 banner.jpg", []),
    GameProfile("fnac3", "Five Nights at Candy's 3", "ini", "APPDATA_MMF", "fnac3",
                "fnac 3.png", "fnac 3 banner.jpg", []),
    GameProfile("fnacr", "Five Nights at Candy's Remastered", "ini", "APPDATA_MMF", "fnacr",
                "Five Nights at Candy's Remastered.png",
                "Five Nights at Candy's Remastered banner.jpg", []),
    GameProfile("flumpty", "Five Nights at Flumpty's", "ini", "APPDATA_MMF", "flumpty",
                "Five Nights at Flumpty's 1.png",
                "Five Nights at Flumpty's 1 banner.jpg", []),
    GameProfile("jrs", "JR's", "ini", "APPDATA_JRSSAVE", "savedata.ini",
                "jr's.png", "jr's banner.jpg", [
                    FieldConfig("int", "Current night (6+ unlocks the star)", "night", 1, 8),
                    FieldConfig("bool", "Star: Bonnie's Carrot Craze ending", "plat"),
                    FieldConfig("bool", "Star: The Closing Act", "maxstar"),
                    FieldConfig("bool", "Star: SR's", "sr"),
                    FieldConfig("bool", "Present 1 (Free-Mode)", "p1"),
                    FieldConfig("bool", "Present 2 (Free-Mode)", "p2"),
                    FieldConfig("bool", "Present 3 (Free-Mode)", "p3"),
                    FieldConfig("bool", "Present 4 (Free-Mode)", "p4"),
                    FieldConfig("bool", "Mini-star: Relics of the Past", "RP"),
                    FieldConfig("bool", "Mini-star: Unwanted Presence", "UP"),
                    FieldConfig("bool", "Mini-star: A Killing Game", "KG"),
                    FieldConfig("bool", "Mini-star: Haunting Havoc", "HH"),
                    FieldConfig("bool", "Mini-star: Spectral Suspicion", "SS"),
                    FieldConfig("bool", "Mini-star: Paranormal Peril", "PP"),
                ]),
    GameProfile("trtf2", "The Return to Freddy's 2", "ini", "APPDATA_MMF", "trtf2",
                "The Return to Freddy's 2.png",
                "The Return to Freddy's 2 banner.jpg", []),
]


def get_all_profiles() -> List[GameProfile]:
    return GAMES


def get_profile_by_id(game_id: str) -> Optional[GameProfile]:
    for game in GAMES:
        if game.id == game_id:
            return game
    return None
