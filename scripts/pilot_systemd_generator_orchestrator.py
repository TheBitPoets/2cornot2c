#!/usr/bin/env python3
"""Sealed stock-systemd generator orchestration for the Noble pilot boundary.

The selected static generator only reproduces the reviewed stock generator set.
This coordinator, already inside TrustedActivationFence and PID1's mount
namespace, owns preparation, filesystem-wide sealing, closed attestation,
prefix-combination validation and stable-handle adoption. Transaction IDs are
public audit identities, never bearer capabilities.
"""

from __future__ import annotations

import contextlib
import ctypes
import errno
import hashlib
import json
import os
import re
import signal
import socket
import stat
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class GeneratorOrchestratorError(RuntimeError):
    """Generated systemd authority could not be changed safely."""


RUNTIME_ROOT = Path("/run/thebitlab/pilot-generator-orchestrator")
TRANSACTION_ROOT = RUNTIME_ROOT / "transactions"
STATE_PATH = RUNTIME_ROOT / "current-bundle.json"
ORCHESTRATOR_BINARY = Path("/usr/sbin/thebitlab-systemd-generator-orchestrator")
ORCHESTRATOR_ENTRY = Path(
    "/etc/systemd/system-generators/thebitlab-generator-orchestrator"
)
CONTROL_SOCKET = "\0thebitlab-pilot-generator-v1"
TARGETS: Mapping[str, Path] = {
    "early": Path("/run/systemd/generator.early"),
    "normal": Path("/run/systemd/generator"),
    "late": Path("/run/systemd/generator.late"),
}
# Reverse generated-root lookup precedence. If PID1 begins enumeration after
# the selected generator is SIGKILLed, its early -> normal -> late traversal can
# still observe only one of these physically pre-attested prefixes.
ADOPTION_ORDER = ("late", "normal", "early")
LOOKUP_PRECEDENCE = ("early", "normal", "late")
TOKEN_RE = re.compile(r"^[1-9][0-9]{0,19}-[0-9a-f]{32}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ORCHESTRATOR_SOURCE_SHA256 = "69916ddab297cf3f2935d7be60c9c7f9f89515d73805ee694c85e3dd986d23e8"
ORCHESTRATOR_REVIEWED_SHA256 = "7e5c3d164975a8def99a815477a3db440821557e9543452eed60bcc32a96308f"
SOURCE_POLICY_ID = "thebitlab.noble-systemd-generator-policy.v1"
PACKAGE_BASELINE_SHA256 = "35dba57876cd9e9daee5a8f251fffa4e5e820c6edee95637533c4aadb45b05fb"

SELECTED_GENERATORS: tuple[Mapping[str, Any], ...] = (
    {"basename": "systemd-cryptsetup-generator", "path": "/usr/lib/systemd/system-generators/systemd-cryptsetup-generator", "package": "systemd", "package_identity": "systemd=255.4-1ubuntu8.17:amd64", "sha256": "f15c109b8f2989b52d4b9fbe0616c34f1d6fc447b2df50972489befffdcdeeb9", "execution_class": "parallel-ignore-child-exit", "expected_presence": True},
    {"basename": "systemd-debug-generator", "path": "/usr/lib/systemd/system-generators/systemd-debug-generator", "package": "systemd", "package_identity": "systemd=255.4-1ubuntu8.17:amd64", "sha256": "1c4134dfba90289c3f27c4dad93122ad65acba58f0271f9a81f3c70a7d22b0a1", "execution_class": "parallel-ignore-child-exit", "expected_presence": True},
    {"basename": "systemd-fstab-generator", "path": "/usr/lib/systemd/system-generators/systemd-fstab-generator", "package": "systemd", "package_identity": "systemd=255.4-1ubuntu8.17:amd64", "sha256": "15c4d4502f06b8f6d6dafca932edbaafc1dbdb8d7a0edc324f34000a49ba4d08", "execution_class": "parallel-ignore-child-exit", "expected_presence": True},
    {"basename": "systemd-getty-generator", "path": "/usr/lib/systemd/system-generators/systemd-getty-generator", "package": "systemd", "package_identity": "systemd=255.4-1ubuntu8.17:amd64", "sha256": "b25bbe3184dfdc205ca1f226c6829f21b39c132aed726d64deafe1007e45f5b6", "execution_class": "parallel-ignore-child-exit", "expected_presence": True},
    {"basename": "systemd-hibernate-resume-generator", "path": "/usr/lib/systemd/system-generators/systemd-hibernate-resume-generator", "package": "systemd", "package_identity": "systemd=255.4-1ubuntu8.17:amd64", "sha256": "b4f4a82855044c085d8b0f11fa2a04623097922894bd92924badcf2b9900ecfb", "execution_class": "parallel-ignore-child-exit", "expected_presence": True},
    {"basename": "systemd-integritysetup-generator", "path": "/usr/lib/systemd/system-generators/systemd-integritysetup-generator", "package": "systemd", "package_identity": "systemd=255.4-1ubuntu8.17:amd64", "sha256": "e1eeff5894aa94f0bafa9618a2df290bdc7e57a44b0bf5c83c8e0a72b91260d2", "execution_class": "parallel-ignore-child-exit", "expected_presence": True},
    {"basename": "systemd-rc-local-generator", "path": "/usr/lib/systemd/system-generators/systemd-rc-local-generator", "package": "systemd", "package_identity": "systemd=255.4-1ubuntu8.17:amd64", "sha256": "1940b17c163d9c1b5b98db9be3fe07204a33f3f4a23572934d731d7f0336ef80", "execution_class": "parallel-ignore-child-exit", "expected_presence": True},
    {"basename": "systemd-run-generator", "path": "/usr/lib/systemd/system-generators/systemd-run-generator", "package": "systemd", "package_identity": "systemd=255.4-1ubuntu8.17:amd64", "sha256": "d0e4b0d8470530116b9b6919d2cd8455d97eaad89ace11d7a3b7387a41831302", "execution_class": "parallel-ignore-child-exit", "expected_presence": True},
    {"basename": "systemd-system-update-generator", "path": "/usr/lib/systemd/system-generators/systemd-system-update-generator", "package": "systemd", "package_identity": "systemd=255.4-1ubuntu8.17:amd64", "sha256": "ed7791c0a28a4404065e863e703a469f3b3213a291a05baa960c83877de1d994", "execution_class": "parallel-ignore-child-exit", "expected_presence": True},
    {"basename": "systemd-sysv-generator", "path": "/usr/lib/systemd/system-generators/systemd-sysv-generator", "package": "systemd", "package_identity": "systemd=255.4-1ubuntu8.17:amd64", "sha256": "e4557b5fc18adad8b41da15bf5297c121a9f8445bb4c9c9d34a83b262c6507b4", "execution_class": "parallel-ignore-child-exit", "expected_presence": True},
    {"basename": "systemd-veritysetup-generator", "path": "/usr/lib/systemd/system-generators/systemd-veritysetup-generator", "package": "systemd", "package_identity": "systemd=255.4-1ubuntu8.17:amd64", "sha256": "75385259d93f97d88c26d36d1d904600707e551388d1558b98259307c9b45f7e", "execution_class": "parallel-ignore-child-exit", "expected_presence": True},
)
MASKED_GENERATORS = tuple(
    sorted((*[str(item["basename"]) for item in SELECTED_GENERATORS], "systemd-gpt-auto-generator"))
)
EXEC_SLOTS = (
    "ExecCondition", "ExecStartPre", "ExecStart", "ExecStartPost",
    "ExecReload", "ExecStop", "ExecStopPost",
)

MS_RDONLY = 1
MS_NOSUID = 2
MS_NODEV = 4
MS_REMOUNT = 32
MS_BIND = 4096
MNT_DETACH = 2
SYS_OPEN_TREE = 428
SYS_MOVE_MOUNT = 429
OPEN_TREE_CLONE = 1
MOVE_MOUNT_F_EMPTY_PATH = 0x4
MOVE_MOUNT_T_EMPTY_PATH = 0x40

if os.name == "posix":
    _LIBC: ctypes.CDLL | None = ctypes.CDLL(None, use_errno=True)
else:
    _LIBC = None


@dataclass(frozen=True)
class MountRecord:
    mount_id: int
    parent_id: int
    major_minor: str
    root: str
    target: Path
    options: frozenset[str]
    filesystem: str
    source: str
    super_options: frozenset[str]


@dataclass(frozen=True)
class RootManifest:
    root_class: str
    records: tuple[tuple[Any, ...], ...]
    sha256: str


@dataclass(frozen=True)
class EffectiveGraph:
    identity: str
    records: tuple[tuple[str, ...], ...]


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _decode_mount_path(value: str) -> Path:
    for encoded, decoded in (("\\040", " "), ("\\011", "\t"), ("\\012", "\n"), ("\\134", "\\")):
        value = value.replace(encoded, decoded)
    return Path(value)


def _mount_records() -> tuple[MountRecord, ...]:
    records: list[MountRecord] = []
    for line in Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines():
        left, right = line.split(" - ", 1)
        fields, filesystem = left.split(), right.split()
        records.append(
            MountRecord(
                int(fields[0]), int(fields[1]), fields[2], fields[3],
                _decode_mount_path(fields[4]), frozenset(fields[5].split(",")),
                filesystem[0], filesystem[1], frozenset(filesystem[2].split(",")),
            )
        )
    return tuple(records)


def _mount_id(descriptor: int) -> int:
    for line in Path(f"/proc/self/fdinfo/{descriptor}").read_text(encoding="ascii").splitlines():
        if line.startswith("mnt_id:"):
            return int(line.split(":", 1)[1])
    raise GeneratorOrchestratorError("Descriptor senza mount ID")


def _row_for_fd(descriptor: int) -> MountRecord:
    mount_id = _mount_id(descriptor)
    rows = [record for record in _mount_records() if record.mount_id == mount_id]
    if len(rows) != 1:
        raise GeneratorOrchestratorError(f"Mount ID non univoco: {mount_id}")
    return rows[0]


def _mount(source: str | None, target: Path, filesystem: str | None, flags: int, data: str | None = None) -> None:
    if _LIBC is None:
        raise GeneratorOrchestratorError("mount disponibile soltanto su Linux")
    encoded = lambda value: None if value is None else value.encode("utf-8")
    if _LIBC.mount(encoded(source), encoded(str(target)), encoded(filesystem), flags, encoded(data)) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(target))


