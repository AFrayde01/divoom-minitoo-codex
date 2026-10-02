#!/usr/bin/env python3
"""Compare identical static MiniToo artwork at JPEG qualities 95, 97 and 98."""

from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
import logging
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timedelta, timezone

from PIL import Image, ImageChops, ImageDraw, ImageStat


ROOT = Path(__file__).resolve().parents[1]
# Use this checkout's renderer/assets even when another version is installed.
sys.path.insert(0, str(ROOT / "src"))

from divoom_minitoo_codex.activity import CodexActivity
from divoom_minitoo_codex.appserver import UsageSnapshot, UsageWindow
from divoom_minitoo_codex.bridge import MiniTooBridge, MiniTooError
from divoom_minitoo_codex.diagnostics import PrivateRotatingFileHandler
from divoom_minitoo_codex.render import ANIME_PALETTES, _draw_pixel_text, encode_for_minitoo, render_usage


QUALITIES = (95, 97, 98)
FRAME_SIZE = (160, 128)
LABEL_BOX = (8, 112, 89, 123)


def comparison_image(color: str, filename: Path | None) -> Image.Image:
    if filename is not None:
        with Image.open(filename) as source:
            image = source.convert("RGB")
        if image.size != FRAME_SIZE:
            raise ValueError("The comparison image must be exactly 160x128; it will not be resized.")
        return image
    now = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    snapshot = UsageSnapshot(
        plan_type="pro",
        windows=(UsageWindow("7D", 21, 10_080, int((now + timedelta(days=4)).timestamp())),),
    )
    return render_usage(
        snapshot, now, activity=CodexActivity(working=False, hooks_installed=True),
        theme="anime-pixel", anime_color=color, animation_frame=0,
    )


def prepare(
    image: Image.Image, output: Path, qualities: tuple[int, ...] = QUALITIES,
) -> tuple[dict[str, object], list[bytes]]:
    output.mkdir(parents=True, exist_ok=True)
    image.save(output / "original.png", optimize=True)
    variants = []
    frames = []
    for quality in qualities:
        labelled = image.copy()
        draw = ImageDraw.Draw(labelled)
        left, top, right, bottom = LABEL_BOX
        # Clear the whole original footer caption, including its first rows.
        # Sample inside the footer, not its colored bottom border.
        draw.rectangle((left, top, right - 1, bottom - 1), fill=image.getpixel((88, 118)))
        _draw_pixel_text(draw, f"JPEG {quality}", 10, 115, (240, 249, 245))
        source_filename = f"quality-{quality}-source.png"
        labelled.save(output / source_filename, optimize=True)
        # All portrait pixels stay identical. The identifying label is in
        # separate JPEG blocks below the portrait, never across the eyes.
        jpeg = encode_for_minitoo(labelled, quality=quality, pixel_art=True)
        frames.append(jpeg)
        filename = f"quality-{quality}.jpg"
        (output / filename).write_bytes(jpeg)
        with Image.open(BytesIO(jpeg)) as decoded:
            delta = ImageChops.difference(labelled, decoded.convert("RGB"))
            variants.append({
                "quality": quality,
                "file": filename,
                "source_file": source_filename,
                "portrait_rgb_sha256": hashlib.sha256(labelled.crop((8, 30, 86, 108)).tobytes()).hexdigest(),
                "bytes": len(jpeg),
                "sampling": "4:4:4",
                "mean_absolute_rgb_difference": round(sum(ImageStat.Stat(delta).mean) / 3, 4),
                "maximum_rgb_difference": max(high for _, high in delta.getextrema()),
                "sent": False,
                "acknowledged": False,
                "chunks": None,
                "observation": None,
            })
    report: dict[str, object] = {
        "source_rgb_sha256": hashlib.sha256(image.tobytes()).hexdigest(),
        "dimensions": list(image.size),
        "static_frame": True,
        "quality_label_box": list(LABEL_BOX),
        "state": "prepared",
        "current_quality": None,
        "variants": variants,
    }
    return report, frames


def save_report(output: Path, report: dict[str, object]) -> None:
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--address", default=os.environ.get("MINITOO_ADDRESS"), help="MiniToo Bluetooth address.")
    result.add_argument("--color", choices=tuple(ANIME_PALETTES), default="green", help="Portrait color (default: green).")
    result.add_argument("--image", type=Path, help="Use an existing 160x128 image instead of the illustrative adult dashboard.")
    result.add_argument("--output", type=Path, default=ROOT / "build/jpeg-quality-comparison", help="Directory for images and the local report.")
    result.add_argument("--prepare-only", action="store_true", help="Write the comparison files without opening Bluetooth.")
    result.add_argument("--quality", type=int, choices=QUALITIES, help="Send just one quality instead of the full sequence.")
    result.add_argument("--hold-seconds", type=float, default=20, help="Seconds to inspect each quality before the next upload (default: 20).")
    result.add_argument("--interactive", action="store_true", help="Wait for your observation after each upload instead of advancing automatically.")
    result.add_argument("--bridge", type=Path, default=ROOT / "build/minitoo-bridge", help=argparse.SUPPRESS)
    result.add_argument("--port", type=int, default=40684, help=argparse.SUPPRESS)
    return result


