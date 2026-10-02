"""Connection failures simulated without opening a Bluetooth device."""

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from divoom_minitoo_codex import cli
from divoom_minitoo_codex.bridge import (
    BRIDGE_RESPONSE_TIMEOUT_SECONDS,
    MiniTooBridge,
    MiniTooError,
)


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.bridge = MiniTooBridge(Path("unused-bridge"), "AA:BB:CC:DD:EE:FF")
        self.bridge.process = MagicMock()
        self.bridge.process.poll.return_value = None
        self.bridge._auth_token = "a" * 64

    def send_response(self, chunks):
        connection = MagicMock()
        connection.__enter__.return_value = connection
        connection.recv.side_effect = chunks
        with patch("divoom_minitoo_codex.bridge.socket.create_connection", return_value=connection):
            result = self.bridge.send_frames([b"jpeg"])
        return result, connection

    def test_fragmented_response_and_timeout_outlive_bluetooth_deadline(self):
        result, connection = self.send_response([b'{"ok":true,', b'"acknowledged":true}\nignored'])
        self.assertIs(result["acknowledged"], True)
        self.assertGreater(BRIDGE_RESPONSE_TIMEOUT_SECONDS, 40)
        self.assertEqual(connection.settimeout.call_args_list[0].args, (60,))

    def test_empty_response_preserves_bridge_diagnostics(self):
        self.bridge._stderr_tail.append("Bluetooth RFCOMM channel closed")
        with self.assertRaisesRegex(MiniTooError, "sent no data.*RFCOMM channel closed"):
            self.send_response([b""])

    def test_socket_error_includes_stage_and_bridge_diagnostics(self):
        self.bridge._stderr_tail.append("device disconnected")
        with patch("divoom_minitoo_codex.bridge.socket.create_connection", side_effect=ConnectionRefusedError("refused")):
            with self.assertRaisesRegex(MiniTooError, "connecting to the local bridge.*device disconnected"):
                self.bridge.send_frames([b"jpeg"])

    def test_only_boolean_success_is_accepted(self):
        for response in [{"ok": "true"}, {"ok": "false"}, [], None]:
            with self.subTest(response=response), self.assertRaises(MiniTooError):
                self.send_response([json.dumps(response).encode() + b"\n"])

    def test_unacknowledged_frame_is_retried_over_a_new_session(self):
        with patch.object(self.bridge, "close") as close, patch.object(
            self.bridge, "send_frames", side_effect=[
                {"ok": True, "acknowledged": False, "message": "no ack"},
                {"ok": True, "acknowledged": True},
            ]
        ) as send:
            result = self.bridge.send_frames_with_recovery([b"jpeg"], require_ack=True)
        self.assertIs(result["reconnected"], True)
        self.assertEqual(send.call_count, 2)
        close.assert_called_once()

    def test_recovery_is_bounded_and_preserves_both_failures(self):
        with patch.object(self.bridge, "close") as close, patch.object(
            self.bridge, "send_frames", side_effect=[MiniTooError("original timeout"), MiniTooError("reconnect refused")]
        ) as send:
            with self.assertRaisesRegex(MiniTooError, "original timeout.*reconnect refused"):
                self.bridge.send_frames_with_recovery([b"jpeg"], require_ack=True)
        self.assertEqual(send.call_count, 2)
        self.assertEqual(close.call_count, 2)

    def test_timebox_does_not_require_a_minitoo_ack(self):
        with patch.object(self.bridge, "send_frames", return_value={"ok": True, "message": "image sent"}) as send:
            result = self.bridge.send_frames_with_recovery([b"pixels"])
        self.assertIs(result["reconnected"], False)
        send.assert_called_once()

    def test_exited_bridge_is_started_before_the_next_request(self):
        self.bridge.process.poll.return_value = 1
        with patch.object(self.bridge, "start") as start:
            self.send_response([b'{"ok":true}\n'])
        start.assert_called_once()

    def test_start_does_not_treat_another_listener_as_ready(self):
        self.bridge.process = None
        process = MagicMock()
        process.poll.return_value = None
        process.stderr = None
        with patch("divoom_minitoo_codex.bridge.Path.is_file", return_value=True), patch(
            "divoom_minitoo_codex.bridge.subprocess.Popen", return_value=process
        ), patch("divoom_minitoo_codex.bridge.time.monotonic", side_effect=[0, 0, 16]), patch(
            "divoom_minitoo_codex.bridge.Event"
        ) as event, patch("divoom_minitoo_codex.bridge.socket.create_connection") as connect:
            event.return_value.wait.return_value = False
            with self.assertRaisesRegex(MiniTooError, "did not start listening"):
                self.bridge.start()
        connect.assert_not_called()
        process.terminate.assert_called_once()
        self.assertIsNone(self.bridge.process)

    def test_start_accepts_its_own_child_readiness_message(self):
        self.bridge.process = None
        process = MagicMock()
        process.poll.return_value = None
        process.stderr = io.BytesIO(b"MiniToo bridge: authenticated local listener ready on port 40584.\n")
        with patch("divoom_minitoo_codex.bridge.Path.is_file", return_value=True), patch(
            "divoom_minitoo_codex.bridge.subprocess.Popen", return_value=process
        ):
            self.bridge.start()
        self.assertIs(self.bridge.process, process)
        bootstrap = process.stdin.write.call_args.args[0].decode().strip()
        self.assertEqual(len(bootstrap), 64)
        self.assertEqual(bootstrap, self.bridge._auth_token)
        process.stdin.close.assert_called_once()
        self.bridge.close()

    def test_old_binary_is_rejected(self):
        self.bridge.process = None
        process = MagicMock()
        process.poll.return_value = None
        process.stderr = io.BytesIO(b"MiniToo bridge: local listener ready on port 40584.\n")
        with patch("divoom_minitoo_codex.bridge.Path.is_file", return_value=True), patch(
            "divoom_minitoo_codex.bridge.subprocess.Popen", return_value=process
        ), self.assertRaisesRegex(MiniTooError, "outdated.*authenticate"):
            self.bridge.start()
        process.terminate.assert_called_once()

    def test_request_uses_new_credential_after_restart(self):
        self.bridge.process.poll.return_value = 1
        def restart():
            self.bridge.process.poll.return_value = None
            self.bridge._auth_token = "b" * 64
        with patch.object(self.bridge, "start", side_effect=restart):
            _, connection = self.send_response([b'{"ok":true}\n'])
        body = json.loads(connection.sendall.call_args.args[0])
        self.assertEqual(body["authToken"], "b" * 64)

    def test_credential_is_absent_from_process_arguments(self):
        self.bridge.process = None
        process = MagicMock()
        process.poll.return_value = None
        process.stderr = io.BytesIO(b"MiniToo bridge: authenticated local listener ready on port 40584.\n")
        with patch("divoom_minitoo_codex.bridge.Path.is_file", return_value=True), patch(
            "divoom_minitoo_codex.bridge.subprocess.Popen", return_value=process
        ) as popen:
            self.bridge.start()
        self.assertNotIn(self.bridge._auth_token, repr(popen.call_args))
        self.assertEqual(popen.call_args.kwargs["stdin"], subprocess.PIPE)
        self.bridge.close()

    def test_start_preserves_listener_failure_and_cleans_up_the_child(self):
        self.bridge.process = None
        process = MagicMock()
        process.poll.return_value = 1
        process.stderr = io.BytesIO(b"MiniToo bridge listener failed: Address already in use\n")
        with patch("divoom_minitoo_codex.bridge.Path.is_file", return_value=True), patch(
            "divoom_minitoo_codex.bridge.subprocess.Popen", return_value=process
        ):
            with self.assertRaisesRegex(MiniTooError, "exited with code 1.*Address already in use"):
                self.bridge.start()
        self.assertIsNone(self.bridge.process)

    def test_local_response_deadline_does_not_reset_on_fragmented_data(self):
        with patch("divoom_minitoo_codex.bridge.time.monotonic", side_effect=[100, 110, 120]):
            _, connection = self.send_response([b'{"ok":', b'true}\n'])
        self.assertEqual([call.args[0] for call in connection.settimeout.call_args_list], [60, 50, 40])

    def test_close_kills_a_bridge_that_ignores_termination(self):
        process = self.bridge.process
        process.wait.side_effect = [subprocess.TimeoutExpired("bridge", 3), 0]
        self.bridge.close()
        process.kill.assert_called_once()
        self.assertIsNone(self.bridge.process)


