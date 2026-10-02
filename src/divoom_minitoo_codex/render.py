"""Render a compact Codex usage dashboard in the MiniToo's 160x128 frame."""

from __future__ import annotations

import math
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .appserver import ResetCredit, UsageSnapshot, UsageWindow
from .activity import CodexActivity, read_activity
from .i18n import display_text

WIDTH = 160
HEIGHT = 128

BACKGROUND = (9, 13, 25)
CARD = (18, 25, 43)
CARD_EDGE = (37, 49, 72)
TEXT = (239, 244, 255)
MUTED = (133, 153, 186)
ACCENTS = ((63, 224, 211), (168, 125, 255))

_DIGITS = {
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("110", "001", "111", "100", "111"),
    "3": ("110", "001", "111", "001", "110"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "110", "001", "110"),
    "6": ("011", "100", "111", "101", "111"),
    "7": ("111", "001", "010", "010", "010"),
    "8": ("111", "101", "111", "101", "111"),
    "9": ("111", "101", "111", "001", "110"),
    "%": ("101", "001", "010", "100", "101"),
}

THEMES = {
    "neon": "Neon dashboard (current design)",
    "pixel-art": "Pixel art adventure",
    "anime": "Anime portrait with eyelid blink",
    "anime-pixel": "Adult pixel art anime portrait with eyelid blink",
    "anime-pixel-chibi": "Chibi pixel art anime portrait with eyelid blink",
    "anime-pixel-detail": "Detailed adult pixel art portrait with eyelid blink",
}

PIXEL_PORTRAIT_THEMES = ("anime-pixel", "anime-pixel-chibi", "anime-pixel-detail")
PORTRAIT_THEMES = ("anime", *PIXEL_PORTRAIT_THEMES)


class AnimePalette(NamedTuple):
    hue_shift: int
    paper: tuple[int, int, int]
    dark: tuple[int, int, int]
    light: tuple[int, int, int]
    frame: tuple[int, int, int]
    frame_light: tuple[int, int, int]
    primary: tuple[int, int, int]
    secondary: tuple[int, int, int]
    badge: tuple[int, int, int]
    badge_edge: tuple[int, int, int]
    idle: tuple[int, int, int]
    working: tuple[int, int, int]
    setup: tuple[int, int, int]
    card: tuple[int, int, int]
    card_edge: tuple[int, int, int]
    ink: tuple[int, int, int]
    muted: tuple[int, int, int]
    bar_bg: tuple[int, int, int]
    footer: tuple[int, int, int]


ANIME_PALETTES = {
    "purple": AnimePalette(
        hue_shift=0, paper=(20, 12, 24), dark=(7, 5, 12), light=(116, 62, 112),
        frame=(93, 43, 83), frame_light=(218, 126, 184), primary=(245, 74, 138),
        secondary=(195, 100, 183), badge=(46, 25, 48), badge_edge=(145, 75, 132),
        idle=(220, 133, 206), working=(255, 92, 141), setup=(245, 191, 102),
        card=(33, 20, 39), card_edge=(99, 55, 95), ink=(255, 236, 247),
        muted=(202, 169, 199), bar_bg=(74, 46, 72), footer=(211, 173, 203),
    ),
    "red": AnimePalette(
        hue_shift=66, paper=(24, 10, 16), dark=(10, 4, 8), light=(123, 55, 66),
        frame=(92, 33, 45), frame_light=(229, 120, 139), primary=(255, 67, 94),
        secondary=(208, 90, 111), badge=(50, 19, 25), badge_edge=(145, 53, 65),
        idle=(232, 128, 143), working=(255, 80, 101), setup=(246, 201, 123),
        card=(36, 17, 24), card_edge=(106, 41, 53), ink=(255, 237, 237),
        muted=(211, 166, 172), bar_bg=(78, 40, 49), footer=(218, 171, 177),
    ),
    "blue": AnimePalette(
        hue_shift=221, paper=(9, 14, 28), dark=(4, 6, 17), light=(58, 78, 139),
        frame=(34, 48, 104), frame_light=(132, 152, 232), primary=(87, 149, 255),
        secondary=(146, 129, 238), badge=(20, 29, 57), badge_edge=(76, 100, 185),
        idle=(149, 165, 249), working=(88, 159, 255), setup=(246, 201, 123),
        card=(17, 23, 44), card_edge=(52, 67, 127), ink=(236, 241, 255),
        muted=(161, 175, 218), bar_bg=(41, 52, 87), footer=(163, 178, 224),
    ),
    "green": AnimePalette(
        hue_shift=151, paper=(10, 21, 18), dark=(4, 10, 9), light=(62, 116, 91),
        frame=(28, 81, 59), frame_light=(133, 210, 162), primary=(69, 206, 136),
        secondary=(68, 177, 170), badge=(19, 40, 30), badge_edge=(64, 135, 99),
        idle=(133, 221, 163), working=(71, 225, 138), setup=(246, 201, 123),
        card=(17, 35, 25), card_edge=(47, 102, 71), ink=(236, 251, 238),
        muted=(160, 201, 170), bar_bg=(37, 72, 50), footer=(166, 208, 175),
    ),
}

_PIXEL_GLYPHS = {
    **_DIGITS,
    "A": ("010", "101", "111", "101", "101"),
    "B": ("110", "101", "110", "101", "110"),
    "C": ("011", "100", "100", "100", "011"),
    "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"),
    "F": ("111", "100", "110", "100", "100"),
    "G": ("011", "100", "101", "101", "011"),
    "H": ("101", "101", "111", "101", "101"),
    "I": ("111", "010", "010", "010", "111"),
    "J": ("001", "001", "001", "101", "010"),
    "K": ("101", "101", "110", "101", "101"),
    "L": ("100", "100", "100", "100", "111"),
    "M": ("101", "111", "111", "101", "101"),
    "N": ("101", "111", "111", "111", "101"),
    "O": ("010", "101", "101", "101", "010"),
    "P": ("110", "101", "110", "100", "100"),
    "Q": ("010", "101", "101", "111", "011"),
    "R": ("110", "101", "110", "101", "101"),
    "S": ("011", "100", "010", "001", "110"),
    "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"),
    "V": ("101", "101", "101", "101", "010"),
    "W": ("101", "101", "111", "111", "101"),
    "X": ("101", "101", "010", "101", "101"),
    "Y": ("101", "101", "010", "010", "010"),
    "Z": ("111", "001", "010", "100", "111"),
    "!": ("010", "010", "010", "000", "010"),
    "?": ("110", "001", "010", "000", "010"),
    ".": ("000", "000", "000", "000", "010"),
    ":": ("000", "010", "000", "010", "000"),
    "-": ("000", "000", "111", "000", "000"),
    "+": ("000", "010", "111", "010", "000"),
    "/": ("001", "001", "010", "100", "100"),
    "@": ("01110", "10001", "10111", "10101", "01111"),
    "_": ("000", "000", "000", "000", "111"),
    " ": ("000", "000", "000", "000", "000"),
}


