"""Bootstrap entry-point for the compiled GUI binary.

This thin wrapper ensures any startup failure — including a missing PySide6
library or DLL-load error — is captured, logged to disk, and presented to the
user via a native OS dialog (no Qt dependency required for error reporting).

The Nuitka build uses this file as the entry point instead of gui.py so that
the heavy PySide6 import is deferred and can be caught.  When the binary is
re-invoked in CLI mode (--__cli-mode__), PySide6 is never loaded at all —
only the lightweight CLI modules are imported.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path


def _show_crash_dialog(tb_text: str, log_path: Path) -> None:
    """Best-effort native dialog to report a start-up crash."""
    if sys.platform.startswith("win"):
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(  # type: ignore[attr-defined]
                0,
                f"程序启动失败 (Failed to start):\n\n{tb_text}\n\n"
                f"日志已保存到 (Log saved to):\n{log_path}",
                "ROM Batch Renamer \u2013 启动错误",
                0x10,  # MB_ICONERROR
            )
        except Exception:
            pass
    else:
        sys.stderr.write(f"FATAL:\n{tb_text}\nLog saved to: {log_path}\n")


def main() -> None:
    # Hidden flag: the GUI binary re-invokes itself in CLI mode.
    # Handle this *before* importing PySide6 so the CLI path stays lightweight.
    if "--__cli-mode__" in sys.argv:
        sys.argv.remove("--__cli-mode__")
        from ai_rom_batch_renamer.main import app as cli_app

        cli_app()
        return

    try:
        from ai_rom_batch_renamer.gui import launch_gui

        raise SystemExit(launch_gui())
    except SystemExit:
        raise
    except Exception:
        import tempfile

        crash_log = Path(tempfile.gettempdir()) / "ai-rom-batch-renamer-crash.log"
        tb_text = traceback.format_exc()
        try:
            crash_log.write_text(
                f"ai-rom-batch-renamer GUI crash\n"
                f"Python {sys.version}\n"
                f"Platform: {sys.platform}\n"
                f"argv: {sys.argv}\n\n"
                f"{tb_text}",
                encoding="utf-8",
            )
        except Exception:
            pass
        _show_crash_dialog(tb_text, crash_log)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
