VERSION = "3.1.1"

# Canonical region codes produced by getRegion and used across the app.
# Keep this list in sync with any region mapping logic.
ALLOWED_REGION_CODES = {"US", "JP", "EU", "繁", "简", "简&繁", "WW", "UE"}

# Maps platform aliases to canonical platform strings
# (matching the CSV file names under assets/rom-name-alias-cn).
# Each entry is (canonical_name, [alias, ...]).  The canonical name itself is
# also registered as an alias (lowercased) automatically.
# Lookup is always done with .strip().lower() on the user-supplied value.
_PLATFORM_ALIAS_DEFS: list[tuple[str, list[str]]] = [
    ("Nintendo - Game Boy", ["gb", "game boy", "gameboy", "nintendo game boy"]),
    (
        "Nintendo - Game Boy Color",
        ["gbc", "game boy color", "gameboy color", "nintendo game boy color"],
    ),
    (
        "Nintendo - Game Boy Advance",
        ["gba", "game boy advance", "gameboy advance", "nintendo game boy advance"],
    ),
    (
        "Nintendo - Nintendo Entertainment System",
        ["nes", "fc", "famicom", "family computer", "nintendo entertainment system"],
    ),
    (
        "Nintendo - Super Nintendo Entertainment System",
        [
            "snes",
            "sfc",
            "super nes",
            "super nintendo",
            "super famicom",
            "super nintendo entertainment system",
        ],
    ),
    ("Nintendo - Nintendo 64", ["n64", "nintendo 64", "nintendo64"]),
    ("Nintendo - GameCube", ["gc", "ngc", "gamecube", "nintendo gamecube"]),
    ("Nintendo - Wii", ["wii", "nintendo wii"]),
    ("Nintendo - Wii U", ["wiiu", "wii u", "nintendo wii u"]),
    ("Nintendo - Switch", ["switch", "ns", "nintendo switch"]),
    ("Nintendo - Switch 2", ["switch2", "ns2", "nintendo switch 2"]),
    ("Nintendo - Nintendo DS", ["ds", "nds", "nintendo ds"]),
    ("Nintendo - Nintendo 3DS", ["3ds", "nintendo 3ds"]),
    ("Nintendo - New Nintendo 3DS", ["n3ds", "new 3ds", "new nintendo 3ds"]),
    ("Nintendo - Virtual Boy", ["vb", "virtual boy", "nintendo virtual boy"]),
    ("Nintendo - Pokemon Mini", ["pokemini", "pokemon mini", "pokemon-mini"]),
    ("Nintendo - Sufami Turbo", ["sufami", "sufami turbo"]),
    (
        "Nintendo - Family Computer Disk System",
        ["fds", "famicom disk system", "family computer disk system"],
    ),
    (
        "Nintendo - Game & Watch",
        ["g&w", "game watch", "game & watch", "game and watch"],
    ),
    (
        "Sega - Mega Drive - Genesis",
        [
            "md",
            "genesis",
            "mega drive",
            "sega genesis",
            "sega mega drive",
            "mega drive genesis",
        ],
    ),
    (
        "Sega - Master System - Mark III",
        [
            "sms",
            "master system",
            "mark iii",
            "sega master system",
            "master system mark iii",
        ],
    ),
    ("Sega - Game Gear", ["gg", "game gear", "sega game gear"]),
    ("Sega - Saturn", ["ss", "saturn", "sega saturn"]),
    ("Sega - Dreamcast", ["dc", "dreamcast", "sega dreamcast"]),
    ("Sega - SG-1000", ["sg1000", "sg-1000", "sega sg-1000", "sega sg1000"]),
    ("Sega - 32X", ["32x", "sega 32x"]),
    ("Sega - Mega CD & Sega CD", ["mcd", "mega cd", "sega cd", "mega cd sega cd"]),
    (
        "Sony - PlayStation",
        ["ps", "ps1", "psx", "playstation", "playstation 1", "sony playstation"],
    ),
    (
        "Sony - PlayStation 2",
        ["ps2", "playstation 2", "playstation2", "sony playstation 2"],
    ),
    (
        "Sony - PlayStation 3",
        ["ps3", "playstation 3", "playstation3", "sony playstation 3"],
    ),
    (
        "Sony - PlayStation Vita",
        [
            "psv",
            "psvita",
            "ps vita",
            "playstation vita",
            "sony ps vita",
            "sony playstation vita",
        ],
    ),
    ("Sony - PlayStation Portable", ["psp", "playstation portable", "sony psp"]),
    (
        "NEC - PC Engine - TurboGrafx-16",
        [
            "pce",
            "tg16",
            "tg-16",
            "pc engine",
            "turbografx",
            "turbografx-16",
            "turbografx16",
        ],
    ),
    (
        "NEC - PC Engine CD & TurboGrafx CD",
        ["pce cd", "tg cd", "pc engine cd", "turbografx cd"],
    ),
    ("NEC - PC Engine SuperGrafx", ["sgx", "supergrafx", "pc engine supergrafx"]),
    ("NEC - PC-FX", ["pcfx", "pc-fx", "nec pc-fx"]),
    ("SNK - NeoGeo Pocket", ["ngp", "neo geo pocket", "neogeo pocket"]),
    (
        "SNK - NeoGeo Pocket Color",
        ["ngpc", "neo geo pocket color", "neogeo pocket color"],
    ),
    ("Bandai - WonderSwan", ["ws", "wonderswan", "bandai wonderswan"]),
    ("Bandai - WonderSwan Color", ["wsc", "wonderswan color"]),
    ("Microsoft - MSX", ["msx"]),
    ("Microsoft - MSX2", ["msx2"]),
    ("Microsoft - Xbox", ["xbox", "xbox 1", "microsoft xbox", "og xbox"]),
    ("Microsoft - Xbox 360", ["x360", "xbox 360", "xbox360", "microsoft xbox 360"]),
    ("Commodore - Commodore 64", ["c64", "commodore 64", "commodore64", "cbm 64"]),
    ("Commodore - Amiga", ["amiga", "commodore amiga"]),
    ("Coleco - ColecoVision", ["coleco", "colecovision"]),
    ("Mattel - Intellivision", ["intv", "intellivision", "mattel intellivision"]),
    ("GCE - Vectrex", ["vectrex", "gce vectrex"]),
    ("Sharp - X68000", ["x68000", "x68k", "sharp x68000"]),
    ("Arcade - MAME", ["mame", "arcade mame"]),
    ("Arcade - CPS1", ["cps1", "capcom play system 1", "capcom cps1"]),
    ("Arcade - CPS2", ["cps2", "capcom play system 2", "capcom cps2"]),
    ("Arcade - CPS3", ["cps3", "capcom play system 3", "capcom cps3"]),
    ("Arcade - NEOGEO", ["neogeo", "neo geo", "neo-geo", "arcade neogeo"]),
    (
        "Panasonic - 3DO Interactive Multiplayer",
        ["3do", "panasonic 3do", "3do interactive multiplayer"],
    ),
    ("Atari - Atari 2600", ["2600", "atari 2600"]),
    ("Atari - Atari 5200", ["5200", "atari 5200"]),
    ("Atari - Atari 7800", ["7800", "atari 7800"]),
    ("Atari - Atari Lynx", ["lynx", "atari lynx"]),
    ("Atari - Atari Jaguar", ["jaguar", "atari jaguar"]),
    ("Atari - Atari Jaguar CD", ["jaguar cd", "atari jaguar cd"]),
    ("Atari - Atari ST", ["st", "atari st", "atarist"]),
]

# Build the flat lookup dict; canonical name itself is also a valid key.
PLATFORM_ALIASES: dict[str, str] = {
    alias: canonical
    for canonical, aliases in _PLATFORM_ALIAS_DEFS
    for alias in [canonical.lower(), *aliases]
}
