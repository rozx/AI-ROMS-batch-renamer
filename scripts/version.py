"""Version bumping utilities using bump2version and .bumpversion.cfg.

This script invokes `bump2version` from the repository root so it can
update both pyproject.toml and ai_rom_batch_renamer/modules/const.py
according to the existing configuration.
"""

import subprocess
import sys
from pathlib import Path


def _project_root() -> Path:
    # scripts/version.py -> scripts -> repo root
    return Path(__file__).resolve().parent.parent


def _run_bump2version(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["bump2version", *args], cwd=_project_root(), check=True)


def run_bump2version(part_or_version: str, allow_dirty: bool = True) -> None:
    """Run bump2version with the given part (patch|minor|major) or exact version.

    If `part_or_version` matches one of the parts, bump that part; otherwise treat it
    as an exact version and pass `--new-version`.
    """
    parts = {"patch", "minor", "major"}
    if part_or_version in parts:
        cmd = []
        if allow_dirty:
            cmd.append("--allow-dirty")
        cmd.append(part_or_version)
    else:
        cmd = []
        if allow_dirty:
            cmd.append("--allow-dirty")
        cmd.extend(["--new-version", part_or_version, "patch"])  # default part required by CLI

    try:
        _run_bump2version(cmd)
        print("✓ Successfully updated version with bump2version")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to bump version: {e}", file=sys.stderr)
        sys.exit(e.returncode or 1)
    except FileNotFoundError:
        print(
            "✗ 'bump2version' not found. Install with: poetry add --group dev bump2version",
            file=sys.stderr,
        )
        sys.exit(1)


def bump_version() -> None:
    """Interactive version bump - prompts for version part."""
    print("Select version part to bump:")
    print("1. patch (x.x.X)")
    print("2. minor (x.X.0)")
    print("3. major (X.0.0)")

    choice = input("Enter choice (1-3): ").strip()

    parts = {"1": "patch", "2": "minor", "3": "major"}
    part = parts.get(choice)

    if not part:
        print("Invalid choice", file=sys.stderr)
        sys.exit(1)

    run_bump2version(part)


def bump_patch() -> None:
    """Bump patch version (x.x.X)."""
    run_bump2version("patch")


def bump_minor() -> None:
    """Bump minor version (x.X.0)."""
    run_bump2version("minor")


def bump_major() -> None:
    """Bump major version (X.0.0)."""
    run_bump2version("major")


if __name__ == "__main__":
    bump_version()