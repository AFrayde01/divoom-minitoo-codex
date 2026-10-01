"""Private rotating diagnostic logs for a user-launched monitor."""

from __future__ import annotations

import os
import pwd
import stat
from logging.handlers import RotatingFileHandler
from pathlib import Path


def default_log_path(device: str, port: int) -> Path:
    try:
        user_home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    except KeyError:
        user_home = Path.home()
    return user_home / "Library" / "Logs" / "divoom-minitoo-codex" / f"{device}-{port}.log"


def _check_file(fd: int, path: Path) -> None:
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
        raise OSError(f"Diagnostic log must be a regular, unshared file owned by this user: {path}")
    os.fchmod(fd, 0o600)


def secure_existing_log(path: Path) -> None:
    """Protect an existing active/rotated log without following symlinks."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return
    try:
        _check_file(fd, path)
    finally:
        os.close(fd)


def private_log_directory(path: Path) -> None:
    """Restrict only the application's own dedicated default directory."""
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        if os.fstat(fd).st_uid != os.getuid():
            raise OSError(f"Diagnostic log directory must belong to this user: {path}")
        os.fchmod(fd, 0o700)
    finally:
        os.close(fd)


class PrivateRotatingFileHandler(RotatingFileHandler):
    """Create and reopen logs privately, including after rotation."""

    def __init__(self, path: Path, *, max_bytes: int = 1024 * 1024, backup_count: int = 2) -> None:
        path = path.expanduser().absolute()  # Do not resolve a final symlink.
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        for index in range(1, backup_count + 1):
            secure_existing_log(Path(f"{path}.{index}"))
        super().__init__(path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")

    def _open(self):
        path = Path(self.baseFilename)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        try:
            _check_file(fd, path)
            return os.fdopen(fd, "a", encoding="utf-8", errors=self.errors)
        except BaseException:
            os.close(fd)
            raise
