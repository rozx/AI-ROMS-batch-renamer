VERSION = "3.1.1"

# Canonical region codes produced by getRegion and used across the app.
# Keep this list in sync with any region mapping logic.
ALLOWED_REGION_CODES = {"US", "JP", "EU", "繁", "简", "简&繁", "WW", "UE"}


def _build_platform_aliases() -> dict:
    """Load platform aliases from the bundled JSON asset.

    Using a JSON file instead of a large Python list literal avoids a
    Nuitka ≤ 2.8 / MSVC bug where module-level code after a large constant
    list is silently dropped during compilation.

    Searches multiple candidate paths (mirroring cn_lookup._resolve_assets_dir)
    so it works in development, Poetry entry-points, AND Nuitka onefile binaries.
    """
    import json
    import os
    import sys
    from pathlib import Path

    _JSON_NAME = "platform-aliases.json"

    candidates = [
        # Development / Poetry: const.py -> modules/ -> ai_rom_batch_renamer/ -> project root -> assets/
        Path(__file__).resolve().parent.parent.parent / "assets" / _JSON_NAME,
        # Nuitka onefile: sys.executable is inside the extracted temp dir
        Path(sys.executable).resolve().parent / "assets" / _JSON_NAME,
        # Nuitka onefile: sys.argv[0] is the original .exe path (usually same dir)
        Path(sys.argv[0]).resolve().parent / "assets" / _JSON_NAME,
        # CWD fallback
        Path(os.getcwd()) / "assets" / _JSON_NAME,
    ]

    for json_path in candidates:
        if json_path.is_file():
            with open(json_path, encoding="utf-8") as f:
                entries = json.load(f)
            result: dict[str, str] = {}
            for entry in entries:
                canonical = entry["canonical"]
                result[canonical.lower()] = canonical
                for alias in entry["aliases"]:
                    result[alias] = canonical
            return result

    # Should never happen — crash with a descriptive message so the error
    # dialog (gui_entry.py) shows exactly what went wrong.
    searched = "\n  ".join(str(p) for p in candidates)
    raise FileNotFoundError(
        f"Cannot find {_JSON_NAME} in any of these locations:\n  {searched}"
    )


PLATFORM_ALIASES = _build_platform_aliases()
