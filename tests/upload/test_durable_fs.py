from __future__ import annotations

import os
from pathlib import Path

import pytest

from agent.screenshot_upload import durable_fs
from agent.screenshot_upload.durable_fs import FilesystemProtocolError


DEVICE_ID = (8, 17)


def _mountinfo_line(path: Path, filesystem_type: str, *, mount_id: int = 42) -> str:
    escaped = str(path.resolve()).replace("\\", "/").replace(" ", "\\040")
    return (
        f"{mount_id} 1 {DEVICE_ID[0]}:{DEVICE_ID[1]} / {escaped} rw,relatime "
        f"- {filesystem_type} /dev/test rw\n"
    )


def _synthetic_filesystem_type(path: Path, mountinfo: str) -> str:
    return durable_fs._linux_filesystem_type_from_mountinfo(
        path.resolve(), DEVICE_ID, mountinfo
    )


@pytest.mark.parametrize("filesystem_type", ["ext4", "xfs", "btrfs", "overlay"])
def test_representative_linux_local_mounts_are_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, filesystem_type: str
) -> None:
    monkeypatch.setattr(
        durable_fs,
        "_linux_filesystem_type",
        lambda path: _synthetic_filesystem_type(path, _mountinfo_line(tmp_path, filesystem_type)),
    )

    durable_fs._ensure_linux_local_filesystem(tmp_path)


@pytest.mark.parametrize("filesystem_type", ["nfs", "nfs4", "cifs", "smb3", "fuse.sshfs"])
def test_linux_network_mounts_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, filesystem_type: str
) -> None:
    monkeypatch.setattr(
        durable_fs,
        "_linux_filesystem_type",
        lambda path: _synthetic_filesystem_type(path, _mountinfo_line(tmp_path, filesystem_type)),
    )

    with pytest.raises(FilesystemProtocolError, match="network filesystem"):
        durable_fs._ensure_linux_local_filesystem(tmp_path)


@pytest.mark.parametrize("filesystem_type", ["tmpfs", "fuse", "futurefs"])
def test_linux_unknown_or_volatile_mounts_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, filesystem_type: str
) -> None:
    monkeypatch.setattr(
        durable_fs,
        "_linux_filesystem_type",
        lambda path: _synthetic_filesystem_type(path, _mountinfo_line(tmp_path, filesystem_type)),
    )

    with pytest.raises(FilesystemProtocolError, match="unsupported"):
        durable_fs._ensure_linux_local_filesystem(tmp_path)


def test_linux_uses_the_longest_matching_mount(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent = tmp_path.parent
    mountinfo = _mountinfo_line(parent, "ext4", mount_id=41) + _mountinfo_line(
        tmp_path, "nfs4", mount_id=42
    )
    monkeypatch.setattr(
        durable_fs,
        "_linux_filesystem_type",
        lambda path: _synthetic_filesystem_type(path, mountinfo),
    )

    with pytest.raises(FilesystemProtocolError, match="network filesystem"):
        durable_fs._ensure_linux_local_filesystem(tmp_path)


def test_linux_mountinfo_path_escapes_are_decoded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spool = tmp_path / "spool with space"
    spool.mkdir()
    monkeypatch.setattr(
        durable_fs,
        "_linux_filesystem_type",
        lambda path: _synthetic_filesystem_type(path, _mountinfo_line(spool, "ext4")),
    )

    durable_fs._ensure_linux_local_filesystem(spool)


def test_linux_missing_or_unmatched_mountinfo_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        durable_fs,
        "_linux_filesystem_type",
        lambda path: _synthetic_filesystem_type(path, "malformed\n"),
    )

    with pytest.raises(FilesystemProtocolError, match="cannot establish"):
        durable_fs._ensure_linux_local_filesystem(tmp_path)


def test_linux_unreadable_mountinfo_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unreadable() -> str:
        raise OSError("synthetic denial")

    monkeypatch.setattr(durable_fs, "_read_linux_mountinfo", unreadable)
    monkeypatch.setattr(durable_fs.os, "major", lambda device: DEVICE_ID[0], raising=False)
    monkeypatch.setattr(durable_fs.os, "minor", lambda device: DEVICE_ID[1], raising=False)

    with pytest.raises(FilesystemProtocolError, match="cannot establish"):
        durable_fs._ensure_linux_local_filesystem(tmp_path)


@pytest.mark.skipif(os.name != "nt", reason="requires a real Windows drive classification")
def test_windows_local_temp_directory_remains_supported(tmp_path: Path) -> None:
    durable_fs.ensure_local_filesystem(tmp_path)


@pytest.mark.skipif(not os.sys.platform.startswith("linux"), reason="requires Linux mountinfo")
def test_actual_linux_temp_directory_has_an_explicit_supported_mount(tmp_path: Path) -> None:
    durable_fs.ensure_local_filesystem(tmp_path)
