"""Watch for active microphone input without accessing audio samples."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path


class BrowserMicrophoneMonitor:
    """Read Core Audio process state from the bundled macOS helper."""

    def __init__(self, executable: Path) -> None:
        self.executable = executable
        self._process: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()
        self._ready = threading.Event()
        self._available: bool | None = None
        self._active = False
        self.error: str | None = None
        self._reader: threading.Thread | None = None

    @property
    def available(self) -> bool:
        with self._lock:
            return self._available is True

    @property
    def active(self) -> bool:
        with self._lock:
            return self._available is True and self._active

    def start(self) -> bool:
        if sys.platform != "darwin":
            self.error = "Automatic browser microphone detection requires macOS."
            return False
        if not self.executable.is_file():
            self.error = f"Browser microphone helper not found at {self.executable}. Run ./install."
            return False
        try:
            self._process = subprocess.Popen(
                [str(self.executable)],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            self.error = f"Could not start browser microphone detection: {exc}"
            return False

        self._reader = threading.Thread(target=self._read_samples, daemon=True)
        self._reader.start()
        if not self._ready.wait(timeout=3):
            self.error = "Browser microphone helper did not report its status."
            self.stop()
            with self._lock:
                self._available = False
            return False
        if not self.available:
            if self.error is None:
                self.error = "Automatic browser microphone detection requires macOS 14.2 or newer."
            self.stop()
            return False
        return True

    def _read_samples(self) -> None:
        process = self._process
        stream = process.stdout if process is not None else None
        if stream is None:
            return
        try:
            for line in stream:
                try:
                    sample = json.loads(line)
                except (json.JSONDecodeError, TypeError):
                    continue
                if not isinstance(sample, dict) or not isinstance(sample.get("available"), bool):
                    continue
                available = sample["available"]
                active = sample.get("active") is True
                with self._lock:
                    self._available = available
                    self._active = active if available else False
                reason = sample.get("reason")
                if not available and isinstance(reason, str):
                    self.error = f"Core Audio could not inspect browser microphone activity: {reason}"
                self._ready.set()
                if not available:
                    return
        finally:
            with self._lock:
                if self._available is None:
                    self._available = False
            self._ready.set()

    def stop(self) -> None:
        process = self._process
        self._process = None
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        if self._reader is not None:
            self._reader.join(timeout=1)
            self._reader = None
        if process is not None and process.stdout is not None:
            process.stdout.close()


def default_browser_microphone_monitor() -> BrowserMicrophoneMonitor:
    helper = Path(__file__).resolve().parents[2] / "build" / "browser-microphone-monitor"
    return BrowserMicrophoneMonitor(helper)
