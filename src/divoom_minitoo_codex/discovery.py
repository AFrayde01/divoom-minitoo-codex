"""Discover supported paired Divoom speakers using macOS IOBluetooth."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .i18n import tr


class DiscoveryError(RuntimeError):
    pass


@dataclass(frozen=True)
class DivoomDevice:
    name: str
    address: str
    model: str
    connected: bool


def normalize_address(address: str, language: str = "en") -> str:
    normalized = address.strip().replace("-", ":").upper()
    if not re.fullmatch(r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}", normalized):
        raise DiscoveryError(tr("Use a Bluetooth MAC address such as AA:BB:CC:DD:EE:FF.", language))
    return normalized


def _model(name: str) -> str | None:
    hint = re.sub(r"[^a-z0-9]", "", name.casefold())
    if "minitoo" in hint:
        return "minitoo"
    if "timeboxmini" in hint:
        return "timebox-mini"
    return None


def discover_devices(language: str = "en") -> list[DivoomDevice]:
    if sys.platform != "darwin":
        raise DiscoveryError(tr("Automatic Bluetooth detection requires macOS.", language))
    helper = Path(__file__).resolve().parents[2] / "build" / "divoom-devices"
    if not helper.is_file():
        raise DiscoveryError(tr("Bluetooth detection helper is missing. Run ./scripts/install.sh once, or provide --address.", language))
    try:
        result = subprocess.run([str(helper)], capture_output=True, text=True, timeout=12)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DiscoveryError(tr("Could not read paired Bluetooth devices: {detail}", language, detail=exc)) from exc
    if result.returncode:
        raise DiscoveryError(tr("Bluetooth detection failed. Check macOS Bluetooth permission and pairing.", language))
    try:
        records = json.loads(result.stdout)["devices"]
        if not isinstance(records, list):
            raise ValueError("Expected a device list")
        devices: dict[str, DivoomDevice] = {}
        for record in records:
            if not isinstance(record, dict):
                continue
            name, address = record.get("name"), record.get("address")
            if not isinstance(name, str) or not isinstance(address, str):
                continue
            model = _model(name)
            if model is None:
                continue
            try:
                address = normalize_address(address)
            except DiscoveryError:
                continue
            # Terminal labels must remain one line even for renamed devices.
            name = "".join(char for char in name if char.isprintable())
            devices[address] = DivoomDevice(name, address, model, record.get("connected") is True)
    except (ValueError, KeyError, TypeError) as exc:
        raise DiscoveryError(tr("Bluetooth detection returned an invalid device inventory.", language)) from exc
    return sorted(devices.values(), key=lambda item: (not item.connected, item.model != "minitoo", item.name.casefold(), item.address))
