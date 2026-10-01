#!/usr/bin/env python3
"""Export current project files without Git history, credentials or local builds."""

import os
import shutil
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_TOP_LEVEL = {".gitignore", "README.md", "README.es.md", "LICENSE", "SECURITY.md",
                    "CONTRIBUTING.md", "THIRD_PARTY_NOTICES.md", "pyproject.toml"}
PUBLIC_DIRECTORIES = {"Sources", "src", "scripts", "tests", "docs", ".github"}


def main() -> None:
    destination = ROOT / "build" / "public-release"
    archive = ROOT / "build" / "public-release.zip"
    if destination.exists() or archive.exists():
        raise SystemExit("A public release export already exists. Move it aside before creating another.")
    result = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                            cwd=ROOT, capture_output=True, check=True)
    files = []
    for name in sorted(set(os.fsdecode(item) for item in result.stdout.split(b"\0") if item)):
        relative = Path(name)
        source = ROOT / relative
        if not source.exists():
            continue  # A locally deleted tracked file must not enter the export.
        if relative.parts[0] not in PUBLIC_DIRECTORIES and name not in PUBLIC_TOP_LEVEL:
            raise SystemExit(f"Review this unexpected publication path first: {name}")
        if source.is_symlink() or not source.is_file() or not source.resolve().is_relative_to(ROOT):
            raise SystemExit(f"Publication exports require regular files: {name}")
        if any(part in {".git", ".codex", ".aws", "__pycache__"} or part.endswith(".egg-info") for part in relative.parts):
            raise SystemExit(f"Private or generated files cannot enter the export: {name}")
        if source.name.startswith(".env") and source.name != ".env.example":
            raise SystemExit(f"Environment files cannot enter the export: {name}")
        if source.name == "auth.json" or source.suffix in {".log", ".key", ".pem", ".pyc", ".bundle", ".sqlite", ".sqlite3"}:
            raise SystemExit(f"Private or generated files cannot enter the export: {name}")
        files.append(relative)
    destination.mkdir(parents=True, mode=0o700)
    for relative in files:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for relative in files:
            output.write(destination / relative, arcname=str(relative))
    archive.chmod(0o600)
    print(f"Exported {len(files)} current project files to {destination}")
    print(f"Archive: {archive}")
    print("No Git history or remote was included. Review the export before creating a new public repository.")


if __name__ == "__main__":
    main()
