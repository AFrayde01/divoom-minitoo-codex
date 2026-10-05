import unittest
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageChops

from divoom_minitoo_codex.activity import CodexActivity
from divoom_minitoo_codex.appserver import ResetCredit, ResetCredits, UsageSnapshot, UsageWindow
from divoom_minitoo_codex.render import ANIME_PALETTES, PORTRAIT_THEMES, THEMES, render_reset_credits, render_usage, render_usage_frames


class DisplayTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
        self.activity = CodexActivity(working=True, hooks_installed=True)
        self.snapshot = UsageSnapshot(
            plan_type="pro", windows=(UsageWindow("7D", 19, 10080, int(self.now.timestamp()) + 86400),),
            reset_credits=ResetCredits(2, (ResetCredit(int(self.now.timestamp()) + 86400 * 3),)),
        )

    def test_all_themes_render_usage_and_resets_at_native_size(self):
        for theme in THEMES:
            for render in (render_usage, render_reset_credits):
                with self.subTest(theme=theme, renderer=render.__name__):
                    image = render(self.snapshot, now=self.now, activity=self.activity, theme=theme)
                    self.assertEqual(image.size, (160, 128))
                    self.assertEqual(image.mode, "RGB")

    def test_portrait_colors_keep_cheeks_and_background_identical_during_blink(self):
        for theme in ("anime", "anime-pixel", "anime-pixel-chibi"):
            boxes = {
                "anime": ((9, 33, 27, 49), (38, 27, 63, 44)),
            "anime-pixel": ((25, 31, 47, 44), (52, 38, 69, 51)),
            "anime-pixel-chibi": ((20, 38, 42, 55), (54, 35, 71, 53), (41, 61, 56, 69)),
            }[theme]
            for color in ANIME_PALETTES:
                frames = render_usage_frames(self.snapshot, self.now, activity=self.activity, theme=theme, anime_color=color)
                opened = frames[0].crop((8, 30, 86, 108))
                blink = frames[4].crop((8, 30, 86, 108))
                diff = ImageChops.difference(opened, blink)
                self.assertIsNotNone(diff.getbbox(), (theme, color, "blink is missing"))
                for y in range(78):
                    for x in range(78):
                        if not any(left <= x < right and top <= y < bottom for left, top, right, bottom in boxes):
                            self.assertEqual(opened.getpixel((x, y)), blink.getpixel((x, y)), (theme, color, x, y))

    def test_adult_and_chibi_are_distinct_but_share_dashboard_layout(self):
        adult = render_usage(self.snapshot, self.now, activity=self.activity, theme="anime-pixel")
        chibi = render_usage(self.snapshot, self.now, activity=self.activity, theme="anime-pixel-chibi")
        diff = ImageChops.difference(adult, chibi)
        self.assertIsNotNone(diff.getbbox())
        diff.paste((0, 0, 0), (8, 30, 86, 108))
        self.assertIsNone(diff.getbbox())

    def test_plus_plan_two_window_bars_use_the_selected_palette_family(self):
        plus_snapshot = UsageSnapshot(
            plan_type="plus",
            windows=(
                UsageWindow("5H", 38, 300, int(self.now.timestamp()) + 7200),
                UsageWindow("7D", 21, 10_080, int(self.now.timestamp()) + 4 * 86_400),
            ),
        )
        for theme in PORTRAIT_THEMES:
            for color, palette in ANIME_PALETTES.items():
                with self.subTest(theme=theme, color=color):
                    image = render_usage(
                        plus_snapshot, self.now, self.activity, theme=theme, anime_color=color,
                    )
                    self.assertEqual(image.getpixel((120, 90)), palette.secondary)
        self.assertGreater(ANIME_PALETTES["green"].secondary[1], ANIME_PALETTES["green"].secondary[2] + 30)
        self.assertGreater(ANIME_PALETTES["blue"].secondary[2], ANIME_PALETTES["blue"].secondary[1] + 50)

    def test_header_subtitles_have_at_least_three_blank_rows_below_codex(self):
        for theme in THEMES:
            for render in (render_usage, render_reset_credits):
                with self.subTest(theme=theme, renderer=render.__name__):
                    image = render(self.snapshot, now=self.now, activity=self.activity, theme=theme)
                    # Common empty region after title ink and before subtitle
                    # ink, excluding each theme's left decorative icon.
                    region = image.crop((24, 18, 55, 21))
                    self.assertEqual(len(region.getcolors(region.width * region.height)), 1)

    def test_runtime_pixel_portraits_are_native_rgb_frames(self):
        assets = Path(__file__).resolve().parents[1] / "src/divoom_minitoo_codex/assets"
        for name in ("anime_pixel_portrait", "anime_pixel_chibi_portrait"):
            for suffix in ("", "_blink"):
                with Image.open(assets / f"{name}{suffix}.png") as image:
                    self.assertEqual(image.size, (78, 78))
                    self.assertEqual(image.mode, "RGB")
                    if name == "anime_pixel_chibi_portrait":
                        self.assertLessEqual(len(image.getcolors(78 * 78)), 16)
