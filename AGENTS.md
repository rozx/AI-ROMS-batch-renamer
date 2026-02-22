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

# Launch GUI
poetry run gui

# Hot reload (GUI dev mode)
poetry run dev

# Build binary (Nuitka)
poetry run build --verbose

# Version bump (syncs pyproject.toml + const.py)
poetry run bump          # interactive
poetry run bump-patch    # patch increment
poetry run bump-minor    # minor increment
poetry run bump-major    # major increment
APP_VERSION="3.1.0" poetry run bump  # set exact version from CI tag
```

## CLI Commands

The main entry point (`poetry run main`) exposes these subcommands:

| Command | Description |
|---|---|
| `rename` | Batch rename ROM files (directory or explicit file list) |
| `revert` | Revert previously renamed files using history cache |
| `gui` | Launch the PySide6 GUI |
| `clear-cache` | Clear AI info cache and/or rename history cache |
| `about` | Show version and program info |

### Key `rename` Options
- `--platform / -p` — ROM platform (required for `--cn-lookup`, improves AI results)
- `--ai / -ai` — Enable AI enrichment (default model: deepseek-chat)
- `--cn-lookup / --cn` — Use local Chinese alias CSV database (requires `--platform`)
- `--ai-batch-size` — Number of filenames per AI request (default: 10)
- `--ai-no-cache / -nc` — Bypass AI result cache and always query the API
- `--tavily-api-key / -tav` — Tavily remote MCP key for web-search enhanced AI (no Node.js needed)
- `--force / -f` — Rename files even if they appear already renamed
- `--dry-run / -d` — Preview renames without writing to disk
- `--trim / -t` — Strip noisy tokens from filenames
- `--pinyin / -py` — Prepend pinyin initials for better sort support
- `--recursive / -r` — Recurse into subdirectories
- `--unzip / -u` — Extract ZIP archives before renaming

## Critical Non-Obvious Patterns

### Version Synchronization
Version is defined in TWO places and must stay in sync:
- [`pyproject.toml`](pyproject.toml:8) `version = "..."`
- [`ai_rom_batch_renamer/modules/const.py`](ai_rom_batch_renamer/modules/const.py:1) `VERSION = "..."`

Use `scripts/version.py` via the Poetry scripts (`bump`, `bump-patch`, `bump-minor`, `bump-major`) — do NOT edit manually.

### Region Codes
Canonical region codes are defined in [`const.py`](ai_rom_batch_renamer/modules/const.py:5):
```python
ALLOWED_REGION_CODES = {"US", "JP", "EU", "繁", "简", "简&繁", "WW", "UE"}
```
Any region validation must use these exact values.

### Platform Aliases
[`assets/platform-aliases.json`](assets/platform-aliases.json) defines the canonical-name ↔ alias mappings. [`platform_data.py`](ai_rom_batch_renamer/modules/platform_data.py) loads this JSON and exposes `get_platform_aliases()` — a dict mapping every known alias (lower-cased) to its canonical platform name matching the CSV filenames under `assets/rom-name-alias-cn/`. To add new aliases edit the JSON file, not lookup logic.

### AI Cache Key Format
Cache keys use format `"{platform.lower()}::{romFile.originalFilename}"` — see [`ai.py`](ai_rom_batch_renamer/modules/ai.py#L16). Changing this format breaks existing caches.

### Renamed File Detection
[`utils.isFileRenamed()`](ai_rom_batch_renamer/modules/utils.py) uses specific regex patterns to detect already-renamed files. Files matching the renamed pattern are skipped unless `--force` is used.

### Import Style
Uses absolute package imports (e.g., `from ai_rom_batch_renamer.modules import utils`) to support both Poetry entry points and Nuitka-compiled binaries. Do not use relative imports.

## Exit Codes
- 0: Success
- 1: Generic failure (I/O, permission, GUI runtime error)
- 2: Invalid arguments / missing directory
- 3: AI API error / quota exceeded
- 4: ZIP extraction failure

## Cache Files
Two sqlite3-cache files are stored in the system temp directory (`$TEMP/ai-rom-batch-renamer/`):

| File | Purpose |
|---|---|
| `renamerHistory.cache` | Rename history — required by `revert` command |
| `renamerRomInfoCache.cache` | AI query results — speeds up repeat runs |

Use `poetry run main clear-cache` to inspect and clear cache data. Both files are managed by [`cache.py`](ai_rom_batch_renamer/modules/cache.py).
