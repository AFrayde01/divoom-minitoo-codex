#!/usr/bin/env python3
"""Check native 160x128 RGB usage, animations and reset credits on MiniToo."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from divoom_minitoo_codex.activity import CodexActivity
from divoom_minitoo_codex.appserver import ResetCredit, ResetCredits, UsageSnapshot, UsageWindow
from divoom_minitoo_codex.bridge import MiniTooBridge, MiniTooError
from divoom_minitoo_codex.diagnostics import PrivateRotatingFileHandler
from divoom_minitoo_codex.minitoo_rgb import encode_rgb_animation, zstd_frame_parameters
from divoom_minitoo_codex.render import ANIME_PALETTES, PORTRAIT_THEMES, THEMES, encode_for_minitoo, render_reset_credits, render_usage_frames

STAGES = ("static", "idle-animation", "working-animation", "reset-credits")


def prepare(theme: str, color: str, output: Path, stages: tuple[str, ...]) -> tuple[dict, list[bytes]]:
    output.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    snapshot = UsageSnapshot(
        plan_type="pro", windows=(UsageWindow("7D", 21, 10080, int((now + timedelta(days=4)).timestamp())),),
        reset_credits=ResetCredits(3, tuple(ResetCredit(int((now + timedelta(days=days)).timestamp())) for days in (5, 7, 14))),
    )
    idle = CodexActivity(working=False, hooks_installed=True)
    working = CodexActivity(working=True, hooks_installed=True, active_sessions=1)
    idle_frames = render_usage_frames(snapshot, now, idle, theme=theme, anime_color=color)
    working_frames = render_usage_frames(snapshot, now, working, theme=theme, anime_color=color)
    sources = {
        "static": (idle_frames[0],), "idle-animation": idle_frames, "working-animation": working_frames,
        "reset-credits": (render_reset_credits(snapshot, idle, theme=theme, anime_color=color),),
    }
    variants = []
    payloads = []
    for stage in stages:
        images = sources[stage]
        speed = 1000 if len(images) == 1 else 600 if theme in PORTRAIT_THEMES else 800 if stage == "idle-animation" and theme == "pixel-art" else 400
        start = time.perf_counter()
        payload = encode_rgb_animation(images, speed)
        elapsed_ms = (time.perf_counter() - start) * 1000
        payloads.append(payload)
        (output / f"{stage}.payload").write_bytes(payload)
        (output / f"{stage}.zst").write_bytes(payload[10:])
        for index, image in enumerate(images):
            image.save(output / f"{stage}-{index}.png", optimize=True)
        jpeg_quality = {"anime": 92, "pixel-art": 98, "anime-pixel": 98, "anime-pixel-chibi": 98, "anime-pixel-detail": 98}.get(theme, 88)
        jpeg_bytes = 6 + sum(5 + len(encode_for_minitoo(
            image, quality=jpeg_quality,
            pixel_art=theme == "pixel-art" or (theme in PORTRAIT_THEMES and theme != "anime"),
            preserve_detail=theme in PORTRAIT_THEMES,
        )) for image in images)
        size, window = zstd_frame_parameters(payload[10:])
        variants.append({
            "stage": stage, "frames": len(images), "speed_ms": speed,
            "payload_bytes": len(payload), "jpeg_payload_bytes": jpeg_bytes,
            "raw_rgb_bytes": size, "zstd_window_bytes": window,
            "compression_ms": round(elapsed_ms, 2),
            "source_rgb_sha256": hashlib.sha256(b"".join(image.convert("RGB").tobytes() for image in images)).hexdigest(),
            "sent": False, "acknowledged": False, "chunks": None,
        })
    return {
        "dimensions": [160, 128], "theme": theme, "color": color,
        "illustrative_values": {"remaining_percent": 79, "reset_credits": 3},
        "state": "prepared", "current_stage": None, "variants": variants,
    }, payloads


def save_report(output: Path, report: dict) -> None:
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--address", default=os.environ.get("MINITOO_ADDRESS"))
    parser.add_argument("--theme", choices=tuple(THEMES), default="anime-pixel")
    parser.add_argument("--color", choices=tuple(ANIME_PALETTES), default="green")
    parser.add_argument("--only", choices=STAGES)
    parser.add_argument("--hold-seconds", type=float, default=20)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "build/minitoo-native-rgb-check")
    parser.add_argument("--port", type=int, default=40686, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.prepare_only and not args.address:
        parser.error("provide --address (or MINITOO_ADDRESS), or use --prepare-only")
    if not 5 <= args.hold_seconds <= 300 or not 1 <= args.port <= 65535:
        parser.error("hold time must be 5–300 seconds and the port must be 1–65535")

    output = args.output.expanduser().resolve()
    bridge = None
    handler = None
    report = None
    try:
        stages = (args.only,) if args.only else STAGES
        report, payloads = prepare(args.theme, args.color, output, stages)
        save_report(output, report)
        print("Native 160x128 RGB check: illustrative 79% remaining and 3 resets; no account data is read.")
        for variant in report["variants"]:
            print(f"  {variant['stage']}: {variant['frames']} frames, RGB {variant['payload_bytes'] / 1024:.1f} KiB; JPEG {variant['jpeg_payload_bytes'] / 1024:.1f} KiB")
        print(f"Files and report: {output}", flush=True)
        if args.prepare_only:
            print("Offline preparation complete. No Bluetooth connection was opened.")
            return 0
        compiler = shutil.which("swiftc")
        if sys.platform != "darwin" or compiler is None:
            raise ValueError("The native check requires macOS and Xcode Command Line Tools.")
        binary = output / "minitoo-rgb-check-bridge"
        print("Compiling the RGB-capable bridge...", flush=True)
        result = subprocess.run([
            compiler, "-O", "-module-cache-path", str(output / "swift-module-cache"),
            str(ROOT / "Sources/MiniTooBridge.swift"), "-framework", "IOBluetooth",
            "-framework", "Network", "-o", str(binary),
        ], capture_output=True, text=True, timeout=120)
        if result.returncode:
            raise ValueError("Bridge compilation failed:\n" + result.stderr.strip())
        print("Stop the monitor and close the Divoom app and MiniToo audio connection before sending.")
        print("Check the complete layout, the blink, WORKING animation and reset credits; report any distortion.", flush=True)
        logger = logging.Logger("native-rgb-check", level=logging.INFO)
        handler = PrivateRotatingFileHandler(output / "bridge.log")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        bridge = MiniTooBridge(binary, args.address, port=args.port, logger=logger)
        bridge.frame_encoding = "rgb-zstd"
        for index, (variant, payload) in enumerate(zip(report["variants"], payloads)):
            bridge.close()
            report["state"] = "connecting"
            report["current_stage"] = variant["stage"]
            save_report(output, report)
            print(f"Connecting and sending {variant['stage']}...", flush=True)
            result = bridge.send_frames_with_recovery([payload], speed_ms=variant["speed_ms"], require_ack=True)
            variant.update(sent=True, acknowledged=result.get("acknowledged") is True, chunks=result.get("chunks"))
            report["state"] = "displaying"
            save_report(output, report)
            print(f"Transfer acknowledged ({variant['chunks']} chunks). Inspect {variant['stage']} on the device.", flush=True)
            if index < len(payloads) - 1:
                time.sleep(args.hold_seconds)
        report["state"] = "complete"
        print("Native RGB check complete. Report the layout and animation result, then restart the monitor for live values.")
        return 0
    except (MiniTooError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        if report is not None:
            report["state"] = "stopped"
            report["error"] = str(error).replace(args.address, "<Bluetooth address>") if args.address else str(error)
        print(f"Native RGB check stopped: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        if report is not None:
            report["state"] = "cancelled"
        print("\nNative RGB check cancelled. Restart the normal monitor for live values.", file=sys.stderr)
        return 130
    finally:
        if bridge is not None:
            bridge.close()
        if handler is not None:
            handler.close()
        if report is not None:
            try:
                save_report(output, report)
            except OSError as error:
                print(f"Could not save the report: {error}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