def _umount(target: Path, flags: int = MNT_DETACH) -> None:
    if _LIBC is None or _LIBC.umount2(str(target).encode(), flags) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(target))


def _open_tree(directory_fd: int, name: str) -> int:
    assert _LIBC is not None
    descriptor = _LIBC.syscall(
        SYS_OPEN_TREE, directory_fd, name.encode(), OPEN_TREE_CLONE | os.O_CLOEXEC
    )
    if descriptor < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), name)
    return descriptor


def _move_mount(source_fd: int, target_fd: int) -> None:
    assert _LIBC is not None
    if _LIBC.syscall(
        SYS_MOVE_MOUNT, source_fd, b"", target_fd, b"",
        MOVE_MOUNT_F_EMPTY_PATH | MOVE_MOUNT_T_EMPTY_PATH,
    ) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))


def _safe_directory(path: Path, mode: int = 0o700) -> None:
    path.mkdir(mode=mode, parents=True, exist_ok=True)
    metadata = path.lstat()
    if path.is_symlink() or not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != 0 or metadata.st_gid != 0 or stat.S_IMODE(metadata.st_mode) != mode:
        raise GeneratorOrchestratorError(f"Directory orchestrator non canonica: {path}")


def _hash_descriptor(descriptor: int, size: int) -> str:
    digest = hashlib.sha256()
    offset = 0
    while offset < size:
        chunk = os.pread(descriptor, min(1024 * 1024, size - offset), offset)
        if not chunk:
            raise GeneratorOrchestratorError("File attestato troncato")
        digest.update(chunk)
        offset += len(chunk)
    if os.pread(descriptor, 1, size):
        raise GeneratorOrchestratorError("File attestato cresciuto")
    return digest.hexdigest()


