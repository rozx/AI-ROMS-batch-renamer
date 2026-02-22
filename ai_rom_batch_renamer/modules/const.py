VERSION = "3.1.1"

# Canonical region codes produced by getRegion and used across the app.
# Keep this list in sync with any region mapping logic.
ALLOWED_REGION_CODES = {"US", "JP", "EU", "繁", "简", "简&繁", "WW", "UE"}


def _build_platform_aliases() -> dict:
    """Load platform aliases from the bundled JSON asset.

    Using a JSON file instead of a large Python list literal avoids a
    Nuitka ≤ 2.8 / MSVC bug where module-level code after a large constant
    list is silently dropped during compilation.
    """
    import json
    from pathlib import Path

    # Resolve relative to this file so it works both in source and in a
    # Nuitka onefile binary (where __file__ points into the extracted tmpdir).
    json_path = Path(__file__).parent.parent.parent / "assets" / "platform-aliases.json"
    with open(json_path, encoding="utf-8") as f:
        entries = json.load(f)

    result = {}
    for entry in entries:
        canonical = entry["canonical"]
        result[canonical.lower()] = canonical
        for alias in entry["aliases"]:
            result[alias] = canonical
    return result


PLATFORM_ALIASES = _build_platform_aliases()
