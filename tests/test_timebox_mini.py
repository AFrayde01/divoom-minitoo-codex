import unittest
from datetime import datetime, timezone

from PIL import Image

from divoom_minitoo_codex.appserver import ResetCredits, UsageSnapshot, UsageWindow
from divoom_minitoo_codex.timebox_mini import (
    TIMEBOX_COLORS,
    _DIGITS,
    _LARGE_DIGITS,
    encode_timebox_rgb444,
    render_timebox_reset_credits,
    render_timebox_usage,
    render_timebox_working,
)


class TimeBoxMiniColorTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 5, 12, tzinfo=timezone.utc)
        self.snapshot = UsageSnapshot(
            plan_type="pro",
            windows=(UsageWindow("7D", 0, 10_080, int(self.now.timestamp()) + 86_400),),
            reset_credits=ResetCredits(3, ()),
        )

    def test_accents_are_distinct_and_use_saturated_red_and_green(self):
        self.assertEqual(TIMEBOX_COLORS["red"], (255, 0, 0))
        self.assertEqual(TIMEBOX_COLORS["green"], (0, 255, 0))
        self.assertEqual(len(set(TIMEBOX_COLORS.values())), len(TIMEBOX_COLORS))

    def test_each_screen_uses_the_selected_rgb_accent(self):
        renderers = {
            "bars": lambda color: render_timebox_usage(self.snapshot, self.now, color=color, view="bars"),
            "percent": lambda color: render_timebox_usage(
                self.snapshot, self.now, color=color, view="nearest-percent"
            ),
            "resets": lambda color: render_timebox_reset_credits(self.snapshot, color=color),
            "working": lambda color: render_timebox_working(color=color, animation_frame=0),
        }
        for color_name, rgb in TIMEBOX_COLORS.items():
            for screen, renderer in renderers.items():
                with self.subTest(color=color_name, screen=screen):
                    image = renderer(color_name)
                    colors = dict((pixel, count) for count, pixel in image.getcolors(121))
                    self.assertGreater(colors.get(rgb, 0), 0)

    def test_nine_percent_glyph_has_a_complete_bottom_row(self):
        for used_percent, rightmost_nine_pixel in ((91, 4), (21, 6)):
            snapshot = UsageSnapshot(
                plan_type="pro",
                windows=(UsageWindow("7D", used_percent, 10_080, int(self.now.timestamp()) + 86_400),),
            )
            image = render_timebox_usage(snapshot, self.now, color="green", view="nearest-percent")
            with self.subTest(percent_remaining=100 - used_percent):
                self.assertEqual(image.getpixel((rightmost_nine_pixel, 7)), TIMEBOX_COLORS["green"])

    def test_all_numeral_glyphs_are_complete_and_connected(self):
        for name, glyphs, expected_width, expected_height in (
            ("small", _DIGITS, 3, 5),
            ("large", _LARGE_DIGITS, 5, 7),
        ):
            for digit in "0123456789":
                with self.subTest(font=name, digit=digit):
                    rows = glyphs[digit]
                    self.assertEqual(len(rows), expected_height)
                    self.assertTrue(all(len(row) == expected_width for row in rows))
                    pixels = {
                        (x, y)
                        for y, row in enumerate(rows)
                        for x, value in enumerate(row)
                        if value == "1"
                    }
                    visited = set()
                    pending = [next(iter(pixels))]
                    while pending:
                        x, y = pending.pop()
                        if (x, y) in visited:
                            continue
                        visited.add((x, y))
                        pending.extend(
                            neighbor
                            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
                            if neighbor in pixels and neighbor not in visited
                        )
                    self.assertEqual(visited, pixels)

        self.assertEqual(_DIGITS["9"][-1], "111")
        self.assertEqual(_LARGE_DIGITS["9"][-1], "11111")

    def test_percent_sign_uses_the_original_compact_diagonal(self):
        self.assertEqual(_DIGITS["%"], ("101", "001", "010", "100", "101"))

    def test_rgb444_stream_preserves_selected_rgb_channel_order(self):
        for color_name, rgb in TIMEBOX_COLORS.items():
            with self.subTest(color=color_name):
                stream = encode_timebox_rgb444(Image.new("RGB", (11, 11), rgb))
                self.assertEqual(len(stream), 182)
                nibbles = [nibble for byte in stream for nibble in (byte & 0x0F, byte >> 4)]
                expected = tuple(channel >> 4 for channel in rgb)
                self.assertEqual(nibbles[:3], list(expected))
                self.assertEqual(nibbles[3:6], list(expected))
                self.assertEqual(nibbles[363], 0)  # Padding nibble after 121 RGB pixels.


if __name__ == "__main__":
    unittest.main()
