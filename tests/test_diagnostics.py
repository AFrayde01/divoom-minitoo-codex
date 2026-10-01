import logging
import os
import stat
import tempfile
import unittest
from pathlib import Path

from divoom_minitoo_codex.diagnostics import PrivateRotatingFileHandler, private_log_directory


class DiagnosticPrivacyTests(unittest.TestCase):
    def test_logs_and_rotated_backups_are_private_under_permissive_umask(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "monitor.log"
            for item in (path, Path(f"{path}.1"), Path(f"{path}.2")):
                item.write_text("old diagnostics\n")
                item.chmod(0o644)
            previous = os.umask(0)
            try:
                handler = PrivateRotatingFileHandler(path, max_bytes=32)
                for _ in range(5):
                    handler.emit(logging.makeLogRecord({"msg": "new diagnostic entry"}))
                handler.close()
            finally:
                os.umask(previous)
            for item in (path, Path(f"{path}.1"), Path(f"{path}.2")):
                self.assertEqual(stat.S_IMODE(item.stat().st_mode), 0o600)

    def test_dedicated_directory_is_private_but_custom_parent_is_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            parent.chmod(0o755)
            handler = PrivateRotatingFileHandler(parent / "custom.log")
            handler.close()
            self.assertEqual(stat.S_IMODE(parent.stat().st_mode), 0o755)
            default = parent / "app-logs"
            private_log_directory(default)
            self.assertEqual(stat.S_IMODE(default.stat().st_mode), 0o700)

    def test_symlinks_hardlinks_and_fifos_are_rejected_without_touching_target(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            target = parent / "target"
            target.write_text("keep me")
            target.chmod(0o644)
            symlink, hardlink, fifo = (parent / name for name in ("symlink", "hardlink", "fifo"))
            symlink.symlink_to(target)
            os.link(target, hardlink)
            os.mkfifo(fifo)
            for path in (symlink, hardlink, fifo):
                with self.subTest(path=path), self.assertRaises(OSError):
                    PrivateRotatingFileHandler(path)
            self.assertEqual(target.read_text(), "keep me")
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o644)

    def test_rotated_symlink_and_directory_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            target = parent / "target"
            target.write_text("keep me")
            path = parent / "monitor.log"
            Path(f"{path}.1").symlink_to(target)
            with self.assertRaises(OSError):
                PrivateRotatingFileHandler(path)
            linked = parent / "linked"
            linked.symlink_to(parent, target_is_directory=True)
            with self.assertRaises(OSError):
                private_log_directory(linked)