def _reset_display_text(resets_at: int | None, window_duration_mins: int | None, language: str = "en") -> str:
    if resets_at is None:
        return "--"
    reset_at = datetime.fromtimestamp(resets_at).astimezone()
    if window_duration_mins is not None and window_duration_mins <= 1_440:
        return reset_at.strftime("%H:%M")
    return reset_at.strftime("%d/%m" if language == "es" else "%m/%d")


def _reset_time_remaining(window: UsageWindow, now: datetime) -> float | None:
    """Return the share of the quota window left before its next reset."""
    if window.resets_at is None or window.window_duration_mins is None or window.window_duration_mins <= 0:
        return None
    duration_seconds = window.window_duration_mins * 60
    seconds_left = window.resets_at - now.timestamp()
    return min(1.0, max(0.0, seconds_left / duration_seconds))


def _reset_expiry_rows(
    snapshot: UsageSnapshot,
    now: datetime,
    limit: int = 3,
    language: str = "en",
) -> tuple[tuple[str, ...], int]:
    credits = snapshot.reset_credits.credits
    if not credits:
        return (), 0

    def expiry_order(credit: ResetCredit) -> tuple[int, int]:
        if not credit.expiration_known:
            return (2, 0)
        if credit.expires_at is None:
            return (1, 0)
        return (0, credit.expires_at)

    ordered = sorted(credits, key=expiry_order)[: snapshot.reset_credits.available_count]
    rows: list[str] = []
    for index, credit in enumerate(ordered[:limit], start=1):
        if not credit.expiration_known:
            expiry = display_text("DATE N/A", language)
        elif credit.expires_at is None:
            expiry = display_text("NO EXPIRY", language)
        else:
            expiry_at = datetime.fromtimestamp(credit.expires_at).astimezone()
            days_left = max(0, math.ceil((credit.expires_at - now.timestamp()) / 86_400))
            date = expiry_at.strftime("%d/%m/%y" if language == "es" else "%m/%d/%y")
            expiry = f"{date} {days_left}D"
        rows.append(f"{index} {expiry}")
    return tuple(rows), max(0, snapshot.reset_credits.available_count - len(rows))


def _quota_remaining_percent(window: UsageWindow) -> int:
    """Codex reports usedPercent; the display shows the available share."""
    return max(0, min(100, 100 - window.used_percent))


def _draw_progress_bar(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fraction: float | None,
    track: tuple[int, int, int],
    fill: tuple[int, int, int],
    radius: int = 0,
) -> None:
    """Draw a filled meter for quota or time remaining."""
    left, top, right, bottom = box
    draw.rounded_rectangle(box, radius=radius, fill=track)
    if fraction is None:
        return
    fill_width = round((right - left + 1) * max(0.0, min(1.0, fraction)))
    if fill_width > 0:
        draw.rounded_rectangle(
            (left, top, left + fill_width - 1, bottom),
            radius=radius,
            fill=fill,
        )


def _draw_vertical_progress_bar(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fraction: float | None,
    track: tuple[int, int, int],
    fill: tuple[int, int, int],
    radius: int = 0,
) -> None:
    """Draw a bottom-up meter for the time remaining until refill."""
    left, top, right, bottom = box
    draw.rounded_rectangle(box, radius=radius, fill=track)
    if fraction is None:
        return
    fill_height = round((bottom - top + 1) * max(0.0, min(1.0, fraction)))
    if fill_height > 0:
        draw.rounded_rectangle(
            (left, bottom - fill_height + 1, right, bottom),
            radius=radius,
            fill=fill,
        )


def _bar_color(used: int, accent: tuple[int, int, int]) -> tuple[int, int, int]:
    if used >= 90:
        return (255, 91, 119)
    if used >= 75:
        return (255, 190, 76)
    return accent


def _draw_big_percent(
    draw: ImageDraw.ImageDraw,
    value: int,
    box: tuple[int, int, int, int],
    color: tuple[int, int, int],
) -> None:
    text = f"{value}%"
    scale = 2
    gap = 2
    glyph_width = 3 * scale
    glyph_height = 5 * scale
    total_width = len(text) * glyph_width + (len(text) - 1) * gap
    left, top, right, bottom = box
    x = left + (right - left - total_width) // 2
    y = top + (bottom - top - glyph_height) // 2

    for character in text:
        pattern = _DIGITS[character]
        for row, pixels in enumerate(pattern):
            for column, pixel in enumerate(pixels):
                if pixel == "1":
                    draw.rectangle(
                        (
                            x + column * scale,
                            y + row * scale,
                            x + (column + 1) * scale - 1,
                            y + (row + 1) * scale - 1,
                        ),
                        fill=color,
                    )
        x += glyph_width + gap


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    left: int,
    right: int,
    y: int,
    color: tuple[int, int, int],
) -> None:
    bounds = draw.textbbox((0, 0), text, font=font)
    width = bounds[2] - bounds[0]
    x = left + (right - left + 1 - width) // 2 - bounds[0]
    draw.text((x, y), text, font=font, fill=color)


def _draw_account_footer(
    draw: ImageDraw.ImageDraw,
    snapshot: UsageSnapshot,
    color: tuple[int, int, int],
    pixel_art: bool = False,
) -> None:
    """Identify the quota account without overlapping the plan or frame."""
    font = _anime_font(8, pixel_art=pixel_art)
    left, right = 9, WIDTH - 10
    available_width = right - left + 1
    email = snapshot.account_email or ""
    email = "".join(character for character in email if character.isprintable()).strip().upper()

    def width(text: str) -> int:
        bounds = draw.textbbox((0, 0), text, font=font)
        return bounds[2] - bounds[0]

    def text_y(text: str) -> int:
        bounds = draw.textbbox((0, 0), text, font=font)
        # Center the visible ink in rows 113–121, including email descenders.
        return 113 + (9 - (bounds[3] - bounds[1])) // 2 - bounds[1]

    plan = f"PLAN {(snapshot.plan_type or '--').upper()}"
    # Reserve the plan's space first so long addresses never hide it.
    email_width = available_width - width(plan) - 8
    if width(email) > email_width:
        prefix = email
        while prefix and width(prefix + "...") > email_width:
            prefix = prefix[:-1]
        email = prefix + "..."
    if email:
        draw.text((left, text_y(email)), email, font=font, fill=color)
    draw.text((right - width(plan) + 1, text_y(plan)), plan, font=font, fill=color)


def _draw_text_centered_at(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    center_x: float,
    y: int,
    color: tuple[int, int, int],
) -> None:
    bounds = draw.textbbox((0, 0), text, font=font)
    width = bounds[2] - bounds[0]
    x = round(center_x - width / 2 - bounds[0])
    draw.text((x, y), text, font=font, fill=color)


