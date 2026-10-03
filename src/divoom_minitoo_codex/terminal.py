"""Terminal selection menus, welcome screen and compact live status."""

from __future__ import annotations

import os
import select
import shutil
import sys
import unicodedata
from datetime import datetime
from typing import TextIO

from .i18n import tr


class TerminalUI:
    def __init__(
        self,
        stream: TextIO | None = None,
        *,
        sent: str = "compact",
        input_stream: TextIO | None = None,
        language: str = "en",
    ) -> None:
        self.stream = stream if stream is not None else sys.stdout
        self.input_stream = input_stream if input_stream is not None else sys.stdin
        self.interactive = bool(self.stream.isatty() and os.environ.get("TERM") != "dumb")
        self.color = self.interactive and "NO_COLOR" not in os.environ
        self.can_prompt = self.interactive and self.input_stream.isatty()
        self.detailed = sent == "detailed"
        self._status_active = False
        self.language = language

    def tr(self, text: str, **values: object) -> str:
        return tr(text, self.language, **values)

    def _style(self, text: str, code: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.color else text

    def _fit(self, text: str) -> str:
        """Clip visible text so cursor-based rows cannot wrap."""
        width = max(1, shutil.get_terminal_size(fallback=(80, 24)).columns - 1)
        used = 0
        for index, char in enumerate(text):
            used += 0 if unicodedata.combining(char) else 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
            if used >= width:
                return text[:index] + "…" if index < len(text) - 1 or used > width else text
        return text

    def choose(
        self, title: str, options: tuple[tuple[str, str], ...], default: str,
        *, show_values: bool = True,
    ) -> str:
        """Navigate a live menu with arrows; fall back to line input if needed."""
        if not self.can_prompt:
            return default
        self.finish()
        try:
            import termios
            import tty
            descriptor = self.input_stream.fileno()
            previous = termios.tcgetattr(descriptor)
        except (ImportError, OSError, ValueError, AttributeError):
            return self._choose_line(title, options, default, show_values=show_values)
        selected = next(index for index, (value, _) in enumerate(options) if value == default)
        print(self._style(self._fit(f"  {title}"), "1;38;5;147"), file=self.stream)

        def draw() -> None:
            for index, (value, label) in enumerate(options):
                row = f"  {'›' if index == selected else ' '} {index + 1}. {value if show_values else label}"
                if show_values and label and label != value:
                    row += f"  ·  {label}"
                print(
                    "\r\033[2K" + self._style(self._fit(row), "1;38;5;117" if index == selected else "38;5;250"),
                    file=self.stream,
                )
            print(
                "\r\033[2K" + self._style(self._fit(self.tr("  ↑ ↓ move · Enter select · 1–9 jump · Esc/Q cancel")), "38;5;245"),
                file=self.stream, flush=True,
            )

        self.stream.write("\033[?25l")
        try:
            tty.setcbreak(descriptor)
            draw()
            while True:
                key = self._read_key(descriptor)
                if key == "enter":
                    break
                if key == "cancel":
                    raise KeyboardInterrupt
                if key == "up":
                    selected = (selected - 1) % len(options)
                elif key == "down":
                    selected = (selected + 1) % len(options)
                elif key.isdecimal() and 1 <= int(key) <= len(options):
                    selected = int(key) - 1
                else:
                    continue
                self.stream.write(f"\033[{len(options) + 1}A")
                draw()
            # Collapse the menu to the chosen value before showing the next one.
            self.stream.write(f"\033[{len(options) + 1}A\r\033[J")
            value, label = options[selected]
            row = f"  ✓ {value if show_values else label}"
            if show_values and label and label != value:
                row += f"  ·  {label}"
            print(self._style(self._fit(row), "38;5;117"), file=self.stream)
            print(file=self.stream, flush=True)
            return value
        finally:
            termios.tcsetattr(descriptor, termios.TCSADRAIN, previous)
            self.stream.write("\033[?25h")
            self.stream.flush()

    def _read_key(self, descriptor: int) -> str:
        key = os.read(descriptor, 1)
        if not key:
            raise EOFError(self.tr("Selection input closed."))
        if key in (b"\r", b"\n"):
            return "enter"
        if key in (b"q", b"Q", b"\x03"):
            return "cancel"
        if key == b"\x1b":
            sequence = b""
            for _ in range(2):
                if not select.select([descriptor], [], [], 0.1)[0]:
                    break
                sequence += os.read(descriptor, 1)
            if sequence in (b"[A", b"OA"):
                return "up"
            if sequence in (b"[B", b"OB"):
                return "down"
            return "cancel" if not sequence else ""
        return key.decode("ascii", errors="ignore")

    def _choose_line(
        self, title: str, options: tuple[tuple[str, str], ...], default: str,
        *, show_values: bool = True,
    ) -> str:
        selected = next(index for index, (value, _) in enumerate(options, 1) if value == default)
        names = {value.casefold(): value for value, _ in options}
        names.update({label.casefold(): value for value, label in options if label})
        default_label = dict(options)[default] if not show_values else default
        print(self._style(f"  {title}", "1;38;5;147"), file=self.stream)
        for index, (value, label) in enumerate(options, 1):
            marker = "›" if value == default else " "
            row = f"  {marker} {index}. {value if show_values else label}"
            if show_values and label and label != value:
                row += f"  ·  {label}"
            print(self._style(row, "38;5;117" if value == default else "38;5;250"), file=self.stream)
        while True:
            print(
                self.tr("  Number or name [{selected}] (Enter keeps {default}): ", selected=selected, default=default_label),
                end="", file=self.stream, flush=True,
            )
            answer = self.input_stream.readline()
            if not answer:
                raise EOFError(self.tr("Selection input closed."))
            answer = answer.strip().lower()
            if not answer:
                chosen = default
            elif answer.isdecimal() and 1 <= int(answer) <= len(options):
                chosen = options[int(answer) - 1][0]
            elif answer in names:
                chosen = names[answer]
            else:
                print(self.tr("  Choose one of the listed numbers or names."), file=self.stream)
                continue
            print(file=self.stream)
            return chosen

    def ask(self, message: str) -> str:
        self.finish()
        print(f"  {message}: ", end="", file=self.stream, flush=True)
        answer = self.input_stream.readline()
        if not answer:
            raise EOFError(self.tr("Selection input closed."))
        return answer.strip()

    def startup(
        self, *, device: str, theme: str, color: str, interval: int,
        log_path: str, encoding: str | None = None, profile: str | None = None,
    ) -> None:
        if not self.interactive:
            return
        width = 58
        edge = self._style("│", "38;5;69")
        print(self._style("╭" + "─" * width + "╮", "38;5;69"), file=self.stream)
        rows = [
            ("  ◈  DIVOOM × CODEX", "1;38;5;147"),
            (self.tr("     Your usage, a little closer."), "38;5;245"),
            ("", "0"),
            (self.tr("  Device   {device}", device=device), "38;5;117"),
            (self.tr("  Theme    {theme}  ·  {color}", theme=self.tr(theme), color=self.tr(color)), "38;5;147"),
        ]
        if encoding is not None:
            rows.append((self.tr("  Format   {encoding}", encoding=encoding), "38;5;117"))
        if profile is not None:
            profile = profile if len(profile) <= 44 else profile[:41] + "..."
            rows.append((self.tr("  Account  {profile}", profile=profile), "38;5;117"))
        rows.extend((
            (self.tr("  Refresh  {interval}s  ·  activity hooks checked each second", interval=interval), "38;5;250"),
            (self.tr("  Output   {output}  ·  Ctrl+C to stop", output=self.tr("detailed" if self.detailed else "compact")), "38;5;250"),
        ))
        for text, style in rows:
            print(edge + self._style(text.ljust(width), style) + edge, file=self.stream)
        print(self._style("╰" + "─" * width + "╯", "38;5;69"), file=self.stream)
        print(self._style(self.tr("  Log: {path}\n", path=log_path), "38;5;245"), file=self.stream)

    def step(self, message: str) -> None:
        if self.interactive:
            print(self._style("  ◇ ", "38;5;117") + message, file=self.stream, flush=True)

    def update(self, message: str, *, compact_message: str | None = None) -> None:
        """Refresh one visible row; redirected/detailed output stays line-based."""
        if self.detailed or not self.interactive:
            self.report(message)
            return
        text = (compact_message if compact_message is not None else message).replace("\n", " ").replace("\r", " ")
        text = f"  • {datetime.now():%H:%M:%S}  {text}"
        text = self._fit(text)
        self.stream.write("\r\033[2K" + self._style(text, "38;5;117"))
        self.stream.flush()
        self._status_active = True

    def finish(self) -> None:
        """Leave the cursor on a new line before a message, prompt or exit."""
        if self._status_active:
            print(file=self.stream, flush=True)
            self._status_active = False

    def report(self, message: str, *, error: bool = False) -> None:
        self.finish()
        stream = sys.stderr if error else self.stream
        if self.interactive and stream.isatty():
            prefix = self._style("  ! " if error else "  • ", "38;5;203" if error else "38;5;117")
            print(prefix + message, file=stream, flush=True)
        else:
            print(message, file=stream)
