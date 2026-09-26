"""Filesystem operations used by the crash-safe spool protocol."""

from __future__ import annotations

import errno
import os
from pathlib import Path
import stat
import sys
from typing import Callable


class FilesystemProtocolError(RuntimeError):
    pass


MutationGuard = Callable[[], object]
Barrier = Callable[[str], None]


_SUPPORTED_LINUX_LOCAL_FILESYSTEMS = frozenset(
    {
        "bcachefs",
        "btrfs",
        "ext2",
        "ext3",
        "ext4",
        "f2fs",
        "jfs",
        "nilfs2",
        "overlay",
        "reiserfs",
        "xfs",
        "zfs",
    }
)
_LINUX_NETWORK_FILESYSTEMS = frozenset(
    {
        "9p",
        "afs",
        "ceph",
        "cifs",
        "coda",
        "davfs",
        "gcsfuse",
        "glusterfs",
        "lustre",
        "ncpfs",
        "nfs",
        "nfs4",
        "smb2",
        "smb3",
        "sshfs",
    }
)


def _is_reparse(stat_result: os.stat_result) -> bool:
    attributes = getattr(stat_result, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse)


def ensure_regular_file(path: Path, *, allow_missing: bool = False) -> os.stat_result | None:
    try:
        result = path.lstat()
    except FileNotFoundError:
        if allow_missing:
            return None
        raise FilesystemProtocolError(f"required file is missing: {path.name}") from None
    if stat.S_ISLNK(result.st_mode) or _is_reparse(result) or not stat.S_ISREG(result.st_mode):
        raise FilesystemProtocolError(f"path is not an ordinary regular file: {path}")
    return result


def ensure_directory(path: Path, *, allow_missing: bool = False) -> os.stat_result | None:
    try:
        result = path.lstat()
    except FileNotFoundError:
        if allow_missing:
            return None
        raise FilesystemProtocolError(f"required directory is missing: {path}") from None
    if stat.S_ISLNK(result.st_mode) or _is_reparse(result) or not stat.S_ISDIR(result.st_mode):
        raise FilesystemProtocolError(f"path is not an ordinary directory: {path}")
    return result


def _ensure_windows_local_filesystem(path: Path) -> None:
    import ctypes

    resolved = path.resolve(strict=True)
    anchor = resolved.anchor or str(resolved)
    drive_type = ctypes.windll.kernel32.GetDriveTypeW(anchor)
    # DRIVE_UNKNOWN, DRIVE_NO_ROOT_DIR, and DRIVE_REMOTE cannot establish the
    # local same-volume durability assumptions required by this protocol.
    if drive_type in (0, 1, 4):
        raise FilesystemProtocolError("upload spool must use a local filesystem")


def _decode_mountinfo_path(raw: str) -> str:
    decoded: list[str] = []
    index = 0
    while index < len(raw):
        if raw[index] != "\\":
            decoded.append(raw[index])
            index += 1
            continue
        escape = raw[index + 1 : index + 4]
        if len(escape) != 3 or any(character not in "01234567" for character in escape):
            raise ValueError("invalid mountinfo path escape")
        decoded.append(chr(int(escape, 8)))
        index += 4
    return "".join(decoded)


def _read_linux_mountinfo() -> str:
    return Path("/proc/self/mountinfo").read_text(encoding="utf-8", errors="surrogateescape")


def _linux_filesystem_type_from_mountinfo(
    resolved: Path, device_id: tuple[int, int], mountinfo: str
) -> str:
    best_match: tuple[int, int, str] | None = None

    for order, line in enumerate(mountinfo.splitlines()):
        fields = line.split()
        try:
            separator = fields.index("-")
            major_text, minor_text = fields[2].split(":", 1)
            mount_point = Path(_decode_mountinfo_path(fields[4]))
            filesystem_type = fields[separator + 1].lower()
            parsed_device = (int(major_text), int(minor_text))
        except (IndexError, TypeError, ValueError):
            continue
        if parsed_device != device_id or not mount_point.is_absolute():
            continue
        try:
            resolved.relative_to(mount_point)
        except ValueError:
            continue
        candidate = (len(mount_point.parts), order, filesystem_type)
        if best_match is None or candidate[:2] >= best_match[:2]:
            best_match = candidate

    if best_match is None:
        raise FilesystemProtocolError("cannot establish the upload spool filesystem type")
    return best_match[2]


