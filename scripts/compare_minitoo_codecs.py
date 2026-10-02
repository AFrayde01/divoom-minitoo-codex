#!/usr/bin/env python3
"""Compare a MiniToo JPEG with the same pixels sent through its RGB888 route."""

from __future__ import annotations

import argparse
from io import BytesIO
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from PIL import Image, ImageChops, ImageDraw, ImageStat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from compare_minitoo_jpeg import comparison_image
from divoom_minitoo_codex.bridge import MiniTooBridge, MiniTooError
from divoom_minitoo_codex.diagnostics import PrivateRotatingFileHandler
from divoom_minitoo_codex.render import ANIME_PALETTES, _draw_pixel_text

SIZE = (128, 128)
PORTRAIT_BOX = (25, 18, 103, 96)
FLAT_REGION = (8, 114, 120, 123)
BAR_COLOR = (62, 116, 91)
BACKGROUND = (10, 21, 18)
CODECS = ("jpeg", "rgb")


def raw_zstd(rgb: bytes) -> bytes:
    """One lossless raw block, explicit 128 KiB window, no dictionary/checksum."""
    if len(rgb) != SIZE[0] * SIZE[1] * 3:
        raise ValueError("RGB input must contain exactly 49152 bytes.")
    # FCS flag 1 = two bytes with a +256 offset. Single-segment flag is
    # unset; window descriptor 0x38 explicitly selects window_log=17.
    header = bytes.fromhex("28 b5 2f fd 40 38") + (len(rgb) - 256).to_bytes(2, "little")
    block = ((len(rgb) << 3) | 1).to_bytes(3, "little")
    return header + block + rgb


def prepare(color: str, output: Path, codecs: tuple[str, ...]) -> tuple[dict, dict[str, bytes]]:
    output.mkdir(parents=True, exist_ok=True)
    dashboard = comparison_image(color, None)
    portrait = dashboard.crop((8, 30, 86, 108))
    canvas = Image.new("RGB", SIZE, BACKGROUND)
    canvas.paste(portrait, PORTRAIT_BOX[:2])
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((24, 17, 103, 96), outline=(133, 221, 163))
    draw.rectangle((8, 100, 119, 122), fill=BAR_COLOR)
    _draw_pixel_text(draw, "CHECK", 16, 104, (240, 249, 245), scale=2)
    canvas.save(output / "original.png", optimize=True)

    variants = []
    wire_frames = {}
    for codec in codecs:
        image = canvas.copy()
        label = "JPEG 98" if codec == "jpeg" else "RGB"
        _draw_pixel_text(ImageDraw.Draw(image), label, 8, 4, (240, 249, 245), scale=2)
        image.save(output / f"{codec}-source.png", optimize=True)
        variant = {
            "codec": codec, "label": label,
            "portrait_rgb_sha256": hashlib.sha256(image.crop(PORTRAIT_BOX).tobytes()).hexdigest(),
            "flat_region_color": list(BAR_COLOR),
            "sent": False, "acknowledged": False, "chunks": None, "observation": None,
        }
        if codec == "jpeg":
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=98, subsampling=0, optimize=True)
            frame = buffer.getvalue()
            (output / "jpeg-98.jpg").write_bytes(frame)
            with Image.open(BytesIO(frame)) as decoded:
                delta = ImageChops.difference(image, decoded.convert("RGB"))
                variant["mean_absolute_rgb_difference"] = round(sum(ImageStat.Stat(delta).mean) / 3, 4)
                variant["maximum_rgb_difference"] = max(high for _, high in delta.getextrema())
            variant["payload_bytes"] = len(frame) + 11
        else:
            frame = image.tobytes()
            zstd = raw_zstd(frame)
            (output / "rgb888.bin").write_bytes(frame)
            (output / "rgb888.zst").write_bytes(zstd)
            variant["mean_absolute_rgb_difference"] = 0
            variant["maximum_rgb_difference"] = 0
            variant["payload_bytes"] = len(zstd) + 10
        wire_frames[codec] = frame
        variants.append(variant)
    return {
        "dimensions": list(SIZE), "portrait_box": list(PORTRAIT_BOX),
        "flat_region": list(FLAT_REGION), "static_frame": True,
        "zstd_window_log": 17, "zstd_block_type": "raw",
        "state": "prepared", "current_codec": None, "variants": variants,
    }, wire_frames


