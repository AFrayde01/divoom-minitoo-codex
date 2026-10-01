"""A compact terminal welcome screen with clean redirected output."""

from __future__ import annotations

import os
import sys
from typing import TextIO


class TerminalUI:
    def __init__(self, stream: TextIO | None = None) -> None:
        self.stream = stream if stream is not None else sys.stdout
        self.interactive = bool(self.stream.isatty() and os.environ.get("TERM") != "dumb")
        self.color = self.interactive and "NO_COLOR" not in os.environ

    def _style(self, text: str, code: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.color else text

    def startup(self, *, device: str, theme: str, color: str, interval: int, log_path: str) -> None:
        if not self.interactive:
            return
        width = 58
        edge = self._style("│", "38;5;69")
        print(self._style("╭" + "─" * width + "╮", "38;5;69"), file=self.stream)
        rows = (
            ("  ◈  DIVOOM × CODEX", "1;38;5;147"),
            ("     Your usage, a little closer.", "38;5;245"),
            ("", "0"),
            (f"  Device   {device}", "38;5;117"),
            (f"  Theme    {theme}  ·  {color}", "38;5;147"),
            (f"  Refresh  {interval}s  ·  activity hooks checked each second", "38;5;250"),
        )
        for text, style in rows:
            print(edge + self._style(text.ljust(width), style) + edge, file=self.stream)
        print(self._style("╰" + "─" * width + "╯", "38;5;69"), file=self.stream)
        print(self._style(f"  Log: {log_path}\n", "38;5;245"), file=self.stream)

    def step(self, message: str) -> None:
        if self.interactive:
            print(self._style("  ◇ ", "38;5;117") + message, file=self.stream, flush=True)

    def report(self, message: str, *, error: bool = False) -> None:
        stream = sys.stderr if error else self.stream
        if self.interactive and stream.isatty():
            prefix = self._style("  ! " if error else "  • ", "38;5;203" if error else "38;5;117")
            print(prefix + message, file=stream, flush=True)
        else:
            print(message, file=stream)
