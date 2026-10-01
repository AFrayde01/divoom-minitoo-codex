import io
import os
import unittest
from unittest.mock import patch

from divoom_minitoo_codex.terminal import TerminalUI


class TtyStream(io.StringIO):
    def isatty(self):
        return True


class TerminalTests(unittest.TestCase):
    def welcome(self, stream):
        ui = TerminalUI(stream)
        ui.startup(device="MiniToo", theme="anime-pixel-chibi", color="green", interval=60, log_path="/tmp/private.log")
        ui.step("Connecting…")
        ui.report("Display updated")
        return stream.getvalue()

    def test_interactive_welcome_contains_configuration(self):
        with patch.dict(os.environ, {"TERM": "xterm-256color"}, clear=True):
            output = self.welcome(TtyStream())
        self.assertIn("DIVOOM × CODEX", output)
        self.assertIn("anime-pixel-chibi", output)
        self.assertIn("green", output)
        self.assertIn("\033[", output)

    def test_redirected_output_is_plain_and_compact(self):
        output = self.welcome(io.StringIO())
        self.assertEqual(output, "Display updated\n")

    def test_no_color_and_dumb_term_are_respected(self):
        with patch.dict(os.environ, {"TERM": "xterm", "NO_COLOR": ""}, clear=True):
            self.assertNotIn("\033[", self.welcome(TtyStream()))
        with patch.dict(os.environ, {"TERM": "dumb"}, clear=True):
            self.assertEqual(self.welcome(TtyStream()), "Display updated\n")
