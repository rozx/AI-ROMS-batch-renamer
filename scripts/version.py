"""Version management utilities.

Provides two approaches:
1. Legacy bump functions (patch/minor/major) that relied on bump2version.
2. Direct setting of an explicit version across `pyproject.toml` and
   `ai_rom_batch_renamer/modules/const.py` without invoking bump2version.

This allows CI to call:
    poetry run python scripts/version.py --set 2.1.0
or (tag style):
    poetry run python scripts/version.py --set v2.1.0

and guarantee both metadata files are synchronized even if bump2version
is unavailable or misbehaving.
"""

from __future__ import annotations

import argparse
import locale
import os
import re
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

try:
    import toml  # type: ignore
except ImportError:  # pragma: no cover
    toml = None  # fallback to manual text edit


POETRY_SECTION = ("tool", "poetry")


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _pyproject_path() -> Path:
    return _project_root() / "pyproject.toml"


def _const_path() -> Path:
    return _project_root() / "ai_rom_batch_renamer" / "modules" / "const.py"


def _supports_unicode() -> bool:
    enc = (
        getattr(sys.stdout, "encoding", None)
        or locale.getpreferredencoding(False)
        or ""
    ).lower()
    return "utf" in enc


def _symbol(ok: bool = True, warn: bool = False) -> str:
    if not _supports_unicode():
        if warn:
            return "WARN"
        return "OK" if ok else "ERR"
    if warn:
        return "⚠"
    return "✓" if ok else "✗"


def _normalize_version(v: str) -> str:
    v = v.strip()
    if v.startswith("v"):
        v = v[1:]
    # Basic semantic version validation (major.minor.patch)
    if not re.match(r"^\d+\.\d+\.\d+$", v):
        print(
            f"{_symbol(False)} Provided version '{v}' is not in form X.Y.Z",
            file=sys.stderr,
        )
        sys.exit(2)
    return v


def _write_const(version: str) -> None:
    """Replace only the VERSION assignment line, preserving the rest of the file.

    A previous implementation rewrote the whole file as a single line, which
    silently dropped the Nuitka workaround comments kept in const.py.
    """
    path = _const_path()
    text = path.read_text(encoding="utf-8")
    new_text, n = re.subn(
        r'(?m)^VERSION\s*=\s*["\'][^"\']*["\']',
        f'VERSION = "{version}"',
        text,
        count=1,
    )
    if n == 0:  # file without the marker — fall back to full rewrite
        new_text = f'VERSION = "{version}"\n'
    path.write_text(new_text, encoding="utf-8")


def _write_bumpversion_cfg(version: str) -> None:
    """Keep .bumpversion.cfg current_version in sync.

    Without this, a later ``--bump`` fails because bump2version searches for
    the stale version string recorded in the config.
    """
    path = _project_root() / ".bumpversion.cfg"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    new_text, n = re.subn(
        r"(?m)^current_version\s*=\s*\S+",
        f"current_version = {version}",
        text,
        count=1,
    )
    if n:
        path.write_text(new_text, encoding="utf-8")


def _write_pyproject(version: str) -> None:
    path = _pyproject_path()
    text = path.read_text(encoding="utf-8")
    # Precise in-place regex update only. A previous implementation round-tripped
    # the file through toml.loads/dumps, which reformatted the whole document
    # (array trailing commas, inline dependency tables exploded into separate
    # [tool.poetry.dependencies.*] tables) and produced huge spurious diffs.
    new_text = _regex_update_version(text, version)
    if toml:  # safety net: verify the edited file still parses
        try:
            parsed = toml.loads(new_text)
            got = parsed.get("tool", {}).get("poetry", {}).get("version")
            if got != version:
                print(
                    f"{_symbol(False, True)} TOML parse-check mismatch: got {got!r}",
                    file=sys.stderr,
                )
        except Exception as e:
            print(
                f"{_symbol(False, True)} edited pyproject.toml failed to parse ({e})",
                file=sys.stderr,
            )
    path.write_text(new_text, encoding="utf-8")


