"""Discover local Codex profiles and verify their account and usage access."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .activity import USER_HOME
from .appserver import AppServerError, CodexAccount, CodexAppServer
from .i18n import tr


PROFILE_LOOKUP_TIMEOUT_SECONDS = 12.0


class ProfileError(RuntimeError):
    pass


@dataclass(frozen=True)
class CodexProfile:
    home: Path
    name: str


@dataclass(frozen=True)
class ProfileAccount:
    profile: CodexProfile
    account: CodexAccount | None = None
    lookup_failed: bool = False
    usage_verified: bool = False
    validation_error: Exception | None = field(default=None, repr=False)


@dataclass(frozen=True)
class AccountChoice:
    primary: ProfileAccount
    profiles: tuple[CodexProfile, ...]


def profile_name(home: Path) -> str:
    home = home.expanduser().resolve()
    parall = (USER_HOME / "Library/Application Support/Parall").resolve()
    if home.name == ".codex" and home.parent.parent == parall:
        name = f"Parall · {home.parent.name}"
    elif home == (USER_HOME / ".codex").resolve():
        name = "Codex · default profile"
    elif home == (Path.home() / ".codex").resolve():
        name = "Codex · current profile"
    else:
        name = f"Codex · {home.parent.name if home.name == '.codex' else home.name}"
    return "".join(character for character in name if character.isprintable())


def discover_profiles(extra_home: Path | None = None) -> list[CodexProfile]:
    """List existing directories, including Parall instances that are closed."""
    candidates = [USER_HOME / ".codex", Path.home() / ".codex"]
    if os.environ.get("CODEX_HOME"):
        candidates.append(Path(os.environ["CODEX_HOME"]))
    if extra_home is not None:
        candidates.append(extra_home)
    parall = USER_HOME / "Library/Application Support/Parall"
    if parall.is_dir():
        candidates.extend(sorted(parall.glob("*/.codex")))
    profiles: dict[Path, CodexProfile] = {}
    for candidate in candidates:
        home = candidate.expanduser().resolve()
        if home.is_dir():
            profiles.setdefault(home, CodexProfile(home, profile_name(home)))
    return list(profiles.values())


def _inspect_profile(profile: CodexProfile, executable: str) -> ProfileAccount:
    account = None
    try:
        with CodexAppServer(
            executable, timeout=PROFILE_LOOKUP_TIMEOUT_SECONDS, codex_home=profile.home,
        ) as server:
            account = server.read_account()
            if account is None or account.auth_type != "chatgpt":
                return ProfileAccount(profile, account)
            snapshot = server.read_usage()
            if snapshot.account_email and account.email and snapshot.account_email.casefold() != account.email.casefold():
                raise AppServerError("The Codex profile's account changed while checking usage. Restart ./start.")
            return ProfileAccount(profile, account, usage_verified=True)
    except (AppServerError, OSError, subprocess.SubprocessError) as exc:
        # Keep failed checks for diagnostics, never as verified menu options.
        return ProfileAccount(profile, account, lookup_failed=account is None, validation_error=exc)


def inspect_accounts(
    profiles: list[CodexProfile], executable: str,
    *, on_profile: Callable[[CodexProfile], None] | None = None,
) -> list[ProfileAccount]:
    """Verify usage serially to avoid simultaneous refreshes in cloned profiles."""
    accounts = []
    for profile in profiles:
        if on_profile is not None:
            on_profile(profile)
        accounts.append(_inspect_profile(profile, executable))
    return accounts


def account_identity(account: CodexAccount | None) -> tuple[str, str] | None:
    if account is None or account.auth_type != "chatgpt" or not account.email:
        return None
    return account.email.casefold(), (account.plan_type or "").casefold()


def account_choices(
    accounts: list[ProfileAccount], preferred_home: Path | None = None,
) -> list[AccountChoice]:
    """Group matching account labels while preserving their profile aliases."""
    has_chatgpt = any(
        not item.lookup_failed and item.account is not None and item.account.auth_type == "chatgpt"
        for item in accounts
    )
    groups: dict[tuple[str, ...], list[ProfileAccount]] = {}
    for item in accounts:
        account = item.account
        if has_chatgpt and not item.lookup_failed and (account is None or account.auth_type != "chatgpt"):
            continue
        identity = account_identity(account)
        if not item.lookup_failed and identity is not None:
            # Include the plan: the same email can have different subscriptions.
            key = ("chatgpt", *identity)
        else:
            # A missing identity or failed lookup cannot establish a duplicate.
            key = ("profile", str(item.profile.home))
        groups.setdefault(key, []).append(item)

    parall = (USER_HOME / "Library/Application Support/Parall").resolve()
    default_home = (USER_HOME / ".codex").resolve()

    def rank(item: ProfileAccount) -> tuple[bool, bool, int, str]:
        home = item.profile.home
        instance = home.parent.name.casefold()
        if home.name == ".codex" and home.parent.parent == parall:
            priority = 0 if instance == "codex" or instance.startswith("codex ") else 3
        elif home == default_home:
            priority = 1
        else:
            priority = 2
        # Live usage access comes before a saved directory or an app name.
        return not item.usage_verified, home != preferred_home, priority, str(home)

    choices = []
    for group in groups.values():
        members = sorted(group, key=rank)
        choices.append(AccountChoice(members[0], tuple(item.profile for item in members)))
    return choices


def account_label(item: ProfileAccount, language: str = "en") -> str:
    parts = [tr(item.profile.name, language)]
    if item.lookup_failed:
        parts.append(tr("Account unavailable", language))
    elif item.account is None:
        parts.append(tr("Not signed in", language))
    elif item.account.auth_type != "chatgpt":
        parts.append(tr("No ChatGPT usage limits", language))
    else:
        if item.account.plan_type:
            parts.append(f"PLAN {item.account.plan_type.upper()}")
        if item.account.email:
            email = item.account.email.upper()
            parts.append(email if len(email) <= 36 else email[:33] + "...")
    return " · ".join(parts)
