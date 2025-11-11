# ROM AI Batch Renamer Agent Guide

This document is a condensed, agent-oriented version of `README.md`, focused on automations, scripted usage, and integration points.

## 1. Purpose

Automate intelligent batch renaming of retro game ROM files using AI enrichment (title prettification, platform hints) plus optional pinyin initial prefixing for improved sorting.

## 2. Core Capabilities

- AI-powered title extraction / beautification
- Pinyin initial insertion (optional)
- Batch rename across directories (with recursion)
- ZIP extraction + rename (with password support)
- Include / exclude filtering by file extension
- Safe revert (original filename history tracked)
- Dry-run preview mode

## 3. Primary CLI Interface

```bash
renamer [command] [options]
```

Commands:

- `rename`  Batch rename
- `revert`  Restore original filenames
- `about`   Show tool info

## 4. Rename Command Options (Summary)

| Option | Alias | Type | Notes |
|--------|-------|------|-------|
| --directory | -dir | TEXT | Target directory root |
| --files | -files | TEXT | One or more explicit files (may repeat) |
| --trim | -t | FLAG | Clean noisy filename segments |
| --dry-run | -d | FLAG | No mutation; output planned changes |
| --pinyin | -py | FLAG | Add leading pinyin initial (Chinese title) |
| --includes | -i | TEXT | Process only these extensions (repeatable) |
| --excludes | -e | TEXT | Skip these extensions (repeatable) |
| --output | -o | FLAG | Print only new names (quiet mode) |
| --recursive | -r | FLAG | Descend into subdirectories |
| --unzip | -u | FLAG | Extract ZIPs then operate on contents |
| --password | -pwd | TEXT | ZIP password (if encrypted) |
| --ai | -ai | FLAG | Enable AI beautification / translation |
| --model | -m | TEXT | AI model identifier (e.g. gpt-4o-mini) |
| --api-key | -key | TEXT | API key (overrides config) |
| --endpoint | -ep | TEXT | Custom API base URL |
| --platform | -p | TEXT | Platform hint (e.g. GBA, NDS) |

Minimal example (recursive + AI + pinyin, preview only):

```bash
renamer rename -r -d -ai -py -dir "~/ROMs" -m "gpt-4o-mini" -p "GBA"
```

## 5. Revert Command Options (Summary)

| Option | Alias | Type | Notes |
|--------|-------|------|-------|
| --directory | -dir | TEXT | Root to search for renamed files |
| --files | -files | TEXT | Explicit files to revert |
| --recursive | -r | FLAG | Traverse subfolders |
| --dry-run | -d | FLAG | Show intended reverts only |

Example (dry-run revert):

```bash
renamer revert -d -dir "~/ROMs"
```

## 6. AI Integration Notes

Configuration precedence (highest first): CLI flag > environment variable > `config.json`.

Suggested environment variables:

- `RENAMER_API_KEY`
- `RENAMER_MODEL`
- `RENAMER_ENDPOINT`

Performance tips:

- Batch files to reduce API round trips.
- Use `--includes` to narrow extensions and avoid waste.
- Future: local cache layer (see Roadmap) will reduce duplicate AI calls.

## 7. Automation Patterns

1. Nightly standardization job:
   - Run with `--dry-run` first; if diff minimal, re-run without.
2. ZIP ingestion pipeline:
   - Place new archives in `incoming/`; script runs: unzip + rename + move to catalog.
3. Platform-specific refinement:
   - Maintain mapping file for platform codes; pass via `--platform`.

Pseudo workflow script sketch:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$1"
renamer rename -r -ai -py -t -dir "$ROOT" -m "gpt-4o-mini" -p "GBA" --includes gba --includes zip --unzip
```

### 7.1 CI/CD Build and Versioning (Option B)

- Source of truth for version is the Release Drafter tag (e.g. `v2.1.0`).
- Build jobs read the tag from an artifact, derive `APP_VERSION` (strip `v`), and force Poetry to that version before building.
- Assets are uploaded to the same drafted release using the provided upload URL.

Key environment flow per job:

1) Download `releaseUploadUrl.txt` and `releaseTagName.txt` artifacts.
2) Set `APP_VERSION` from `TAG_NAME` by removing the leading `v`.
3) Run `poetry version "$APP_VERSION"` to sync app metadata with the release tag.
4) Build using the dynamic builder:

```bash
poetry run build --verbose
```

Notes:

- `scripts/build.py` computes platform-specific Nuitka flags (icon, temp dir, output name) automatically.
- You can override defaults: `--outdir`, `--name`, `--icon`, `--extra` for raw Nuitka args, `--dry-run`.

### 7.2 Local Version Bumping (bump2version)

This repo uses bump2version to keep versions in sync across files.

- Config: `.bumpversion.cfg` updates both `pyproject.toml` and `ai_rom_batch_renamer/modules/const.py`.
- Default behavior (no commit, no tag):

```bash
# Interactive (select patch/minor/major via Poetry script)
poetry run bump

# Direct part bump
poetry run bump-patch
poetry run bump-minor
poetry run bump-major
```

Optional CI sync of const.py:

- If you use Option B (Release Drafter tag) and want `const.py` to reflect the tag in build artifacts without committing it, add a pre-build step:

```bash
# Example: set const.py to the tag-derived version in CI without committing changes
bump2version --allow-dirty --new-version "$APP_VERSION" patch
```

This ensures the app's About/version output matches the release tag.

## 8. Exit / Error Semantics (Recommended)

- Exit 0: All requested operations succeeded
- Exit 1: Generic failure (I/O, permission)
- Exit 2: Invalid arguments / missing directory
- Exit 3: AI API error / quota exceeded
- Exit 4: ZIP extraction failure

(Adjust if current implementation differs; align scripts accordingly.)

## 9. File History / Revert Strategy

- Original names are cached (see `renamerHistory.cache`).
- Revert reads mapping and reconstructs prior filenames.
- Ensure backup retention if running destructive batch jobs (e.g. commit cache file to VCS or copy before runs).

## 10. Roadmap Snapshot

- Multi-model support (✔)
- Third-party OpenAI-compatible endpoints (✔)
- Local cache (planned)
- GUI frontend (planned)

## 11. Best Practices

- Always begin with `--dry-run` when adjusting filters.
- Keep API keys outside version control (use `apiKey.txt` or env vars).
- Avoid renaming already curated sets—check with `--output` first.
- Use `--trim` to normalize before AI step for cleaner prompts.

## 12. Troubleshooting

| Symptom | Cause | Mitigation |
|---------|-------|-----------|
| Slow runs | Large ZIPs / many API calls | Use includes/excludes, enable caching when available |
| Wrong year in title | AI hallucination | Provide platform (`-p`), consider manual override pass |
| Missing pinyin initial | Non-Chinese title | Expected (only added when Chinese characters parsed) |
| Revert fails | Cache entry missing | Ensure cache file not deleted; fallback manual rename |

## 13. Contribution Hooks (Agent Perspective)

Potential automated PRs:

- Add local caching layer (new module `cache_local.py` + tests)
- Abstract AI provider interface (strategy pattern)
- Integrate logging verbosity flags (`--verbose`, `--quiet`)
- Add JSON output mode for machine parsing (`--json`) for pipeline consumption
- Add release notes validation to ensure `pyproject.toml` version matches tag when using Option A
- Add smoke tests for built binaries (hash, basic `--help` run) in CI

## 14. License

MIT (see `LICENSE`). Safe for internal automation and redistribution.

---

Made with ❤️ for retro gaming enthusiasts.
