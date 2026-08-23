#!/usr/bin/env python3
"""Kernel-enforced snapshot fence for privileged pilot activation boundaries.

The trusted caller supplies closed directory and regular-file surfaces.  This
module copies them to a dedicated tmpfs, remounts the complete tmpfs superblock
read-only, and bind-mounts the copies over the host paths in PID 1's mount
namespace.  Attestation and privileged use therefore resolve the copied inode,
not a mutable inode that was merely checked earlier.
"""

from __future__ import annotations

import contextlib
import ctypes
import errno
import hashlib
import json
import os
import shutil
import stat
import tempfile
import time
import uuid
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self


class TrustedActivationFenceError(RuntimeError):
    """The host surface cannot be frozen or recovered safely."""


RUNTIME_ROOT = Path("/run/thebitlab/pilot-activation-fence")
STATE_PATH = RUNTIME_ROOT / "state.json"
TRANSACTION_ROOT = RUNTIME_ROOT / "transactions"
ACTIVATION_LOCK = RUNTIME_ROOT / "activation.lock"
PACKAGE_LOCK_PATHS = (
    Path("/var/lib/dpkg/lock-frontend"),
    Path("/var/lib/dpkg/lock"),
    Path("/var/cache/apt/archives/lock"),
)
PROC_MOUNTINFO = Path("/proc/self/mountinfo")
MS_RDONLY = 1
MS_NOSUID = 2
MS_NODEV = 4
MS_REMOUNT = 32
MS_BIND = 4096
MNT_DETACH = 2
TMPFS_MAGIC = 0x01021994
_LOCK_TIMEOUT_SECONDS = 30.0
_ACTIVE_TRANSACTIONS: list[dict[str, Any]] = []

if os.name == "posix":
    import fcntl

    _LIBC: ctypes.CDLL | None = ctypes.CDLL(None, use_errno=True)
    _LIBC.mount.argtypes = (
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_ulong,
        ctypes.c_void_p,
    )
    _LIBC.mount.restype = ctypes.c_int
    _LIBC.umount2.argtypes = (ctypes.c_char_p, ctypes.c_int)
    _LIBC.umount2.restype = ctypes.c_int
else:
    fcntl = None  # type: ignore[assignment]
    _LIBC = None


@dataclass(frozen=True)
class MountRecord:
    mount_id: int
    parent_id: int
    major_minor: str
    root: str
    mount_point: Path
    options: frozenset[str]
    filesystem: str
    source: str
    super_options: frozenset[str]


@dataclass
class _HeldLocks:
    descriptors: list[int]

    def close(self) -> None:
        for descriptor in reversed(self.descriptors):
            with contextlib.suppress(OSError):
                os.close(descriptor)
        self.descriptors.clear()


def _decode_mount_field(value: str) -> str:
    for encoded, decoded in (("\\040", " "), ("\\011", "\t"), ("\\012", "\n"), ("\\134", "\\")):
        value = value.replace(encoded, decoded)
    return value


def _mount_records() -> tuple[MountRecord, ...]:
    try:
        lines = PROC_MOUNTINFO.read_text(encoding="ascii").splitlines()
    except OSError as exc:
        raise TrustedActivationFenceError("mountinfo non leggibile") from exc
    records: list[MountRecord] = []
    for line in lines:
        left, separator, right = line.partition(" - ")
        if not separator:
            raise TrustedActivationFenceError("mountinfo non interpretabile")
        fields = left.split()
        tail = right.split()
        if len(fields) < 6 or len(tail) < 3:
            raise TrustedActivationFenceError("mountinfo incompleto")
        records.append(
            MountRecord(
                int(fields[0]),
                int(fields[1]),
                fields[2],
                _decode_mount_field(fields[3]),
                Path(_decode_mount_field(fields[4])),
                frozenset(fields[5].split(",")),
                tail[0],
                _decode_mount_field(tail[1]),
                frozenset(tail[2].split(",")),
            )
        )
    return tuple(records)