def _inventory_directory(directory_fd: int, root_class: str, prefix: str = ".") -> list[tuple[Any, ...]]:
    metadata = os.fstat(directory_fd)
    if not stat.S_ISDIR(metadata.st_mode):
        raise GeneratorOrchestratorError("Root generated non directory")
    result: list[tuple[Any, ...]] = [
        (prefix, "d", stat.S_IMODE(metadata.st_mode), metadata.st_uid, metadata.st_gid, "")
    ]
    for name in sorted(os.listdir(directory_fd)):
        if not name or name in {".", ".."} or "/" in name or "\0" in name:
            raise GeneratorOrchestratorError("Nome generated non canonico")
        child = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        relative = name if prefix == "." else f"{prefix}/{name}"
        if child.st_dev != metadata.st_dev:
            raise GeneratorOrchestratorError(f"Mount nested/cross-device generated: {relative}")
        mode = stat.S_IMODE(child.st_mode)
        if stat.S_ISDIR(child.st_mode):
            descriptor = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory_fd)
            try:
                result.extend(_inventory_directory(descriptor, root_class, relative))
            finally:
                os.close(descriptor)
        elif stat.S_ISREG(child.st_mode):
            if child.st_nlink != 1:
                raise GeneratorOrchestratorError(f"Hardlink generated vietato: {relative}")
            descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory_fd)
            try:
                before = os.fstat(descriptor)
                digest = _hash_descriptor(descriptor, before.st_size)
                after = os.fstat(descriptor)
            finally:
                os.close(descriptor)
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise GeneratorOrchestratorError(f"File generated mutato durante hash: {relative}")
            result.append((relative, "f", mode, child.st_uid, child.st_gid, digest))
        elif stat.S_ISLNK(child.st_mode):
            result.append((relative, "l", mode, child.st_uid, child.st_gid, os.readlink(name, dir_fd=directory_fd)))
        else:
            raise GeneratorOrchestratorError(f"Tipo generated non supportato: {relative}")
    return result


