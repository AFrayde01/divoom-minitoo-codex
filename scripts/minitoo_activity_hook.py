#!/usr/bin/env python3
"""Store minimal Codex turn activity for the MiniToo monitor.

The hook intentionally records only session/turn identifiers and lifecycle
timestamps. It never stores prompts, responses, or tool output.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ACTIVE_TTL_SECONDS = 24 * 60 * 60


def _read_state(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    sessions = data.get("sessions")
    if not isinstance(sessions, dict):
        sessions = {}
    data["sessions"] = sessions
    return data


def _write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(state, output, separators=(",", ":"))
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def update_activity(path: Path, event: dict[str, Any], now: float | None = None) -> None:
    session_id = event.get("session_id")
    event_name = event.get("hook_event_name")
    if not isinstance(session_id, str) or not session_id or not isinstance(event_name, str):
        return

    current_time = now if now is not None else time.time()
    lock_path = path.with_name(f"{path.name}.lock")
    lock_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with lock_path.open("a", encoding="utf-8") as lock_file:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        state = _read_state(path)
        sessions = state["sessions"]

        # Expire abandoned turns, for example after Codex is force-quit.
        for stale_id, session in list(sessions.items()):
            try:
                updated_at = float(session.get("updated_at", 0))
            except (AttributeError, TypeError, ValueError):
                updated_at = 0
            if current_time - updated_at >= ACTIVE_TTL_SECONDS:
                sessions.pop(stale_id, None)

        if event_name == "UserPromptSubmit":
            sessions[session_id] = {
                "status": "working",
                "turn_id": event.get("turn_id"),
                "updated_at": current_time,
            }
            state["last_turn_at"] = current_time
        elif event_name in {"Stop", "Interrupt"}:
            state["last_turn_at"] = current_time
            sessions.pop(session_id, None)
        elif event_name == "SessionEnd":
            sessions.pop(session_id, None)
        elif event_name == "SessionStart":
            # A compacted session is still active; startup/resume clears stale
            # state left by a force-quit before the next prompt arrives.
            if event.get("source") != "compact":
                sessions.pop(session_id, None)
        else:
            return

        state["installed"] = True
        _write_state(path, state)
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--state-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        event = json.load(sys.stdin)
        if isinstance(event, dict):
            update_activity(args.state_file, event)
    except Exception as exc:
        # A status indicator must never interrupt a Codex turn.
        print(f"MiniToo activity hook ignored an error: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