def _top_mount(path: Path) -> MountRecord | None:
    matches = [record for record in _mount_records() if record.mount_point == path]
    return matches[-1] if matches else None


def _mount(
    source: str | None,
    target: Path,
    filesystem: str | None,
    flags: int,
    data: str | None = None,
) -> None:
    if _LIBC is None:
        raise TrustedActivationFenceError("Mount fence disponibile soltanto su Linux")
    encoded_source = source.encode() if source is not None else None
    encoded_filesystem = filesystem.encode() if filesystem is not None else None
    encoded_data = data.encode() if data is not None else None
    if _LIBC.mount(
        encoded_source,
        os.fsencode(target),
        encoded_filesystem,
        flags,
        encoded_data,
    ) != 0:
        error = ctypes.get_errno()
        raise TrustedActivationFenceError(
            f"mount kernel fallita per {target}: {os.strerror(error)}"
        )


def _umount(path: Path) -> None:
    if _LIBC is None:
        raise TrustedActivationFenceError("Mount fence disponibile soltanto su Linux")
    if _LIBC.umount2(os.fsencode(path), 0) == 0:
        return
    error = ctypes.get_errno()
    if error == errno.EBUSY and _LIBC.umount2(os.fsencode(path), MNT_DETACH) == 0:
        if _top_mount(path) is None:
            return
        error = errno.EBUSY
    raise TrustedActivationFenceError(
        f"umount kernel fallita per {path}: {os.strerror(error)}"
    )


def _safe_runtime_root() -> None:
    RUNTIME_ROOT.mkdir(parents=True, mode=0o700, exist_ok=True)
    TRANSACTION_ROOT.mkdir(mode=0o700, exist_ok=True)
    for path in (RUNTIME_ROOT, TRANSACTION_ROOT):
        metadata = path.stat()
        if metadata.st_uid != 0 or metadata.st_mode & 0o077 or path.is_symlink():
            raise TrustedActivationFenceError(f"Runtime fence non root-only: {path}")


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    _safe_runtime_root()
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary_path.unlink(missing_ok=True)


def _read_state() -> dict[str, Any] | None:
    try:
        metadata = STATE_PATH.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise TrustedActivationFenceError("Metadata fence non verificabile") from exc
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != 0 or metadata.st_mode & 0o077:
        raise TrustedActivationFenceError("Metadata fence non root-only/regolare")
    try:
        value = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise TrustedActivationFenceError("Metadata fence non interpretabile") from exc
    if not isinstance(value, dict) or value.get("schema") != "thebitlab.activation-fence.v1":
        raise TrustedActivationFenceError("Schema metadata fence inatteso")
    return value


def _write_transactions(transactions: Sequence[Mapping[str, Any]], *, poisoned: bool = False) -> None:
    if not transactions:
        STATE_PATH.unlink(missing_ok=True)
        return
    _atomic_json(
        STATE_PATH,
        {
            "schema": "thebitlab.activation-fence.v1",
            "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip(),
            "poisoned": poisoned,
            "transactions": list(transactions),
        },
    )