def _draw_window(
    draw: ImageDraw.ImageDraw,
    font: ImageFont.ImageFont,
    window: UsageWindow,
    box: tuple[int, int, int, int],
    now: datetime,
    accent: tuple[int, int, int],
    language: str = "en",
) -> None:
    left, top, right, bottom = box
    height = bottom - top
    color = _bar_color(window.used_percent, accent)

    draw.rounded_rectangle(box, radius=8, fill=CARD, outline=CARD_EDGE, width=1)
    _draw_vertical_progress_bar(
        draw,
        (left + 7, top + 8, left + 10, top + height - 8),
        _reset_time_remaining(window, now),
        track=(34, 43, 62),
        fill=(93, 160, 198),
        radius=1,
    )

    label = window.label.upper()[:8]
    draw.text((left + 16, top + 8), label, font=font, fill=MUTED)
    left_label = display_text("LEFT", language)
    left_width = draw.textbbox((0, 0), left_label, font=font)[2]
    draw.text((right - left_width - 8, top + 8), left_label, font=font, fill=(89, 108, 141))

    quota_left = _quota_remaining_percent(window)
    _draw_big_percent(
        draw,
        quota_left,
        (left + 13, top + 20, right - 7, top + 42),
        TEXT,
    )

    bar_left = left + 16
    bar_right = right - 8
    bar_top = top + 45
    bar_bottom = bar_top + 7
    _draw_progress_bar(
        draw,
        (bar_left, bar_top, bar_right, bar_bottom),
        quota_left / 100,
        track=(43, 53, 74),
        fill=color,
        radius=3,
    )

    reset = _reset_display_text(window.resets_at, window.window_duration_mins, language)
    reset_font = _anime_font(7) if right - left < 100 else font
    reset_text = f"{display_text('RESET', language)} {reset}"
    if language == "es":
        # Keep the longer label clear of the refill-time meter, and center it
        # on the same content region as the quota bar.
        reset_font = _anime_font(6) if right - left < 100 else font
        _draw_centered_text(draw, reset_text, reset_font, bar_left, bar_right, bottom - 15, (194, 207, 229))
    else:
        _draw_centered_text(draw, reset_text, reset_font, left, right, bottom - 15, (194, 207, 229))


def _render_neon(
    snapshot: UsageSnapshot,
    now: datetime | None = None,
    activity: CodexActivity | None = None,
    animation_frame: int = 0,
    language: str = "en",
) -> Image.Image:
    now = now or datetime.now().astimezone()
    activity = activity or read_activity()
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    # A slim cyan-to-violet top rule gives the dark screen a little energy.
    for x in range(WIDTH):
        mix = x / max(1, WIDTH - 1)
        color = tuple(round(ACCENTS[0][i] * (1 - mix) + ACCENTS[1][i] * mix) for i in range(3))
        draw.line((x, 0, x, 2), fill=color)

    # Pixel mark and title.
    draw.rectangle((9, 9, 12, 12), fill=ACCENTS[0])
    draw.rectangle((14, 9, 17, 12), fill=(73, 168, 203))
    draw.rectangle((9, 14, 12, 17), fill=(73, 168, 203))
    draw.rectangle((14, 14, 17, 17), fill=ACCENTS[1])
    draw.text((23, 8), "CODEX", font=font, fill=TEXT)
    draw.text((23, 20), display_text("USAGE", language), font=font, fill=MUTED)

    status_label = display_text("WORK", language) if activity.working else display_text("IDLE", language) if activity.hooks_installed else display_text("SETUP", language)
    status_color = (71, 225, 162) if activity.working else (111, 136, 174) if activity.hooks_installed else (255, 190, 76)
    status_width = draw.textbbox((0, 0), status_label, font=font)[2]
    badge_left = WIDTH - 8 - status_width - 21
    draw.rounded_rectangle((badge_left, 8, WIDTH - 8, 25), radius=6, fill=(22, 31, 52), outline=(43, 58, 84))
    icon_left, icon_top = badge_left + 5, 13
    if activity.working:
        spinner = ((icon_left + 2, icon_top), (icon_left + 4, icon_top + 2), (icon_left + 2, icon_top + 4), (icon_left, icon_top + 2))
        for index, (dot_x, dot_y) in enumerate(spinner):
            dot_color = status_color if index == animation_frame % len(spinner) else (57, 93, 105)
            draw.rectangle((dot_x, dot_y, dot_x + 1, dot_y + 1), fill=dot_color)
    else:
        draw.ellipse((icon_left + 1, icon_top + 1, icon_left + 4, icon_top + 4), fill=status_color)
    draw.text((badge_left + 12, 12), status_label, font=font, fill=status_color)
    draw.line((8, 32, WIDTH - 8, 32), fill=(31, 42, 63), width=1)

    windows = list(snapshot.windows[:2])
    if len(windows) == 2:
        card_boxes = ((7, 39, 78, 108), (82, 39, 153, 108))
    elif len(windows) == 1:
        card_boxes = ((8, 39, 152, 108),)
    else:
        draw.rounded_rectangle((8, 43, WIDTH - 8, 99), radius=8, fill=CARD, outline=CARD_EDGE)
        draw.text((18, 67), display_text("NO USAGE DATA", language), font=font, fill=(255, 190, 76))
        card_boxes = ()

    for index, (window, box) in enumerate(zip(windows, card_boxes)):
        _draw_window(draw, font, window, box, now, ACCENTS[min(index, len(ACCENTS) - 1)], language)

    # Leave a few pixels of physical safe area below the footer; the MiniToo
    # can crop the last row or two at the bottom edge depending on alignment.
    draw.line((8, 111, WIDTH - 8, 111), fill=(31, 42, 63), width=1)
    _draw_account_footer(draw, snapshot, (112, 132, 166))
    return image


def _pixel_text_width(text: str, scale: int = 1) -> int:
    """Measure bitmap text, including the wider email at-sign."""
    advances = sum(len(_PIXEL_GLYPHS.get(character, _PIXEL_GLYPHS["?"])[0]) + 1 for character in text.upper())
    return max(0, (advances - 1) * scale)


def _draw_pixel_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    color: tuple[int, int, int] | int,
    scale: int = 1,
) -> int:
    """Draw a tiny bitmap font and return the occupied width."""
    text = text.upper()
    glyph_x = x
    for character in text:
        pattern = _PIXEL_GLYPHS.get(character, _PIXEL_GLYPHS["?"])
        for row, pixels in enumerate(pattern):
            for column, pixel in enumerate(pixels):
                if pixel == "1":
                    draw.rectangle(
                        (
                            glyph_x + column * scale,
                            y + row * scale,
                            glyph_x + (column + 1) * scale - 1,
                            y + (row + 1) * scale - 1,
                        ),
                        fill=color,
                    )
        glyph_x += (len(pattern[0]) + 1) * scale
    return _pixel_text_width(text, scale)


