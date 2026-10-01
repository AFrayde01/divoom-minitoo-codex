#!/usr/bin/env python3
"""Generate README previews from the actual MiniToo and TimeBox renderers."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image

from divoom_minitoo_codex.activity import CodexActivity
from divoom_minitoo_codex.appserver import ResetCredit, ResetCredits, UsageSnapshot, UsageWindow
from divoom_minitoo_codex.render import render_reset_credits, render_usage, render_usage_frames
from divoom_minitoo_codex.timebox_mini import (
    render_timebox_reset_credits,
    render_timebox_usage,
    render_timebox_working,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "images"


def save(image: Image.Image, name: str) -> None:
    """Save a two-times-size PNG so native 160x128 pixels remain clear in README."""
    image.convert("RGB").resize((320, 256), Image.Resampling.NEAREST).save(
        OUTPUT / name,
        optimize=True,
    )


def save_timebox_animation(
    images: list[Image.Image],
    name: str,
    durations: list[int] | None = None,
) -> None:
    """Save renderer frames as an enlarged, looping TimeBox Mini GIF."""
    frames = [
        image.convert("RGB").resize((440, 440), Image.Resampling.NEAREST)
        for image in images
    ]
    palette = frames[0].quantize(colors=16, method=Image.Quantize.FASTOCTREE)
    indexed_frames = [
        frame.quantize(palette=palette, dither=Image.Dither.NONE)
        for frame in frames
    ]
    indexed_frames[0].save(
        OUTPUT / name,
        format="GIF",
        save_all=True,
        append_images=indexed_frames[1:],
        duration=durations or (2200, 2200, 1200),
        loop=0,
        disposal=2,
        optimize=True,
    )


def save_anime_animation(images: tuple[Image.Image, ...], name: str = "anime-demo.gif") -> None:
    """Preview the actual anime frames with a shared palette and 600 ms cadence."""
    frames = [
        frame.convert("RGB").resize((320, 256), Image.Resampling.NEAREST)
        for frame in images
    ]
    palette = frames[0].quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    indexed = [
        frame.quantize(palette=palette, dither=Image.Dither.NONE)
        for frame in frames
    ]
    indexed[0].save(
        OUTPUT / name,
        save_all=True,
        append_images=indexed[1:],
        duration=600,
        loop=0,
        disposal=2,
        optimize=True,
    )


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    now = datetime(2026, 9, 29, 12, 0).astimezone()
    snapshot = UsageSnapshot(
        plan_type="plus",
        windows=(
            UsageWindow("5H", 38, 300, int((now + timedelta(hours=3, minutes=10)).timestamp())),
            UsageWindow("7D", 21, 10_080, int((now + timedelta(days=4, hours=6)).timestamp())),
        ),
        reset_credits=ResetCredits(
            available_count=3,
            credits=(
                ResetCredit(int((now + timedelta(days=9)).timestamp())),
                ResetCredit(int((now + timedelta(days=18)).timestamp())),
                ResetCredit(int((now + timedelta(days=29)).timestamp())),
            ),
        ),
    )
    activity = CodexActivity(working=True, hooks_installed=True)

    for theme in ("neon", "pixel-art"):
        save(render_usage(snapshot, now, activity, theme=theme), f"{theme}.png")
        save(render_reset_credits(snapshot, activity, theme=theme, now=now), f"{theme}-resets.png")

    for theme in ("anime", "anime-pixel", "anime-pixel-chibi"):
        for color in ("purple", "red", "blue", "green"):
            save(
                render_usage(snapshot, now, activity, theme=theme, anime_color=color),
                f"{theme}-{color}.png",
            )
        save_anime_animation(
            render_usage_frames(snapshot, now, activity, theme=theme), f"{theme}-demo.gif"
        )
        single_window = UsageSnapshot(plan_type="pro", windows=(snapshot.windows[1],))
        if theme == "anime-pixel":
            save_anime_animation(
                render_usage_frames(
                    single_window, now, activity, theme=theme, anime_color="green"
                ),
                "anime-pixel-green-pro-demo.gif",
            )
        save(
            render_usage(single_window, now, activity, theme=theme, anime_color="purple"),
            f"{theme}-single-window.png",
        )
        save(
            render_reset_credits(snapshot, activity, theme=theme, anime_color="purple", now=now),
            f"{theme}-resets.png",
        )

    default_usage_frames = [
        *(render_timebox_working(color="cyan", animation_frame=frame) for frame in range(8)),
        render_timebox_usage(snapshot, now, color="cyan"),
        render_timebox_usage(snapshot, now, color="cyan", view="nearest-percent"),
        render_timebox_reset_credits(snapshot, color="cyan"),
    ]
    timebox_frame_durations = [240] * 8 + [900, 900, 900]
    save_timebox_animation(default_usage_frames, "timebox-mini-demo.gif", timebox_frame_durations)

    single_weekly = UsageSnapshot(
        plan_type="pro",
        windows=(snapshot.windows[1],),
        reset_credits=snapshot.reset_credits,
    )
    weekly_usage_frames = [
        *(render_timebox_working(color="cyan", animation_frame=frame) for frame in range(8)),
        render_timebox_usage(single_weekly, now, color="cyan"),
        render_timebox_usage(single_weekly, now, color="cyan", view="nearest-percent"),
        render_timebox_reset_credits(single_weekly, color="cyan"),
    ]
    save_timebox_animation(weekly_usage_frames, "timebox-mini-7d-demo.gif", timebox_frame_durations)
    print(f"Wrote theme gallery to {OUTPUT}")


if __name__ == "__main__":
    main()
