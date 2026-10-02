"""Remember display choices separately for each Divoom model."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def preferences_path(device: str) -> Path:
    if device not in ("minitoo", "timebox-mini"):
        raise ValueError(f"Unknown Divoom device: {device}")
    return Path.home() / "Library" / "Application Support" / "divoom-minitoo-codex" / f"{device}.json"


def load_preferences(device: str) -> dict[str, str]:
    path = preferences_path(device)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    value = json.loads(text)
    if not isinstance(value, dict) or value.get("version") != 1:
        raise ValueError("Unsupported display preferences format.")
    return {
        key: value[key]
        for key in ("theme", "color")
        if isinstance(value.get(key), str)
    }


def load_language() -> str:
    path = preferences_path("minitoo").with_name("language.json")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return "en"
    if not isinstance(value, dict) or value.get("version") != 1 or value.get("language") not in ("en", "es"):
        raise ValueError("Unsupported language preferences format.")
    return value["language"]


def save_language(language: str) -> None:
    if language not in ("en", "es"):
        raise ValueError(f"Unsupported language: {language}")
    _save(preferences_path("minitoo").with_name("language.json"), {"language": language})


def save_preferences(device: str, *, theme: str, color: str | None) -> None:
    _save(preferences_path(device), {"theme": theme, "color": color})


def _save(path: Path, values: dict[str, str | None]) -> None:
    """Atomically save preferences with private file permissions."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.stem}-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump({"version": 1, **values}, output, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