def _linux_filesystem_type(path: Path) -> str:
    try:
        resolved = path.resolve(strict=True)
        device = resolved.stat().st_dev
        device_id = (os.major(device), os.minor(device))
        mountinfo = _read_linux_mountinfo()
    except (OSError, UnicodeError) as exc:
        raise FilesystemProtocolError("cannot establish the upload spool filesystem type") from exc
    return _linux_filesystem_type_from_mountinfo(resolved, device_id, mountinfo)


def _ensure_linux_local_filesystem(path: Path) -> None:
    filesystem_type = _linux_filesystem_type(path)
    if filesystem_type in _SUPPORTED_LINUX_LOCAL_FILESYSTEMS:
        return
    if filesystem_type in _LINUX_NETWORK_FILESYSTEMS or filesystem_type.startswith("fuse."):
        raise FilesystemProtocolError(
            f"upload spool must not use a network filesystem ({filesystem_type})"
        )
    raise FilesystemProtocolError(
        f"upload spool filesystem is unsupported ({filesystem_type})"
    )


def ensure_local_filesystem(path: Path) -> None:
    """Require an explicitly supported local filesystem for the spool."""
    if os.name == "nt":
        _ensure_windows_local_filesystem(path)
        return
    if sys.platform.startswith("linux"):
        _ensure_linux_local_filesystem(path)
        return
    raise FilesystemProtocolError("cannot establish a supported local upload spool filesystem")


def sync_directory(path: Path) -> None:
    """Flush directory metadata where the platform exposes that operation."""
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_temp(
    path: Path,
    data: bytes,
    *,
    guard: MutationGuard | None = None,
    barrier: Barrier | None = None,
    barrier_name: str = "temp_fsynced",
) -> None:
    if guard is not None:
        guard()
    ensure_directory(path.parent)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise
    if barrier is not None:
        barrier(barrier_name)


def publish_file_no_replace(
    temp_path: Path,
    final_path: Path,
    *,
    guard: MutationGuard | None = None,
    barrier: Barrier | None = None,
    barrier_name: str = "renamed",
) -> None:
    """Publish a flushed file without ever replacing an existing authority."""
    ensure_regular_file(temp_path)
    if guard is not None:
        guard()
    try:
        os.link(temp_path, final_path)
    except FileExistsError:
        raise
    except OSError as exc:
        raise FilesystemProtocolError("filesystem does not support atomic no-overwrite publication") from exc
    if barrier is not None:
        barrier(barrier_name)
    if guard is not None:
        guard()
    temp_path.unlink()
    sync_directory(final_path.parent)


def replace_file(
    temp_path: Path,
    final_path: Path,
    *,
    guard: MutationGuard | None = None,
    barrier: Barrier | None = None,
    barrier_name: str = "replaced",
) -> None:
    ensure_regular_file(temp_path)
    if guard is not None:
        guard()
    os.replace(temp_path, final_path)
    if barrier is not None:
        barrier(barrier_name)
    sync_directory(final_path.parent)


def rename_directory_no_replace(
    source: Path,
    destination: Path,
    *,
    guard: MutationGuard | None = None,
    barrier: Barrier | None = None,
    barrier_name: str = "renamed",
) -> None:
    ensure_directory(source)
    ensure_directory(destination.parent)
    if guard is not None:
        guard()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    if os.name == "nt":
        os.rename(source, destination)
    else:
        # renameat2 is the only portable-enough Linux primitive available here
        # that guarantees no replacement under a race.
        import ctypes

        libc = ctypes.CDLL(None, use_errno=True)
        renameat2 = getattr(libc, "renameat2", None)
        if renameat2 is None:
            raise FilesystemProtocolError("atomic no-overwrite directory rename is unsupported")
        renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        renameat2.restype = ctypes.c_int
        result = renameat2(
            -100,
            os.fsencode(source),
            -100,
            os.fsencode(destination),
            1,
        )
        if result != 0:
            error = ctypes.get_errno()
            if error == errno.EEXIST:
                raise FileExistsError(destination)
            raise OSError(error, os.strerror(error), str(source))
    if barrier is not None:
        barrier(barrier_name)
    sync_directory(source.parent)
    if destination.parent != source.parent:
        sync_directory(destination.parent)


def resolved_within(path: Path, root: Path) -> Path:
    resolved_root = root.resolve(strict=True)
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise FilesystemProtocolError("path escapes spool root") from exc
    return resolved
