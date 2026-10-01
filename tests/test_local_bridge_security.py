"""Exercise both real Swift loopback listeners with simulated Bluetooth."""

import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


@unittest.skipUnless(sys.platform == "darwin" and shutil.which("swiftc"), "requires macOS and Swift")
class LocalBridgeSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="divoom-ipc-check-")
        cls.directory = Path(cls.temp.name)
        cls.root = Path(__file__).resolve().parents[1]
        cls.executables = {}
        cls.production_executables = {}
        harness = (cls.root / "tests/LocalBridgeHarness.swift").read_text()
        for kind in ("MiniToo", "TimeBoxMini"):
            source = (cls.root / f"Sources/{kind}Bridge.swift").read_text()
            production = source.split("\nlet arguments = CommandLine.arguments\n", 1)[0]
            acknowledgements = ""
            if kind == "MiniToo":
                acknowledgements = '''
                channel.onWrite = { packet in
                    let bytes = Array(packet)
                    let response = bytes[4] == 0
                        ? Data([0x01,0x07,0x00,0x04,0x8B,0x55,0x00,0x01,0xEC,0x00,0x02])
                        : Data([0x01,0x09,0x00,0x04,0xBD,0x55,0x13,0x01,0x05,0x00,0x38,0x01,0x02])
                    var mutable = response
                    mutable.withUnsafeMutableBytes { buffer in
                        bridge.delegate.rfcommChannelData(nil, data: buffer.baseAddress, length: buffer.count)
                    }
                }
                '''
            main = cls.directory / "main.swift"
            main.write_text(production + "\n" + harness.replace("TEST_BRIDGE_TYPE", kind + "Bridge").replace("TEST_MINITOO_ACKS", acknowledgements))
            executable = cls.directory / kind
            result = subprocess.run(["swiftc", "-module-cache-path", str(cls.directory / "cache"), str(main),
                                     "-framework", "IOBluetooth", "-framework", "Network", "-o", str(executable)],
                                    capture_output=True, text=True, timeout=60)
            if result.returncode:
                raise AssertionError(result.stderr)
            cls.executables[kind] = executable
            main.write_text(source)
            production_executable = cls.directory / (kind + "-production")
            result = subprocess.run(["swiftc", "-module-cache-path", str(cls.directory / "cache"), str(main),
                                     "-framework", "IOBluetooth", "-framework", "Network", "-o", str(production_executable)],
                                    capture_output=True, text=True, timeout=60)
            if result.returncode:
                raise AssertionError(result.stderr)
            cls.production_executables[kind] = production_executable

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def request(self, port, body, *, eof=False, fragmented=False):
        with socket.create_connection(("127.0.0.1", port), timeout=2) as connection:
            data = json.dumps(body).encode() + (b"" if eof else b"\n")
            if fragmented:
                connection.sendall(data[:8])
                time.sleep(0.05)
                connection.sendall(data[8:])
            else:
                connection.sendall(data)
            if eof:
                connection.shutdown(socket.SHUT_WR)
            response = bytearray()
            while b"\n" not in response:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                response.extend(chunk)
            return json.loads(response.split(b"\n", 1)[0])

    def test_authentication_limits_timeouts_and_authorized_frames(self):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", 0))
            except PermissionError:
                if os.environ.get("DIVOOM_REQUIRE_LOOPBACK") == "1":
                    self.fail("the required loopback security check cannot bind a local port")
                self.skipTest("sandbox blocks loopback listeners; run this check outside the sandbox or in CI")
        token = "a" * 64
        for kind, executable in self.executables.items():
            with self.subTest(device=kind), socket.socket() as reservation:
                reservation.bind(("127.0.0.1", 0))
                port = reservation.getsockname()[1]
                reservation.close()
                log = tempfile.TemporaryFile(mode="w+b")
                process = subprocess.Popen([str(executable), str(port)], stdin=subprocess.PIPE, stderr=log)
                try:
                    process.stdin.write((token + "\n").encode())
                    process.stdin.close()
                    deadline = time.monotonic() + 5
                    while True:
                        log.seek(0)
                        if b"authenticated local listener ready" in log.read():
                            break
                        if process.poll() is not None or time.monotonic() >= deadline:
                            self.fail("test listener did not start")
                        time.sleep(0.02)
                    frame = b"jpeg" if kind == "MiniToo" else bytes(182)
                    with socket.socket() as competing:
                        competing.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        competing.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                        with self.assertRaises(OSError):
                            competing.bind(("127.0.0.1", port))
                    body = {"framesBase64": [base64.b64encode(frame).decode()], "speedMs": 0}
                    for bad_token in (None, "b" * 64, "a" * 63, "a" * 64 + "extra"):
                        rejected = dict(body)
                        if bad_token is not None:
                            rejected["authToken"] = bad_token
                        self.assertFalse(self.request(port, rejected)["ok"])
                    log.seek(0)
                    self.assertNotIn(b"TEST_BLUETOOTH_WRITE", log.read())
                    # Partial requests consume bounded slots, then expire even
                    # if a client continues trickling bytes into the socket.
                    slow = [socket.create_connection(("127.0.0.1", port), timeout=2) for _ in range(2)]
                    for connection in slow:
                        connection.sendall(b"{")
                    time.sleep(0.1)
                    with socket.create_connection(("127.0.0.1", port), timeout=2) as excess:
                        self.assertEqual(excess.recv(1), b"")
                    time.sleep(0.4)
                    slow[0].sendall(b" ")
                    time.sleep(0.5)
                    for connection in slow:
                        self.assertEqual(connection.recv(1), b"")
                        connection.close()
                    body["authToken"] = token
                    for options in ({"fragmented": True}, {"eof": True}):
                        self.assertTrue(self.request(port, body, **options)["ok"])
                    log.seek(0)
                    self.assertIn(b"TEST_BLUETOOTH_WRITE", log.read())
                    log.seek(0)
                    self.assertNotIn(token.encode(), log.read())
                finally:
                    process.terminate()
                    process.wait(timeout=3)
                    log.close()

    def test_real_swift_request_parser_rejects_unauthorized_requests(self):
        for kind, executable in self.executables.items():
            with self.subTest(device=kind):
                result = subprocess.run([str(executable), "--validate-only"], capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Authentication validation passed", result.stdout)
                self.assertNotIn("TEST_BLUETOOTH_WRITE", result.stderr)

    def test_missing_or_invalid_bootstrap_exits_before_bluetooth(self):
        for kind, executable in self.production_executables.items():
            for bootstrap in ("", "short\n", "g" * 64 + "\n"):
                with self.subTest(device=kind, bootstrap_length=len(bootstrap)):
                    result = subprocess.run([str(executable), "AA:BB:CC:DD:EE:FF", "40584"],
                                            input=bootstrap, capture_output=True, text=True, timeout=5)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn("Missing or invalid local bridge credential", result.stderr)
                    self.assertNotIn("RFCOMM", result.stderr)
