"""Client for a bundled local Divoom Bluetooth display bridge."""

from __future__ import annotations

import base64
import json
import logging
import secrets
import socket
import subprocess
import time
from collections import deque
from pathlib import Path
from threading import Event, Lock, Thread


# MiniToo allows up to 40 seconds for its Bluetooth transaction. The local
# caller must outlive that deadline and leave time for the JSON response.
BRIDGE_RESPONSE_TIMEOUT_SECONDS = 60
MAX_REQUEST_BYTES = 512 * 1024
AUTHENTICATED_READY_MARKER = "authenticated local listener ready on port"


class MiniTooError(RuntimeError):
    """Raised when a Divoom bridge cannot display an image."""


class MiniTooBridge:
    def __init__(
        self, executable: Path, address: str, port: int = 40584, display_name: str = "MiniToo",
        logger: logging.Logger | None = None,
    ) -> None:
        self.executable = executable
        self.address = address
        self.port = port
        self.display_name = display_name
        self.logger = logger
        self.process: subprocess.Popen[bytes] | None = None
        self._stderr_tail: deque[str] = deque(maxlen=20)
        self._stderr_lock = Lock()
        self._stderr_thread: Thread | None = None
        self._auth_token: str | None = None
        self._protocol_mismatch = False

    def _capture_stderr(self, stream: object, ready: Event) -> None:
        read_line = getattr(stream, "readline")
        for raw_line in iter(read_line, b""):
            line = raw_line.decode("utf-8", errors="replace").strip()
            if line:
                with self._stderr_lock:
                    self._stderr_tail.append(line)
                if self.logger is not None:
                    self.logger.info(line)
                if f"{AUTHENTICATED_READY_MARKER} {self.port}." in line:
                    ready.set()
                elif "local listener ready on port" in line:
                    self._protocol_mismatch = True
                    ready.set()

    def _bridge_diagnostics(self) -> str:
        process = self.process
        exit_status = process.poll() if process is not None else None
        with self._stderr_lock:
            lines = list(self._stderr_tail)
        details = []
        if exit_status is not None:
            details.append(f"bridge process exited with code {exit_status}")
        if lines:
            details.append("bridge log: " + " | ".join(lines[-5:]))
        return "; ".join(details)

    def start(self) -> None:
        if self.process is not None and self.process.poll() is None:
            return
        self.close()
        with self._stderr_lock:
            self._stderr_tail.clear()
        self._protocol_mismatch = False
        if not self.executable.is_file():
            raise MiniTooError(
                f"Bluetooth bridge not found at {self.executable}. Run scripts/install.sh first."
            )
        try:
            self._auth_token = secrets.token_hex(32)
            self.process = subprocess.Popen(
                [str(self.executable), self.address, str(self.port)],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            # A private inherited pipe keeps the per-run credential out of
            # process arguments, environment variables, logs and the filesystem.
            assert self.process.stdin is not None
            self.process.stdin.write((self._auth_token + "\n").encode("ascii"))
            self.process.stdin.close()
        except OSError as exc:
            self.close()
            raise MiniTooError(f"Could not start the {self.display_name} bridge: {exc}") from exc
        ready = Event()
        if self.process.stderr is not None:
            self._stderr_thread = Thread(
                target=self._capture_stderr, args=(self.process.stderr, ready), daemon=True
            )
            self._stderr_thread.start()

        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                if self._stderr_thread is not None:
                    self._stderr_thread.join(timeout=1)
                diagnostics = self._bridge_diagnostics()
                self.close()
                raise MiniTooError(
                    f"{self.display_name} bridge stopped while connecting. Check the Bluetooth address, "
                    "pairing, and macOS Bluetooth permission."
                    + (f" Details: {diagnostics}." if diagnostics else "")
                )
            # A connect-only probe can accidentally find another monitor on
            # this port. Only the child we started can declare itself ready.
            if ready.wait(timeout=0.15) and self.process.poll() is None:
                if self._protocol_mismatch:
                    self.close()
                    raise MiniTooError(
                        f"The {self.display_name} bridge is outdated and does not authenticate local requests. "
                        "Rebuild it with scripts/install.sh, then restart the monitor."
                    )
                return
        diagnostics = self._bridge_diagnostics()
        self.close()
        detail = f" Details: {diagnostics}." if diagnostics else ""
        raise MiniTooError(
            f"{self.display_name} bridge did not start listening on localhost:{self.port} within 15 seconds."
            + " Rebuild the authenticated bridges with scripts/install.sh if upgrading."
            + detail
        )

    def send_jpeg(self, jpeg: bytes) -> dict[str, object]:
        return self.send_frames([jpeg], speed_ms=0)

    def send_frames(self, frames: list[bytes], speed_ms: int = 400) -> dict[str, object]:
        if not frames or len(frames) > 8:
            raise MiniTooError("The display bridge supports between 1 and 8 image frames.")
        if not 0 <= speed_ms <= 65_535:
            raise MiniTooError("Animation speed must be between 0 and 65535 ms.")
        # Validate size before connecting, then encode the current credential
        # after startup/recovery has created it.
        request_body: dict[str, object] = {
            "framesBase64": [base64.b64encode(frame).decode("ascii") for frame in frames],
            "speedMs": speed_ms,
            "authToken": "0" * 64,
        }
        request = json.dumps(request_body, separators=(",", ":")).encode() + b"\n"
        if len(request) > MAX_REQUEST_BYTES:
            raise MiniTooError("Image request exceeds the bridge's 512 KiB limit.")
        if self.process is None or self.process.poll() is not None:
            self.start()
        if self._auth_token is None:
            raise MiniTooError("The local bridge has no authentication credential. Restart the monitor.")
        request_body["authToken"] = self._auth_token
        request = json.dumps(request_body, separators=(",", ":")).encode() + b"\n"
        stage = "connecting to the local bridge"
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=10) as conn:
                conn.settimeout(BRIDGE_RESPONSE_TIMEOUT_SECONDS)
                stage = "sending the image request"
                conn.sendall(request)
                response = bytearray()
                stage = "waiting for the Bluetooth transfer response"
                deadline = time.monotonic() + BRIDGE_RESPONSE_TIMEOUT_SECONDS
                while b"\n" not in response:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError("the bridge response deadline expired")
                    conn.settimeout(remaining)
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    response.extend(chunk)
                    if len(response) > 64 * 1024:
                        raise MiniTooError("The bridge response exceeded 64 KiB.")
        except OSError as exc:
            diagnostics = self._bridge_diagnostics()
            raise MiniTooError(
                f"{self.display_name} connection failed while {stage}: {exc}."
                + (f" Details: {diagnostics}." if diagnostics else "")
            ) from exc
        try:
            raw_response = bytes(response).split(b"\n", 1)[0].strip()
            if not raw_response:
                raise json.JSONDecodeError("empty response", "", 0)
            # The bridge uses newline-delimited JSON. Ignore any bytes after
            # the first complete line so a transport close cannot corrupt it.
            result = json.loads(raw_response.splitlines()[0])
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            preview = bytes(response[:160]).decode("utf-8", errors="replace").strip()
            detail = f" Received: {preview!r}." if preview else " The bridge sent no data."
            diagnostics = self._bridge_diagnostics()
            if diagnostics:
                detail += f" Details: {diagnostics}."
            raise MiniTooError(f"{self.display_name} bridge returned an invalid response.{detail}") from exc
        if not isinstance(result, dict):
            raise MiniTooError(f"{self.display_name} bridge returned an invalid response type.")
        if result.get("ok") is not True:
            diagnostics = self._bridge_diagnostics()
            message = result.get("message") or f"{self.display_name} did not accept the image."
            raise MiniTooError(str(message) + (f" Details: {diagnostics}." if diagnostics else ""))
        return result

    def send_frames_with_recovery(
        self, frames: list[bytes], speed_ms: int = 400, *, require_ack: bool = False
    ) -> dict[str, object]:
        """Retry one failed transaction over a new Bluetooth session."""
        failures: list[str] = []
        for attempt in range(2):
            try:
                if attempt:
                    self.close()
                result = self.send_frames(frames, speed_ms=speed_ms)
                if require_ack and result.get("acknowledged") is not True:
                    diagnostics = self._bridge_diagnostics()
                    raise MiniTooError(
                        f"{self.display_name} transfer was not confirmed: "
                        + str(result.get("message", "no final acknowledgement"))
                        + (f". Details: {diagnostics}." if diagnostics else "")
                    )
                result["reconnected"] = bool(attempt)
                return result
            except MiniTooError as exc:
                failures.append(str(exc))
                if self.logger is not None:
                    self.logger.warning("Transfer attempt %s/2 failed: %s", attempt + 1, exc)
        self.close()
        raise MiniTooError(
            f"{self.display_name} transfer failed after one reconnect. "
            + " Initial attempt: " + failures[0]
            + " Reconnect attempt: " + failures[1]
        )

    def close(self) -> None:
        process = self.process
        self.process = None
        self._auth_token = None
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        if self._stderr_thread is not None:
            self._stderr_thread.join(timeout=1)
            self._stderr_thread = None
        if process is not None and process.stderr is not None:
            process.stderr.close()
        if process is not None and process.stdin is not None:
            process.stdin.close()

    def __enter__(self) -> "MiniTooBridge":
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
