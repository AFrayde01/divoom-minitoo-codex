"""Run the real Swift transfer code against an in-memory RFCOMM channel."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(sys.platform == "darwin" and shutil.which("swiftc"), "requires macOS and Swift")
class SwiftBridgeTests(unittest.TestCase):
    def test_packet_parsing_chunk_retransmission_and_disconnect(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "Sources/MiniTooBridge.swift").read_text()
        # Keep production types and transfer logic; replace only the entry
        # point that normally opens Bluetooth and starts the localhost server.
        production, entry_point = source.split("\nlet arguments = CommandLine.arguments\n", 1)
        self.assertIn("bridge.start(resetBluetoothLink: resetBluetoothLink)", entry_point)
        harness = (root / "tests/MiniTooBridgeHarness.swift").read_text()
        with tempfile.TemporaryDirectory(prefix="divoom-bridge-check-") as directory:
            directory = Path(directory)
            script = directory / "main.swift"
            executable = directory / "bridge-check"
            script.write_text(production + "\n" + harness)
            build = subprocess.run(
                ["swiftc", "-module-cache-path", str(directory / "cache"), str(script),
                 "-framework", "IOBluetooth", "-framework", "Network", "-o", str(executable)],
                capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(build.returncode, 0, build.stderr)
            try:
                run = subprocess.run([str(executable)], capture_output=True, text=True, timeout=15)
            except subprocess.TimeoutExpired as exc:
                self.fail(f"Swift simulation timed out. Last bridge output: {exc.stderr!r}")
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("transfer simulations passed", run.stdout)


if __name__ == "__main__":
    unittest.main()