def save_report(output: Path, report: dict) -> None:
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def compile_bridge(codec: str) -> Path:
    compiler = shutil.which("swiftc")
    if sys.platform != "darwin" or compiler is None:
        raise ValueError("The codec comparison requires macOS and the Swift compiler (Xcode Command Line Tools).")
    directory = ROOT / "build/minitoo-codec-diagnostic"
    directory.mkdir(parents=True, exist_ok=True)
    binary = directory / f"{codec}-bridge"
    flag = "MINITOO_SQUARE_JPEG_DIAGNOSTIC" if codec == "jpeg" else "MINITOO_RGB_DIAGNOSTIC"
    print(f"Compiling the separate {codec.upper()} diagnostic bridge...", flush=True)
    # Always rebuild, so an old JPEG-only bridge cannot accept raw RGB bytes.
    result = subprocess.run([
        compiler, "-O", "-D", flag, "-module-cache-path", str(directory / "swift-module-cache"),
        str(ROOT / "Sources/MiniTooBridge.swift"), "-framework", "IOBluetooth",
        "-framework", "Network", "-o", str(binary),
    ], capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise ValueError(f"Could not compile the {codec} diagnostic bridge:\n{result.stderr.strip()}")
    return binary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--address", default=os.environ.get("MINITOO_ADDRESS"), help="MiniToo Bluetooth address.")
    parser.add_argument("--color", choices=tuple(ANIME_PALETTES), default="green")
    parser.add_argument("--only", choices=CODECS, help="Send just one codec.")
    parser.add_argument("--hold-seconds", type=float, default=30, help="Seconds between the two frames (default: 30).")
    parser.add_argument("--interactive", action="store_true", help="Enter an optional observation to advance.")
    parser.add_argument("--prepare-only", action="store_true", help="Create files without compiling or connecting.")
    parser.add_argument("--output", type=Path, default=ROOT / "build/minitoo-codec-comparison")
    parser.add_argument("--port", type=int, default=40685, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.prepare_only and not args.address:
        parser.error("provide --address (or MINITOO_ADDRESS), or use --prepare-only")
    if not 5 <= args.hold_seconds <= 300 or not 1 <= args.port <= 65535:
        parser.error("hold time must be 5–300 seconds and the port must be 1–65535")
    if args.interactive and not args.prepare_only and not sys.stdin.isatty():
        parser.error("--interactive requires a Terminal; omit it for automatic sending")

    output = args.output.expanduser().resolve()
    report = None
    bridge = None
    handler = None
    try:
        codecs = (args.only,) if args.only else CODECS
        report, frames = prepare(args.color, output, codecs)
        save_report(output, report)
        print("Prepared the same 78x78 portrait and a uniform green CHECK bar in a 128x128 diagnostic canvas.")
        print("The portrait is copied at native size. Only the top codec label changes.")
        for variant in report["variants"]:
            print(f"  {variant['label']}: {variant['payload_bytes'] / 1024:.1f} KiB payload")
        print(f"Files and report: {output}", flush=True)
        if args.prepare_only:
            print("Offline preparation complete. No Bluetooth connection was opened.")
            return 0

        binaries = {codec: compile_bridge(codec) for codec in codecs}
        print("Stop the monitor and close the Divoom app and MiniToo audio connection before sending.")
        print("This is an experimental codec comparison using 128x128 frames, not the normal dashboard.")
        print("Observe the alternating checkerboard patches below CHECK and near the eyes/forehead.")
        print("Confirm the top label changes; transfer acknowledgement alone does not prove correct display.", flush=True)
        logger = logging.Logger("codec-comparison", level=logging.INFO)
        handler = PrivateRotatingFileHandler(output / "bridge.log")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)

        for index, variant in enumerate(report["variants"]):
            codec = variant["codec"]
            bridge = MiniTooBridge(binaries[codec], args.address, port=args.port, logger=logger)
            bridge.diagnostic_codec = "jpeg128" if codec == "jpeg" else "rgb888-zstd"
            report["state"] = "connecting"
            report["current_codec"] = codec
            save_report(output, report)
            print(f"Connecting for {variant['label']}...", flush=True)
            bridge.start()
            report["state"] = "transferring"
            save_report(output, report)
            print(f"Sending {variant['label']}...", flush=True)
            result = bridge.send_frames_with_recovery([frames[codec]], speed_ms=1000, require_ack=True)
            variant.update(sent=True, acknowledged=result.get("acknowledged") is True, chunks=result.get("chunks"))
            report["state"] = "displaying"
            save_report(output, report)
            bridge.close()
            bridge = None
            print(f"Transfer acknowledged ({variant['chunks']} chunks). Check that {variant['label']} is visible at the top.", flush=True)
            if args.interactive:
                variant["observation"] = input("Observation, including a blank/glitched display if present (Enter advances): ").strip() or None
                save_report(output, report)
            elif index < len(report["variants"]) - 1:
                print(f"Keeping {variant['label']} visible for {args.hold_seconds:g}s...", flush=True)
                time.sleep(args.hold_seconds)
        report["state"] = "complete"
        print("Comparison complete. Restart the normal monitor to restore live usage.")
        print("Please report whether RGB displayed correctly and whether the checkerboard changed.")
        return 0
    except (MiniTooError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        if report is not None:
            report["state"] = "stopped"
            report["error"] = str(error).replace(args.address, "<Bluetooth address>") if args.address else str(error)
        print(f"Comparison stopped: {error}", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        if report is not None:
            report["state"] = "cancelled"
        print("\nComparison cancelled. Restart the normal monitor for live values.", file=sys.stderr)
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
                print(f"Could not save the final report: {error}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
