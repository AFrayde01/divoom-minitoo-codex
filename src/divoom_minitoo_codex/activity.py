"""Read activity state written by the optional Codex lifecycle hooks."""

from __future__ import annotations

import json
import os
import pwd
import re
import shlex
import stat
import time
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
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
HOOK_EVENTS = ("SessionStart", "UserPromptSubmit", "Stop", "Interrupt", "SessionEnd")
HOOK_SCRIPT_NAME = "minitoo_activity_hook.py"
LIFECYCLE_TAIL_BYTES = 256 * 1024
_LIFECYCLE_LINE = re.compile(
    rb'"type"\s*:\s*"event_msg".*"payload"\s*:\s*\{\s*"type"\s*:\s*"(task_complete|turn_aborted)"'
)
_TIMESTAMP_FIELD = re.compile(rb'(?<!\\)"timestamp"\s*:\s*("(?:[^"\\]|\\.)*")')
_TURN_FIELD = re.compile(rb'(?<!\\)"turn_id"\s*:\s*("(?:[^"\\]|\\.)*")')


@dataclass(frozen=True)
class ActivityHookStatus:
    configured: bool
    reason: str


def inspect_activity_hooks(codex_home: Path, state_file: Path | None = None) -> ActivityHookStatus:
    """Inspect Divoom hook definitions and targets; this does not assert trust."""
    hooks_file = codex_home / "hooks.json"
    if not hooks_file.is_file():
        return ActivityHookStatus(False, "Activity hooks are missing from this profile")
    try:
        data = json.loads(hooks_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ActivityHookStatus(False, "Could not read this profile's activity hooks")
    if not isinstance(data, dict) or not isinstance(data.get("hooks"), dict):
        return ActivityHookStatus(False, "Activity hooks are missing from this profile")
    expected_state = (state_file or Path(os.environ.get("CODEX_MINITOO_ACTIVITY_FILE", ACTIVITY_FILE))).expanduser().resolve()
    configured_events = set()
    for event in HOOK_EVENTS:
        groups = data["hooks"].get(event)
        if not isinstance(groups, list):
            continue
        for group in groups:
            handlers = group.get("hooks") if isinstance(group, dict) else None
            if not isinstance(handlers, list):
                continue
            for handler in handlers:
                command = handler.get("command") if isinstance(handler, dict) else None
                if not isinstance(command, str) or HOOK_SCRIPT_NAME not in command:
                    continue
                try:
                    tokens = shlex.split(command)
                    script = next(Path(token) for token in tokens if Path(token).name == HOOK_SCRIPT_NAME)
                    state_index = tokens.index("--state-file") + 1
                    target = Path(tokens[state_index]).expanduser().resolve()
                except (ValueError, StopIteration, IndexError):
                    return ActivityHookStatus(False, "Activity hook command is invalid")
                if not script.is_absolute() or not script.is_file():
                    return ActivityHookStatus(False, "Activity hook script is missing")
                if target != expected_state:
                    return ActivityHookStatus(False, "Activity hooks write to a different state file")
                try:
                    profile_index = tokens.index("--codex-home") + 1
                    source_home = Path(tokens[profile_index]).expanduser().resolve()
                except (ValueError, IndexError):
                    return ActivityHookStatus(False, "Activity hooks need the profile tracking update")
                if source_home != codex_home.expanduser().resolve():
                    return ActivityHookStatus(False, "Activity hooks identify a different profile")
                configured_events.add(event)
    if configured_events != set(HOOK_EVENTS):
        return ActivityHookStatus(False, "Some activity lifecycle hooks are missing")
    return ActivityHookStatus(True, "Activity hooks are configured; review their trust in Codex")


@dataclass(frozen=True)
class CodexActivity:
    working: bool = False
    hooks_installed: bool = False
    active_sessions: int = 0


@lru_cache(maxsize=128)
def _completed_turns(
    path: Path, _modified_ns: int, size: int,
) -> tuple[tuple[str, float], ...]:
    """Read only terminal lifecycle records; never retain message contents.

    This is a best-effort fallback for a missed Stop hook. Codex transcript
    formats can change, so an unknown record never proves that a turn ended.
    """
    completed = []
    try:
        with path.open("rb") as source:
            offset = max(0, size - LIFECYCLE_TAIL_BYTES)
            source.seek(offset)
            chunk = source.read(min(LIFECYCLE_TAIL_BYTES, size - offset))
            if offset:
                _, _, chunk = chunk.partition(b"\n")  # Discard a partial leading record.
            for line in chunk.splitlines(keepends=True):
                match = _LIFECYCLE_LINE.search(line)
                if match is None or not line.endswith(b"\n"):
                    continue
                try:
                    timestamp_field = _TIMESTAMP_FIELD.search(line[:match.start()])
                    turn_field = _TURN_FIELD.search(line[match.end():])
                    if timestamp_field is None or turn_field is None:
                        continue
                    # Decode only the two metadata strings, never the message
                    # or tool payload that may accompany a lifecycle record.
                    timestamp = datetime.fromisoformat(json.loads(timestamp_field[1]).replace("Z", "+00:00"))
                    if timestamp.tzinfo is None:
                        continue
                    completed.append((json.loads(turn_field[1]), timestamp.timestamp()))
                except (ValueError, TypeError, AttributeError, OverflowError):
                    continue
    except OSError:
        pass
    return tuple(completed)


def _turn_has_ended(state: dict[str, Any]) -> bool:
    owner_pid = state.get("owner_pid")
    if isinstance(owner_pid, int) and not isinstance(owner_pid, bool) and owner_pid > 1:
        try:
            os.kill(owner_pid, 0)
        except ProcessLookupError:
            return True
        except (OSError, OverflowError):
            pass  # Lack of permission does not prove that the owner exited.
    transcript = state.get("transcript_path")
    turn_id = state.get("turn_id")
    if not isinstance(transcript, str) or not isinstance(turn_id, str) or not turn_id:
        return False
    path = Path(transcript)
    if not path.is_absolute() or path.suffix != ".jsonl":
        return False
    try:
        info = path.lstat()
    except (OSError, ValueError):
        return False
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
        return False
    return any(
        completed_id == turn_id
        for completed_id, _ in _completed_turns(path, info.st_mtime_ns, info.st_size)
    )


def read_activity(
    path: Path | None = None, now: float | None = None,
    *, codex_homes: Iterable[Path] | None = None,
) -> CodexActivity:
    """Read selected profiles' turns, excluding confirmed completed owners.

    Unattributed legacy records are excluded whenever a profile scope is
    supplied. Reinstalling the hooks migrates those records out of the file.
    """
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
    allowed = (
        {str(home.expanduser().resolve()) for home in codex_homes}
        if codex_homes is not None else None
    )
    active_count = 0
    for state in sessions.values():
        if not isinstance(state, dict) or state.get("status") != "working":
            continue
        source_home = state.get("codex_home")
        if data.get("version") == 2 and not isinstance(source_home, str):
            continue
        if allowed is not None and (not isinstance(source_home, str) or source_home not in allowed):
            continue
        try:
            updated_at = float(state.get("updated_at", 0))
        except (TypeError, ValueError):
            continue
        if 0 <= current_time - updated_at < ACTIVE_TTL_SECONDS and not _turn_has_ended(state):
            active_count += 1

    recent_activity = False
    try:
        last_turn_at = float(data.get("last_turn_at", 0))
        # The old global pulse cannot be attributed to a selected account.
        recent_activity = (
            allowed is None and data.get("version") != 2
            and 0 <= current_time - last_turn_at < ACTIVITY_PULSE_SECONDS
        )
    except (TypeError, ValueError):
        pass

    installed = data.get("installed") is True
    if allowed is not None:
        registered = data.get("profiles")
        installed = isinstance(registered, list) and any(
            home in registered and inspect_activity_hooks(Path(home), activity_path).configured
            for home in allowed
        )
    return CodexActivity(
        working=active_count > 0 or recent_activity,
        hooks_installed=installed,
        active_sessions=active_count,
    )
