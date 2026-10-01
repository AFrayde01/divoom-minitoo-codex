"""Read activity state written by the optional Codex lifecycle hooks."""

from __future__ import annotations

import json
import os
import pwd
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    USER_HOME = Path(pwd.getpwuid(os.getuid()).pw_dir)
except (KeyError, OSError):
    USER_HOME = Path.home()
ACTIVITY_FILE = Path(
    os.environ.get(
        "CODEX_MINITOO_ACTIVITY_FILE",
        USER_HOME / ".codex" / "divoom-minitoo-codex-activity.json",
    )
)
ACTIVE_TTL_SECONDS = 24 * 60 * 60
ACTIVITY_PULSE_SECONDS = 8


@dataclass(frozen=True)
class CodexActivity:
    working: bool = False
    hooks_installed: bool = False
    active_sessions: int = 0


def read_activity(path: Path | None = None, now: float | None = None) -> CodexActivity:
    """Return whether any recent Codex session has an active turn."""
    activity_path = path or Path(os.environ.get("CODEX_MINITOO_ACTIVITY_FILE", ACTIVITY_FILE))
    try:
        data: Any = json.loads(activity_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return CodexActivity()
    if not isinstance(data, dict):
        return CodexActivity()

    sessions = data.get("sessions")
    if not isinstance(sessions, dict):
        sessions = {}
    current_time = now if now is not None else time.time()
    active_count = 0
    for state in sessions.values():
        if not isinstance(state, dict) or state.get("status") != "working":
            continue
        try:
            updated_at = float(state.get("updated_at", 0))
        except (TypeError, ValueError):
            continue
        if 0 <= current_time - updated_at < ACTIVE_TTL_SECONDS:
            active_count += 1

    recent_activity = False
    try:
        last_turn_at = float(data.get("last_turn_at", 0))
        recent_activity = 0 <= current_time - last_turn_at < ACTIVITY_PULSE_SECONDS
    except (TypeError, ValueError):
        pass

    return CodexActivity(
        working=active_count > 0 or recent_activity,
        hooks_installed=data.get("installed") is True,
        active_sessions=active_count,
    )