def _draw_pixel_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    center_x: int,
    y: int,
    color: tuple[int, int, int],
    scale: int = 1,
) -> None:
    width = _pixel_text_width(text, scale)
    _draw_pixel_text(draw, text, center_x - width // 2, y, color, scale=scale)


def _draw_pixel_mascot(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    activity: CodexActivity,
    animation_frame: int,
) -> None:
    scale = 3
    bob = 1 if animation_frame in (1, 2) else 0
    y += bob
    draw.rectangle((x + 4, y + 25, x + 21, y + 27), fill=(7, 13, 27))

    body = (
        "..BBBB..",
        ".BWWWWB.",
        "BWCEWCEB",
        "BWCEWCEB",
        "BWWMMWWB",
        ".BWWWWB.",
        "..B..B..",
        ".BB..BB.",
    )
    edge = (30, 167, 181)
    face = (164, 225, 231)
    eye = (218, 255, 255)
    detail = (53, 143, 169)
    mouth = (19, 69, 91)
    if not activity.working and not activity.hooks_installed:
        edge, detail, eye = (199, 145, 53), (255, 198, 74), (255, 229, 153)
    elif not activity.working:
        edge, detail = (51, 133, 155), (45, 105, 130)
    if not activity.working and animation_frame == 3:
        eye = (83, 148, 164)

    colors = {"B": edge, "W": face, "C": detail, "E": eye, "M": mouth}
    for row, pixels in enumerate(body):
        for column, pixel in enumerate(pixels):
            if pixel != ".":
                draw.rectangle(
                    (
                        x + column * scale,
                        y + row * scale,
                        x + (column + 1) * scale - 1,
                        y + (row + 1) * scale - 1,
                    ),
                    fill=colors[pixel],
                )

    if activity.working:
        # Tiny sparks orbit the bot as it works through a turn.
        spark_positions = ((37, 33), (35, 51), (39, 42), (32, 31))
        spark_x, spark_y = spark_positions[animation_frame % len(spark_positions)]
        spark_color = (255, 220, 94) if animation_frame % 2 == 0 else (83, 239, 218)
        draw.rectangle((spark_x, spark_y, spark_x + 2, spark_y + 2), fill=spark_color)
        if animation_frame % 2:
            draw.rectangle((x - 3, y + 9, x - 1, y + 11), fill=(83, 239, 218))
    elif not activity.hooks_installed:
        warning_positions = ((27, -2), (28, -4), (29, -2), (28, 0))
        warning_x, warning_y = warning_positions[animation_frame % len(warning_positions)]
        _draw_pixel_text(draw, "!", x + warning_x, y + warning_y, (255, 205, 86), scale=2)


def _draw_pixel_window(
    draw: ImageDraw.ImageDraw,
    window: UsageWindow,
    box: tuple[int, int, int, int],
    now: datetime,
    accent: tuple[int, int, int],
    language: str = "en",
) -> None:
    left, top, right, bottom = box
    draw.rectangle(box, fill=(13, 23, 43), outline=(42, 69, 101), width=1)
    _draw_vertical_progress_bar(
        draw,
        (left + 2, top + 6, left + 4, bottom - 5),
        _reset_time_remaining(window, now),
        track=(31, 46, 68),
        fill=(81, 159, 195),
    )
    # A blocky corner pixel preserves the retro HUD shape.
    draw.rectangle((right - 5, bottom - 3, right - 2, bottom - 2), fill=accent)

    center_x = (left + right) // 2
    label = f"{window.label.upper()[:6]} {display_text('LEFT', language)}"
    _draw_pixel_centered_text(draw, label, center_x, top + 3, (129, 171, 205))
    quota_left = _quota_remaining_percent(window)
    _draw_pixel_centered_text(draw, f"{quota_left}%", center_x, top + 11, TEXT, scale=2)
    reset_text = f"{display_text('RESET', language)} {_reset_display_text(window.resets_at, window.window_duration_mins, language)}"
    _draw_pixel_centered_text(draw, reset_text, center_x, top + 36, (161, 195, 219))

    available_width = right - left - 10
    gap = 2 if available_width > 70 else 1
    segment_width = (available_width - gap * 9) // 10
    segments_width = segment_width * 10 + gap * 9
    bar_left = center_x - segments_width // 2

    def draw_segments(y: int, height: int, fraction: float | None, fill: tuple[int, int, int]) -> None:
        filled_segments = max(0.0, min(10.0, (fraction or 0) * 10))
        for segment in range(10):
            segment_left = bar_left + segment * (segment_width + gap)
            draw.rectangle(
                (segment_left, y, segment_left + segment_width - 1, y + height - 1),
                fill=(31, 46, 68),
            )
            filled_pixels = round(segment_width * max(0.0, min(1.0, filled_segments - segment)))
            if filled_pixels:
                draw.rectangle(
                    (segment_left, y, segment_left + filled_pixels - 1, y + height - 1),
                    fill=fill,
                )

    draw_segments(top + 25, 7, quota_left / 100, _bar_color(window.used_percent, accent))


def _render_pixel_art(
    snapshot: UsageSnapshot,
    now: datetime,
    activity: CodexActivity,
    animation_frame: int,
    language: str = "en",
) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), (7, 12, 27))
    draw = ImageDraw.Draw(image)

    # A deep-blue pixel frame and twinkling stars establish the retro game look.
    draw.rectangle((3, 3, WIDTH - 4, HEIGHT - 5), outline=(34, 56, 87), width=1)
    draw.rectangle((5, 5, WIDTH - 6, HEIGHT - 7), outline=(17, 34, 58), width=1)
    stars = ((10, 30), (151, 33), (146, 51), (22, 57), (4, 97), (156, 82), (31, 108), (137, 108))
    for index, (star_x, star_y) in enumerate(stars):
        bright = (index + animation_frame) % 4 == 0
        color = (98, 211, 238) if bright else (39, 71, 111)
        draw.rectangle((star_x, star_y, star_x + 1, star_y + 1), fill=color)

    draw.rectangle((7, 7, WIDTH - 8, 26), fill=(10, 20, 39))
    draw.rectangle((11, 10, 13, 12), fill=(66, 231, 214))
    draw.rectangle((14, 13, 16, 15), fill=(169, 119, 255))
    _draw_pixel_text(draw, "CODEX", 21, 8, TEXT, scale=2)
    _draw_pixel_text(draw, display_text("USAGE ARCADE", language), 21, 22, (94, 147, 185))

    if activity.working:
        status, detail, status_color = display_text("WORK", language), display_text("THINKING", language), (70, 235, 174)
    elif activity.hooks_installed:
        status, detail, status_color = display_text("IDLE", language), display_text("ON STANDBY", language), (106, 174, 211)
    else:
        status, detail, status_color = display_text("SETUP", language), display_text("INSTALL HOOKS", language), (255, 195, 76)
    draw.rectangle((118, 11, 121, 14), fill=status_color)
    _draw_pixel_text(draw, status, 125, 10, status_color)
    draw.line((8, 28, WIDTH - 8, 28), fill=(35, 56, 82), width=1)

    _draw_pixel_mascot(draw, 10, 31, activity, animation_frame)
    _draw_pixel_text(draw, status, 43, 33, status_color, scale=2)
    _draw_pixel_text(draw, detail, 43, 46, (144, 174, 203))
    draw.line((8, 57, WIDTH - 8, 57), fill=(35, 56, 82), width=1)

    windows = list(snapshot.windows[:2])
    if len(windows) == 2:
        boxes = ((7, 61, 78, 106), (82, 61, 153, 106))
    elif len(windows) == 1:
        boxes = ((8, 61, 152, 106),)
    else:
        draw.rectangle((8, 65, WIDTH - 8, 103), fill=(13, 23, 43), outline=(42, 69, 101))
        _draw_pixel_text(draw, display_text("NO USAGE DATA", language), 18, 80, (255, 195, 76), scale=2)
        boxes = ()
    for index, (window, box) in enumerate(zip(windows, boxes)):
        _draw_pixel_window(draw, window, box, now, ACCENTS[min(index, len(ACCENTS) - 1)], language)

    draw.line((8, 111, WIDTH - 8, 111), fill=(35, 56, 82), width=1)
    _draw_account_footer(draw, snapshot, (102, 139, 174), pixel_art=True)
    return image