def main() -> int:
    arguments = parser()
    args = arguments.parse_args()
    if not args.prepare_only and not args.address:
        arguments.error("provide --address (or MINITOO_ADDRESS), or use --prepare-only")
    if not 1 <= args.port <= 65_535:
        arguments.error("the bridge port must be between 1 and 65535")
    if not 5 <= args.hold_seconds <= 300:
        arguments.error("--hold-seconds must be between 5 and 300")
    if args.interactive and not args.prepare_only and not sys.stdin.isatty():
        arguments.error("--interactive requires a Terminal; omit it for automatic sending")

    output = args.output.expanduser().resolve()
    bridge = None
    report = None
    log_handler = None
    try:
        image = comparison_image(args.color, args.image)
        qualities = (args.quality,) if args.quality is not None else QUALITIES
        report, frames = prepare(image, output, qualities)
        save_report(output, report)
        print(f"Prepared one 160x128 drawing at qualities {', '.join(map(str, qualities))}; only the footer labels change.")
        print(f"Files and report: {output}")
        for variant in report["variants"]:
            print(f"  Quality {variant['quality']}: {variant['bytes'] / 1024:.1f} KiB, 4:4:4")
        if args.prepare_only:
            print("Offline preparation complete. No Bluetooth connection was opened.")
            return 0

        print("The MiniToo monitor, Divoom app and MiniToo audio profile must already be disconnected.")
        print("Sending starts now. The display footer identifies JPEG 95, JPEG 97 or JPEG 98.")
        print("Default dashboard values are illustrative: 79% remaining; Codex IDLE.")
        logger = logging.Logger("jpeg-comparison", level=logging.INFO)
        log_handler = PrivateRotatingFileHandler(output / "bridge.log")
        log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(log_handler)
        print(f"Bluetooth diagnostics: {output / 'bridge.log'}", flush=True)
        bridge = MiniTooBridge(args.bridge, args.address, port=args.port, logger=logger)
        for index, (variant, jpeg) in enumerate(zip(report["variants"], frames)):
            # Separate sessions avoid carrying a prior transfer's connection
            # state into this small, controlled comparison.
            bridge.close()
            report["state"] = "connecting"
            report["current_quality"] = variant["quality"]
            save_report(output, report)
            logger.info("Starting a fresh session for JPEG quality %s", variant["quality"])
            print(f"Connecting for JPEG {variant['quality']}...", flush=True)
            bridge.start()
            report["state"] = "transferring"
            save_report(output, report)
            print(f"Sending quality {variant['quality']}...", flush=True)
            response = bridge.send_frames_with_recovery([jpeg], speed_ms=0, require_ack=True)
            variant["sent"] = True
            variant["acknowledged"] = response.get("acknowledged") is True
            variant["chunks"] = response.get("chunks")
            report["state"] = "displaying"
            save_report(output, report)
            print(f"Quality {variant['quality']} acknowledged. Inspect the eyes, forehead and hair edges.")
            print(f"Check that the screen footer now says JPEG {variant['quality']} (chunks: {variant['chunks']}).", flush=True)
            if args.interactive:
                variant["observation"] = input("Your observation (optional; Enter advances): ").strip() or None
                save_report(output, report)
            elif index < len(frames) - 1:
                print(f"Keeping JPEG {variant['quality']} on screen for {args.hold_seconds:g}s...", flush=True)
                time.sleep(args.hold_seconds)
        report["state"] = "complete"
        print(f"Comparison complete. The display is left on quality {qualities[-1]}; restart your monitor for live values.")
        print(f"Results: {output / 'report.json'}")
        return 0
    except (MiniTooError, OSError, ValueError) as error:
        if report is not None:
            report["state"] = "stopped"
            report["error"] = str(error).replace(args.address, "<Bluetooth address>") if args.address else str(error)
        print(f"Comparison stopped: {error}", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        if report is not None:
            report["state"] = "cancelled"
        print("\nComparison cancelled. Restart your monitor to restore live values.", file=sys.stderr)
        return 130
    finally:
        if bridge is not None:
            bridge.close()
        if log_handler is not None:
            log_handler.close()
        if report is not None:
            try:
                save_report(output, report)
            except OSError as error:
                print(f"Could not save the final local report: {error}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
