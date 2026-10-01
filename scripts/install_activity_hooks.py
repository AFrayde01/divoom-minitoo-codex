#!/usr/bin/env python3
"""Install or remove user-level Codex hooks for MiniToo activity status."""

from __future__ import annotations

import argparse
import json
import os
import pwd
import shlex
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

try:
    USER_HOME = Path(pwd.getpwuid(os.getuid()).pw_dir)
except (KeyError, OSError):
    USER_HOME = Path.home()
CODEX_HOME = Path(os.environ.get("CODEX_HOME", USER_HOME / ".codex")).expanduser()
ACTIVITY_FILE = Path(
    os.environ.get(
        "CODEX_MINITOO_ACTIVITY_FILE",
        USER_HOME / ".codex" / "divoom-minitoo-codex-activity.json",
    )
).expanduser()
HOOK_SCRIPT = Path(__file__).resolve().with_name("minitoo_activity_hook.py")
EVENTS = ("SessionStart", "UserPromptSubmit", "Stop", "Interrupt", "SessionEnd")
MARKER = HOOK_SCRIPT.name


def _read_config(hooks_file: Path) -> dict[str, Any]:
    if not hooks_file.exists():
        return {"hooks": {}}
    try:
        value = json.loads(hooks_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"Could not parse {hooks_file}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected a JSON object in {hooks_file}.")
    hooks = value.get("hooks")
    if hooks is None:
        value["hooks"] = {}
    elif not isinstance(hooks, dict):
        raise RuntimeError(f"Expected a 'hooks' object in {hooks_file}.")
    return value


def _remove_our_hooks(hooks: dict[str, Any]) -> None:
    for event_name, groups in list(hooks.items()):
        if not isinstance(groups, list):
            continue
        kept_groups = []
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                kept_groups.append(group)
                continue
            handlers = [
                handler
                for handler in group["hooks"]
                if not isinstance(handler, dict)
                or MARKER not in str(handler.get("command", ""))
            ]
            if handlers:
                updated_group = dict(group)
                updated_group["hooks"] = handlers
                kept_groups.append(updated_group)
        if kept_groups:
            hooks[event_name] = kept_groups
        else:
            hooks.pop(event_name, None)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def discover_profiles(explicit_home: Path | None = None) -> list[Path]:
    candidates = [USER_HOME / ".codex"]
    if os.environ.get("CODEX_HOME"):
        candidates.append(Path(os.environ["CODEX_HOME"]).expanduser())
    if explicit_home is not None:
        candidates.append(explicit_home.expanduser())
    current_home_profile = Path.home() / ".codex"
    if current_home_profile.exists():
        candidates.append(current_home_profile)

    app_profiles = USER_HOME / "Library" / "Application Support" / "Parall"
    if app_profiles.is_dir():
        candidates.extend(sorted(app_profiles.glob("ChatGPT*/.codex")))

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        marker = str(resolved)
        if marker not in seen:
            seen.add(marker)
            unique.append(resolved)
    return unique


def install(codex_home: Path, state_file: Path | None = None) -> None:
    hooks_file = codex_home / "hooks.json"
    state_file = (state_file or ACTIVITY_FILE).expanduser()
    config = _read_config(hooks_file)
    hooks: dict[str, Any] = config["hooks"]
    _remove_our_hooks(hooks)
    command = (
        f"/usr/bin/python3 {shlex.quote(str(HOOK_SCRIPT))} "
        f"--state-file {shlex.quote(str(state_file))}"
    )
    for event_name in EVENTS:
        hooks.setdefault(event_name, []).append(
            {"hooks": [{"type": "command", "command": command, "timeout": 2}]}
        )

    if hooks_file.exists():
        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup = hooks_file.with_name(f"hooks.json.backup-{stamp}")
        shutil.copy2(hooks_file, backup)
        print(f"Existing hooks backed up to {backup}")

    _atomic_write(hooks_file, json.dumps(config, indent=2) + "\n")
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        state = {}
    if not isinstance(state, dict):
        state = {}
    state["installed"] = True
    if not isinstance(state.get("sessions"), dict):
        state["sessions"] = {}
    profiles = state.get("profiles")
    if not isinstance(profiles, list):
        profiles = []
    profile = str(codex_home.expanduser().resolve())
    if profile not in profiles:
        profiles.append(profile)
    state["profiles"] = profiles
    _atomic_write(state_file, json.dumps(state, indent=2) + "\n")
    print(f"MiniToo activity hooks installed in {hooks_file}.")
    print(f"Shared activity state: {state_file}")
    print("Review and trust the new hooks in Codex, then restart that Codex profile for activity tracking.")


def uninstall(codex_home: Path, state_file: Path | None = None) -> None:
    hooks_file = codex_home / "hooks.json"
    state_file = (state_file or ACTIVITY_FILE).expanduser()
    if hooks_file.exists():
        config = _read_config(hooks_file)
        _remove_our_hooks(config["hooks"])
        _atomic_write(hooks_file, json.dumps(config, indent=2) + "\n")
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        state = {}
    if not isinstance(state, dict):
        state = {}
    profiles = state.get("profiles")
    if not isinstance(profiles, list):
        profiles = []
    profile = str(codex_home.expanduser().resolve())
    state["profiles"] = [item for item in profiles if item != profile]
    state["installed"] = bool(state["profiles"])
    if not state["installed"]:
        state["sessions"] = {}
    _atomic_write(state_file, json.dumps(state, indent=2) + "\n")
    print(f"MiniToo activity hooks removed from {hooks_file}. Other hooks were preserved.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "uninstall"), nargs="?", default="install")
    parser.add_argument("--codex-home", type=Path, help="Codex profile directory; defaults to CODEX_HOME or ~/.codex.")
    parser.add_argument("--all-profiles", action="store_true", help="Install in the CLI and detected Codex App profiles.")
    parser.add_argument("--state-file", type=Path, help="Shared activity file; use the same path for each profile.")
    args = parser.parse_args()
    try:
        if args.all_profiles:
            homes = discover_profiles(args.codex_home)
            for home in homes:
                install(home, args.state_file) if args.action == "install" else uninstall(home, args.state_file)
        else:
            home = args.codex_home or CODEX_HOME
            install(home, args.state_file) if args.action == "install" else uninstall(home, args.state_file)
    except (OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
