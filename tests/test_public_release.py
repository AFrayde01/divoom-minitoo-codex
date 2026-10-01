import importlib.util
import io
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/prepare_public_release.py"
spec = importlib.util.spec_from_file_location("public_release_export", SCRIPT)
export = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export)


class PublicReleaseTests(unittest.TestCase):
    def run_export(self, root, names):
        result = SimpleNamespace(stdout=b"\0".join(str(name).encode() for name in names) + b"\0")
        with patch.object(export, "ROOT", root), patch.object(export.subprocess, "run", return_value=result), redirect_stdout(io.StringIO()):
            export.main()

    def test_current_content_is_exported_without_history_and_existing_export_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "README.md").write_text("current content")
            (root / ".git").mkdir()
            (root / ".git/old-history").write_text("retired content")
            self.run_export(root, ["README.md"])
            with zipfile.ZipFile(root / "build/public-release.zip") as archive:
                self.assertEqual(archive.namelist(), ["README.md"])
                self.assertEqual(archive.read("README.md"), b"current content")
            with self.assertRaisesRegex(SystemExit, "already exists"):
                self.run_export(root, ["README.md"])

    def test_private_files_unexpected_paths_and_external_directory_links_are_rejected(self):
        for name in ("auth.json", "docs/history.bundle", "docs/.env", "docs/.codex/state.json"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("private fixture")
                with self.assertRaises(SystemExit):
                    self.run_export(root, [name])
                self.assertFalse((root / "build/public-release").exists())
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as external:
            root, outside = Path(directory).resolve(), Path(external).resolve()
            (outside / "private.py").write_text("outside source")
            (root / "src").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(SystemExit, "regular files"):
                self.run_export(root, ["src/private.py"])
