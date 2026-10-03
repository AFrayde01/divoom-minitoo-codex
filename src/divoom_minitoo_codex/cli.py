"""CLI entry point."""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import shlex
import sys
import time
from contextlib import ExitStack, contextmanager
from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path

from .appserver import AccountAuthenticationError, AppServerError, CodexAppServer, UsageSnapshot
from .activity import ACTIVITY_FILE, inspect_activity_hooks, read_activity
from .bridge import MiniTooBridge, MiniTooError
from .diagnostics import PrivateRotatingFileHandler, default_log_path, private_log_directory, secure_existing_log
from .discovery import DiscoveryError, discover_devices, normalize_address
from .preferences import (
    load_preferences, save_preferences, load_language, save_language,
    load_account_profile, save_account_profile,
)
from .profiles import (
    ProfileError, account_choices, account_identity, account_label,
    discover_profiles, inspect_accounts, profile_name,
)
from .i18n import LANGUAGES, tr, translate_error
from .terminal import TerminalUI
from .minitoo_rgb import encode_rgb_animation
from .render import (
    ANIME_PALETTES,
    PORTRAIT_THEMES,
    THEMES,
    encode_for_minitoo,
    render_reset_credits,
    render_usage_frames,
)
from .timebox_mini import (
    TIMEBOX_COLORS,
    encode_timebox_rgb444,
    render_timebox_reset_credits,
    render_timebox_usage,
    render_timebox_working,
)

RESET_CREDITS_SCREEN_INTERVAL_SECONDS = 5 * 60
RESET_CREDITS_SCREEN_DURATION_SECONDS = 8
TIMEBOX_MINI_USAGE_PAGE_SECONDS = 10
TIMEBOX_MINI_WORKING_CYCLE_SECONDS = 10
TIMEBOX_MINI_WORKING_PERCENT_SECONDS = 2


def _default_bridge(device: str) -> Path:
    executable = "timebox-mini-bridge" if device == "timebox-mini" else "minitoo-bridge"
    return Path(__file__).resolve().parents[2] / "build" / executable


