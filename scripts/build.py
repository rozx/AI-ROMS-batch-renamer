#!/usr/bin/env python3
"""
Dynamic Nuitka build script for AI ROM Batch Renamer.

It computes platform-specific options (icon, temp dir, output filename),
reads the version from APP_VERSION env or pyproject.toml, and runs Nuitka.

Usage examples:
    poetry run build
    poetry run build --target both --outdir ./dist --verbose
    poetry run build --target gui --name custom-name --dry-run
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


TARGET_ENTRY = {
    "cli": "main.py",
    "gui": "gui.py",
}


def read_version(pyproject_path: Path) -> str | None:
    # Prefer APP_VERSION from environment (e.g., set by CI from tag)
    app_version = os.environ.get("APP_VERSION")
    if app_version:
        return app_version.strip()

    # Fallback: parse pyproject.toml
    try:
        import toml  # provided by project dependencies
    except Exception:
        return None

    try:
        data = toml.loads(pyproject_path.read_text(encoding="utf-8"))
        return data.get("tool", {}).get("poetry", {}).get("version")
    except Exception:
        return None


def detect_platform() -> str:
    sys_plat = sys.platform
    if sys_plat.startswith("win"):
        return "Windows"
    if sys_plat == "darwin":
        return "MacOS"
    return "Linux"


def default_output_name(base: str = "ai-rom-batch-renamer", target: str = "cli") -> str:
    plat = detect_platform()
    suffix = {
        "Windows": "Windows-X64",
        "MacOS": "MacOS-X64",
        "Linux": "Linux-X64",
    }[plat]
    ext = ".exe" if plat == "Windows" else ""
    target_suffix = "gui" if target == "gui" else "cli"
    return f"{base}-{suffix}-{target_suffix}{ext}"


def default_temp_dir_spec() -> str:
    plat = detect_platform()
    if plat == "Windows":
        return r"{TEMP}\ai-rom-batch-renamer"
    return r"{TEMP}/ai-rom-batch-renamer"


def default_icon_path(project_root: Path) -> str:
    plat = detect_platform()
    icon_dir = project_root / "assets" / "icos"

    if plat == "Windows":
        return str(icon_dir / "icon.ico")
    if plat == "MacOS":
        return str(icon_dir / "icon.icns")
    return str(icon_dir / "icon.png")


def _compute_entry(project_root: Path, args: argparse.Namespace, target: str) -> str:
    if args.entry:
        return args.entry
    return str(project_root / "ai_rom_batch_renamer" / TARGET_ENTRY[target])


def build(args: argparse.Namespace, target: str = "cli") -> int:
    project_root = Path(__file__).resolve().parent.parent
    pyproject = project_root / "pyproject.toml"
    entry = _compute_entry(project_root, args, target)
    outdir = args.outdir or str(project_root / "dist")
    name = args.name or default_output_name(target=target)
    tempdir_spec = args.tempdir or default_temp_dir_spec()
    app_version = args.version or read_version(pyproject)
    include_pkg_data = args.include_package_data or ["pinyin"]
    plat = detect_platform()

    nuitka_cmd = [
        sys.executable,
        "-m",
        "nuitka",
    ]

    if args.onefile:
        nuitka_cmd.append("--onefile")
        # Nuitka requires '=' form for this option
        nuitka_cmd.append(f"--onefile-tempdir-spec={tempdir_spec}")

    # Nuitka expects these options in '--option=value' form
    nuitka_cmd.append(f"--output-dir={outdir}")
    nuitka_cmd.append(f"--output-filename={name}")

    if args.assume_yes:
        nuitka_cmd.append("--assume-yes-for-downloads")

    for pkg in include_pkg_data:
        nuitka_cmd.append(f"--include-package-data={pkg}")

    # Icons per platform
    icon_path = args.icon
    if plat == "Windows" and icon_path:
        nuitka_cmd.append(f"--windows-icon-from-ico={icon_path}")
    if plat == "MacOS" and icon_path:
        nuitka_cmd.append(f"--macos-app-icon={icon_path}")

    # GUI build on Windows: disable console by default unless user overrides via --extra
    if (
        plat == "Windows"
        and target == "gui"
        and not args.no_windows_disable_console
        and not (args.extra and any(opt.startswith("--windows-console-mode") for opt in args.extra))
    ):
        nuitka_cmd.append("--windows-console-mode=disable")

    # Append extra raw options if provided
    if args.extra:
        nuitka_cmd.extend(args.extra)

    # Source entry
    nuitka_cmd.append(entry)

    if args.verbose or args.dry_run:
        print("Detected platform:", plat)
        print("Build target:", target)
        print("App version:", app_version or "unknown")
        print("Running:")
        print(" ".join(nuitka_cmd))

    if args.dry_run:
        return 0

    env = os.environ.copy()
    if app_version:
        # Some apps read version from env at runtime/build time
        env["APP_VERSION"] = app_version

    # Ensure output directory exists
    try:
        os.makedirs(outdir, exist_ok=True)
    except Exception as e:
        print(f"Failed to create output directory '{outdir}': {e}")
        return 1

    proc = subprocess.run(nuitka_cmd, env=env)
    return proc.returncode


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build with Nuitka (dynamic spec)")
    parser.add_argument(
        "--target",
        choices=["cli", "gui", "both"],
        default="cli",
        help="Build target: cli(main.py), gui(gui.py), or both (default: cli)",
    )
    parser.add_argument(
        "--entry",
        default=None,
        help="Entry script override (by default derives from --target)",
    )
    parser.add_argument("--outdir", default=None, help="Output directory (default: ./dist)")
    parser.add_argument("--name", default=None, help="Output filename (auto-computed per OS if omitted)")
    parser.add_argument("--tempdir", default=None, help="Onefile temp dir spec (default per OS)")
    parser.add_argument(
        "--icon",
        default=None,
        help="Icon path for Windows(.ico) / MacOS(.icns)",
    )
    parser.add_argument("--version", default=None, help="Override app version")
    parser.add_argument("--include-package-data", nargs="*", default=None, help="Packages to include data for")
    parser.add_argument("--onefile", action="store_true", default=True, help="Build as onefile (default)")
    parser.add_argument("--no-onefile", dest="onefile", action="store_false", help="Disable onefile mode")
    parser.add_argument("--assume-yes", action="store_true", default=True, help="Assume yes for downloads (default)")
    parser.add_argument("--no-assume-yes", dest="assume_yes", action="store_false", help="Disable assume yes")
    parser.add_argument("--extra", nargs=argparse.REMAINDER, help="Extra raw Nuitka options (placed at end)")
    parser.add_argument(
        "--no-windows-disable-console",
        action="store_true",
        help="For GUI target on Windows, do not add --windows-console-mode=disable automatically",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print command only")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.icon is None:
        project_root = Path(__file__).resolve().parent.parent
        args.icon = default_icon_path(project_root)

    if args.target == "both" and args.entry:
        print("--entry cannot be used with --target both. Please build targets separately or remove --entry.")
        sys.exit(2)

    if args.target == "both" and args.name:
        print("--name cannot be used with --target both. Use default names or build targets separately.")
        sys.exit(2)

    targets = ["cli", "gui"] if args.target == "both" else [args.target]

    for target in targets:
        code = build(args, target=target)
        if code != 0:
            sys.exit(code)

    sys.exit(0)


if __name__ == "__main__":
    main()