class _PixelFont(ImageFont.ImageFont):
    """Expose the dashboard's bitmap glyphs through Pillow's text API."""

    def __init__(self, size: int) -> None:
        self.height = max(5, size - 2)
        self.scale = 2 if size >= 10 else 1

    def getbbox(self, text: str, *args: object, **kwargs: object) -> tuple[int, int, int, int]:
        width = _pixel_text_width(text, self.scale)
        return (0, 0, width, self.height)

    def getlength(self, text: str, *args: object, **kwargs: object) -> float:
        return float(self.getbbox(text)[2])

    def getmask(self, text: str, mode: str = "", *args: object, **kwargs: object):
        width = max(1, self.getbbox(text)[2])
        mask = Image.new("L", (width, 5 * self.scale), 0)
        _draw_pixel_text(ImageDraw.Draw(mask), text, 0, 0, 255, scale=self.scale)
        return mask.resize((width, self.height), Image.Resampling.NEAREST).im


@lru_cache(maxsize=32)
def _anime_font(size: int, bold: bool = False, pixel_art: bool = False) -> ImageFont.ImageFont:
    """Choose bitmap glyphs or a smooth system font with a portable fallback."""
    if pixel_art:
        return _PixelFont(size)
    suffix = "Arial Bold.ttf" if bold else "Arial.ttf"
    font_path = f"/System/Library/Fonts/Supplemental/{suffix}"
    try:
        return ImageFont.truetype(font_path, size=size)
    except OSError:
        try:
            return ImageFont.load_default(size=size)
        except TypeError:  # Pillow versions before scalable default fonts.
            return ImageFont.load_default()


def _anime_reset_text(resets_at: int | None, window_duration_mins: int | None, language: str = "en") -> str:
    return _reset_display_text(resets_at, window_duration_mins, language)


@lru_cache(maxsize=8)
def _open_anime_portrait(blinking: bool, pixel_art: bool = False, chibi: bool = False, detail: bool = False) -> Image.Image:
    """Load the matching open or closed portrait at native display size."""
    prefix = (
        "anime_pixel_detail_portrait" if detail else
        "anime_pixel_chibi_portrait" if chibi else
        "anime_pixel_portrait" if pixel_art else "anime_portrait"
    )
    filename = f"{prefix}_blink.png" if blinking else f"{prefix}.png"
    portrait_path = Path(__file__).parent / "assets" / filename
    with Image.open(portrait_path) as source:
        return source.convert("RGB")


@lru_cache(maxsize=32)
def _anime_portrait(blinking: bool, color: str, pixel_art: bool = False, chibi: bool = False, detail: bool = False) -> Image.Image:
    """Return the selected portrait palette, optionally with closed eyelids."""
    portrait = _open_anime_portrait(blinking, pixel_art, chibi, detail).copy()
    palette = ANIME_PALETTES[color]
    if palette.hue_shift:
        hsv = portrait.convert("HSV")
        recolored = []
        changed = []
        for hue, saturation, value in hsv.getdata():
            # Include the new bob's blue-violet shadows as well as highlights.
            tint = 160 <= hue <= 245 and saturation >= 50
            if tint:
                hue = (hue + palette.hue_shift) % 256
                saturation = min(255, round(saturation * 1.12))
            recolored.append((hue, saturation, value))
            changed.append(tint)
        hsv.putdata(recolored)
        tinted = hsv.convert("RGB")
        # Keep original skin/blush RGB values instead of rounding them through HSV.
        portrait.putdata([
            after if tint else before
            for before, after, tint in zip(portrait.getdata(), tinted.getdata(), changed)
        ])
    return portrait


def _draw_anime_mascot(
    image: Image.Image,
    x: int,
    y: int,
    activity: CodexActivity,
    animation_frame: int,
    anime_color: str,
    pixel_art: bool = False,
    chibi: bool = False,
    detail: bool = False,
) -> None:
    """Place one complete portrait frame for the blink animation."""
    del activity
    image.paste(_anime_portrait(animation_frame % 6 == 4, anime_color, pixel_art, chibi, detail), (x, y))


def _draw_anime_window(
    draw: ImageDraw.ImageDraw,
    window: UsageWindow,
    box: tuple[int, int, int, int],
    accent: tuple[int, int, int],
    palette: AnimePalette,
    now: datetime,
    pixel_art: bool = False,
    language: str = "en",
) -> None:
    left, top, right, bottom = box
    label_font = _anime_font(9, bold=True, pixel_art=pixel_art)
    value_font = _anime_font(10, bold=True, pixel_art=pixel_art)
    draw.rounded_rectangle(box, radius=0 if pixel_art else 5, fill=palette.card, outline=palette.card_edge, width=1)
    _draw_vertical_progress_bar(
        draw,
        (left + 3, top + 6, left + 5, bottom - 6),
        _reset_time_remaining(window, now),
        track=palette.bar_bg,
        fill=palette.idle,
        radius=0 if pixel_art else 1,
    )

    label = window.label.upper()[:4]
    draw.text((left + 9, top + 4), label, font=label_font, fill=palette.muted)
    quota_left = _quota_remaining_percent(window)
    percent = f"{quota_left}%"
    percent_width = draw.textbbox((0, 0), percent, font=value_font)[2]
    draw.text((right - percent_width - 6, top + 3), percent, font=value_font, fill=palette.ink)

    bar_left = left + 9
    bar_right = right - 6
    bar_top = top + 17
    bar_bottom = bar_top + 7
    _draw_progress_bar(
        draw,
        (bar_left, bar_top, bar_right, bar_bottom),
        quota_left / 100,
        track=palette.bar_bg,
        fill=_bar_color(window.used_percent, accent),
        radius=0 if pixel_art else 2,
    )

    reset = f"{display_text('RESET', language)} {_anime_reset_text(window.resets_at, window.window_duration_mins, language)}"
    reset_font = _anime_font(7, bold=True, pixel_art=pixel_art)
    _draw_centered_text(draw, reset, reset_font, left + (4 if language == "es" else 0), right, top + 27, palette.muted)