def inventory_root(directory_fd: int, root_class: str) -> RootManifest:
    records = tuple(_inventory_directory(directory_fd, root_class))
    digest = hashlib.sha256(_canonical_json([root_class, records])).hexdigest()
    return RootManifest(root_class, records, digest)


def _expected_stock_records(root_class: str) -> tuple[tuple[Any, ...], ...]:
    root = ((".", "d", 0o755, 0, 0, ""),)
    if root_class != "normal":
        return root
    return root + (
        ("getty.target.wants", "d", 0o755, 0, 0, ""),
        ("getty.target.wants/console-getty.service", "l", 0o777, 0, 0, "/usr/lib/systemd/system/console-getty.service"),
        ("local-fs.target.wants", "d", 0o755, 0, 0, ""),
        ("local-fs.target.wants/systemd-remount-fs.service", "l", 0o777, 0, 0, "/usr/lib/systemd/system/systemd-remount-fs.service"),
    )


def _semantic_records(manifests: Mapping[str, RootManifest]) -> tuple[tuple[str, ...], ...]:
    units: dict[str, tuple[str, str, str]] = {}
    dependencies: list[tuple[str, str, str, str]] = []
    for root_class in LOOKUP_PRECEDENCE:
        manifest = manifests[root_class]
        for record in manifest.records:
            relative, kind, _mode, _uid, _gid, value = record
            if relative == ".":
                continue
            parts = str(relative).split("/")
            if len(parts) == 1 and (kind == "f" or kind == "l") and any(parts[0].endswith(suffix) for suffix in (".service", ".timer", ".socket", ".path", ".mount", ".automount", ".target")):
                units.setdefault(parts[0], (root_class, kind, str(value)))
            elif len(parts) == 2 and parts[0].endswith((".wants", ".requires", ".upholds")) and kind == "l":
                relation, _, edge = parts[0].rpartition(".")
                dependencies.append((relation, edge, parts[1], f"{root_class}:{value}"))
    records = [("unit", name, *identity) for name, identity in sorted(units.items())]
    records.extend(("dependency", *edge) for edge in sorted(dependencies))
    return tuple(records)


def effective_graph(manifests: Mapping[str, RootManifest]) -> EffectiveGraph:
    if set(manifests) != set(TARGETS):
        raise GeneratorOrchestratorError("Root class effective graph incompleta")
    records = _semantic_records(manifests)
    identity = hashlib.sha256(
        _canonical_json({"roots": {key: manifests[key].sha256 for key in sorted(manifests)}, "semantics": records})
    ).hexdigest()
    return EffectiveGraph(identity, records)


def validate_production_graph(manifests: Mapping[str, RootManifest]) -> EffectiveGraph:
    for root_class, manifest in manifests.items():
        allowed = {((".", "d", 0o755, 0, 0, ""),), _expected_stock_records(root_class)}
        if manifest.records not in allowed:
            raise GeneratorOrchestratorError(f"Manifest generated fuori policy: {root_class}")
    graph = effective_graph(manifests)
    allowed_semantics = {
        (),
        (
            ("dependency", "getty.target", "wants", "console-getty.service", "normal:/usr/lib/systemd/system/console-getty.service"),
            ("dependency", "local-fs.target", "wants", "systemd-remount-fs.service", "normal:/usr/lib/systemd/system/systemd-remount-fs.service"),
        ),
    }
    if graph.records not in allowed_semantics:
        raise GeneratorOrchestratorError("Semantica generated combinata fuori policy")
    return graph


