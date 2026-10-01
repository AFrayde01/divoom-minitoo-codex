"""CLI entry point."""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from .appserver import AppServerError, CodexAppServer
from .activity import read_activity
from .bridge import MiniTooBridge, MiniTooError
from .diagnostics import PrivateRotatingFileHandler, default_log_path, private_log_directory, secure_existing_log
from .terminal import TerminalUI
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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-minitoo",
        description="Display Codex usage limits on a Divoom MiniToo or TimeBox Mini.",
    )
    parser.add_argument(
        "--address",
        default=os.environ.get("MINITOO_ADDRESS"),
        help="Divoom Bluetooth MAC address (or set MINITOO_ADDRESS).",
    )
    parser.add_argument(
        "--codex-bin",
        default=os.environ.get("CODEX_BIN", "codex"),
        help="Path to the Codex executable (or set CODEX_BIN).",
    )
    parser.add_argument(
        "--codex-home",
        type=Path,
        help="Codex profile whose sign-in and usage limits should be queried.",
    )
    parser.add_argument(
        "--device",
        choices=("minitoo", "timebox-mini"),
        default="minitoo",
        help="Divoom model: minitoo (default) or timebox-mini.",
    )
    parser.add_argument("--bridge", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--port", type=int, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--interval", type=int, default=60, help="Refresh interval in seconds (default: 60).")
    parser.add_argument(
        "--theme",
        choices=tuple(THEMES),
        default="neon",
        help="MiniToo theme: neon, pixel-art, anime, anime-pixel, or anime-pixel-chibi. TimeBox Mini always uses its compact default layout.",
    )
    parser.add_argument(
        "--color",
        "-color",
        choices=tuple(dict.fromkeys((*TIMEBOX_COLORS, *ANIME_PALETTES))),
        default=None,
        help="TimeBox Mini accent (cyan by default, purple, red, blue, green) or MiniToo portrait theme color.",
    )
    parser.add_argument("--once", action="store_true", help="Refresh the display once and exit.")
    parser.add_argument("--preview", type=Path, help="Save a preview image without using Bluetooth.")
    parser.add_argument("--activity-file", type=Path, help=argparse.SUPPRESS)
    parser.add_argument(
        "--log-file", type=Path,
        help="Diagnostic log path (default: ~/Library/Logs/divoom-minitoo-codex/<device>-<port>.log; private, rotates at 1 MiB).",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.device == "timebox-mini":
        if args.theme != "neon":
            print(
                f"TimeBox Mini supports only its compact default theme; ignoring --theme {args.theme}.",
                file=sys.stderr,
            )
        if args.color is not None and args.color not in TIMEBOX_COLORS:
            print(
                f"TimeBox Mini does not support --color {args.color}; using the default cyan accent.",
                file=sys.stderr,
            )
            args.color = None
    elif args.color is not None and args.theme not in PORTRAIT_THEMES:
        print(f"The {args.theme} theme does not support --color; using its default colors.", file=sys.stderr)
        args.color = None
    elif args.color is not None and args.color not in ANIME_PALETTES:
        print(f"The {args.theme} theme does not support --color {args.color}; using the default purple palette.", file=sys.stderr)
        args.color = None
    if args.interval < 10:
        print("The minimum refresh interval is 10 seconds.", file=sys.stderr)
        return 2
    if not args.preview and not args.address:
        print("Provide --address XX:XX:XX:XX:XX:XX or set MINITOO_ADDRESS.", file=sys.stderr)
        return 2
    if args.port is not None and not 1 <= args.port <= 65_535:
        print("The local bridge port must be between 1 and 65535.", file=sys.stderr)
        return 2

    bridge: MiniTooBridge | None = None
    previous_digest: str | None = None
    next_display_retry: float | None = None
    display_failures = 0
    logger: logging.Logger | None = None
    log_handler: PrivateRotatingFileHandler | None = None
    terminal = TerminalUI()

    def report(message: str, *, error: bool = False) -> None:
        terminal.report(message, error=error)
        if logger is not None:
            logger.log(logging.ERROR if error else logging.INFO, message)

    try:
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
            )
            if not terminal.interactive:
                report(f"Diagnostic log: {log_path}")
            logger.info("Monitor starting: device=%s theme=%s port=%s", args.device, args.theme, bridge_port)
            terminal.step("Connecting to Codex and reading account usage…")
        with CodexAppServer(args.codex_bin, codex_home=args.codex_home) as codex:
            if not args.preview:
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
                device_name = "TimeBox Mini" if args.device == "timebox-mini" else "MiniToo"
                report(f"Monitoring {device_name} at {args.address}; reading Codex usage every {args.interval}s.")

            snapshot = codex.read_usage()
            if not args.preview:
                terminal.step("Usage received. Connecting to the authenticated Bluetooth bridge…")
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
                activity = read_activity(args.activity_file)
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
                        )
                    if args.preview:
                        args.preview.parent.mkdir(parents=True, exist_ok=True)
                        images[0].save(args.preview)
                        print(f"Preview saved to {args.preview}")
                        return 0

                    if args.device == "timebox-mini":
                        frames = [encode_timebox_rgb444(images[0])]
                    else:
                        jpeg_quality = {"anime": 92, "pixel-art": 98, "anime-pixel": 98, "anime-pixel-chibi": 98}.get(args.theme, 88)
                        frames = [
                            encode_for_minitoo(
                                image,
                                quality=jpeg_quality,
                                pixel_art=args.theme in ("pixel-art", "anime-pixel", "anime-pixel-chibi"),
                                preserve_detail=args.theme in PORTRAIT_THEMES,
                            )
                            for image in images
                        ]
                    digest = hashlib.sha256(b"\0".join(frames)).hexdigest()
                    if digest != previous_digest and (
                        next_display_retry is None or loop_time >= next_display_retry
                    ):
                        assert bridge is not None
                        if len(frames) > 1:
                            if args.theme in PORTRAIT_THEMES:
                                animation_speed = 600
                            elif args.theme == "pixel-art" and not activity.working:
                                animation_speed = 800
                            else:
                                animation_speed = 400
                        else:
                            animation_speed = 0
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
                            report(f"{exc} Retrying the current screen in {retry_delay}s.", error=True)
                            previous_activity_state = activity_state
                            previous_screen_mode = screen_mode
                            previous_timebox_view = timebox_view
                            time.sleep(1)
                            continue
                        next_display_retry = None
                        display_failures = 0
                        animation_only = (
                            timebox_animation_changed
                            and not refreshed
                            and activity_state == previous_activity_state
                            and not screen_changed
                            and not timebox_view_changed
                        )
                        if not animation_only:
                            activity_label = "working" if activity.working else "idle" if activity.hooks_installed else "hooks not installed"
                            if result.get("reconnected"):
                                update_label = "Display updated after reconnect"
                            else:
                                update_label = "Display updated"
                            report(
                                update_label + ": "
                                + ", ".join(f"{window.label} {100 - window.used_percent}% left" for window in snapshot.windows)
                                + f"; Codex {activity_label}"
                                + ("; showing reset credits" if screen_mode == "reset-credits" else "; showing usage")
                                + f" ({result.get('message', 'ok')})."
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
    except (AppServerError, MiniTooError, OSError) as exc:
        report(str(exc), error=True)
        return 1
    except KeyboardInterrupt:
        report("\nMonitor stopped.")
        return 0
    finally:
        if bridge is not None:
            bridge.close()
        if log_handler is not None:
            log_handler.close()


if __name__ == "__main__":
    raise SystemExit(main())
