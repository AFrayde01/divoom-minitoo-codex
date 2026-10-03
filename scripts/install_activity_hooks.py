#!/usr/bin/env python3
"""Set up, inspect, install, or remove Codex activity hooks for Divoom displays."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import pwd
import shlex
import shutil
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from divoom_minitoo_codex.activity import HOOK_EVENTS, inspect_activity_hooks
from divoom_minitoo_codex.terminal import TerminalUI

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
EVENTS = HOOK_EVENTS
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
        candidates.extend(sorted(app_profiles.glob("*/.codex")))

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        marker = str(resolved)
        if marker not in seen:
            seen.add(marker)
            unique.append(resolved)
    return unique


@contextmanager
def _locked_state(state_file: Path):
    """Use the same lock as the hook so installation preserves live activity."""
    lock_path = state_file.with_name(f"{state_file.name}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with lock_path.open("a", encoding="utf-8") as lock_file:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                state = {}
            if not isinstance(state, dict):
                state = {}
            yield state
            _atomic_write(state_file, json.dumps(state, indent=2) + "\n")
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def install(codex_home: Path, state_file: Path | None = None) -> None:
    codex_home = codex_home.expanduser().resolve()
    hooks_file = codex_home / "hooks.json"
    state_file = (state_file or ACTIVITY_FILE).expanduser().resolve()
    config = _read_config(hooks_file)
    original_config = json.dumps(config, sort_keys=True)
    hooks: dict[str, Any] = config["hooks"]
    _remove_our_hooks(hooks)
    command = (
        f"/usr/bin/python3 {shlex.quote(str(HOOK_SCRIPT))} "
        f"--state-file {shlex.quote(str(state_file))} "
        f"--codex-home {shlex.quote(str(codex_home))}"
    )
    for event_name in EVENTS:
        hooks.setdefault(event_name, []).append(
            {"hooks": [{"type": "command", "command": command, "timeout": 2}]}
        )

    changed = not hooks_file.exists() or json.dumps(config, sort_keys=True) != original_config
    if changed and hooks_file.exists():
        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup = hooks_file.with_name(f"hooks.json.backup-{stamp}")
        shutil.copy2(hooks_file, backup)
        print(f"Existing hooks backed up to {backup}")

    if changed:
        _atomic_write(hooks_file, json.dumps(config, indent=2) + "\n")
    with _locked_state(state_file) as state:
        state["installed"] = True
        if not isinstance(state.get("sessions"), dict):
            state["sessions"] = {}
        # Older records have no origin and cannot be attributed safely.
        state["sessions"] = {
            key: item for key, item in state["sessions"].items()
            if isinstance(item, dict) and isinstance(item.get("codex_home"), str)
        }
        state["version"] = 2
        state.pop("last_turn_at", None)
        profiles = state.get("profiles")
        if not isinstance(profiles, list):
            profiles = []
        profile = str(codex_home.expanduser().resolve())
        if profile not in profiles:
            profiles.append(profile)
        state["profiles"] = profiles
    print(f"MiniToo activity hooks {'installed' if changed else 'already configured'} in {hooks_file}.")
    print(f"Shared activity state: {state_file}")
    if changed:
        print("Review and trust the new hooks in Codex, then restart that Codex profile for activity tracking.")


def uninstall(codex_home: Path, state_file: Path | None = None) -> None:
    hooks_file = codex_home / "hooks.json"
    state_file = (state_file or ACTIVITY_FILE).expanduser().resolve()
    if hooks_file.exists():
        config = _read_config(hooks_file)
        _remove_our_hooks(config["hooks"])
        _atomic_write(hooks_file, json.dumps(config, indent=2) + "\n")
    with _locked_state(state_file) as state:
        profiles = state.get("profiles")
        if not isinstance(profiles, list):
            profiles = []
        profile = str(codex_home.expanduser().resolve())
        state["profiles"] = [item for item in profiles if item != profile]
        sessions = state.get("sessions")
        if isinstance(sessions, dict):
            state["sessions"] = {
                key: item for key, item in sessions.items()
                if not isinstance(item, dict) or item.get("codex_home") != profile
            }
        state["installed"] = bool(state["profiles"])
        if not state["installed"]:
            state["sessions"] = {}
    print(f"MiniToo activity hooks removed from {hooks_file}. Other hooks were preserved.")


def _profile_label(home: Path) -> str:
    home = home.expanduser().resolve()
    parall = (USER_HOME / "Library" / "Application Support" / "Parall").resolve()
    if home == (USER_HOME / ".codex").resolve():
        return "Codex · default profile"
    if home.name == ".codex" and home.parent.parent == parall:
        return f"Parall · {home.parent.name}"
    return f"Codex · {home.name if home.name != '.codex' else home.parent.name}"


def _setup_profiles(args: argparse.Namespace) -> list[Path]:
    if args.codex_home is not None:
        return [args.codex_home.expanduser().resolve()]
    profiles = discover_profiles()
    if args.all_profiles:
        return profiles
    terminal = TerminalUI()
    if not terminal.can_prompt:
        print("No interactive terminal detected; installing in all detected profiles.")
        print("Pass --codex-home PATH to install in one profile.")
        return profiles
    if not profiles:
        return []

    scope = terminal.choose(
        "Install Divoom activity hooks in",
        (("all", "All detected profiles (recommended)"), ("one", "One selected profile")),
        "all",
        show_values=False,
    )
    if scope == "all":
        return profiles

    options = tuple(
        (str(home), f"{_profile_label(home)} · {home}")
        for home in profiles
    )
    selected = terminal.choose("Select a Codex profile", options, options[0][0], show_values=False)
    return [Path(selected)]


def _show_trust_instructions(profiles: list[Path]) -> None:
    changed = [home for home in profiles if (home / "hooks.json").is_file()]
    print("\nNext, review and trust the Divoom hooks in each selected profile:")
    for home in changed:
        print(f"\n{_profile_label(home)}")
        print(f"  CODEX_HOME={shlex.quote(str(home))} codex")
        print("  In that CLI session, run /hooks and review/trust the Divoom hooks.")
        print("  Then restart that Codex or Parall instance.")
    print("\nCodex does not let the installer trust hooks automatically.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "setup", "uninstall", "status"), nargs="?", default="install")
    parser.add_argument("--codex-home", type=Path, help="Codex profile directory; defaults to CODEX_HOME or ~/.codex.")
    parser.add_argument("--all-profiles", action="store_true", help="Include the CLI and all detected Parall Codex profiles.")
    parser.add_argument("--state-file", type=Path, help="Shared activity file; use the same path for each profile.")
    args = parser.parse_args()
    try:
        if args.action == "setup":
            if args.codex_home is not None and args.all_profiles:
                raise RuntimeError("Choose either --codex-home PATH or --all-profiles for setup.")
            try:
                homes = _setup_profiles(args)
            except (EOFError, KeyboardInterrupt):
                print("\nSetup cancelled; no hooks were changed.")
                return 130
        else:
            homes = discover_profiles(args.codex_home) if args.all_profiles else [args.codex_home or CODEX_HOME]
        if not homes:
            raise RuntimeError("No Codex profiles found. Sign in or pass --codex-home PATH.")
        complete = True
        for home in homes:
            home = home.expanduser().resolve()
            if args.action == "status":
                status = inspect_activity_hooks(home, args.state_file)
                print(f"{'Configured' if status.configured else 'Needs attention'}: {home}")
                print(f"  {status.reason}")
                complete = complete and status.configured
            elif args.action in {"install", "setup"}:
                install(home, args.state_file)
            else:
                uninstall(home, args.state_file)
        if args.action == "setup" and complete:
            _show_trust_instructions(homes)
        if not complete:
            return 1
    except (OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
