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
import re
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
_STATE_SCHEMA = "thebitlab.activation-fence.v2"
_MANIFEST_SCHEMA = "thebitlab.activation-fence-manifest.v1"
_MANIFEST_NAME = "transaction-manifest.json"
_MOUNT_SOURCE_PREFIX = "thebitlab-pilot-fence:"
_TOKEN_RE = re.compile(r"^[1-9][0-9]{0,19}-[0-9a-f]{32}$")
_TRANSACTION_NAMES = frozenset(
    {
        "trusted-activation-base",
        "trusted-systemd-execution",
        "trusted-systemd-generated-output",
    }
)
_TRANSACTION_PHASES = frozenset({"planned", "witnessed", "sealed", "active", "teardown"})
USR_MERGE_ALIASES: Mapping[Path, str] = {
    Path("/bin"): "usr/bin",
    Path("/sbin"): "usr/sbin",
    Path("/lib"): "usr/lib",
    Path("/lib64"): "usr/lib64",
}
_USRMERGE_ALIASES = USR_MERGE_ALIASES

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


def _canonical_transaction_root(token: str) -> Path:
    if not _TOKEN_RE.fullmatch(token):
        raise TrustedActivationFenceError("Token transaction fence non canonico")
    return TRANSACTION_ROOT / token


def _canonical_absolute(value: object, *, label: str) -> Path:
    if not isinstance(value, str):
        raise TrustedActivationFenceError(f"{label} fence non stringa")
    path = Path(value)
    if not path.is_absolute() or path != Path(os.path.abspath(path)) or ".." in path.parts:
        raise TrustedActivationFenceError(f"{label} fence non canonico")
    return path


def _validate_target_record(target: object, *, active: bool) -> None:
    if not isinstance(target, dict):
        raise TrustedActivationFenceError("Target metadata fence non oggetto")
    allowed = {
        "path", "kind", "lower", "snapshot", "created", "manifest",
        "source_hardlinks", "underlying_manifest", "symlink_intent",
    }
    if set(target) - allowed:
        raise TrustedActivationFenceError("Target metadata fence con campi sconosciuti")
    required = {"path", "kind", "lower", "snapshot", "created"}
    if active:
        required |= {"manifest", "source_hardlinks"}
    if not required <= set(target):
        raise TrustedActivationFenceError("Target metadata fence incompleto")
    path = _canonical_absolute(target["path"], label="Path target")
    if path in {Path("/"), Path("/run"), Path("/run/lock"), RUNTIME_ROOT, TRANSACTION_ROOT}:
        raise TrustedActivationFenceError("Target fence vietato")
    if target["kind"] not in {"directory", "file"} or not isinstance(target["created"], bool):
        raise TrustedActivationFenceError("Tipo target fence non valido")
    for key, prefix in (("lower", "lower/"), ("snapshot", "snapshot/")):
        value = target[key]
        if (
            not isinstance(value, str)
            or not value.startswith(prefix)
            or not value[len(prefix) :].isdigit()
            or "/" in value[len(prefix) :]
        ):
            raise TrustedActivationFenceError(f"Riferimento {key} fence non canonico")
    if "source_hardlinks" in target and not (
        isinstance(target["source_hardlinks"], (list, tuple))
        and all(isinstance(item, str) for item in target["source_hardlinks"])
    ):
        raise TrustedActivationFenceError("Hardlink metadata fence non canonici")
    if "manifest" in target and not isinstance(target["manifest"], dict):
        raise TrustedActivationFenceError("Manifest target fence non canonico")
    if "underlying_manifest" in target and not isinstance(target["underlying_manifest"], dict):
        raise TrustedActivationFenceError("Manifest underlying fence non canonico")
    intent = target.get("symlink_intent")
    if intent is not None and (
        not isinstance(intent, dict)
        or set(intent) != {"relative", "target"}
        or not all(isinstance(intent[key], str) for key in intent)
    ):
        raise TrustedActivationFenceError("Intent symlink fence non canonico")