def _draw_anime_vertical_window(
    draw: ImageDraw.ImageDraw,
    window: UsageWindow,
    box: tuple[int, int, int, int],
    accent: tuple[int, int, int],
    palette: AnimePalette,
    now: datetime,
    pixel_art: bool = False,
    language: str = "en",
) -> None:
    """Use the full single-window panel for a bottom-up vertical meter."""
    left, top, right, bottom = box
    label_font = _anime_font(9, bold=True, pixel_art=pixel_art)
    value_font = _anime_font(10, bold=True, pixel_art=pixel_art)
    # Reserve a clear footer for the longer Spanish refill label. Both meters
    # stop above it so the text cannot crowd the side meter or the quota fill.
    meter_bottom = bottom - (20 if language == "es" else 16)
    time_meter_bottom = meter_bottom if language == "es" else bottom - 6
    draw.rounded_rectangle(box, radius=0 if pixel_art else 5, fill=palette.card, outline=palette.card_edge, width=1)
    _draw_vertical_progress_bar(
        draw,
        (left + 3, top + 6, left + 5, time_meter_bottom),
        _reset_time_remaining(window, now),
        track=palette.bar_bg,
        fill=palette.idle,
        radius=0 if pixel_art else 1,
    )

    label = window.label.upper()[:4]
    draw.text((left + 9, top + 4), label, font=label_font, fill=palette.muted)
    quota_left = _quota_remaining_percent(window)
    percent = f"{quota_left}%"

    meter_width = 30
    content_left = left + 7
    content_right = right - 3
    meter_left = content_left + (content_right - content_left - meter_width) // 2
    meter_right = meter_left + meter_width
    meter_center_x = (meter_left + meter_right) / 2
    _draw_text_centered_at(draw, percent, value_font, meter_center_x, top + 13, palette.ink)

    meter_top = top + 29
    draw.rounded_rectangle(
        (meter_left, meter_top, meter_right, meter_bottom),
        radius=0 if pixel_art else 4,
        fill=palette.bar_bg,
    )
    fill_height = round((meter_bottom - meter_top) * quota_left / 100)
    if fill_height > 0:
        draw.rounded_rectangle(
            (meter_left + 1, meter_bottom - fill_height, meter_right - 1, meter_bottom - 1),
            radius=0 if pixel_art else 3,
            fill=_bar_color(window.used_percent, accent),
        )

    reset = f"{display_text('RESET', language)} {_anime_reset_text(window.resets_at, window.window_duration_mins, language)}"
    reset_font = _anime_font(7, bold=True, pixel_art=pixel_art)
    _draw_text_centered_at(draw, reset, reset_font, meter_center_x, bottom - 12, palette.muted)


def _render_anime(
    snapshot: UsageSnapshot,
    now: datetime,
    activity: CodexActivity,
    animation_frame: int,
    anime_color: str,
    pixel_art: bool = False,
    chibi: bool = False,
    detail: bool = False,
    language: str = "en",
) -> Image.Image:
    palette = ANIME_PALETTES[anime_color]
    image = Image.new("RGB", (WIDTH, HEIGHT), palette.paper)
    draw = ImageDraw.Draw(image)
    title_font = _anime_font(12, bold=True, pixel_art=pixel_art)
    status_font = _anime_font(10, bold=True, pixel_art=pixel_art)
    caption_font = _anime_font(7, pixel_art=pixel_art)

    # Keep a compact palette-matched frame around the portrait and usage.
    draw.rectangle((2, 2, WIDTH - 3, HEIGHT - 3), outline=palette.dark, width=2)
    draw.rectangle((5, 5, WIDTH - 6, HEIGHT - 6), outline=palette.light, width=1)
    draw.text((9, 7), "CODEX", font=title_font, fill=palette.ink)
    draw.text((10, 22 if pixel_art else 20), display_text("USAGE", language), font=caption_font, fill=palette.idle)

    if activity.working:
        status, status_color = display_text("WORKING", language), palette.working
    elif activity.hooks_installed:
        status, status_color = display_text("IDLE", language), palette.idle
    else:
        status, status_color = display_text("SETUP", language), palette.setup
    draw.rounded_rectangle((76, 5, 152, 26), radius=0 if pixel_art else 6, fill=palette.badge, outline=palette.badge_edge)
    if activity.working:
        equalizer_frames = (
            (3, 6, 4), (5, 3, 7), (7, 4, 2),
            (4, 7, 5), (2, 5, 7), (6, 2, 4),
        )
        for index, height in enumerate(equalizer_frames[animation_frame % 6]):
            x = 82 + index * 3
            draw.rounded_rectangle((x, 20 - height, x + 1, 19), radius=0 if pixel_art else 1, fill=status_color)
    else:
        if pixel_art:
            draw.rectangle((82, 12, 88, 18), fill=status_color)
        else:
            draw.ellipse((82, 12, 88, 18), fill=status_color)
    status_width = draw.textbbox((0, 0), status, font=status_font)[2]
    status_x = 94 + (54 - status_width) // 2
    draw.text((status_x, 11 if pixel_art else 9), status, font=status_font, fill=status_color)

    frame_box = (4, 27, 89, 109)
    draw.rectangle(frame_box, fill=palette.dark, outline=palette.dark, width=2)
    draw.rectangle((7, 29, 86, 108), fill=palette.frame, outline=palette.frame_light, width=1)
    _draw_anime_mascot(image, 8, 30, activity, animation_frame, anime_color, pixel_art, chibi, detail)

    windows = list(snapshot.windows[:2])
    if len(windows) == 1:
        _draw_anime_vertical_window(draw, windows[0], (92, 29, 153, 109), palette.primary, palette, now, pixel_art, language)
    elif windows:
        accents = (palette.primary, palette.secondary)
        boxes = ((92, 29, 153, 67), (92, 71, 153, 109))
        for index, (window, box) in enumerate(zip(windows, boxes)):
            _draw_anime_window(draw, window, box, accents[min(index, 1)], palette, now, pixel_art, language)
    else:
        draw.rounded_rectangle((92, 42, 153, 96), radius=0 if pixel_art else 5, fill=palette.card, outline=palette.card_edge)
        message_font = _anime_font(8, bold=True, pixel_art=pixel_art)
        draw.text((97, 62), display_text("NO USAGE", language), font=message_font, fill=palette.primary)
        draw.text((104, 74), display_text("DATA", language), font=message_font, fill=palette.primary)

    draw.line((8, 111, WIDTH - 8, 111), fill=palette.light, width=1)
    _draw_account_footer(draw, snapshot, palette.footer, pixel_art=pixel_art)
    return image


