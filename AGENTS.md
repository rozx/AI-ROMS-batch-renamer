# AGENTS.md

This file provides guidance to agents when working with code in this repository.
Always use Chinese when communicating with users, but code comments and commit messages should be in English.

## Build/Test Commands

```bash
# Run all tests
poetry run pytest

# Run a single test file
poetry run pytest tests/test_is_file_renamed.py

# Run a single test function
poetry run pytest tests/test_is_file_renamed.py::test_is_file_renamed

# Build binary (Nuitka)
poetry run build --verbose

# Version bump (syncs pyproject.toml + const.py)
poetry run bump          # interactive
poetry run bump-patch    # direct
APP_VERSION="3.1.0" poetry run bump  # set exact version from CI tag
```

## Critical Non-Obvious Patterns

### Version Synchronization
Version is defined in TWO places and must stay in sync:
- [`pyproject.toml`](pyproject.toml:8) `version = "..."`
- [`ai_rom_batch_renamer/modules/const.py`](ai_rom_batch_renamer/modules/const.py:1) `VERSION = "..."`

Use bump2version or `scripts/version.py` - do NOT edit manually.

### Region Codes
Canonical region codes are defined in [`const.py`](ai_rom_batch_renamer/modules/const.py:5):
```python
ALLOWED_REGION_CODES = {"US", "JP", "EU", "繁", "简", "简&繁", "WW", "UE"}
```
Any region validation must use these exact values.

### AI Cache Key Format
Cache keys use format `"{platform.lower()}::{filename}"` - see [`ai.py`](ai_rom_batch_renamer/modules/ai.py:12). Changing this breaks existing caches.

### Renamed File Detection
[`utils.isFileRenamed()`](ai_rom_batch_renamer/modules/utils.py) uses specific regex patterns to detect already-renamed files. Files matching the renamed pattern are skipped unless `--force` is used.

### Import Style
Uses absolute package imports (e.g., `from ai_rom_batch_renamer.modules import utils`) to support both Poetry entry points and Nuitka-compiled binaries. Do not use relative imports.

## Exit Codes
- 0: Success
- 1: Generic failure (I/O, permission)
- 2: Invalid arguments / missing directory
- 3: AI API error / quota exceeded
- 4: ZIP extraction failure

## History Cache
Rename history stored in `renamerHistory.cache` (sqlite3-cache). Required for `revert` command - do not delete.