def _validate_alias_record(alias: object) -> None:
    if not isinstance(alias, dict) or set(alias) != {"path", "target", "snapshot"}:
        raise TrustedActivationFenceError("Alias metadata fence non canonico")
    path = _canonical_absolute(alias["path"], label="Path alias")
    expected = _USRMERGE_ALIASES.get(path)
    if expected is None or alias["target"] != expected:
        raise TrustedActivationFenceError("Alias usrmerge fence fuori policy")
    snapshot = alias["snapshot"]
    if not isinstance(snapshot, str) or not snapshot.startswith("snapshot/"):
        raise TrustedActivationFenceError("Snapshot alias fence non canonica")


def _validate_mount_witness(value: object, *, token: str) -> None:
    if not isinstance(value, dict) or set(value) != {
        "mount_id", "parent_id", "major_minor", "filesystem", "source",
        "root", "mount_point", "options",
    }:
        raise TrustedActivationFenceError("Kernel witness fence non canonico")
    if not isinstance(value["mount_id"], int) or not isinstance(value["parent_id"], int):
        raise TrustedActivationFenceError("Mount ID witness non canonico")
    if value["filesystem"] != "tmpfs" or value["source"] != _MOUNT_SOURCE_PREFIX + token:
        raise TrustedActivationFenceError("Source witness fence non canonica")
    if value["root"] != "/" or value["mount_point"] != str(_canonical_transaction_root(token)):
        raise TrustedActivationFenceError("Mount point witness fence non canonico")
    if not isinstance(value["major_minor"], str) or not isinstance(value["options"], list):
        raise TrustedActivationFenceError("Device/options witness fence non canonici")


def _validate_transaction_shape(transaction: object) -> None:
    if not isinstance(transaction, dict):
        raise TrustedActivationFenceError("Transaction metadata fence non oggetto")
    allowed = {"name", "token", "phase", "root", "targets", "aliases", "mount"}
    if set(transaction) - allowed or not {"name", "token", "phase", "root", "targets", "aliases"} <= set(transaction):
        raise TrustedActivationFenceError("Transaction metadata fence non chiusa")
    name, token, phase = transaction["name"], transaction["token"], transaction["phase"]
    if name not in _TRANSACTION_NAMES or not isinstance(token, str) or phase not in _TRANSACTION_PHASES:
        raise TrustedActivationFenceError("Identity/fase transaction fence non valida")
    if _canonical_absolute(transaction["root"], label="Root transaction") != _canonical_transaction_root(token):
        raise TrustedActivationFenceError("Root/token transaction fence divergenti")
    if not isinstance(transaction["targets"], list) or not isinstance(transaction["aliases"], list):
        raise TrustedActivationFenceError("Inventario transaction fence non lista")
    active = phase in {"sealed", "active", "teardown"}
    for target in transaction["targets"]:
        _validate_target_record(target, active=active)
    for alias in transaction["aliases"]:
        _validate_alias_record(alias)
    if phase != "planned":
        _validate_mount_witness(transaction.get("mount"), token=token)
    elif "mount" in transaction:
        raise TrustedActivationFenceError("Transaction planned con falsa kernel authority")


def _validate_state_document(value: object) -> None:
    if not isinstance(value, dict) or set(value) != {"schema", "boot_id", "poisoned", "transactions"}:
        raise TrustedActivationFenceError("Schema metadata fence non chiuso")
    if value["schema"] != _STATE_SCHEMA or not isinstance(value["boot_id"], str):
        raise TrustedActivationFenceError("Schema/boot metadata fence inatteso")
    if not isinstance(value["poisoned"], bool) or not isinstance(value["transactions"], list):
        raise TrustedActivationFenceError("Metadata fence non canonici")
    tokens: set[str] = set()
    for transaction in value["transactions"]:
        _validate_transaction_shape(transaction)
        token = transaction["token"]
        if token in tokens:
            raise TrustedActivationFenceError("Token transaction fence duplicato")
        tokens.add(token)


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
    _validate_state_document(value)
    return value