def _render_neon_reset_credits(snapshot: UsageSnapshot, now: datetime, language: str = "en") -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    title_font = _anime_font(9, bold=True)
    count_font = _anime_font(22, bold=True)
    row_font = _anime_font(9, bold=True)
    caption_font = _anime_font(7, bold=True)
    for x in range(WIDTH):
        mix = x / max(1, WIDTH - 1)
        color = tuple(round(ACCENTS[0][i] * (1 - mix) + ACCENTS[1][i] * mix) for i in range(3))
        draw.line((x, 0, x, 2), fill=color)

    draw.rectangle((9, 9, 12, 12), fill=ACCENTS[0])
    draw.rectangle((14, 9, 17, 12), fill=(73, 168, 203))
    draw.rectangle((9, 14, 12, 17), fill=(73, 168, 203))
    draw.rectangle((14, 14, 17, 17), fill=ACCENTS[1])
    draw.text((23, 8), "CODEX", font=font, fill=TEXT)
    draw.text((23, 20), display_text("RESET CREDITS", language), font=font, fill=MUTED)
    draw.line((8, 31, WIDTH - 8, 31), fill=(31, 42, 63), width=1)

    draw.rounded_rectangle((8, 37, 152, 106), radius=8, fill=CARD, outline=CARD_EDGE)
    _draw_centered_text(draw, display_text("AVAILABLE", language), _anime_font(7, bold=True) if language == "es" else font, 12, 58, 44, MUTED)
    _draw_centered_text(draw, str(snapshot.reset_credits.available_count), count_font, 12, 58, 54, ACCENTS[0])
    _draw_centered_text(draw, display_text("RESETS", language), _anime_font(7, bold=True) if language == "es" else font, 12, 58, 84, TEXT)
    draw.line((65, 43, 65, 100), fill=CARD_EDGE, width=1)
    draw.text((73, 44), display_text("EXPIRY / DAYS LEFT", language), font=caption_font, fill=MUTED)

    rows, more_count = _reset_expiry_rows(snapshot, now, language=language)
    if rows:
        for index, row in enumerate(rows):
            draw.text((73, 56 + index * 12), row, font=row_font, fill=TEXT)
        if more_count:
            draw.text((73, 94), display_text("+{count} MORE", language, count=more_count), font=font, fill=MUTED)
    else:
        draw.text((73, 60), display_text("DATE N/A", language), font=title_font, fill=(255, 190, 76))

    draw.line((8, 111, WIDTH - 8, 111), fill=(31, 42, 63), width=1)
    _draw_account_footer(draw, snapshot, (112, 132, 166))
    return image


def _render_pixel_reset_credits(
    snapshot: UsageSnapshot,
    now: datetime,
    animation_frame: int = 0,
    language: str = "en",
) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), (7, 12, 27))
    draw = ImageDraw.Draw(image)
    draw.rectangle((3, 3, WIDTH - 4, HEIGHT - 5), outline=(34, 56, 87), width=1)
    draw.rectangle((5, 5, WIDTH - 6, HEIGHT - 7), outline=(17, 34, 58), width=1)
    stars = ((10, 30), (151, 33), (146, 51), (22, 57), (4, 97), (156, 82), (31, 108), (137, 108))
    for index, (star_x, star_y) in enumerate(stars):
        color = (98, 211, 238) if (index + animation_frame) % 4 == 0 else (39, 71, 111)
        draw.rectangle((star_x, star_y, star_x + 1, star_y + 1), fill=color)

    draw.rectangle((7, 7, WIDTH - 8, 26), fill=(10, 20, 39))
    _draw_pixel_text(draw, "CODEX", 21, 8, TEXT, scale=2)
    _draw_pixel_text(draw, display_text("RESET VAULT", language), 21, 22, (94, 147, 185))
    draw.line((8, 28, WIDTH - 8, 28), fill=(35, 56, 82), width=1)

    draw.rectangle((9, 36, 151, 106), fill=(13, 23, 43), outline=(42, 69, 101))
    _draw_pixel_centered_text(draw, display_text("AVAILABLE {count}", language, count=snapshot.reset_credits.available_count), 80, 39, (98, 211, 238), scale=1)
    _draw_pixel_centered_text(draw, display_text("DATE / DAYS LEFT", language), 80, 48, (94, 147, 185), scale=1)
    draw.line((15, 57, WIDTH - 15, 57), fill=(35, 56, 82), width=1)
    rows, more_count = _reset_expiry_rows(snapshot, now, language=language)
    if rows:
        for index, row in enumerate(rows):
            row = row.replace("/", "-")
            _draw_pixel_centered_text(draw, row, 80, 60 + index * 12, TEXT, scale=2)
        if more_count:
            _draw_pixel_centered_text(draw, display_text("+{count} MORE", language, count=more_count), 80, 98, (94, 147, 185))
    else:
        _draw_pixel_centered_text(draw, display_text("EXPIRY DATE N/A", language), 80, 72, (255, 195, 76), scale=2)

    draw.line((8, 111, WIDTH - 8, 111), fill=(35, 56, 82), width=1)
    _draw_account_footer(draw, snapshot, (102, 139, 174), pixel_art=True)
    return image


