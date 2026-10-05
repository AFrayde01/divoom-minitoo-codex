"""Compact dashboard and RGB444 encoding for the Divoom TimeBox Mini."""

from __future__ import annotations

from datetime import datetime

from PIL import Image, ImageDraw

from .appserver import UsageSnapshot, UsageWindow

SIZE = 11

# The TimeBox Mini has only 121 LEDs, so keep one quiet dashboard layout and
# let the user change its accent color. Use a true black background; RGB444
# otherwise makes even very dark navy pixels visibly blue on the device.
TIMEBOX_COLORS = {
    # Use saturated RGB accents: the TimeBox Mini's coarse LED palette can
    # shift softer shades toward cyan, especially mint greens.
    "cyan": (0, 255, 255),
    "purple": (192, 0, 255),
    "red": (255, 0, 0),
    "blue": (0, 96, 255),
    "green": (0, 255, 0),
}

_DIGITS = {
    "0": ("111", "101", "101", "101", "111"),
    "1": ("110", "010", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"),
    "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "7": ("111", "001", "001", "001", "001"),
    "8": ("111", "101", "111", "101", "111"),
    "9": ("111", "101", "111", "001", "111"),
    "%": ("101", "001", "010", "100", "101"),
}

_LARGE_DIGITS = {
    "0": ("11111", "10001", "10001", "10001", "10001", "10001", "11111"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("11111", "00001", "00001", "11111", "10000", "10000", "11111"),
    "3": ("11111", "00001", "00001", "11111", "00001", "00001", "11111"),
    "4": ("10001", "10001", "10001", "11111", "00001", "00001", "00001"),
    "5": ("11111", "10000", "10000", "11111", "00001", "00001", "11111"),
    "6": ("11111", "10000", "10000", "11111", "10001", "10001", "11111"),
    "7": ("11111", "00001", "00001", "00001", "00001", "00001", "00001"),
    "8": ("11111", "10001", "10001", "11111", "10001", "10001", "11111"),
    "9": ("11111", "10001", "10001", "11111", "00001", "00001", "11111"),
}

def _colors(color: str | None) -> tuple[tuple[int, int, int], ...]:
    selected = color or "cyan"
    if selected not in TIMEBOX_COLORS:
        raise ValueError(f"Unknown TimeBox Mini color {selected!r}; choose from: {', '.join(TIMEBOX_COLORS)}")
    primary = TIMEBOX_COLORS[selected]
    return (
        (0, 0, 0),
        (16, 16, 16),
        primary,
    )


def _text_width(text: str, spacing: int = 1) -> int:
    return len(text) * 3 + max(0, len(text) - 1) * spacing


def _draw_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    color: tuple[int, int, int],
    *,
    spacing: int = 1,
) -> None:
    font = _DIGITS
    x = max(0, (SIZE - _text_width(text, spacing)) // 2)
    for character in text:
        glyph = font.get(character)
        if glyph:
            for row, bits in enumerate(glyph):
                for column, bit in enumerate(bits):
                    if bit == "1" and x + column < SIZE and y + row < SIZE:
                        draw.point((x + column, y + row), fill=color)
        x += 3 + spacing


def _draw_large_count(draw: ImageDraw.ImageDraw, count: int, color: tuple[int, int, int]) -> None:
    text = str(count)
    spacing = 1
    text_width = len(text) * 5 + max(0, len(text) - 1) * spacing
    x = max(0, (SIZE - text_width) // 2)
    y = (SIZE - 7) // 2
    for character in text:
        for row, bits in enumerate(_LARGE_DIGITS[character]):
            for column, bit in enumerate(bits):
                if bit == "1":
                    draw.point((x + column, y + row), fill=color)
        x += 5 + spacing


def _horizontal_bar(
    draw: ImageDraw.ImageDraw,
    y: int,
    fraction: float | None,
    track: tuple[int, int, int],
    fill: tuple[int, int, int],
    *,
    thickness: int = 3,
) -> None:
    draw.rectangle((1, y, 9, y + thickness - 1), fill=track)
    if fraction is not None:
        count = max(0, min(9, round(fraction * 9)))
        if count:
            draw.rectangle((1, y, count, y + thickness - 1), fill=fill)


def _vertical_bar(
    draw: ImageDraw.ImageDraw,
    x: int,
    fraction: float | None,
    track: tuple[int, int, int],
    fill: tuple[int, int, int],
    *,
    thickness: int = 3,
) -> None:
    draw.rectangle((x, 1, x + thickness - 1, 9), fill=track)
    if fraction is not None:
        count = max(0, min(9, round(fraction * 9)))
        if count:
            draw.rectangle((x, 10 - count, x + thickness - 1, 9), fill=fill)


def _quota_left(window: UsageWindow) -> float:
    return max(0, min(100, 100 - window.used_percent)) / 100


def render_timebox_working(
    *,
    color: str | None = None,
    animation_frame: int = 0,
) -> Image.Image:
    """Render a full-matrix pulse for the TimeBox Mini while Codex works."""
    background, _track, primary = _colors(color)
    image = Image.new("RGB", (SIZE, SIZE), background)
    draw = ImageDraw.Draw(image)

    dim = tuple(max(2, channel // 10) for channel in primary)
    center = (SIZE - 1) // 2
    radius = (5, 4, 3, 2, 1, 2, 3, 4)[animation_frame % 8]
    inner_radius = max(0, radius - 1)
    for y in range(SIZE):
        for x in range(SIZE):
            distance = max(abs(x - center), abs(y - center))
            pixel = primary if distance == radius else dim if distance == inner_radius else background
            draw.point((x, y), fill=pixel)
    return image


def render_timebox_usage(
    snapshot: UsageSnapshot,
    now: datetime,
    *,
    color: str | None = None,
    view: str = "bars",
) -> Image.Image:
    """Render quota bars or the nearest refill's usage percentage."""
    background, track, primary = _colors(color)
    image = Image.new("RGB", (SIZE, SIZE), background)
    draw = ImageDraw.Draw(image)

    if not snapshot.windows:
        return image

    if view == "bars":
        windows = tuple(sorted(
            snapshot.windows,
            key=lambda item: (
                item.window_duration_mins is None,
                item.window_duration_mins if item.window_duration_mins is not None else float("inf"),
            ),
        ))[:3]
        if len(windows) == 1 and windows[0].label.upper() == "7D":
            vertical_thickness = 5
            _vertical_bar(
                draw,
                (SIZE - vertical_thickness) // 2,
                _quota_left(windows[0]),
                track,
                primary,
                thickness=vertical_thickness,
            )
        elif len(windows) == 1:
            _horizontal_bar(draw, (SIZE - 3) // 2, _quota_left(windows[0]), track, primary)
        elif len(windows) == 2:
            rows = (1, 7)
            for window, row in zip(windows, rows):
                _horizontal_bar(draw, row, _quota_left(window), track, primary)
        else:
            rows = (0, 4, 8)
            for window, row in zip(windows, rows):
                _horizontal_bar(draw, row, _quota_left(window), track, primary)
    elif view == "nearest-percent":
        now_timestamp = now.timestamp()
        known = [window for window in snapshot.windows if window.resets_at is not None]
        upcoming = [window for window in known if window.resets_at > now_timestamp]
        if upcoming:
            window = min(upcoming, key=lambda item: item.resets_at or 0)
        elif known:
            window = min(known, key=lambda item: abs((item.resets_at or 0) - now_timestamp))
        else:
            window = snapshot.windows[0]
        percent_remaining = round(max(0, min(100, 100 - window.used_percent)))
        percent_text = f"{percent_remaining}%" if percent_remaining < 100 else "100"
        _draw_text(draw, percent_text, 3, primary, spacing=1)
    else:
        raise ValueError("TimeBox Mini usage view must be 'bars' or 'nearest-percent'.")
    return image


def render_timebox_reset_credits(
    snapshot: UsageSnapshot,
    *,
    color: str | None = None,
) -> Image.Image:
    """Render only the available reset count, large and centered."""
    background, _track, primary = _colors(color)
    image = Image.new("RGB", (SIZE, SIZE), background)
    draw = ImageDraw.Draw(image)
    count = min(99, snapshot.reset_credits.available_count)
    _draw_large_count(draw, count, primary)
    return image


def encode_timebox_rgb444(image: Image.Image) -> bytes:
    """Pack an 11x11 RGB image into the TimeBox Mini's 12-bit pixel stream."""
    if image.size != (SIZE, SIZE):
        image = image.resize((SIZE, SIZE), Image.Resampling.NEAREST)
    values: list[int] = []
    for red, green, blue in image.convert("RGB").getdata():
        values.extend((red >> 4, green >> 4, blue >> 4))
    if len(values) % 2:
        values.append(0)
    return bytes(values[index] | (values[index + 1] << 4) for index in range(0, len(values), 2))