def _write_transactions(transactions: Sequence[Mapping[str, Any]], *, poisoned: bool = False) -> None:
    if not transactions:
        STATE_PATH.unlink(missing_ok=True)
        return
    _atomic_json(
        STATE_PATH,
        {
            "schema": _STATE_SCHEMA,
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


def _fault(point: str, name: str = "") -> None:
    expected_name = os.environ.get("THEBITLAB_ACTIVATION_CRASH_FENCE_NAME", "")
    if (
        os.environ.get("THEBITLAB_EPHEMERAL_CRASH_TEST") == "1"
        and os.environ.get("THEBITLAB_ACTIVATION_CRASH_POINT") == point
        and (not expected_name or expected_name == name)
    ):
        os._exit(97)


def _mount_witness(record: MountRecord) -> dict[str, Any]:
    return {
        "mount_id": record.mount_id,
        "parent_id": record.parent_id,
        "major_minor": record.major_minor,
        "filesystem": record.filesystem,
        "source": record.source,
        "root": record.root,
        "mount_point": str(record.mount_point),
        "options": sorted(record.options),
    }


def _kernel_root_mount(token: str, *, require_read_only: bool) -> MountRecord:
    root = _canonical_transaction_root(token)
    record = _top_mount(root)
    if (
        record is None
        or record.filesystem != "tmpfs"
        or record.source != _MOUNT_SOURCE_PREFIX + token
        or record.root != "/"
        or record.mount_point != root
        or not {"nosuid", "nodev"} <= record.options
        or (require_read_only and "ro" not in record.options)
    ):
        raise TrustedActivationFenceError("Kernel identity root fence non verificata")
    return record


def _assert_witness_current(transaction: Mapping[str, Any], record: MountRecord) -> None:
    witness = transaction.get("mount")
    _validate_mount_witness(witness, token=str(transaction["token"]))
    if witness != _mount_witness(record):
        raise TrustedActivationFenceError("Kernel witness fence stale/ABA")


def _manifest_value(transaction: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": _MANIFEST_SCHEMA,
        "transaction": {
            "name": transaction["name"],
            "token": transaction["token"],
            "phase": "sealed",
            "root": transaction["root"],
            "targets": transaction["targets"],
            "aliases": transaction["aliases"],
            "mount": transaction["mount"],
        },
    }


def _read_immutable_manifest(root: Path, token: str) -> dict[str, Any]:
    path = root / _MANIFEST_NAME
    try:
        metadata = path.lstat()
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise TrustedActivationFenceError("Manifest immutabile fence non leggibile") from exc
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != 0
        or metadata.st_gid != 0
        or metadata.st_mode & 0o077
        or metadata.st_nlink != 1
        or not isinstance(value, dict)
        or set(value) != {"schema", "transaction"}
        or value["schema"] != _MANIFEST_SCHEMA
    ):
        raise TrustedActivationFenceError("Manifest immutabile fence non canonico")
    transaction = value["transaction"]
    _validate_transaction_shape(transaction)
    if transaction["token"] != token or transaction["phase"] != "sealed":
        raise TrustedActivationFenceError("Manifest immutabile fence con identity divergente")
    return transaction


def _authoritative_manifest(transaction: Mapping[str, Any]) -> dict[str, Any]:
    token = str(transaction["token"])
    root = _canonical_transaction_root(token)
    manifest = _read_immutable_manifest(root, token)
    for key in ("name", "token", "root", "targets", "aliases", "mount"):
        if transaction.get(key) != manifest[key]:
            # Mutable state may add only reconciliation fields to targets. Compare the
            # immutable authority-bearing core separately below.
            if key != "targets":
                raise TrustedActivationFenceError("Metadata mutable/manifest fence divergenti")
    if len(transaction["targets"]) != len(manifest["targets"]):
        raise TrustedActivationFenceError("Inventario target mutable divergente")
    core = {"path", "kind", "lower", "snapshot", "created", "manifest", "source_hardlinks"}
    for mutable, frozen in zip(transaction["targets"], manifest["targets"], strict=True):
        if {key: mutable.get(key) for key in core} != {key: frozen.get(key) for key in core}:
            raise TrustedActivationFenceError("Target mutable/manifest fence divergente")
    return manifest


def _accepted_underlying_manifest(
    target: Mapping[str, Any], current: dict[str, list[Any]]
) -> dict[str, list[Any]]:
    expected = dict(target["manifest"])
    path = Path(str(target["path"]))
    if target["kind"] != "directory" or path != Path("/etc"):
        return expected
    relative = "systemd/system/multi-user.target.wants/nginx.service"
    record = current.get(relative)
    if (
        record is not None
        and record[0] == "l"
        and record[2] == 0
        and record[3] == 0
        and record[4] == "/usr/lib/systemd/system/nginx.service"
    ):
        expected[relative] = record
    return expected


def _validate_transaction(transaction: Mapping[str, Any], *, require_underlying: bool) -> None:
    _validate_transaction_shape(transaction)
    token = str(transaction["token"])
    root = _canonical_transaction_root(token)
    root_mount = _kernel_root_mount(token, require_read_only=True)
    _assert_witness_current(transaction, root_mount)
    manifest = _authoritative_manifest(transaction)
    device = root_mount.major_minor
    source = root_mount.source
    for target in manifest["targets"]:
        target_path = Path(target["path"])
        mounted = _top_mount(target_path)
        if (
            mounted is None
            or mounted.major_minor != device
            or mounted.source != source
            or mounted.root != "/" + str(target["snapshot"]).lstrip("/")
            or "ro" not in mounted.options
        ):
            raise TrustedActivationFenceError(f"Bind snapshot non verificata: {target_path}")
        snapshot = root / str(target["snapshot"])
        if _current_manifest(snapshot, str(target["kind"])) != target["manifest"]:
            raise TrustedActivationFenceError(f"Byte snapshot fence mutati: {target_path}")
        if require_underlying:
            lower = root / str(target["lower"])
            current = _current_manifest(lower, str(target["kind"]))
            accepted = _accepted_underlying_manifest(target, current)
            if current != accepted:
                raise TrustedActivationFenceError(
                    "Underlying mutato durante fence; protezione lasciata attiva: "
                    f"{target_path}"
                )
    for alias in manifest["aliases"]:
        path = Path(alias["path"])
        mounted = _top_mount(path)
        if (
            mounted is None
            or mounted.major_minor != device
            or mounted.source != source
            or mounted.root != "/" + str(alias["snapshot"]).lstrip("/")
            or "ro" not in mounted.options
        ):
            raise TrustedActivationFenceError(f"Alias usrmerge non frozen: {path}")


def _transaction_source_records(token: str, root_mount: MountRecord) -> tuple[MountRecord, ...]:
    source = _MOUNT_SOURCE_PREFIX + token
    records = tuple(
        record for record in _mount_records()
        if record.source == source and record.major_minor == root_mount.major_minor
    )
    if root_mount not in records:
        raise TrustedActivationFenceError("Root mount transaction non inventariata")
    for record in records:
        if record == root_mount:
            continue
        if not record.root.startswith(("/lower/", "/snapshot/")):
            raise TrustedActivationFenceError("Mount transaction con root kernel inattesa")
    return records


def _restore_usrmerge_aliases(manifest: Mapping[str, Any]) -> None:
    for alias in reversed(manifest["aliases"]):
        path = Path(alias["path"])
        target = str(alias["target"])
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            metadata = None
        if metadata is not None and stat.S_ISLNK(metadata.st_mode):
            if os.readlink(path) == target and metadata.st_uid == 0 and metadata.st_gid == 0:
                continue
            raise TrustedActivationFenceError(f"Alias usrmerge esterna divergente: {path}")
        if metadata is None or not stat.S_ISDIR(metadata.st_mode):
            raise TrustedActivationFenceError(f"Mountpoint alias usrmerge non ripristinabile: {path}")
        try:
            path.rmdir()
            os.symlink(target, path)
        except OSError as exc:
            raise TrustedActivationFenceError(f"Restore alias usrmerge fallito: {path}") from exc


def _remove_kernel_transaction(token: str, manifest: Mapping[str, Any] | None) -> None:
    root = _canonical_transaction_root(token)
    root_mount = _kernel_root_mount(token, require_read_only=False)
    records = _transaction_source_records(token, root_mount)
    external = sorted(
        (record for record in records if record.mount_point != root),
        key=lambda record: (len(record.mount_point.parts), record.mount_id),
        reverse=True,
    )
    for record in external:
        current = _top_mount(record.mount_point)
        if current is None or current.mount_id != record.mount_id:
            raise TrustedActivationFenceError("Mount transaction cambiata durante cleanup")
        _umount(record.mount_point)
        _fault(
            "fence_during_teardown",
            str(manifest.get("name", "")) if manifest is not None else "",
        )
    _umount(root)
    try:
        root.rmdir()
    except OSError as exc:
        raise TrustedActivationFenceError("Root transaction non vuota/sicura dopo umount") from exc
    if manifest is not None:
        _restore_usrmerge_aliases(manifest)


def _remove_transaction(transaction: Mapping[str, Any]) -> None:
    _validate_transaction(transaction, require_underlying=True)
    manifest = _authoritative_manifest(transaction)
    _remove_kernel_transaction(str(transaction["token"]), manifest)


def _remove_incomplete_transaction(
    transaction: Mapping[str, Any], *, trusted_in_process: bool = False
) -> None:
    """Unwind only mounts carrying the exact transaction-unique kernel source."""

    _validate_transaction_shape(transaction)
    token = str(transaction["token"])
    root = _canonical_transaction_root(token)
    root_mount = _top_mount(root)
    if root_mount is None:
        if not root.exists() and not root.is_symlink():
            return
        if not trusted_in_process:
            raise TrustedActivationFenceError(
                "Root planned senza kernel witness; recovery manuale senza rimozione"
            )
        try:
            metadata = root.lstat()
            if not stat.S_ISDIR(metadata.st_mode) or root.is_symlink():
                raise OSError(errno.EINVAL, "root planned non directory")
            root.rmdir()
        except OSError as exc:
            raise TrustedActivationFenceError("Root planned non vuota; recovery manuale") from exc
        return
    root_mount = _kernel_root_mount(token, require_read_only=False)
    manifest: Mapping[str, Any] | None = None
    if "ro" in root_mount.options:
        manifest = _read_immutable_manifest(root, token)
    _remove_kernel_transaction(token, manifest)


def _kernel_orphan_tokens() -> tuple[str, ...]:
    tokens: set[str] = set()
    for record in _mount_records():
        if not record.source.startswith(_MOUNT_SOURCE_PREFIX) or record.root != "/":
            continue
        token = record.source.removeprefix(_MOUNT_SOURCE_PREFIX)
        try:
            expected = _canonical_transaction_root(token)
        except TrustedActivationFenceError:
            continue
        if record.mount_point == expected:
            tokens.add(token)
    return tuple(sorted(tokens))


def recover_stale_fences() -> None:
    """Recover only transaction mounts proven by their exact kernel identity."""

    state = _read_state()
    recorded_tokens = {
        str(transaction["token"]) for transaction in state["transactions"]
    } if state is not None else set()
    kernel_tokens = set(_kernel_orphan_tokens())
    try:
        entries = tuple(TRANSACTION_ROOT.iterdir()) if TRANSACTION_ROOT.exists() else ()
    except OSError as exc:
        raise TrustedActivationFenceError("Transaction root non enumerabile") from exc
    for entry in entries:
        try:
            metadata = entry.lstat()
        except OSError as exc:
            raise TrustedActivationFenceError("Transaction entry non verificabile") from exc
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or entry.is_symlink()
            or not _TOKEN_RE.fullmatch(entry.name)
        ):
            raise TrustedActivationFenceError(
                "Transaction entry senza kernel witness; recovery manuale senza rimozione"
            )
        if entry.name not in kernel_tokens:
            raise TrustedActivationFenceError(
                "Root planned senza kernel witness; recovery manuale senza rimozione"
            )
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
    if state is not None and state["boot_id"] != boot_id:
        raise TrustedActivationFenceError("Metadata fence appartiene a un altro boot")
    if state is not None and state["poisoned"]:
        raise TrustedActivationFenceError(
            "Fence stale non recuperabile automaticamente; underlying da ispezionare"
        )
    transactions = list(state["transactions"]) if state is not None else []
    orphan_tokens = kernel_tokens - recorded_tokens

    # Validate every active authority before mutating any mount. Planned/witnessed
    # JSON is only a hint; cleanup derives the mounted set from mountinfo source.
    for transaction in transactions:
        if transaction["phase"] == "active":
            _validate_transaction(transaction, require_underlying=True)
        elif transaction["phase"] in {"sealed", "teardown"}:
            _authoritative_manifest(transaction)
    for transaction in reversed(transactions):
        if transaction["phase"] == "active":
            _remove_transaction(transaction)
        else:
            _remove_incomplete_transaction(transaction)
    for token in sorted(orphan_tokens, reverse=True):
        root = _canonical_transaction_root(token)
        root_mount = _kernel_root_mount(token, require_read_only=False)
        manifest = _read_immutable_manifest(root, token) if "ro" in root_mount.options else None
        _remove_kernel_transaction(token, manifest)
    _write_transactions(())


