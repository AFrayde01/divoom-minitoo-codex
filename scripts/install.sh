#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This version requires macOS (MiniToo and TimeBox Mini use Bluetooth Classic RFCOMM)." >&2
  exit 1
fi

command -v swiftc >/dev/null || {
  echo "Install Xcode Command Line Tools first: xcode-select --install" >&2
  exit 1
}

python3 -m venv .venv
.venv/bin/python -m pip install -e .

mkdir -p build
swiftc -O -module-cache-path build/swift-module-cache Sources/MiniTooBridge.swift -framework IOBluetooth -framework Network -o build/minitoo-bridge
swiftc -O -module-cache-path build/swift-module-cache Sources/TimeBoxMiniBridge.swift -framework IOBluetooth -framework Network -o build/timebox-mini-bridge
swiftc -O -module-cache-path build/swift-module-cache Sources/BluetoothDevices.swift -framework IOBluetooth -o build/divoom-devices

.venv/bin/python scripts/install_activity_hooks.py setup "$@"

echo "Installation complete."
echo "Run: ./start"
