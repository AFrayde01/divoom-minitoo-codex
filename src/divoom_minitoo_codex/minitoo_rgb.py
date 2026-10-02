"""Native MiniToo RGB888 animation payloads, compressed without color loss."""

from __future__ import annotations

import shutil
import subprocess

from PIL import Image

from .bridge import MiniTooError

SIZE = (160, 128)
WINDOW_LOG = 17
COMPRESSION_LEVEL = 10
MAX_PAYLOAD_BYTES = 384 * 1024


def zstd_frame_parameters(data: bytes) -> tuple[int, int]:
    """Read declared RGB size/window; the Swift bridge also checks block bounds."""
    if len(data) < 8 or data[:4] != bytes.fromhex("28 b5 2f fd") or data[4] & 0x1B:
        raise MiniTooError("RGB compression requires standard Zstandard without a dictionary.")
    descriptor = data[4]
    single_segment = bool(descriptor & 0x20)
    offset = 5
    window = 0
    if not single_segment:
        base = 1 << (10 + (data[offset] >> 3))
        window = base + (base // 8) * (data[offset] & 7)
        offset += 1
    size_bytes = (1 if single_segment else 0, 2, 4, 8)[descriptor >> 6]
    if not size_bytes or offset + size_bytes > len(data):
        raise MiniTooError("RGB Zstandard must declare its decompressed size.")
    content_size = int.from_bytes(data[offset:offset + size_bytes], "little")
    if size_bytes == 2:
        content_size += 256
    if single_segment:
        window = content_size
    return content_size, window


def compress_rgb(rgb: bytes) -> bytes:
    try:
        import zstandard as zstd
    except ImportError as error:
        # Existing installations can use an already installed zstd CLI while
        # upgrading. New installs receive the Python dependency automatically.
        executable = shutil.which("zstd")
        if executable is None:
            raise MiniTooError("RGB encoding requires zstandard. Run scripts/install.sh to update the installation.") from error
        try:
            result = subprocess.run(
                [executable, "-q", "-c", "--single-thread", f"-{COMPRESSION_LEVEL}",
                 f"--zstd=wlog={WINDOW_LOG}", f"--stream-size={len(rgb)}", "--no-check"],
                input=rgb, capture_output=True, timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise MiniTooError(f"Could not run the RGB compressor: {exc}") from exc
        if result.returncode:
            raise MiniTooError("Could not compress RGB: " + result.stderr[:300].decode("utf-8", errors="replace").strip())
        compressed = result.stdout
    else:
        parameters = zstd.ZstdCompressionParameters.from_level(
            COMPRESSION_LEVEL, window_log=WINDOW_LOG,
            write_content_size=1, write_checksum=0, write_dict_id=0,
        )
        try:
            compressed = zstd.ZstdCompressor(compression_params=parameters).compress(rgb)
        except zstd.ZstdError as error:
            raise MiniTooError(f"Could not compress the RGB animation: {error}") from error
    content_size, window = zstd_frame_parameters(compressed)
    if content_size != len(rgb) or not 0 < window <= 1 << WINDOW_LOG:
        raise MiniTooError("The RGB compressor produced an incompatible Zstandard frame.")
    return compressed


def pack_rgb_zstd(zstd: bytes, frame_count: int, speed_ms: int) -> bytes:
    if not 1 <= frame_count <= 8 or not 0 <= speed_ms <= 65535:
        raise MiniTooError("RGB animations require 1–8 frames and a speed between 0 and 65535 ms.")
    if not zstd.startswith(bytes.fromhex("28 b5 2f fd")):
        raise MiniTooError("RGB frames require a standard Zstandard stream.")
    payload = bytes((0x25, frame_count)) + speed_ms.to_bytes(2, "big") + bytes((8, 10))
    payload += len(zstd).to_bytes(4, "big") + zstd
    if len(payload) >= MAX_PAYLOAD_BYTES:
        raise MiniTooError("The compressed RGB animation exceeds the local bridge size limit.")
    return payload


def encode_rgb_animation(images: tuple[Image.Image, ...], speed_ms: int) -> bytes:
    if not 1 <= len(images) <= 8 or any(image.size != SIZE for image in images):
        raise MiniTooError("RGB animations require 1–8 frames at exactly 160x128; frames are not resized.")
    rgb = b"".join(image.convert("RGB").tobytes() for image in images)
    return pack_rgb_zstd(compress_rgb(rgb), len(images), speed_ms)
