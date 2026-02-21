"""Hot reload script for GUI development.

Watches ai_rom_batch_renamer/ for .py file changes and restarts the GUI automatically.
Usage: poetry run dev
"""

import subprocess
import sys
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

WATCH_DIR = Path(__file__).parent.parent / "ai_rom_batch_renamer"
DEBOUNCE_SECONDS = 0.8


class GUIReloadHandler(FileSystemEventHandler):
    def __init__(self):
        self.process: subprocess.Popen | None = None
        self._debounce_timer: threading.Timer | None = None
        self._lock = threading.Lock()
        self._start()

    def _start(self):
        print("[hotreload] Starting GUI...", flush=True)
        self.process = subprocess.Popen(
            [sys.executable, "-m", "ai_rom_batch_renamer.gui"],
            cwd=str(Path(__file__).parent.parent),
        )

    def _restart(self):
        with self._lock:
            if self.process and self.process.poll() is None:
                print("[hotreload] Stopping GUI...", flush=True)
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            self._start()

    def _schedule_restart(self, path: str):
        if self._debounce_timer:
            self._debounce_timer.cancel()
        self._debounce_timer = threading.Timer(DEBOUNCE_SECONDS, self._restart)
        self._debounce_timer.start()
        print(f"[hotreload] Change detected: {path}", flush=True)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".py"):
            self._schedule_restart(event.src_path)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".py"):
            self._schedule_restart(event.src_path)

    def stop(self):
        if self._debounce_timer:
            self._debounce_timer.cancel()
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


def main():
    print(f"[hotreload] Watching {WATCH_DIR} for changes...", flush=True)
    handler = GUIReloadHandler()
    observer = Observer()
    observer.schedule(handler, str(WATCH_DIR), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
            # If GUI was closed manually, restart it
            if handler.process and handler.process.poll() is not None:
                print("[hotreload] GUI exited, restarting...", flush=True)
                handler._start()
    except KeyboardInterrupt:
        print("\n[hotreload] Shutting down...", flush=True)
        observer.stop()
        handler.stop()
    observer.join()


if __name__ == "__main__":
    main()
