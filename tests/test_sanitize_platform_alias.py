import pytest
from ai_rom_batch_renamer.modules import utils as utilsModule


# fmt: off
@pytest.mark.parametrize("alias, expected", [
    # Short codes
    ("gb",           "Nintendo - Game Boy"),
    ("gbc",          "Nintendo - Game Boy Color"),
    ("gba",          "Nintendo - Game Boy Advance"),
    ("nes",          "Nintendo - Nintendo Entertainment System"),
    ("snes",         "Nintendo - Super Nintendo Entertainment System"),
    ("n64",          "Nintendo - Nintendo 64"),
    ("gamecube",     "Nintendo - GameCube"),
    ("gc",           "Nintendo - GameCube"),
    ("wii",          "Nintendo - Wii"),
    ("wiiu",         "Nintendo - Wii U"),
    ("nds",          "Nintendo - Nintendo DS"),
    ("ds",           "Nintendo - Nintendo DS"),
    ("3ds",          "Nintendo - Nintendo 3DS"),
    ("new 3ds",      "Nintendo - New Nintendo 3DS"),
    ("n3ds",         "Nintendo - New Nintendo 3DS"),
    ("vb",           "Nintendo - Virtual Boy"),
    ("fds",          "Nintendo - Family Computer Disk System"),
    # Full / common names (mixed case)
    ("Game Boy",     "Nintendo - Game Boy"),
    ("game boy color", "Nintendo - Game Boy Color"),
    ("Super Nintendo", "Nintendo - Super Nintendo Entertainment System"),
    ("Super Famicom",  "Nintendo - Super Nintendo Entertainment System"),
    ("famicom",        "Nintendo - Nintendo Entertainment System"),
    # Sega
    ("genesis",       "Sega - Mega Drive - Genesis"),
    ("mega drive",    "Sega - Mega Drive - Genesis"),
    ("md",            "Sega - Mega Drive - Genesis"),
    ("sms",           "Sega - Master System - Mark III"),
    ("master system", "Sega - Master System - Mark III"),
    ("gg",            "Sega - Game Gear"),
    ("game gear",     "Sega - Game Gear"),
    ("saturn",        "Sega - Saturn"),
    ("dc",            "Sega - Dreamcast"),
    ("dreamcast",     "Sega - Dreamcast"),
    ("32x",           "Sega - 32X"),
    ("sega cd",       "Sega - Mega CD & Sega CD"),
    ("mega cd",       "Sega - Mega CD & Sega CD"),
    # Sony
    ("ps1",      "Sony - PlayStation"),
    ("psx",      "Sony - PlayStation"),
    ("playstation", "Sony - PlayStation"),
    ("psp",      "Sony - PlayStation Portable"),
    # NEC
    ("pce",          "NEC - PC Engine - TurboGrafx-16"),
    ("pc engine",    "NEC - PC Engine - TurboGrafx-16"),
    ("turbografx",   "NEC - PC Engine - TurboGrafx-16"),
    ("tg16",         "NEC - PC Engine - TurboGrafx-16"),
    ("pce cd",       "NEC - PC Engine CD & TurboGrafx CD"),
    ("supergrafx",   "NEC - PC Engine SuperGrafx"),
    # SNK
    ("ngp",                 "SNK - NeoGeo Pocket"),
    ("neo geo pocket",      "SNK - NeoGeo Pocket"),
    ("ngpc",                "SNK - NeoGeo Pocket Color"),
    ("neogeo pocket color", "SNK - NeoGeo Pocket Color"),
    # Bandai
    ("ws",              "Bandai - WonderSwan"),
    ("wonderswan",      "Bandai - WonderSwan"),
    ("wsc",             "Bandai - WonderSwan Color"),
    ("wonderswan color","Bandai - WonderSwan Color"),
    # Microsoft
    ("msx",  "Microsoft - MSX"),
    ("msx2", "Microsoft - MSX2"),
    # Arcade
    ("cps1",   "Arcade - CPS1"),
    ("cps2",   "Arcade - CPS2"),
    ("cps3",   "Arcade - CPS3"),
    ("neogeo", "Arcade - NEOGEO"),
    ("neo geo","Arcade - NEOGEO"),
    # Panasonic / Atari
    ("3do",       "Panasonic - 3DO Interactive Multiplayer"),
    ("atari 2600","Atari - Atari 2600"),
    ("2600",      "Atari - Atari 2600"),
    ("atari 5200","Atari - Atari 5200"),
    ("atari 7800","Atari - Atari 7800"),
    # Case-insensitive variants
    ("GB",          "Nintendo - Game Boy"),
    ("GBA",         "Nintendo - Game Boy Advance"),
    ("GENESIS",     "Sega - Mega Drive - Genesis"),
    ("PSP",         "Sony - PlayStation Portable"),
    ("  psp  ",     "Sony - PlayStation Portable"),
    # Sentinels that bypass validation
    ("unknown",  "unknown"),
    ("",         ""),
])
# fmt: on
def test_sanitize_platform(alias: str, expected: str):
    assert utilsModule.sanitizePlatform(alias) == expected


# ---------------------------------------------------------------------------
# Error cases: unrecognised platform must raise ValueError
# ---------------------------------------------------------------------------


def test_sanitize_platform_unknown_raises():
    with pytest.raises(ValueError, match="Unknown platform"):
        utilsModule.sanitizePlatform("My Custom Platform")


def test_sanitize_platform_close_match_in_error(monkeypatch):
    """Error message should contain a close-match suggestion."""
    with pytest.raises(ValueError) as exc_info:
        utilsModule.sanitizePlatform("game boi")
    msg = str(exc_info.value)
    # "game boi" is close to Game Boy aliases – at least one suggestion expected
    assert "Nintendo - Game Boy" in msg


def test_sanitize_platform_no_close_match_lists_all():
    """When no close match exists the error lists supported platforms."""
    with pytest.raises(ValueError) as exc_info:
        utilsModule.sanitizePlatform("zzzzzzzzz")
    msg = str(exc_info.value)
    assert "Nintendo - Game Boy" in msg  # canonical names always appear