def validate_reachable_prefixes(old: Mapping[str, RootManifest], new: Mapping[str, RootManifest], validator: Callable[[Mapping[str, RootManifest]], EffectiveGraph] = validate_production_graph) -> tuple[EffectiveGraph, ...]:
    current = dict(old)
    results = [validator(current)]
    for root_class in ADOPTION_ORDER:
        current[root_class] = new[root_class]
        results.append(validator(current))
    return tuple(results)


def _verify_ro_bundle(descriptors: Mapping[str, int]) -> Mapping[str, MountRecord]:
    rows = {key: _row_for_fd(descriptor) for key, descriptor in descriptors.items()}
    if any("ro" not in row.options or "ro" not in row.super_options for row in rows.values()):
        raise GeneratorOrchestratorError("Output PID1 non filesystem/VFS RO")
    return rows


def _current_ro_authority() -> tuple[dict[str, int], dict[str, RootManifest]]:
    descriptors: dict[str, int] = {}
    try:
        for root_class, target in TARGETS.items():
            descriptors[root_class] = os.open(target, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        _verify_ro_bundle(descriptors)
        manifests = {key: inventory_root(descriptor, key) for key, descriptor in descriptors.items()}
        validate_production_graph(manifests)
        return descriptors, manifests
    except Exception:
        for descriptor in descriptors.values():
            with contextlib.suppress(OSError):
                os.close(descriptor)
        raise


def _seal_stage(stage_fd: int, initial: MountRecord) -> tuple[MountRecord, tuple[MountRecord, ...]]:
    cwd = os.open(".", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fchdir(stage_fd)
        _mount(None, Path("."), None, MS_REMOUNT | MS_RDONLY | MS_NOSUID | MS_NODEV)
    finally:
        os.fchdir(cwd)
        os.close(cwd)
    sealed = _row_for_fd(stage_fd)
    if sealed.mount_id != initial.mount_id or sealed.major_minor != initial.major_minor or "ro" not in sealed.options or "ro" not in sealed.super_options:
        raise GeneratorOrchestratorError("Seal staging identity divergente")
    aliases = [record for record in _mount_records() if record.major_minor == sealed.major_minor and record.filesystem == sealed.filesystem]
    for alias in aliases:
        if "rw" in alias.options:
            _mount(None, alias.target, None, MS_REMOUNT | MS_BIND | MS_RDONLY | MS_NOSUID | MS_NODEV)
    aliases = [record for record in _mount_records() if record.major_minor == sealed.major_minor and record.filesystem == sealed.filesystem]
    if any("rw" in record.options or "rw" in record.super_options for record in aliases):
        raise GeneratorOrchestratorError("Alias staging RW dopo seal")
    return sealed, tuple(aliases)


def _write_audit(value: Mapping[str, Any]) -> None:
    temporary = STATE_PATH.with_name(f".{STATE_PATH.name}.{os.getpid()}")
    temporary.write_bytes(_canonical_json(value) + b"\n")
    temporary.chmod(0o600)
    os.replace(temporary, STATE_PATH)


def _helper_main(token: str, stage_fd: int, result_fd: int, seam_callback: Callable[[str], None] | None) -> int:
    def seam(name: str) -> None:
        if seam_callback is not None:
            seam_callback(name)

    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listener.bind(CONTROL_SOCKET)
        listener.listen(1)
        listener.settimeout(30)
        os.write(result_fd, b"READY\n")
        seam("before-staging")
        connection, _ = listener.accept()
        with connection:
            connection.settimeout(30)
            stage = TRANSACTION_ROOT / token / "stage"
            connection.sendall(
                (f"PREPARED\t{token}\t{stage / 'normal'}\t{stage / 'early'}\t{stage / 'late'}\n").encode("ascii")
            )
            seam("during-inner-generation")
            request = b""
            while not request.endswith(b"\n") and len(request) < 256:
                chunk = connection.recv(256 - len(request))
                if not chunk:
                    raise GeneratorOrchestratorError("Orchestrator disconnesso prima di GENERATED")
                request += chunk
            if request != f"GENERATED\t{token}\n".encode("ascii"):
                raise GeneratorOrchestratorError("Richiesta orchestrator non canonica")
            seam("after-generators-exit")
            initial = _row_for_fd(stage_fd)
            stage_stat = os.fstat(stage_fd)
            expected_stage = TRANSACTION_ROOT / token / "stage"
            if initial.target != expected_stage or initial.filesystem != "tmpfs" or initial.source != f"thebitlab-generator-stage:{token}" or "rw" not in initial.options:
                raise GeneratorOrchestratorError("Staging mount witness divergente")
            seam("before-seal")
            seam("during-seal")
            sealed, aliases = _seal_stage(stage_fd, initial)
            seam("after-seal")
            new_fds = {
                key: os.open(key, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=stage_fd)
                for key in TARGETS
            }
            old_fds: dict[str, int] = {}
            clones: dict[str, int] = {}
            target_fds: dict[str, int] = {}
            try:
                seam("during-attestation")
                new_manifests = {key: inventory_root(descriptor, key) for key, descriptor in new_fds.items()}
                validate_production_graph(new_manifests)
                old_fds, old_manifests = _current_ro_authority()
                prefix_graphs = validate_reachable_prefixes(old_manifests, new_manifests)
                seam("after-attestation")
                clones = {key: _open_tree(stage_fd, key) for key in TARGETS}
                target_fds = {
                    key: os.open(target, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
                    for key, target in TARGETS.items()
                }
                seam("before-first-adoption")
                adopted: list[str] = []
                for root_class in ADOPTION_ORDER:
                    _move_mount(clones[root_class], target_fds[root_class])
                    adopted.append(root_class)
                    seam(f"after-{len(adopted)}-adoption")
                final_descriptors = {
                    key: os.open(target, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
                    for key, target in TARGETS.items()
                }
                try:
                    rows = _verify_ro_bundle(final_descriptors)
                    final_manifests = {key: inventory_root(descriptor, key) for key, descriptor in final_descriptors.items()}
                    final_graph = validate_production_graph(final_manifests)
                    if any(final_manifests[key].sha256 != new_manifests[key].sha256 for key in TARGETS):
                        raise GeneratorOrchestratorError("Verify-use manifest dopo adoption divergente")
                finally:
                    for descriptor in final_descriptors.values():
                        os.close(descriptor)
                inventory_identity = hashlib.sha256(_canonical_json(SELECTED_GENERATORS)).hexdigest()
                evidence = {
                    "schema": "thebitlab.generator-bundle.v1",
                    "token": token,
                    "selected_generator_inventory": inventory_identity,
                    "source_policy_identity": SOURCE_POLICY_ID,
                    "orchestrator_source_sha256": ORCHESTRATOR_SOURCE_SHA256,
                    "orchestrator_artifact_sha256": ORCHESTRATOR_REVIEWED_SHA256,
                    "package_baseline_identity": PACKAGE_BASELINE_SHA256,
                    "root_manifests": {key: new_manifests[key].sha256 for key in sorted(TARGETS)},
                    "effective_graph_identity": final_graph.identity,
                    "reachable_prefix_graphs": [graph.identity for graph in prefix_graphs],
                    "seal": {
                        "mount_id": sealed.mount_id,
                        "device": sealed.major_minor,
                        "inode_device": stage_stat.st_dev,
                        "inode": stage_stat.st_ino,
                        "aliases": [(record.mount_id, str(record.target), sorted(record.options), sorted(record.super_options)) for record in aliases],
                    },
                    "adoption_order": list(ADOPTION_ORDER),
                    "adopted_mounts": {key: {"mount_id": rows[key].mount_id, "device": rows[key].major_minor, "root": rows[key].root} for key in sorted(rows)},
                }
                bundle_id = hashlib.sha256(_canonical_json(evidence)).hexdigest()
                evidence["bundle_id"] = bundle_id
                _write_audit(evidence)
                connection.sendall(f"PASS\t{bundle_id}\n".encode("ascii"))
                os.write(result_fd, b"PASS\t" + bundle_id.encode("ascii") + b"\n")
                seam("after-third-adoption-before-exit")
                return 0
            finally:
                for group in (target_fds, clones, old_fds, new_fds):
                    for descriptor in group.values():
                        with contextlib.suppress(OSError):
                            os.close(descriptor)
    except BaseException as exc:
        message = f"ERROR\t{type(exc).__name__}:{exc}\n".encode("utf-8", "replace")[:2048]
        with contextlib.suppress(OSError):
            os.write(result_fd, message)
        return 2
    finally:
        listener.close()


def _purge_detached_staging(directory_fd: int) -> None:
    """Remove untrusted transaction contents FD-relative after mount detachment."""

    root_device = os.fstat(directory_fd).st_dev
    for name in sorted(os.listdir(directory_fd)):
        metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if metadata.st_dev != root_device:
            raise GeneratorOrchestratorError(f"Cleanup staging cross-device: {name}")
        if stat.S_ISDIR(metadata.st_mode):
            child = os.open(
                name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=directory_fd,
            )
            try:
                _purge_detached_staging(child)
            finally:
                os.close(child)
            os.rmdir(name, dir_fd=directory_fd)
        else:
            os.unlink(name, dir_fd=directory_fd)


def recover_stale_transactions() -> None:
    """Detach only canonical stale staging anchors; adopted clones stay valid."""

    _safe_directory(RUNTIME_ROOT)
    _safe_directory(TRANSACTION_ROOT)
    for transaction in tuple(TRANSACTION_ROOT.iterdir()):
        if transaction.is_symlink() or not transaction.is_dir() or TOKEN_RE.fullmatch(transaction.name) is None:
            raise GeneratorOrchestratorError(f"Transaction staging estranea: {transaction}")
        children = {child.name: child for child in transaction.iterdir()}
        if set(children) - {"stage", "safe"}:
            raise GeneratorOrchestratorError(f"Topology stale transaction estranea: {transaction}")
        for leaf in ("stage", "safe"):
            root = children.get(leaf)
            if root is None:
                continue
            if root.is_symlink() or not root.is_dir():
                raise GeneratorOrchestratorError(f"Root stale transaction non canonica: {root}")
            rows = [record for record in _mount_records() if record.target == root]
            while rows:
                if any(
                    record.filesystem != "tmpfs"
                    or record.source not in {
                        f"thebitlab-generator-stage:{transaction.name}",
                        f"thebitlab-generator-safe:{transaction.name}",
                    }
                    for record in rows
                ):
                    raise GeneratorOrchestratorError(f"Mount stale transaction estraneo: {root}")
                _umount(root)
                rows = [record for record in _mount_records() if record.target == root]
            nested_mounts = [
                record for record in _mount_records()
                if root in record.target.parents
            ]
            if nested_mounts:
                raise GeneratorOrchestratorError(f"Mount nested stale transaction: {nested_mounts[0].target}")
            descriptor = os.open(
                root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
            )
            try:
                _purge_detached_staging(descriptor)
            finally:
                os.close(descriptor)
            root.rmdir()
        transaction.rmdir()


def _prepare_stage(token: str) -> tuple[Path, int]:
    _safe_directory(RUNTIME_ROOT)
    _safe_directory(TRANSACTION_ROOT)
    transaction = TRANSACTION_ROOT / token
    transaction.mkdir(mode=0o700)
    stage = transaction / "stage"
    stage.mkdir(mode=0o755)
    _mount(f"thebitlab-generator-stage:{token}", stage, "tmpfs", MS_NOSUID | MS_NODEV, "mode=0755,size=64m")
    for root_class in TARGETS:
        (stage / root_class).mkdir(mode=0o755)
    descriptor = os.open(stage, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    return transaction, descriptor


def provision_safe_output() -> str:
    """Provision canonical SAFE-EMPTY roots before the hostile operating phase.

    This is a provisioning operation, not an activation fallback. Production
    activation refuses to generate unless all three current roots are already
    a closed filesystem-RO authority.
    """
    _safe_directory(RUNTIME_ROOT)
    _safe_directory(TRANSACTION_ROOT)
    token = f"{os.getpid()}-{uuid.uuid4().hex}"
    transaction = TRANSACTION_ROOT / token
    transaction.mkdir(mode=0o700)
    safe = transaction / "safe"
    safe.mkdir(mode=0o755)
    _mount(f"thebitlab-generator-safe:{token}", safe, "tmpfs", MS_NOSUID | MS_NODEV, "mode=0755,size=4m")
    for root_class, target in TARGETS.items():
        target.mkdir(mode=0o755, parents=True, exist_ok=True)
        (safe / root_class).mkdir(mode=0o755)
    safe_fd = os.open(safe, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        initial = _row_for_fd(safe_fd)
        _seal_stage(safe_fd, initial)
        clones = {key: _open_tree(safe_fd, key) for key in TARGETS}
        target_fds = {key: os.open(path, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC) for key, path in TARGETS.items()}
        try:
            for root_class in ADOPTION_ORDER:
                _move_mount(clones[root_class], target_fds[root_class])
        finally:
            for descriptor in (*clones.values(), *target_fds.values()):
                os.close(descriptor)
        descriptors, manifests = _current_ro_authority()
        try:
            graph = validate_production_graph(manifests)
        finally:
            for descriptor in descriptors.values():
                os.close(descriptor)
        evidence = {
            "schema": "thebitlab.generator-bundle.v1", "bundle_id": "",
            "token": token, "safe_empty": True,
            "root_manifests": {key: manifests[key].sha256 for key in sorted(manifests)},
            "effective_graph_identity": graph.identity,
            "adoption_order": list(ADOPTION_ORDER),
        }
        evidence["bundle_id"] = hashlib.sha256(_canonical_json({**evidence, "bundle_id": None})).hexdigest()
        _write_audit(evidence)
        return str(evidence["bundle_id"])
    finally:
        os.close(safe_fd)
        with contextlib.suppress(OSError):
            _umount(safe)
        for root_class in TARGETS:
            with contextlib.suppress(FileNotFoundError):
                (safe / root_class).rmdir()
        with contextlib.suppress(OSError):
            safe.rmdir()
            transaction.rmdir()


def orchestrated_reload(reload_call: Callable[[], tuple[int, str]], seam_callback: Callable[[str], None] | None = None) -> Mapping[str, Any]:
    """Run one trusted reload while old validated output stays authoritative."""
    recover_stale_transactions()
    old_descriptors, _old_manifests = _current_ro_authority()
    for descriptor in old_descriptors.values():
        os.close(descriptor)
    token = f"{os.getpid()}-{uuid.uuid4().hex}"
    if not TOKEN_RE.fullmatch(token):
        raise GeneratorOrchestratorError("Token transaction non canonico")
    transaction, stage_fd = _prepare_stage(token)
    read_fd, write_fd = os.pipe2(os.O_CLOEXEC)
    helper_pid = os.fork()
    if helper_pid == 0:
        os.close(read_fd)
        result = _helper_main(token, stage_fd, write_fd, seam_callback)
        os._exit(result)
    os.close(write_fd)
    try:
        ready = os.read(read_fd, 64)
        if ready != b"READY\n":
            raise GeneratorOrchestratorError(f"Helper non ready: {ready!r}")
        code, detail = reload_call()
        result = b""
        deadline = time.monotonic() + 35
        while not result.endswith(b"\n") and time.monotonic() < deadline:
            chunk = os.read(read_fd, 2048)
            if not chunk:
                break
            result += chunk
        _pid, status = os.waitpid(helper_pid, 0)
        helper_code = os.waitstatus_to_exitcode(status)
        if code != 0 or helper_code != 0 or not result.startswith(b"PASS\t"):
            raise GeneratorOrchestratorError(
                f"Reload orchestrato fallito manager={code} helper={helper_code} result={result!r} detail={detail[-300:]}"
            )
        bundle_id = result.decode("ascii").strip().split("\t", 1)[1]
        if SHA256_RE.fullmatch(bundle_id) is None:
            raise GeneratorOrchestratorError("Bundle ID helper non canonico")
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    finally:
        os.close(read_fd)
        os.close(stage_fd)
        with contextlib.suppress(ProcessLookupError, ChildProcessError):
            os.kill(helper_pid, signal.SIGKILL)
            os.waitpid(helper_pid, 0)
        # The sealed staging anchor is no longer an authority path after detached
        # clones have been adopted. Cleanup failure is availability-only and the
        # exact transaction is retained for recovery/audit rather than broadened.
        stage = transaction / "stage"
        with contextlib.suppress(OSError):
            _umount(stage)
        for root_class in TARGETS:
            with contextlib.suppress(FileNotFoundError):
                (stage / root_class).rmdir()
        with contextlib.suppress(OSError):
            stage.rmdir()
            transaction.rmdir()