class MonitorRecoveryTests(unittest.TestCase):
    def test_failed_frame_remains_pending_and_retry_is_delayed(self):
        clock = [0.0]
        sent_at = []
        activity = SimpleNamespace(working=False, hooks_installed=True)
        snapshot = SimpleNamespace(windows=[], reset_credits=SimpleNamespace(available_count=0))

        def sleep(seconds):
            clock[0] += seconds

        def read_activity(_):
            if clock[0] >= 12:
                raise KeyboardInterrupt
            return activity

        def send(*args, **kwargs):
            sent_at.append(clock[0])
            if len(sent_at) == 1:
                raise MiniTooError("simulated disconnected device")
            return {"ok": True, "acknowledged": True}

        with tempfile.TemporaryDirectory() as directory, patch.object(
            cli.sys, "argv", ["codex-minitoo", "--address", "AA:BB:CC:DD:EE:FF", "--log-file", str(Path(directory) / "monitor.log")]
        ), patch.object(cli, "secure_existing_log", side_effect=OSError("unrelated legacy file")), patch.object(
            cli, "CodexAppServer"
        ) as server, patch.object(cli, "MiniTooBridge") as bridge, patch.object(
            cli, "read_activity", side_effect=read_activity
        ), patch.object(cli, "render_usage_frames", return_value=(object(),)), patch.object(
            cli, "encode_rgb_animation", return_value=b"unchanged frame"
        ), patch.object(cli, "load_preferences", return_value={}), patch.object(
            cli, "save_preferences"
        ), patch.object(cli.time, "monotonic", side_effect=lambda: clock[0]), patch.object(
            cli.time, "sleep", side_effect=sleep
        ), redirect_stdout(io.StringIO()) as stdout, redirect_stderr(io.StringIO()) as stderr:
            server.return_value.__enter__.return_value.read_usage.return_value = snapshot
            bridge.return_value.send_frames_with_recovery.side_effect = send
            self.assertEqual(cli.main(), 0)
            saved_log = (Path(directory) / "monitor.log").read_text()
        self.assertEqual(sent_at, [0, 5])
        self.assertEqual(stdout.getvalue().count("Display updated:"), 1)
        self.assertIn("Retrying the current screen in 5s", stderr.getvalue())
        self.assertIn("simulated disconnected device", saved_log)
        self.assertEqual(saved_log.count("Display updated:"), 1)


if __name__ == "__main__":
    unittest.main()