def _lock_descriptor(path: Path, *, timeout: float) -> int:
    if fcntl is None:
        raise TrustedActivationFenceError("Host lock disponibile soltanto su Linux")
    path.parent.mkdir(parents=True, mode=0o755, exist_ok=True)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)
    deadline = time.monotonic() + timeout
    while True:
        try:
            fcntl.lockf(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return descriptor
        except OSError as exc:
            if exc.errno not in {errno.EACCES, errno.EAGAIN}:
                os.close(descriptor)
                raise TrustedActivationFenceError(f"Lock host non acquisibile: {path}") from exc
            if time.monotonic() >= deadline:
                os.close(descriptor)
                raise TrustedActivationFenceError(f"Timeout lock host: {path}")
            time.sleep(0.1)


def acquire_host_locks() -> _HeldLocks:
    """Serialize trusted activators and compliant package transactions."""

    _safe_runtime_root()
    descriptors: list[int] = []
    try:
        descriptors.append(_lock_descriptor(ACTIVATION_LOCK, timeout=_LOCK_TIMEOUT_SECONDS))
        for path in PACKAGE_LOCK_PATHS:
            descriptors.append(_lock_descriptor(path, timeout=_LOCK_TIMEOUT_SECONDS))
        return _HeldLocks(descriptors)
    except Exception:
        _HeldLocks(descriptors).close()
        raise


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise TrustedActivationFenceError(f"Snapshot source non regolare: {path}")
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        after = os.fstat(descriptor)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise TrustedActivationFenceError(f"Snapshot source mutata in lettura: {path}")
    finally:
        os.close(descriptor)
    return digest.hexdigest()


def _tree_manifest(root: Path) -> dict[str, list[Any]]:
    manifest: dict[str, list[Any]] = {}

    def visit(directory: Path, relative: Path) -> None:
        try:
            before = directory.lstat()
            entries = sorted(os.scandir(directory), key=lambda item: item.name)
        except OSError as exc:
            raise TrustedActivationFenceError(f"Albero fence non enumerabile: {directory}") from exc
        for entry in entries:
            path = directory / entry.name
            item_relative = relative / entry.name
            key = item_relative.as_posix()
            metadata = entry.stat(follow_symlinks=False)
            common = [metadata.st_mode, metadata.st_uid, metadata.st_gid]
            if stat.S_ISDIR(metadata.st_mode):
                manifest[key] = ["d", *common]
                visit(path, item_relative)
            elif stat.S_ISREG(metadata.st_mode):
                manifest[key] = ["f", *common, metadata.st_size, _file_digest(path)]
            elif stat.S_ISLNK(metadata.st_mode):
                manifest[key] = ["l", *common, os.readlink(path)]
            else:
                raise TrustedActivationFenceError(f"Tipo source fence vietato: {path}")
        after = directory.lstat()
        if (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise TrustedActivationFenceError(f"Directory source mutata in inventario: {directory}")

    visit(root, Path("."))
    return manifest


def _source_hardlinks(root: Path, kind: str) -> tuple[str, ...]:
    if kind == "file":
        return (".",) if root.lstat().st_nlink != 1 else ()
    hardlinks: list[str] = []
    for directory, _directory_names, file_names in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        for name in file_names:
            path = directory_path / name
            metadata = path.lstat()
            if stat.S_ISREG(metadata.st_mode) and metadata.st_nlink != 1:
                hardlinks.append(path.relative_to(root).as_posix())
    return tuple(sorted(hardlinks))


def source_path_had_multiple_links(path: Path) -> bool:
    """Report source hardlinks hidden by an active copy-on-freeze snapshot."""

    for transaction in reversed(_ACTIVE_TRANSACTIONS):
        for target in transaction["targets"]:
            target_path = Path(target["path"])
            try:
                relative = path.relative_to(target_path)
            except ValueError:
                continue
            key = "." if target["kind"] == "file" else relative.as_posix()
            if key in target.get("source_hardlinks", ()):
                return True
    return False


def _copy_tree(source: Path, destination: Path) -> dict[str, list[Any]]:
    shutil.copytree(source, destination, symlinks=True, copy_function=shutil.copy2)
    for source_directory, directory_names, file_names in os.walk(
        source, topdown=False, followlinks=False
    ):
        source_directory_path = Path(source_directory)
        relative = source_directory_path.relative_to(source)
        destination_directory = destination / relative
        for name in (*directory_names, *file_names):
            source_item = source_directory_path / name
            destination_item = destination_directory / name
            metadata = source_item.lstat()
            os.chown(
                destination_item,
                metadata.st_uid,
                metadata.st_gid,
                follow_symlinks=False,
            )
            if not stat.S_ISLNK(metadata.st_mode):
                os.chmod(destination_item, stat.S_IMODE(metadata.st_mode))
        directory_metadata = source_directory_path.lstat()
        os.chown(
            destination_directory,
            directory_metadata.st_uid,
            directory_metadata.st_gid,
            follow_symlinks=False,
        )
        os.chmod(destination_directory, stat.S_IMODE(directory_metadata.st_mode))
    source_manifest = _tree_manifest(source)
    destination_manifest = _tree_manifest(destination)
    if destination_manifest != source_manifest:
        differing = next(
            key for key in sorted(set(source_manifest) | set(destination_manifest))
            if source_manifest.get(key) != destination_manifest.get(key)
        )
        raise TrustedActivationFenceError(
            "Snapshot directory divergente: "
            f"{source}/{differing} source={source_manifest.get(differing)!r} "
            f"snapshot={destination_manifest.get(differing)!r}"
        )
    return source_manifest


def _copy_file(source: Path, destination: Path) -> dict[str, list[Any]]:
    shutil.copy2(source, destination, follow_symlinks=False)
    source_meta = source.lstat()
    os.chown(destination, source_meta.st_uid, source_meta.st_gid)
    os.chmod(destination, stat.S_IMODE(source_meta.st_mode))
    if not stat.S_ISREG(source_meta.st_mode):
        raise TrustedActivationFenceError(f"Fence file non regolare: {source}")
    manifest = {
        ".": [
            "f",
            source_meta.st_mode,
            source_meta.st_uid,
            source_meta.st_gid,
            source_meta.st_size,
            _file_digest(source),
        ]
    }
    destination_meta = destination.lstat()
    destination_record = [
        "f",
        destination_meta.st_mode,
        destination_meta.st_uid,
        destination_meta.st_gid,
        destination_meta.st_size,
        _file_digest(destination),
    ]
    if destination_record != manifest["."]:
        raise TrustedActivationFenceError(f"Snapshot file divergente: {source}")
    return manifest


def _current_manifest(path: Path, kind: str) -> dict[str, list[Any]]:
    if kind == "directory":
        return _tree_manifest(path)
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode):
        raise TrustedActivationFenceError(f"Underlying fence file non regolare: {path}")
    return {
        ".": [
            "f", metadata.st_mode, metadata.st_uid, metadata.st_gid,
            metadata.st_size, _file_digest(path),
        ]
    }


def _same_mount_namespace_as_pid1() -> bool:
    try:
        return os.readlink("/proc/self/ns/mnt") == os.readlink("/proc/1/ns/mnt")
    except OSError as exc:
        raise TrustedActivationFenceError("Mount namespace PID 1 non verificabile") from exc


def _validate_transaction(transaction: Mapping[str, Any], *, require_underlying: bool) -> None:
    root = Path(str(transaction["root"]))
    root_mount = _top_mount(root)
    if root_mount is None or root_mount.filesystem != "tmpfs":
        raise TrustedActivationFenceError("tmpfs fence attesa assente")
    tmpfs_device = root_mount.major_minor
    if "ro" not in root_mount.options:
        raise TrustedActivationFenceError("tmpfs fence non read-only")
    for target in transaction["targets"]:
        target_path = Path(target["path"])
        mounted = _top_mount(target_path)
        if (
            mounted is None
            or mounted.major_minor != tmpfs_device
            or "ro" not in mounted.options
        ):
            raise TrustedActivationFenceError(f"Bind snapshot non verificata: {target_path}")
        snapshot = root / str(target["snapshot"])
        if _current_manifest(snapshot, str(target["kind"])) != target["manifest"]:
            raise TrustedActivationFenceError(f"Byte snapshot fence mutati: {target_path}")
        if require_underlying:
            lower = root / str(target["lower"])
            current = _current_manifest(lower, str(target["kind"]))
            expected_underlying = target.get("underlying_manifest", target["manifest"])
            if current != expected_underlying:
                intent = target.get("symlink_intent")
                accepted = dict(expected_underlying)
                if isinstance(intent, dict):
                    relative = str(intent.get("relative", ""))
                    record = current.get(relative)
                    if (
                        relative
                        and record is not None
                        and record[0] == "l"
                        and record[2] == 0
                        and record[4] == intent.get("target")
                    ):
                        accepted[relative] = record
                if current != accepted:
                    raise TrustedActivationFenceError(
                        "Underlying mutato durante fence; protezione lasciata attiva: "
                        f"{target_path}"
                    )


def _remove_transaction(transaction: Mapping[str, Any]) -> None:
    root = Path(str(transaction["root"]))
    root_mount = _top_mount(root)
    if root_mount is None or root_mount.filesystem != "tmpfs":
        raise TrustedActivationFenceError("Recovery rifiuta mount root non TheBitLab")
    device = root_mount.major_minor
    for target in reversed(transaction["targets"]):
        path = Path(target["path"])
        mounted = _top_mount(path)
        if mounted is not None:
            if mounted.major_minor != device:
                raise TrustedActivationFenceError(f"Recovery rifiuta mount operator: {path}")
            _umount(path)
    for target in reversed(transaction["targets"]):
        lower = root / str(target["lower"])
        if _top_mount(lower) is not None:
            _umount(lower)
    _umount(root)
    shutil.rmtree(root)
    for target in reversed(transaction["targets"]):
        if target.get("created"):
            path = Path(target["path"])
            try:
                path.rmdir()
            except OSError as exc:
                raise TrustedActivationFenceError(
                    f"Directory source temporanea non rimovibile: {path}"
                ) from exc


def _remove_incomplete_transaction(transaction: Mapping[str, Any]) -> None:
    """Unwind setup-only mounts by exact tmpfs device; no trust decision used them."""

    root = Path(str(transaction["root"]))
    root_mount = _top_mount(root)
    if root_mount is not None:
        if root_mount.filesystem != "tmpfs":
            raise TrustedActivationFenceError("Setup recovery rifiuta root mount non tmpfs")
        device = root_mount.major_minor
        for target in reversed(transaction.get("targets", [])):
            path = Path(target["path"])
            mounted = _top_mount(path)
            if mounted is not None and mounted.major_minor == device:
                _umount(path)
        for target in reversed(transaction.get("targets", [])):
            lower = root / str(target["lower"])
            if _top_mount(lower) is not None:
                _umount(lower)
        _umount(root)
    if root.exists():
        shutil.rmtree(root)
    for target in reversed(transaction.get("targets", [])):
        if target.get("created"):
            path = Path(target["path"])
            if path.exists() and not any(path.iterdir()):
                path.rmdir()


def recover_stale_fences() -> None:
    """Unwind exact setup/active mounts after validating their recorded phase."""

    state = _read_state()
    if state is None:
        return
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
    if state.get("boot_id") != boot_id:
        # /run should not survive reboot.  Metadata here would be non-canonical.
        raise TrustedActivationFenceError("Metadata fence appartiene a un altro boot")
    transactions = state.get("transactions")
    if state.get("poisoned") or not isinstance(transactions, list) or not transactions:
        raise TrustedActivationFenceError(
            "Fence stale non recuperabile automaticamente; underlying da ispezionare"
        )
    for transaction in transactions:
        if transaction.get("phase") == "active":
            _validate_transaction(transaction, require_underlying=True)
        elif transaction.get("phase") != "setup":
            raise TrustedActivationFenceError("Fase transaction fence non valida")
    for transaction in reversed(transactions):
        if transaction.get("phase") == "active":
            _remove_transaction(transaction)
        else:
            _remove_incomplete_transaction(transaction)
    _write_transactions(())


class SnapshotMountFence:
    """Freeze exact host directories/files as independent read-only snapshots."""

    def __init__(
        self,
        name: str,
        *,
        directories: Iterable[Path],
        files: Iterable[Path],
    ) -> None:
        self.name = name
        directory_set = tuple(sorted(set(directories), key=lambda path: (len(path.parts), str(path))))
        self.directories = directory_set
        self.files = tuple(
            sorted(
                path for path in set(files)
                if not any(path == directory or directory in path.parents for directory in directory_set)
            )
        )
        self.transaction: dict[str, Any] | None = None

    def __enter__(self) -> Self:
        if os.geteuid() != 0 or not _same_mount_namespace_as_pid1():
            raise TrustedActivationFenceError(
                "Fence richiede root nel mount namespace globale di PID 1"
            )
        _safe_runtime_root()
        state = _read_state()
        transactions = list(state.get("transactions", [])) if state else []
        token = f"{os.getpid()}-{uuid.uuid4().hex}"
        root = TRANSACTION_ROOT / token
        root.mkdir(mode=0o700)
        transaction: dict[str, Any] = {
            "name": self.name,
            "token": token,
            "phase": "setup",
            "root": str(root),
            "targets": [],
        }
        transactions.append(transaction)
        _write_transactions(transactions)
        try:
            _mount("tmpfs", root, "tmpfs", MS_NOSUID | MS_NODEV, "mode=0700,size=256m")
            lower_root = root / "lower"
            snapshot_root = root / "snapshot"
            lower_root.mkdir()
            snapshot_root.mkdir()
            requested = tuple((path, "directory") for path in self.directories) + tuple(
                (path, "file") for path in self.files
            )
            for index, (path, kind) in enumerate(requested):
                if not path.is_absolute() or path != Path(os.path.abspath(path)):
                    raise TrustedActivationFenceError(f"Target fence non canonico: {path}")
                transaction["targets"].append(
                    {
                        "path": str(path),
                        "kind": kind,
                        "lower": f"lower/{index:04d}",
                        "snapshot": f"snapshot/{index:04d}",
                        "created": kind == "directory" and not path.exists(),
                    }
                )
            # Persist the complete cleanup plan before the first source mount/create.
            _write_transactions(transactions)
            for target in transaction["targets"]:
                path = Path(target["path"])
                kind = str(target["kind"])
                if target["created"]:
                    path.mkdir(parents=True, mode=0o755)
                metadata = path.lstat()
                if (kind == "directory") != stat.S_ISDIR(metadata.st_mode) or path.is_symlink():
                    raise TrustedActivationFenceError(f"Tipo target fence inatteso: {path}")
                lower = root / str(target["lower"])
                snapshot = root / str(target["snapshot"])
                if kind == "directory":
                    lower.mkdir()
                    _mount(str(path), lower, None, MS_BIND)
                    manifest = _copy_tree(lower, snapshot)
                else:
                    lower.touch(mode=0o600)
                    _mount(str(path), lower, None, MS_BIND)
                    manifest = _copy_file(lower, snapshot)
                target["manifest"] = manifest
                target["source_hardlinks"] = _source_hardlinks(lower, kind)
            _write_transactions(transactions)
            # A superblock remount, unlike a read-only bind, rejects pre-open writers
            # and makes every alias/bind of the copied inode immutable.
            _mount(
                None,
                root,
                None,
                MS_REMOUNT | MS_RDONLY | MS_NOSUID | MS_NODEV,
                "mode=0700",
            )
            root_record = _top_mount(root)
            if root_record is None or root_record.filesystem != "tmpfs" or "ro" not in root_record.options:
                raise TrustedActivationFenceError("Remount tmpfs read-only non verificato")
            for target in transaction["targets"]:
                _mount(str(root / target["snapshot"]), Path(target["path"]), None, MS_BIND)
            _validate_transaction(transaction, require_underlying=False)
            transaction["phase"] = "active"
            _write_transactions(transactions)
            self.transaction = transaction
            _ACTIVE_TRANSACTIONS.append(transaction)
            return self
        except Exception:
            current = _read_state()
            current_transactions = list(current.get("transactions", [])) if current else []
            try:
                _remove_incomplete_transaction(transaction)
                if current_transactions and current_transactions[-1].get("token") == token:
                    current_transactions.pop()
                _write_transactions(current_transactions)
            except Exception:  # noqa: BLE001 - preserve original setup failure fail-closed.
                _write_transactions(current_transactions, poisoned=True)
            raise

    def create_underlying_symlink(self, path: Path, target_value: str) -> None:
        """Create one declared persistence link while its global namespace stays frozen."""

        if self.transaction is None or not target_value.startswith("/"):
            raise TrustedActivationFenceError("Mutazione persistence fence non valida")
        containing = [
            target for target in self.transaction["targets"]
            if target["kind"] == "directory"
            and (path == Path(target["path"]) or Path(target["path"]) in path.parents)
        ]
        if len(containing) != 1:
            raise TrustedActivationFenceError(f"Symlink fuori dal directory snapshot: {path}")
        record = containing[0]
        root = Path(str(self.transaction["root"]))
        directory = Path(record["path"])
        relative_path = path.relative_to(directory)
        relative = relative_path.as_posix()
        lower_path = root / str(record["lower"]) / relative_path
        if path.exists() or path.is_symlink() or lower_path.exists() or lower_path.is_symlink():
            raise TrustedActivationFenceError(f"Persistence symlink già presente: {path}")
        _validate_transaction(self.transaction, require_underlying=True)
        record["symlink_intent"] = {"relative": relative, "target": target_value}
        state = _read_state()
        transactions = list(state.get("transactions", [])) if state else []
        for index, transaction in enumerate(transactions):
            if transaction.get("token") == self.transaction["token"]:
                transactions[index] = self.transaction
                break
        else:
            raise TrustedActivationFenceError("Transaction persistence non registrata")
        _write_transactions(transactions)
        lower_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = lower_path.with_name(f".{lower_path.name}.{os.getpid()}")
        try:
            os.symlink(target_value, temporary)
            os.replace(temporary, lower_path)
            descriptor = os.open(lower_path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        finally:
            temporary.unlink(missing_ok=True)
        current = _current_manifest(root / str(record["lower"]), "directory")
        expected = dict(record.get("underlying_manifest", record["manifest"]))
        symlink_record = current.get(relative)
        if (
            symlink_record is None
            or symlink_record[0] != "l"
            or symlink_record[2] != 0
            or symlink_record[4] != target_value
        ):
            raise TrustedActivationFenceError(f"Persistence symlink non canonico: {path}")
        expected[relative] = symlink_record
        if current != expected:
            raise TrustedActivationFenceError(
                "Mutazione concorrente durante persistence fence; protezione mantenuta"
            )
        record["underlying_manifest"] = current
        record.pop("symlink_intent", None)
        state = _read_state()
        transactions = list(state.get("transactions", [])) if state else []
        for index, transaction in enumerate(transactions):
            if transaction.get("token") == self.transaction["token"]:
                transactions[index] = self.transaction
                break
        _write_transactions(transactions)

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        if self.transaction is None:
            return False
        state = _read_state()
        transactions = list(state.get("transactions", [])) if state else []
        try:
            _validate_transaction(self.transaction, require_underlying=True)
            _remove_transaction(self.transaction)
        except Exception:
            _write_transactions(transactions, poisoned=True)
            raise
        if not transactions or transactions[-1].get("token") != self.transaction["token"]:
            _write_transactions(transactions, poisoned=True)
            raise TrustedActivationFenceError("Nesting fence divergente")
        transactions.pop()
        _write_transactions(transactions)
        if not _ACTIVE_TRANSACTIONS or _ACTIVE_TRANSACTIONS[-1] is not self.transaction:
            raise TrustedActivationFenceError("Registry runtime fence divergente")
        _ACTIVE_TRANSACTIONS.pop()
        self.transaction = None
        return False


@contextlib.contextmanager
def host_lock_and_recovery() -> Iterator[None]:
    locks = acquire_host_locks()
    try:
        recover_stale_fences()
        yield
    finally:
        locks.close()
