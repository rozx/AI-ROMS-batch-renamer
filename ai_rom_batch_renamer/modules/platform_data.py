"""Platform alias data loader.

Separated from const.py to work around a Nuitka <= 2.8 + MSVC bug where
module-level code beyond simple literal assignments is silently dropped
(or raises swallowed exceptions) when compiling with --include-package.

Usage:
    from ai_rom_batch_renamer.modules.platform_data import get_platform_aliases
    aliases = get_platform_aliases()
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_JSON_NAME = "platform-aliases.json"

# Module-level cache -- populated on first call to get_platform_aliases().
_cache: dict[str, str] | None = None

# Cache for allowed region codes.
_region_cache: frozenset[str] | None = None


def _resolve_json_path() -> Path:
    """Locate the platform-aliases.json asset file.

    Searches multiple candidate paths so it works in:
      - Development / Poetry entry-points
      - Nuitka onefile binaries (extracted temp dir)
    """
    candidates = [
        # Development / Poetry: platform_data.py -> modules/ -> ai_rom_batch_renamer/ -> project root -> assets/
        Path(__file__).resolve().parent.parent.parent / "assets" / _JSON_NAME,
        # Nuitka onefile: sys.executable sits inside the extracted temp dir
        Path(sys.executable).resolve().parent / "assets" / _JSON_NAME,
        # Nuitka onefile: sys.argv[0] is the original .exe path
        Path(sys.argv[0]).resolve().parent / "assets" / _JSON_NAME,
        # CWD fallback
        Path(os.getcwd()) / "assets" / _JSON_NAME,
    ]

    for p in candidates:
        if p.is_file():
            return p

    searched = "\n  ".join(str(p) for p in candidates)
    raise FileNotFoundError(
        f"Cannot find {_JSON_NAME} in any of these locations:\n  {searched}"
    )


def get_allowed_region_codes() -> frozenset[str]:
    """Return the set of canonical region codes (US, JP, EU, WW, UE, 繁, 简, 简&繁).

    Defined as a function (not a module-level constant) to avoid a Nuitka + MSVC
    bug where module-level code beyond simple string literals is silently dropped.
    """
    global _region_cache
    if _region_cache is not None:
        return _region_cache
    _region_cache = frozenset(
        {
            "US",
            "JP",
            "EU",
            "WW",
            "UE",
            "\u7e41",  # 繁
            "\u7b80",  # 简
            "\u7b80&\u7e41",  # 简&繁
        }
    )
    return _region_cache


def get_platform_aliases() -> dict[str, str]:
    """Return a dict mapping every known alias (lower-cased) to its canonical platform name.

    The result is cached after the first call.
    """
    global _cache
    if _cache is not None:
        return _cache

    json_path = _resolve_json_path()
    with open(json_path, encoding="utf-8") as f:
        entries = json.load(f)

    result: dict[str, str] = {}
    for entry in entries:
        canonical = entry["canonical"]
        result[canonical.lower()] = canonical
        for alias in entry["aliases"]:
            result[alias] = canonical

    _cache = result
    return result