class _LocalizedParser(argparse.ArgumentParser):
    def __init__(self, *args: object, language: str = "en", **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.language = language
        if language == "es":
            self._positionals.title = "argumentos posicionales"
            self._optionals.title = "opciones"
            self._actions[0].help = tr("show this help message and exit", language)

    def format_usage(self) -> str:
        return super().format_usage().replace("usage: ", "uso: ", 1) if self.language == "es" else super().format_usage()

    def format_help(self) -> str:
        return super().format_help().replace("usage: ", "uso: ", 1) if self.language == "es" else super().format_help()

    def error(self, message: str) -> None:
        if self.language == "es":
            message = message.replace("unrecognized arguments:", "argumentos no reconocidos:")
            message = message.replace("argument ", "argumento ", 1).replace("invalid choice:", "opción no válida:")
            message = message.replace("choose from", "elige entre").replace("expected one argument", "requiere un valor")
            message = message.replace("invalid int value:", "entero no válido:")
        super().error(message)


def _parser(language: str = "en") -> argparse.ArgumentParser:
    t = lambda text, **values: tr(text, language, **values)
    parser = _LocalizedParser(
        language=language,
        prog="codex-minitoo",
        description=t("Display Codex usage limits on a Divoom MiniToo or TimeBox Mini."),
    )
    parser.add_argument("command", nargs="?", choices=("start",), default="start", help=t("Start the monitor (default)."))
    parser.add_argument("--language", "--lang", choices=tuple(LANGUAGES), default=None,
                        help=t("CLI and display language: en or es. Defaults to the saved choice, initially English."))
    parser.add_argument(
        "--address",
        default=os.environ.get("MINITOO_ADDRESS"),
        help=t("Optional Bluetooth MAC address (or MINITOO_ADDRESS); otherwise detect paired Divoom speakers."),
    )
    parser.add_argument(
        "--codex-bin",
        default=os.environ.get("CODEX_BIN", "codex"),
        help=t("Path to the Codex executable (or set CODEX_BIN)."),
    )
    parser.add_argument(
        "--codex-home",
        type=Path,
        help=t("Codex profile to monitor; overrides the account selector and saved choice."),
    )
    parser.add_argument(
        "--activity-scope", choices=("account", "all"), default="account",
        help=t("Activity: selected account's local profiles (default), or all installed profiles."),
    )
    parser.add_argument(
        "--device",
        choices=("minitoo", "timebox-mini"),
        default=None,
        help=t("Restrict detection to minitoo or timebox-mini. An explicit address without a model uses MiniToo."),
    )
    parser.add_argument("--bridge", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--port", type=int, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--interval", type=int, default=60, help=t("Refresh interval in seconds (default: 60)."))
    parser.add_argument(
        "--encoding", choices=("jpeg", "rgb"), default="rgb",
        help=t("MiniToo image encoding: lossless rgb/Zstandard (default) or jpeg. TimeBox Mini always uses RGB444."),
    )
    parser.add_argument(
        "--theme",
        choices=tuple(THEMES),
        default=None,
        help=t("MiniToo theme: {themes}. Defaults to the saved choice, initially neon. TimeBox Mini uses its compact layout.", themes=", ".join(THEMES)),
    )
    parser.add_argument(
        "--color",
        "-color",
        choices=tuple(dict.fromkeys((*TIMEBOX_COLORS, *ANIME_PALETTES))),
        default=None,
        help=t("Saved color or chosen palette. First use: cyan for TimeBox Mini, purple for MiniToo portraits."),
    )
    parser.add_argument("--once", action="store_true", help=t("Refresh the display once and exit."))
    parser.add_argument("--preview", type=Path, help=t("Save a preview image without using Bluetooth."))
    parser.add_argument(
        "--no-prompt", action="store_true",
        help=t("Start without the selection menus, using explicit options or saved choices."),
    )
    parser.add_argument(
        "--sent", choices=("compact", "detailed"), default="compact",
        help=t("Transfer output: compact updates one terminal row (default); detailed prints every sent update."),
    )
    parser.add_argument("--activity-file", type=Path, help=argparse.SUPPRESS)
    parser.add_argument(
        "--log-file", type=Path,
        help=t("Diagnostic log path (default: ~/Library/Logs/divoom-minitoo-codex/<device>-<port>.log; private, rotates at 1 MiB)."),
    )
    return parser


def _configure_account(args: argparse.Namespace, terminal: TerminalUI) -> None:
    t = terminal.tr
    prompt = terminal.can_prompt and not args.no_prompt and not args.once and not args.preview
    explicit = args.codex_home is not None
    args.codex_profile_aliases = ()
    args.codex_account_identity = None
    saved: Path | None = None
    environment_home: Path | None = None
    if explicit:
        home = args.codex_home.expanduser().resolve()
    else:
        try:
            saved = load_account_profile()
        except (OSError, ValueError) as exc:
            terminal.report(t("Could not read the saved Codex profile. {detail}", detail=exc), error=True)
            saved = None
        raw_environment_home = os.environ.get("CODEX_HOME")
        environment_home = Path(raw_environment_home).expanduser().resolve() if raw_environment_home else None
        if not prompt:
            home = environment_home or saved or (Path.home() / ".codex").resolve()
        else:
            profiles = discover_profiles(saved)
            if not profiles:
                raise ProfileError(t("No Codex profiles found. Sign in to Codex or provide --codex-home."))
            if saved is not None and not saved.is_dir():
                terminal.report(t("The saved Codex profile is no longer available. Choose another profile."), error=True)
                saved = None
            preferred = saved or environment_home or (Path.home() / ".codex").resolve()
            terminal.step(t("Finding Codex profiles and verifying usage access…"))
            accounts = inspect_accounts(
                profiles, args.codex_bin,
                on_profile=lambda profile: terminal.step(t(
                    "Checking usage access: {name}…", name=t(profile.name),
                )),
            )
            grouped = account_choices(accounts, preferred)
            choices = [choice for choice in grouped if choice.primary.usage_verified]
            for choice in grouped:
                if choice.primary.usage_verified:
                    continue
                item = choice.primary
                if isinstance(item.validation_error, AccountAuthenticationError):
                    reason = t("Authentication rejected (401); sign-in required")
                elif item.validation_error is not None:
                    reason = translate_error(str(item.validation_error), args.language)
                elif item.account is None:
                    reason = t("Not signed in")
                else:
                    reason = t("No ChatGPT usage limits")
                terminal.report(t("Omitted {name}: {reason}.", name=t(item.profile.name), reason=reason))
            if not choices:
                errors = [choice.primary.validation_error for choice in grouped]
                if errors and all(isinstance(error, AccountAuthenticationError) for error in errors):
                    raise errors[0]
                raise ProfileError(t("No Codex profile returned live usage. Sign in to Codex or retry after checking the connection."))
            terminal.report(t("Accounts with verified usage access: {count}.", count=len(choices)))
            options = tuple(
                (str(choice.primary.profile.home), account_label(choice.primary, args.language))
                for choice in choices
            )
            default = next(
                (str(choice.primary.profile.home) for choice in choices if any(
                    profile.home == preferred for profile in choice.profiles
                )),
                options[0][0],
            )
            if len(options) == 1:
                selected, label = options[0]
                terminal.report(label)
            else:
                selected = terminal.choose(t("Codex · account"), options, default, show_values=False)
            home = Path(selected)
            choice = next(choice for choice in choices if choice.primary.profile.home == home)
            args.codex_account_identity = account_identity(choice.primary.account)
            args.codex_profile_aliases = tuple(
                profile.home for profile in choice.profiles if profile.home != home
            )
    if not home.is_dir():
        if not explicit and not prompt and saved is None and environment_home is None:
            # Preserve Codex's implicit first-use behavior for its default home.
            args.codex_home = None
            args.codex_profile_name = t("Codex · default profile")
            return
        raise ProfileError(t(
            "Codex profile directory not found: {path}. Run ./start interactively or provide --codex-home.",
            path=home,
        ))
    args.codex_home = home
    args.codex_profile_name = t(profile_name(home))
    if explicit or not prompt:
        terminal.report(t("Codex profile: {name}", name=args.codex_profile_name))


def _report_activity_setup(args: argparse.Namespace, terminal: TerminalUI) -> None:
    """Check every detected app profile because activity is shared across them."""
    t = terminal.tr
    state_file = (args.activity_file or Path(os.environ.get("CODEX_MINITOO_ACTIVITY_FILE", ACTIVITY_FILE))).expanduser().resolve()
    extra_home = args.codex_home
    if extra_home is None:
        try:
            extra_home = load_account_profile()
        except (OSError, ValueError):
            # Account configuration reports an unreadable preference next.
            pass
    missing = False
    for profile in discover_profiles(extra_home):
        status = inspect_activity_hooks(profile.home, state_file)
        if not status.configured:
            missing = True
            terminal.report(t(
                "Activity hooks need attention in {name}: {reason}.",
                name=t(profile.name), reason=t(status.reason),
            ), error=True)
    if missing:
        installer = Path(__file__).resolve().parents[2] / "scripts/install_activity_hooks.py"
        if installer.is_file():
            command = (
                f"{shlex.quote(sys.executable)} {shlex.quote(str(installer))} install --all-profiles "
                f"--state-file {shlex.quote(str(state_file))}"
            )
            terminal.report(t("Hook installation command: {command}", command=command))
        else:
            terminal.report(t("Run scripts/install_activity_hooks.py install --all-profiles from the repository."))
        terminal.report(t("Review and trust the new hooks with /hooks in each affected profile, then restart that Parall instance."))


@contextmanager
def _connect_account(
    args: argparse.Namespace, report: Callable[..., None],
) -> Iterator[tuple[CodexAppServer, UsageSnapshot, Path | None]]:
    """On a startup 401, try only aliases with a freshly matching identity."""
    t = lambda text, **values: tr(text, args.language, **values)
    candidates = (args.codex_home, *args.codex_profile_aliases)
    last_auth_error: AccountAuthenticationError | None = None
    for index, home in enumerate(candidates):
        stack = ExitStack()
        try:
            codex = stack.enter_context(CodexAppServer(args.codex_bin, codex_home=home))
            if index:
                report(t("Trying another profile for the selected account: {name}.", name=t(profile_name(home))))
                identity = account_identity(codex.read_account())
                if identity is None or identity != args.codex_account_identity:
                    report(t("Skipping {name}: its account no longer matches the selected account.", name=t(profile_name(home))))
                    stack.close()
                    continue
            snapshot = codex.read_usage()
        except AccountAuthenticationError as exc:
            stack.close()
            last_auth_error = exc
            if index + 1 < len(candidates):
                report(t("Authentication rejected for {name}; trying a matching profile.", name=t(profile_name(home))), error=True)
            continue
        except AppServerError as exc:
            stack.close()
            if not index:
                raise
            report(t(
                "Could not use matching profile {name}. {detail}",
                name=t(profile_name(home)), detail=translate_error(str(exc), args.language),
            ), error=True)
            continue
        except BaseException:
            stack.close()
            raise
        try:
            yield codex, snapshot, home
        finally:
            stack.close()
        return
    if last_auth_error is not None:
        raise last_auth_error
    raise ProfileError(t("The selected account is no longer available. Restart ./start to select it again."))


def _resolve_device(args: argparse.Namespace, terminal: TerminalUI) -> None:
    t = terminal.tr
    if args.preview:
        args.device = args.device or "minitoo"
        return
    if args.address:
        args.address = normalize_address(args.address, args.language)
        args.device = args.device or "minitoo"
        return
    prompt = terminal.can_prompt and not args.no_prompt and not args.once
    while True:
        terminal.step(t("Finding paired Divoom speakers…"))
        try:
            devices = discover_devices(language=args.language)
            if args.device is not None:
                devices = [device for device in devices if device.model == args.device]
        except DiscoveryError as exc:
            if not prompt:
                raise
            terminal.report(str(exc), error=True)
            devices = []
        if devices:
            if len(devices) > 1:
                if not prompt:
                    raise DiscoveryError(
                        t("Several Divoom speakers are paired. Run ./start interactively to choose, or specify --device / --address.")
                    )
                options = tuple(
                    (device.address, f"{device.name} · {t('connected' if device.connected else 'paired, not connected')}")
                    for device in devices
                )
                address = terminal.choose(t("Divoom · speaker"), options, devices[0].address)
                selected = next(device for device in devices if device.address == address)
            else:
                selected = devices[0]
                terminal.report(t("Detected {name} ({state}).", name=selected.name, state=t("connected" if selected.connected else "paired, not connected")))
            args.address = selected.address
            args.device = selected.model
            return
        message = t(
            "No supported paired Divoom speaker found{model}. Turn it on, enable Bluetooth and pair it in macOS Bluetooth settings.",
            model=t(" for {device}", device=args.device) if args.device is not None else "",
        )
        if not prompt:
            raise DiscoveryError(message + t(" You can also provide --address and --device."))
        terminal.report(message)
        action = terminal.choose(
            t("Connection · next step"),
            (("retry", t("Refresh paired speakers")), ("manual", t("Enter a Bluetooth address"))),
            "retry",
        )
        if action == "manual":
            if args.device is None:
                args.device = terminal.choose(
                    t("Divoom · model"),
                    (("minitoo", "MiniToo TFT"), ("timebox-mini", "TimeBox Mini 11 × 11")),
                    "minitoo",
                )
            while True:
                try:
                    args.address = normalize_address(terminal.ask(t("Bluetooth address")), args.language)
                    return
                except DiscoveryError as exc:
                    terminal.report(str(exc), error=True)


def _configure_display(args: argparse.Namespace, terminal: TerminalUI) -> None:
    t = terminal.tr
    try:
        saved = load_preferences(args.device)
    except (OSError, ValueError) as exc:
        terminal.report(t("Could not read saved display choices; using defaults. {detail}", detail=exc), error=True)
        saved = {}
    prompt = terminal.can_prompt and not args.no_prompt and not args.once and not args.preview

    if args.device == "timebox-mini":
        if args.theme is not None and args.theme != "neon":
            terminal.report(
                t("TimeBox Mini supports only its compact default theme; ignoring --theme {theme}.", theme=args.theme),
                error=True,
            )
        theme = "neon"
        colors = tuple(TIMEBOX_COLORS)
        default_color = "cyan"
    else:
        theme = args.theme or saved.get("theme", "neon")
        if theme not in THEMES:
            theme = "neon"
        if prompt and args.theme is None:
            theme = terminal.choose(t("MiniToo · theme"), tuple((value, t(label)) for value, label in THEMES.items()), theme)
        colors = tuple(ANIME_PALETTES) if theme in PORTRAIT_THEMES else ()
        default_color = "purple"

    color = args.color if args.color is not None else saved.get("color")
    if color is not None and color not in colors:
        if args.color is not None:
            fallback = t("the default {color} palette", color=t(default_color)) if colors else t("its default colors")
            theme_name = theme if args.device == "minitoo" else "TimeBox Mini"
            terminal.report(
                t("The {theme} theme does not support --color {color}; using {fallback}.", theme=theme_name, color=color, fallback=fallback),
                error=True,
            )
        color = None
    if colors:
        color = color or default_color
        if prompt and args.color is None:
            name = "TimeBox Mini" if args.device == "timebox-mini" else "MiniToo"
            color = terminal.choose(t("{name} · color", name=name), tuple((value, t(value)) for value in colors), color)
    elif prompt and args.theme is None:
        terminal.report(t("The {theme} theme uses its own fixed palette.", theme=theme))
    args.theme = theme
    args.color = color
    if not args.once and not args.preview:
        try:
            save_preferences(args.device, theme=theme, color=color)
        except OSError as exc:
            terminal.report(t("Could not save display choices; this monitor will still run. {detail}", detail=exc), error=True)


def main() -> int:
    # Resolve language before parsing so --help and validation use it too.
    language_error = None
    try:
        saved_language = load_language()
    except (OSError, ValueError) as exc:
        saved_language, language_error = "en", exc
    parser_language = saved_language
    for index, argument in enumerate(sys.argv[1:], start=1):
        if argument == "--":
            break
        if argument in ("--language", "--lang") and index + 1 < len(sys.argv):
            value = sys.argv[index + 1]
        elif argument.startswith(("--language=", "--lang=")):
            value = argument.split("=", 1)[1]
        else:
            continue
        if value in LANGUAGES:
            parser_language = value
    args = _parser(parser_language).parse_args()
    explicit_language = args.language is not None
    args.language = args.language or saved_language
    t = lambda text, **values: tr(text, args.language, **values)
    if args.interval < 10:
        print(t("The minimum refresh interval is 10 seconds."), file=sys.stderr)
        return 2
    if args.port is not None and not 1 <= args.port <= 65_535:
        print(t("The local bridge port must be between 1 and 65535."), file=sys.stderr)
        return 2

    bridge: MiniTooBridge | None = None
    previous_digest: str | None = None
    next_display_retry: float | None = None
    display_failures = 0
    logger: logging.Logger | None = None
    log_handler: PrivateRotatingFileHandler | None = None
    terminal = TerminalUI(sent=args.sent, language=args.language)

    def report(
        message: str,
        *,
        error: bool = False,
        update: bool = False,
        compact_message: str | None = None,
    ) -> None:
        if update:
            terminal.update(message, compact_message=compact_message)
        else:
            terminal.report(message, error=error)
        if logger is not None:
            logger.log(logging.ERROR if error else logging.INFO, message)

    try:
        if language_error is not None:
            report(t("Could not read saved language. {detail}", detail=language_error), error=True)
        if terminal.can_prompt and not args.no_prompt and not args.once and not args.preview and not explicit_language:
            args.language = terminal.choose("Language / Idioma", tuple(LANGUAGES.items()), args.language)
            terminal.language = args.language
        if not args.once and not args.preview:
            try:
                save_language(args.language)
            except OSError as exc:
                report(t("Could not save language; this monitor will still run. {detail}", detail=exc), error=True)
        if not args.preview:
            _report_activity_setup(args, terminal)
        _configure_account(args, terminal)
        _resolve_device(args, terminal)
        _configure_display(args, terminal)
        if not args.preview:
            default_port = 40585 if args.device == "timebox-mini" else 40584
            bridge_port = args.port if args.port is not None else default_port
            log_path = (args.log_file or default_log_path(args.device, bridge_port)).expanduser().absolute()
            if args.log_file is None:
                private_log_directory(log_path.parent)
            # Protect diagnostics left by older releases as well as new logs.
            if args.log_file is None and args.bridge is None:
                legacy_path = _default_bridge(args.device).parent / f"{args.device}-{bridge_port}.log"
                for suffix in ("", ".1", ".2"):
                    secure_existing_log(Path(f"{legacy_path}{suffix}"))
            logger = logging.Logger("divoom-monitor", level=logging.INFO)
            log_handler = PrivateRotatingFileHandler(log_path)
            log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            logger.addHandler(log_handler)
            terminal.startup(
                device="TimeBox Mini" if args.device == "timebox-mini" else "MiniToo",
                theme="compact" if args.device == "timebox-mini" else args.theme,
                color=args.color or ("cyan" if args.device == "timebox-mini" else "purple" if args.theme in PORTRAIT_THEMES else "default"),
                interval=args.interval,
                log_path=str(log_path),
                encoding="RGB444" if args.device == "timebox-mini" else "RGB888 / Zstandard" if args.encoding == "rgb" else "JPEG",
                profile=args.codex_profile_name,
            )
            if not terminal.interactive:
                report(t("Diagnostic log: {path}", path=log_path))
            logger.info("Monitor starting: device=%s theme=%s port=%s", args.device, args.theme, bridge_port)
            terminal.step(t("Connecting to Codex and reading account usage…"))
        with _connect_account(args, report) as (codex, snapshot, selected_home):
            account_homes = tuple(dict.fromkeys((
                selected_home or (Path.home() / ".codex").resolve(),
                *args.codex_profile_aliases,
            )))
            activity_homes = account_homes if args.activity_scope == "account" else None
            if selected_home != args.codex_home:
                args.codex_home = selected_home
                args.codex_profile_name = t(profile_name(selected_home))
                report(t("Using matching Codex profile: {name}.", name=args.codex_profile_name))
            if not args.preview:
                report(t(
                    "Activity follows the selected account's local profiles."
                    if activity_homes is not None else "Activity follows all installed local profiles."
                ))
                bridge_path = args.bridge or _default_bridge(args.device)
                default_port = 40585 if args.device == "timebox-mini" else 40584
                bridge_port = args.port if args.port is not None else default_port
                bridge = MiniTooBridge(
                    bridge_path,
                    args.address,
                    bridge_port,
                    display_name="TimeBox Mini" if args.device == "timebox-mini" else "MiniToo",
                    logger=logger,
                )
                if args.device == "minitoo" and args.encoding == "rgb":
                    bridge.frame_encoding = "rgb-zstd"
                    report(t("MiniToo encoding: lossless RGB888/Zstandard at 160x128."))
                device_name = "TimeBox Mini" if args.device == "timebox-mini" else "MiniToo"
                report(t("Monitoring {device} at {address}; reading Codex usage every {interval}s.", device=device_name, address=args.address, interval=args.interval))

            if not args.once and not args.preview and args.codex_home is not None:
                try:
                    save_account_profile(args.codex_home)
                except OSError as exc:
                    report(t("Could not save the Codex profile; this monitor will still run. {detail}", detail=exc), error=True)
            if not args.preview:
                terminal.step(t("Usage received. Connecting to the authenticated Bluetooth bridge…"))
            next_usage_read = time.monotonic() + args.interval
            next_reset_screen = time.monotonic() + RESET_CREDITS_SCREEN_INTERVAL_SECONDS
            reset_screen_until: float | None = None
            previous_activity_state: tuple[bool, bool] | None = None
            previous_screen_mode = "usage"
            timebox_usage_page = "bars"
            next_timebox_usage_page = time.monotonic() + TIMEBOX_MINI_USAGE_PAGE_SECONDS
            previous_timebox_view: str | None = None
            timebox_working_started_at: float | None = None
            while True:
                activity = read_activity(args.activity_file, codex_homes=activity_homes)
                activity_state = (activity.working, activity.hooks_installed)
                turn_finished = (
                    previous_activity_state is not None
                    and previous_activity_state[0]
                    and not activity.working
                )
                refreshed = time.monotonic() >= next_usage_read or turn_finished
                if refreshed:
                    snapshot = codex.read_usage()
                    next_usage_read = time.monotonic() + args.interval

                loop_time = time.monotonic()
                was_working = previous_activity_state is not None and previous_activity_state[0]
                timebox_working_percent = False
                timebox_animation_frame = 0
                if args.device == "timebox-mini":
                    if activity.working:
                        if not was_working or timebox_working_started_at is None:
                            timebox_working_started_at = loop_time
                        working_elapsed = loop_time - timebox_working_started_at
                        working_phase = working_elapsed % TIMEBOX_MINI_WORKING_CYCLE_SECONDS
                        timebox_working_percent = (
                            working_phase
                            >= TIMEBOX_MINI_WORKING_CYCLE_SECONDS - TIMEBOX_MINI_WORKING_PERCENT_SECONDS
                        )
                        timebox_animation_frame = int(working_phase) % 8
                    else:
                        if was_working:
                            timebox_usage_page = "bars"
                            next_timebox_usage_page = loop_time + TIMEBOX_MINI_USAGE_PAGE_SECONDS
                        timebox_working_started_at = None

                if reset_screen_until is not None and loop_time >= reset_screen_until:
                    reset_screen_until = None
                if snapshot.reset_credits.available_count <= 0:
                    reset_screen_until = None
                if reset_screen_until is None and loop_time >= next_reset_screen:
                    next_reset_screen = loop_time + RESET_CREDITS_SCREEN_INTERVAL_SECONDS
                    if snapshot.reset_credits.available_count > 0:
                        reset_screen_until = loop_time + RESET_CREDITS_SCREEN_DURATION_SECONDS

                screen_mode = "reset-credits" if reset_screen_until is not None else "usage"
                screen_changed = screen_mode != previous_screen_mode
                timebox_view_changed = False
                timebox_view = "bars"
                if args.device == "timebox-mini":
                    if screen_mode == "reset-credits":
                        timebox_view = "reset-credits"
                    elif activity.working:
                        timebox_view = "nearest-percent" if timebox_working_percent else "working-animation"
                    else:
                        if screen_changed:
                            timebox_usage_page = "bars"
                            next_timebox_usage_page = loop_time + TIMEBOX_MINI_USAGE_PAGE_SECONDS
                        elif loop_time >= next_timebox_usage_page:
                            timebox_usage_page = "nearest-percent" if timebox_usage_page == "bars" else "bars"
                            next_timebox_usage_page = loop_time + TIMEBOX_MINI_USAGE_PAGE_SECONDS
                        timebox_view = timebox_usage_page
                    timebox_view_changed = timebox_view != previous_timebox_view

                timebox_animation_changed = (
                    args.device == "timebox-mini"
                    and screen_mode == "usage"
                    and timebox_view == "working-animation"
                    and not args.once
                    and not args.preview
                )

                if (
                    args.preview
                    or refreshed
                    or activity_state != previous_activity_state
                    or screen_changed
                    or timebox_view_changed
                    or timebox_animation_changed
                    or (next_display_retry is not None and loop_time >= next_display_retry)
                ):
                    if screen_mode == "reset-credits":
                        if args.device == "timebox-mini":
                            images = (render_timebox_reset_credits(
                                snapshot,
                                color=args.color,
                            ),)
                        else:
                            images = (render_reset_credits(
                                snapshot,
                                activity,
                                theme=args.theme,
                                anime_color=args.color or "purple",
                                language=args.language,
                            ),)
                    elif args.device == "timebox-mini" and timebox_view == "working-animation":
                        images = (render_timebox_working(
                            color=args.color,
                            animation_frame=timebox_animation_frame,
                        ),)
                    elif args.device == "timebox-mini":
                        images = (render_timebox_usage(
                            snapshot,
                            now=datetime.now().astimezone(),
                            color=args.color,
                            view=timebox_view,
                        ),)
                    else:
                        images = render_usage_frames(
                            snapshot,
                            now=datetime.now().astimezone(),
                            activity=activity,
                            theme=args.theme,
                            anime_color=args.color or "purple",
                            language=args.language,
                        )
                    if args.preview:
                        args.preview.parent.mkdir(parents=True, exist_ok=True)
                        images[0].save(args.preview)
                        print(t("Preview saved to {path}", path=args.preview))
                        return 0

                    if len(images) > 1:
                        if args.theme in PORTRAIT_THEMES:
                            animation_speed = 600
                        elif args.theme == "pixel-art" and not activity.working:
                            animation_speed = 800
                        else:
                            animation_speed = 400
                    else:
                        animation_speed = 1000 if args.device == "minitoo" and args.encoding == "rgb" else 0
                    if args.device == "timebox-mini":
                        frames = [encode_timebox_rgb444(images[0])]
                    elif args.encoding == "rgb":
                        frames = [encode_rgb_animation(images, speed_ms=animation_speed)]
                    else:
                        jpeg_quality = {"anime": 92, "pixel-art": 98, "anime-pixel": 98, "anime-pixel-chibi": 98, "anime-pixel-detail": 98}.get(args.theme, 88)
                        frames = [
                            encode_for_minitoo(
                                image,
                                quality=jpeg_quality,
                                pixel_art=args.theme == "pixel-art" or (args.theme in PORTRAIT_THEMES and args.theme != "anime"),
                                preserve_detail=args.theme in PORTRAIT_THEMES,
                            )
                            for image in images
                        ]
                    digest = hashlib.sha256(b"\0".join(frames)).hexdigest()
                    if digest != previous_digest and (
                        next_display_retry is None or loop_time >= next_display_retry
                    ):
                        assert bridge is not None
                        try:
                            result = bridge.send_frames_with_recovery(
                                frames,
                                speed_ms=animation_speed,
                                require_ack=args.device == "minitoo",
                            )
                        except MiniTooError as exc:
                            if args.once:
                                raise
                            display_failures += 1
                            retry_delay = min(60, 5 * (2 ** min(display_failures - 1, 4)))
                            next_display_retry = time.monotonic() + retry_delay
                            # A failed transfer can replace the old screen with
                            # loading; no cached digest is now safe to reuse.
                            previous_digest = None
                            report(t("{detail} Retrying the current screen in {seconds}s.", detail=translate_error(str(exc), args.language), seconds=retry_delay), error=True)
                            previous_activity_state = activity_state
                            previous_screen_mode = screen_mode
                            previous_timebox_view = timebox_view
                            time.sleep(1)
                            continue
                        next_display_retry = None
                        display_failures = 0
                        activity_label = t("working" if activity.working else "idle" if activity.hooks_installed else "hooks not installed")
                        update_label = t("Display updated after reconnect" if result.get("reconnected") else "Display updated")
                        if screen_mode == "reset-credits":
                            view_label = t("reset credits")
                        elif args.device == "timebox-mini" and timebox_view == "working-animation":
                            view_label = t("working animation")
                        elif args.device == "timebox-mini" and timebox_view == "nearest-percent":
                            view_label = t("remaining percentage")
                        else:
                            view_label = t("usage")
                        transfer_message = t(str(result.get("message", "ok")))
                        compact_usage = " / ".join(
                            f"{window.label} {100 - window.used_percent}%" for window in snapshot.windows
                        )
                        compact_usage = t("{usage} left", usage=compact_usage) if compact_usage else t("usage unavailable")
                        compact_transfer = t("{message}, reconnected", message=transfer_message) if result.get("reconnected") else transfer_message
                        report(
                            t("{update}: {usage}; Codex {activity}; showing {view} ({transfer}).",
                              update=update_label,
                              usage=", ".join(t("{label} {percent}% left", label=window.label, percent=100 - window.used_percent) for window in snapshot.windows),
                              activity=activity_label, view=view_label, transfer=transfer_message),
                            update=True,
                            compact_message=f"{compact_usage} | Codex {activity_label} | {view_label} | {compact_transfer}",
                        )
                        previous_digest = digest
                    previous_activity_state = activity_state
                    previous_screen_mode = screen_mode
                    previous_timebox_view = timebox_view
                if args.once:
                    return 0

                remaining = next_usage_read - time.monotonic()
                if remaining > 0:
                    # Check activity each second; read usage on the configured interval.
                    time.sleep(min(1, remaining))
    except AccountAuthenticationError as exc:
        home = exc.codex_home or args.codex_home or (Path.home() / ".codex").resolve()
        report(t(
            "Codex rejected authentication for {name} (401). Sign in again to this profile, then restart the monitor.",
            name=t(profile_name(home)),
        ), error=True)
        report(t("Codex profile directory: {path}", path=home))
        command = f"CODEX_HOME={shlex.quote(str(home))} {shlex.quote(args.codex_bin)} login"
        report(t("Sign-in command: {command}", command=command))
        if logger is not None:
            logger.error("%s", exc)
        return 1
    except (AppServerError, MiniTooError, DiscoveryError, ProfileError, OSError) as exc:
        report(translate_error(str(exc), args.language), error=True)
        return 1
    except EOFError:
        report(t("Selection input closed. Use --no-prompt to start with saved choices."), error=True)
        return 2
    except KeyboardInterrupt:
        report(t("Monitor stopped."))
        return 0
    finally:
        if bridge is not None:
            bridge.close()
        if log_handler is not None:
            log_handler.close()
        terminal.finish()


if __name__ == "__main__":
    raise SystemExit(main())