def _regex_update_version(text: str, version: str) -> str:
    """Replace the top-level version assignment inside [tool.poetry] only.

    Scoping to the section header prevents touching other ``version`` keys
    (e.g. inline dependency entries like ``PySide6 = { version = "..." }``).
    """
    section = re.search(r"(?m)^\[tool\.poetry\]\s*$", text)
    if section:
        head, tail = text[: section.end()], text[section.end() :]
        new_tail, count = re.subn(
            r'(?m)^version\s*=\s*["\'][^"\']*["\']',
            f'version = "{version}"',
            tail,
            count=1,
        )
        if count:
            return head + new_tail
        # No version line in the section — insert one right below the header
        return f'{head}\nversion = "{version}"' + tail
    # Fallback: first bare ``version =`` line anywhere in the file
    pattern = re.compile(r'(?m)^version\s*=\s*["\'][^"\']*["\']')
    new_text, count = pattern.subn(f'version = "{version}"', text, count=1)
    if count == 0:
        print(
            "⚠ No existing version line found; inserting one into [tool.poetry]",
            file=sys.stderr,
        )
        new_text = re.sub(
            r"(\[tool\.poetry\])",
            f'\\1\nversion = "{version}"',
            text,
            count=1,
        )
    return new_text


def set_version(explicit_version: str) -> None:
    version = _normalize_version(explicit_version)
    _write_pyproject(version)
    _write_const(version)
    _write_bumpversion_cfg(version)
    print(f"{_symbol(True)} Set version to {version}")


def current_version() -> str:
    try:
        import toml as _t  # type: ignore

        data = _t.loads(_pyproject_path().read_text(encoding="utf-8"))
        return data.get("tool", {}).get("poetry", {}).get("version", "<unknown>")
    except Exception:
        return "<unknown>"


def _run_bump2version(args: Iterable[str]) -> int:
    try:
        proc = subprocess.run(["bump2version", *args], cwd=_project_root(), check=False)
    except FileNotFoundError:
        print(f"{_symbol(False)} bump2version not installed", file=sys.stderr)
        return 127
    if proc.returncode != 0:
        print(
            f"{_symbol(False)} bump2version failed with exit code {proc.returncode}",
            file=sys.stderr,
        )
    return proc.returncode or 1


def bump_part(part: str, allow_dirty: bool = True) -> None:
    if part not in {"patch", "minor", "major"}:
        print(f"{_symbol(False)} Invalid part '{part}'", file=sys.stderr)
        sys.exit(2)
    args = []
    if allow_dirty:
        args.append("--allow-dirty")
    args.append(part)
    rc = _run_bump2version(args)
    if rc == 0:
        print(f"{_symbol(True)} bump2version {part} succeeded")
    else:
        print(
            "Fallback: derive +1 version manually not implemented; use --set instead",
            file=sys.stderr,
        )
        sys.exit(rc)


# ---- Poetry script entrypoints ----
def bump_version() -> None:
    """Poetry script entrypoint.

    If APP_VERSION is set, directly set that version across files.
    Otherwise, attempt a patch bump via bump2version for convenience.
    """
    env_version = os.getenv("APP_VERSION")
    if env_version:
        set_version(env_version)
        return
    # Default to a patch bump if no explicit version provided
    bump_part("patch")


def bump_patch() -> None:
    bump_part("patch")


def bump_minor() -> None:
    bump_part("minor")


def bump_major() -> None:
    bump_part("major")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Version utility (bump or set explicit version)."
    )
    g = p.add_mutually_exclusive_group(required=False)
    g.add_argument(
        "--set",
        metavar="X.Y.Z",
        help="Set an explicit semantic version across files (accepts leading v prefix).",
    )
    g.add_argument(
        "--bump",
        choices=["patch", "minor", "major"],
        help="Use bump2version to bump one part.",
    )
    p.add_argument(
        "--no-allow-dirty",
        action="store_true",
        help="Do not pass --allow-dirty to bump2version.",
    )
    p.add_argument(
        "--print", action="store_true", help="Print current version and exit."
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    ns = _parse_args(argv or sys.argv[1:])
    if ns.print:
        print(current_version())
        return
    if ns.set:
        set_version(ns.set)
        return
    if ns.bump:
        bump_part(ns.bump, allow_dirty=not ns.no_allow_dirty)
        return
    # No args: provide interactive selection (legacy behavior)
    print("No arguments provided; entering interactive mode.")
    print("Select version part to bump:")
    print("1. patch (x.x.X)")
    print("2. minor (x.X.0)")
    print("3. major (X.0.0)")
    choice = input("Enter choice (1-3): ").strip()
    mapping = {"1": "patch", "2": "minor", "3": "major"}
    part = mapping.get(choice)
    if not part:
        print(f"{_symbol(False)} Invalid choice", file=sys.stderr)
        sys.exit(1)
    bump_part(part)


if __name__ == "__main__":  # pragma: no cover
    main()