def _render_anime_reset_credits(
    snapshot: UsageSnapshot,
    activity: CodexActivity,
    anime_color: str,
    now: datetime,
    pixel_art: bool = False,
    chibi: bool = False,
    detail: bool = False,
    language: str = "en",
) -> Image.Image:
    palette = ANIME_PALETTES[anime_color]
    image = Image.new("RGB", (WIDTH, HEIGHT), palette.paper)
    draw = ImageDraw.Draw(image)
    title_font = _anime_font(12, bold=True, pixel_art=pixel_art)
    caption_font = _anime_font(7, pixel_art=pixel_art)
    small_font = _anime_font(7, bold=True, pixel_art=pixel_art)
    row_font = _anime_font(8, bold=True, pixel_art=pixel_art)
    count_font = _anime_font(8, bold=True, pixel_art=pixel_art)

    draw.rectangle((2, 2, WIDTH - 3, HEIGHT - 3), outline=palette.dark, width=2)
    draw.rectangle((5, 5, WIDTH - 6, HEIGHT - 6), outline=palette.light, width=1)
    draw.text((9, 7), "CODEX", font=title_font, fill=palette.ink)
    draw.text((10, 22 if pixel_art else 20), display_text("RESET CREDITS", language), font=caption_font, fill=palette.idle)

    count = snapshot.reset_credits.available_count
    draw.rounded_rectangle((76, 5, 152, 26), radius=0 if pixel_art else 6, fill=palette.badge, outline=palette.badge_edge)
    _draw_centered_text(draw, display_text("RESET BANK", language), count_font, 77, 151, 11, palette.working)

    frame_box = (4, 27, 89, 109)
    draw.rectangle(frame_box, fill=palette.dark, outline=palette.dark, width=2)
    draw.rectangle((7, 29, 86, 108), fill=palette.frame, outline=palette.frame_light, width=1)
    _draw_anime_mascot(image, 8, 30, activity, animation_frame=0, anime_color=anime_color, pixel_art=pixel_art, chibi=chibi, detail=detail)

    draw.rounded_rectangle((92, 29, 153, 109), radius=0 if pixel_art else 5, fill=palette.card, outline=palette.card_edge)
    _draw_centered_text(draw, display_text("AVAILABLE", language), small_font, 93, 152, 34, palette.muted)
    _draw_centered_text(draw, str(count), _anime_font(14, bold=True, pixel_art=pixel_art), 93, 152, 42, palette.ink)
    draw.line((99, 59, 146, 59), fill=palette.card_edge, width=1)
    _draw_centered_text(draw, display_text("DATE / DAYS", language), small_font, 93, 152, 60, palette.muted)
    rows, more_count = _reset_expiry_rows(snapshot, now, language=language)
    if rows:
        for index, row in enumerate(rows):
            _draw_centered_text(draw, row, row_font, 93, 152, 69 + index * 9, palette.ink)
        if more_count:
            _draw_centered_text(draw, display_text("+{count} MORE", language, count=more_count), small_font, 93, 152, 97, palette.muted)
    else:
        _draw_centered_text(draw, display_text("EXPIRY DATE N/A", language), small_font, 93, 152, 74, palette.setup)

    draw.line((8, 111, WIDTH - 8, 111), fill=palette.light, width=1)
    _draw_account_footer(draw, snapshot, palette.footer, pixel_art=pixel_art)
    return image


def render_reset_credits(
    snapshot: UsageSnapshot,
    activity: CodexActivity,
    theme: str = "neon",
    anime_color: str = "purple",
    now: datetime | None = None,
    language: str = "en",
) -> Image.Image:
    """Render the periodic reset-credit screen in the selected display theme."""
    if theme not in THEMES:
        raise ValueError(f"Unknown theme {theme!r}; choose from: {', '.join(THEMES)}")
    if theme in PORTRAIT_THEMES and anime_color not in ANIME_PALETTES:
        raise ValueError(f"Unknown anime color {anime_color!r}; choose from: {', '.join(ANIME_PALETTES)}")
    now = now or datetime.now().astimezone()
    if theme == "pixel-art":
        return _render_pixel_reset_credits(snapshot, now, language=language)
    if theme in PORTRAIT_THEMES:
        return _render_anime_reset_credits(
            snapshot, activity, anime_color, now, pixel_art=theme != "anime",
            chibi=theme == "anime-pixel-chibi", detail=theme == "anime-pixel-detail", language=language,
        )
    return _render_neon_reset_credits(snapshot, now, language=language)


def render_usage(
    snapshot: UsageSnapshot,
    now: datetime | None = None,
    activity: CodexActivity | None = None,
    animation_frame: int = 0,
    theme: str = "neon",
    anime_color: str = "purple",
    language: str = "en",
) -> Image.Image:
    """Render one 160x128 frame using a named display theme."""
    if theme not in THEMES:
        raise ValueError(f"Unknown theme {theme!r}; choose from: {', '.join(THEMES)}")
    if theme in PORTRAIT_THEMES and anime_color not in ANIME_PALETTES:
        raise ValueError(f"Unknown anime color {anime_color!r}; choose from: {', '.join(ANIME_PALETTES)}")
    now = now or datetime.now().astimezone()
    activity = activity or read_activity()
    if theme == "pixel-art":
        return _render_pixel_art(snapshot, now, activity, animation_frame, language=language)
    if theme in PORTRAIT_THEMES:
        return _render_anime(
            snapshot, now, activity, animation_frame, anime_color, pixel_art=theme != "anime",
            chibi=theme == "anime-pixel-chibi", detail=theme == "anime-pixel-detail", language=language,
        )
    return _render_neon(snapshot, now, activity, animation_frame, language=language)


def render_usage_frames(
    snapshot: UsageSnapshot,
    now: datetime | None = None,
    activity: CodexActivity | None = None,
    theme: str = "neon",
    anime_color: str = "purple",
    language: str = "en",
) -> tuple[Image.Image, ...]:
    """Create native frames for a theme's activity animation."""
    activity = activity or read_activity()
    if theme not in THEMES:
        raise ValueError(f"Unknown theme {theme!r}; choose from: {', '.join(THEMES)}")
    if theme in PORTRAIT_THEMES and anime_color not in ANIME_PALETTES:
        raise ValueError(f"Unknown anime color {anime_color!r}; choose from: {', '.join(ANIME_PALETTES)}")
    now = now or datetime.now().astimezone()
    if theme in PORTRAIT_THEMES:
        # The closed-eye frame is the fifth frame; keeping five frames preserves
        # the blink cadence while avoiding a redundant final open-eye frame.
        frame_indices = range(5)
    elif theme == "pixel-art" and not activity.working:
        # Two alternating frames keep the idle bob and star twinkle while
        # halving the bytes sent for the most common pixel-art state.
        frame_indices = (0, 2)
    elif activity.working:
        frame_indices = range(4)
    else:
        frame_indices = (0,)
    return tuple(
        render_usage(snapshot, now, activity, animation_frame=index, theme=theme, anime_color=anime_color, language=language)
        for index in frame_indices
    )


def encode_for_minitoo(
    image: Image.Image,
    quality: int = 88,
    pixel_art: bool = False,
    preserve_detail: bool = False,
) -> bytes:
    """Encode the frame at its native 160x128 wire dimensions, without stretching."""
    from io import BytesIO

    if image.size != (WIDTH, HEIGHT):
        image = ImageOps.pad(image.convert("RGB"), (WIDTH, HEIGHT), color=BACKGROUND, centering=(0.5, 0.5))
    frame = image.convert("RGB")
    buffer = BytesIO()
    if pixel_art:
        # Keep chroma detail for crisp pixel edges and text, but avoid the
        # oversized near-lossless JPEGs produced by quality 100.
        frame.save(buffer, format="JPEG", quality=quality, subsampling=0, optimize=True)
    else:
        frame.save(
            buffer,
            format="JPEG",
            quality=quality,
            subsampling=0 if preserve_detail else -1,
            optimize=True,
        )
    return buffer.getvalue()