class SnapshotMountFence:
    """Freeze exact host directories/files as independent read-only snapshots."""

    def __init__(
        self,
        name: str,
        *,
        directories: Iterable[Path],
        files: Iterable[Path],
        aliases: Mapping[Path, str] | None = None,
    ) -> None:
        if name not in _TRANSACTION_NAMES:
            raise TrustedActivationFenceError("Nome transaction fence fuori policy")
        self.name = name
        directory_set = tuple(sorted(set(directories), key=lambda path: (len(path.parts), str(path))))
        self.directories = directory_set
        self.files = tuple(
            sorted(
                path for path in set(files)
                if not any(path == directory or directory in path.parents for directory in directory_set)
            )
        )
        alias_value = dict(aliases or {})
        if any(_USRMERGE_ALIASES.get(path) != target for path, target in alias_value.items()):
            raise TrustedActivationFenceError("Alias richiesto fuori policy usrmerge")
        self.aliases = tuple(sorted(alias_value.items(), key=lambda item: str(item[0])))
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
        root = _canonical_transaction_root(token)
        root.mkdir(mode=0o700)
        _fault("fence_after_transaction_root", self.name)
        requested = tuple((path, "directory") for path in self.directories) + tuple(
            (path, "file") for path in self.files
        )
        targets: list[dict[str, Any]] = []
        snapshot_by_source: dict[Path, str] = {}
        for index, (path, kind) in enumerate(requested):
            if not path.is_absolute() or path != Path(os.path.abspath(path)):
                raise TrustedActivationFenceError(f"Target fence non canonico: {path}")
            snapshot = f"snapshot/{index:04d}"
            targets.append(
                {
                    "path": str(path),
                    "kind": kind,
                    "lower": f"lower/{index:04d}",
                    "snapshot": snapshot,
                    "created": kind == "directory" and not path.exists(),
                }
            )
            if kind == "directory":
                snapshot_by_source[path] = snapshot
        aliases: list[dict[str, str]] = []
        for path, target in self.aliases:
            source = Path("/") / target
            snapshot = snapshot_by_source.get(source)
            if snapshot is None:
                raise TrustedActivationFenceError(f"Source alias non inclusa nella fence: {source}")
            aliases.append({"path": str(path), "target": target, "snapshot": snapshot})
        transaction: dict[str, Any] = {
            "name": self.name,
            "token": token,
            "phase": "planned",
            "root": str(root),
            "targets": targets,
            "aliases": aliases,
        }
        transactions.append(transaction)
        _write_transactions(transactions)
        try:
            source = _MOUNT_SOURCE_PREFIX + token
            _mount(source, root, "tmpfs", MS_NOSUID | MS_NODEV, "mode=0700,size=256m")
            _fault("fence_after_root_mount_before_witness", self.name)
            root_record = _kernel_root_mount(token, require_read_only=False)
            transaction["mount"] = _mount_witness(root_record)
            transaction["phase"] = "witnessed"
            _write_transactions(transactions)
            _fault("fence_after_root_mount_witness", self.name)
            lower_root = root / "lower"
            snapshot_root = root / "snapshot"
            lower_root.mkdir()
            snapshot_root.mkdir()
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
                    _fault("fence_during_target_setup", self.name)
                    manifest = _copy_tree(lower, snapshot)
                else:
                    lower.touch(mode=0o600)
                    _mount(str(path), lower, None, MS_BIND)
                    manifest = _copy_file(lower, snapshot)
                _fault("fence_during_snapshot_copy", self.name)
                target["manifest"] = manifest
                target["source_hardlinks"] = list(_source_hardlinks(lower, kind))
            _write_transactions(transactions)

            # Persist the authority manifest while writable, but record the exact
            # options required after the imminent superblock remount.
            final_witness = _mount_witness(root_record)
            final_witness["options"] = sorted(
                (set(final_witness["options"]) - {"rw"}) | {"ro", "nosuid", "nodev"}
            )
            transaction["mount"] = final_witness
            _atomic_json(root / _MANIFEST_NAME, _manifest_value(transaction))
            _mount(
                None,
                root,
                None,
                MS_REMOUNT | MS_RDONLY | MS_NOSUID | MS_NODEV,
                "mode=0700",
            )
            root_record = _kernel_root_mount(token, require_read_only=True)
            _fault("fence_after_ro_remount", self.name)
            transaction["mount"] = _mount_witness(root_record)
            transaction["phase"] = "sealed"
            _write_transactions(transactions)

            for target in transaction["targets"]:
                _mount(str(root / target["snapshot"]), Path(target["path"]), None, MS_BIND)
            for alias in transaction["aliases"]:
                path = Path(alias["path"])
                metadata = path.lstat()
                if (
                    not stat.S_ISLNK(metadata.st_mode)
                    or metadata.st_uid != 0
                    or metadata.st_gid != 0
                    or os.readlink(path) != alias["target"]
                ):
                    raise TrustedActivationFenceError(f"Alias usrmerge baseline divergente: {path}")
                path.unlink()
                path.mkdir(mode=0o755)
                _mount(str(root / alias["snapshot"]), path, None, MS_BIND)
            transaction["phase"] = "active"
            _validate_transaction(transaction, require_underlying=False)
            _write_transactions(transactions)
            _fault("fence_after_active_state", self.name)
            self.transaction = transaction
            _ACTIVE_TRANSACTIONS.append(transaction)
            return self
        except Exception:
            current = _read_state()
            current_transactions = list(current.get("transactions", [])) if current else []
            try:
                _remove_incomplete_transaction(transaction, trusted_in_process=True)
                if current_transactions and current_transactions[-1].get("token") == token:
                    current_transactions.pop()
                _write_transactions(current_transactions)
            except Exception:  # noqa: BLE001 - preserve original setup failure fail-closed.
                _write_transactions(current_transactions, poisoned=True)
            raise

    def create_underlying_symlink(self, path: Path, target_value: str) -> None:
        """Create one declared persistence link while its global namespace stays frozen."""

        if (
            self.transaction is None
            or path != Path("/etc/systemd/system/multi-user.target.wants/nginx.service")
            or target_value != "/usr/lib/systemd/system/nginx.service"
        ):
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
            or symlink_record[3] != 0
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
            self.transaction["phase"] = "teardown"
            for index, recorded in enumerate(transactions):
                if recorded.get("token") == self.transaction["token"]:
                    transactions[index] = self.transaction
                    break
            else:
                raise TrustedActivationFenceError("Transaction teardown non registrata")
            _write_transactions(transactions)
            _fault("fence_before_teardown", self.name)
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
