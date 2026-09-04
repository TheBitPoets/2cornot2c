#!/usr/bin/env python3
"""Pure-Python native code-loading closure attestation for the pilot activator.

This module deliberately performs no subprocess execution.  The already-running
trusted Python interpreter parses ELF program headers, freezes resolution against
repository-reviewed identities, and hashes the frozen files before the first new
native exec in a protected boundary.
"""

from __future__ import annotations

import hashlib
import os
import stat
import struct
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from scripts.pilot_ubuntu_loader_lookup_policy import (
    DEFAULT_LOADER_LOOKUP_DIRECTORIES,
    GLIBC_HWCAPS_LEVELS,
    GLIBC_LEGACY_HWCAPS_APPLICABLE,
    LD_SO_CACHE_REVIEWED_ENTRY_COUNT,
    LD_SO_CACHE_REVIEWED_HWCAP_ENTRIES,
    REVIEWED_BOOTSTRAP_LOOKUP_TREES,
    ReviewedTreeIdentity,
)
from scripts.pilot_ubuntu_reviewed_native_code import (
    DYNAMIC_LOADER_CONFIG_REVIEWED_SHA256,
    LD_SO_CACHE_REVIEWED_SHA256,
    NATIVE_CODE_DEPENDENCIES,
    NATIVE_CODE_PLUGIN_IDENTITIES,
    NATIVE_CODE_REVIEWED_SHA256,
    NATIVE_CODE_SEARCH_PATHS,
    NATIVE_EXECUTABLE_INTERPRETERS,
    PT_INTERP_REVIEWED_IDENTITIES,
)


class NativeExecutionClosureError(RuntimeError):
    """The frozen native runtime does not match the reviewed Noble closure."""


PT_LOAD = 1
PT_DYNAMIC = 2
PT_INTERP = 3
DT_NULL = 0
DT_NEEDED = 1
DT_STRTAB = 5
DT_STRSZ = 10
DT_SONAME = 14
DT_RPATH = 15
DT_RUNPATH = 29
ELF_MACHINE_X86_64 = 62
LD_SO_CACHE = Path("/etc/ld.so.cache")
LD_SO_PRELOAD = Path("/etc/ld.so.preload")
_LOADER_ENVIRONMENT_NAMES = frozenset({"GLIBC_TUNABLES"})
_LD_SO_CACHE_HEADER_SIZE = 48
_LD_SO_CACHE_ENTRY_SIZE = 24


@dataclass(frozen=True)
class ElfIdentity:
    interpreter: str | None
    needed: tuple[str, ...]
    soname: str | None
    rpath: str | None
    runpath: str | None


def _stable_bytes(path: Path) -> bytes:
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    except OSError as exc:
        raise NativeExecutionClosureError(f"Native identity non apribile: {path}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise NativeExecutionClosureError(f"Native identity non regolare: {path}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise NativeExecutionClosureError(f"Native identity mutata in lettura: {path}")
        if before.st_uid != 0 or before.st_mode & 0o022:
            raise NativeExecutionClosureError(f"Native identity con metadata unsafe: {path}")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _digest(path: Path) -> str:
    return hashlib.sha256(_stable_bytes(path)).hexdigest()


def _slice(data: bytes, offset: int, size: int, *, label: str) -> bytes:
    if offset < 0 or size < 0 or offset + size > len(data):
        raise NativeExecutionClosureError(f"ELF {label} fuori limite")
    return data[offset : offset + size]


def _cstring(table: bytes, offset: int, *, label: str) -> str:
    if offset < 0 or offset >= len(table):
        raise NativeExecutionClosureError(f"ELF stringa {label} fuori limite")
    end = table.find(b"\0", offset)
    if end < 0:
        raise NativeExecutionClosureError(f"ELF stringa {label} non terminata")
    try:
        value = table[offset:end].decode("ascii")
    except UnicodeDecodeError as exc:
        raise NativeExecutionClosureError(f"ELF stringa {label} non ASCII") from exc
    if not value or "\n" in value or "\r" in value:
        raise NativeExecutionClosureError(f"ELF stringa {label} non canonica")
    return value


def parse_elf_bytes(data: bytes) -> ElfIdentity:
    """Parse the bounded ELF64 little-endian fields used by the loader policy."""

    if len(data) < 64 or data[:4] != b"\x7fELF":
        raise NativeExecutionClosureError("Identity non ELF")
    if data[4] != 2 or data[5] != 1 or data[6] != 1:
        raise NativeExecutionClosureError("Classe/endianness/versione ELF non supportata")
    header = struct.unpack_from("<16sHHIQQQIHHHHHH", data, 0)
    machine = header[2]
    program_offset = header[5]
    program_entry_size = header[9]
    program_count = header[10]
    if machine != ELF_MACHINE_X86_64 or program_entry_size != 56 or program_count > 256:
        raise NativeExecutionClosureError("Machine/program header ELF fuori baseline")
    if program_offset + program_entry_size * program_count > len(data):
        raise NativeExecutionClosureError("Program header ELF troncati")

    loads: list[tuple[int, int, int]] = []
    dynamic: tuple[int, int] | None = None
    interpreter: str | None = None
    for index in range(program_count):
        fields = struct.unpack_from("<IIQQQQQQ", data, program_offset + index * 56)
        kind, file_offset, virtual_address, file_size = fields[0], fields[2], fields[3], fields[5]
        if file_offset + file_size > len(data):
            raise NativeExecutionClosureError("Segmento ELF troncato")
        if kind == PT_LOAD:
            loads.append((virtual_address, file_offset, file_size))
        elif kind == PT_DYNAMIC:
            if dynamic is not None:
                raise NativeExecutionClosureError("ELF con PT_DYNAMIC multiplo")
            dynamic = (file_offset, file_size)
        elif kind == PT_INTERP:
            raw = _slice(data, file_offset, file_size, label="PT_INTERP")
            if not raw.endswith(b"\0") or raw.count(b"\0") != 1:
                raise NativeExecutionClosureError("PT_INTERP non canonico")
            try:
                interpreter = raw[:-1].decode("ascii")
            except UnicodeDecodeError as exc:
                raise NativeExecutionClosureError("PT_INTERP non ASCII") from exc
            if not interpreter.startswith("/"):
                raise NativeExecutionClosureError("PT_INTERP non assoluto")

    if dynamic is None:
        return ElfIdentity(interpreter, (), None, None, None)
    dynamic_bytes = _slice(data, *dynamic, label="PT_DYNAMIC")
    if len(dynamic_bytes) % 16:
        raise NativeExecutionClosureError("PT_DYNAMIC non allineato")
    tags: list[tuple[int, int]] = []
    for offset in range(0, len(dynamic_bytes), 16):
        tag, value = struct.unpack_from("<qQ", dynamic_bytes, offset)
        if tag == DT_NULL:
            break
        tags.append((tag, value))
    else:
        raise NativeExecutionClosureError("PT_DYNAMIC senza terminatore")
    string_address = next((value for tag, value in tags if tag == DT_STRTAB), None)
    string_size = next((value for tag, value in tags if tag == DT_STRSZ), None)
    string_table = b""
    if string_address is not None or string_size is not None:
        if string_address is None or string_size is None or string_size > len(data):
            raise NativeExecutionClosureError("Dynamic string table incompleta")
        string_offset = None
        for virtual_address, file_offset, file_size in loads:
            if virtual_address <= string_address < virtual_address + file_size:
                candidate = file_offset + string_address - virtual_address
                if candidate + string_size <= file_offset + file_size:
                    string_offset = candidate
                    break
        if string_offset is None:
            raise NativeExecutionClosureError("Dynamic string table non mappabile")
        string_table = _slice(data, string_offset, string_size, label="DT_STRTAB")

    values: dict[int, list[str]] = {}
    for tag, value in tags:
        if tag in {DT_NEEDED, DT_SONAME, DT_RPATH, DT_RUNPATH}:
            values.setdefault(tag, []).append(_cstring(string_table, value, label=str(tag)))
    for singleton in (DT_SONAME, DT_RPATH, DT_RUNPATH):
        if len(values.get(singleton, ())) > 1:
            raise NativeExecutionClosureError(f"Dynamic tag ELF multiplo: {singleton}")
    if DT_RPATH in values and DT_RUNPATH in values:
        raise NativeExecutionClosureError("ELF con RPATH e RUNPATH simultanei")
    return ElfIdentity(
        interpreter,
        tuple(values.get(DT_NEEDED, ())),
        next(iter(values.get(DT_SONAME, ())), None),
        next(iter(values.get(DT_RPATH, ())), None),
        next(iter(values.get(DT_RUNPATH, ())), None),
    )


def parse_elf(path: Path) -> ElfIdentity:
    return parse_elf_bytes(_stable_bytes(path))


def _parse_ld_so_cache(data: bytes) -> tuple[tuple[str, str, int], ...]:
    """Parse bounded glibc cache 1.1 entries, including the hwcap selector."""

    if len(data) < _LD_SO_CACHE_HEADER_SIZE or data[:20] != b"glibc-ld.so.cache1.1":
        raise NativeExecutionClosureError("Formato ld.so.cache fuori baseline")
    entry_count, strings_size = struct.unpack_from("<II", data, 20)
    if entry_count > 10000 or strings_size > len(data):
        raise NativeExecutionClosureError("Dimensioni ld.so.cache fuori limite")
    entries_end = _LD_SO_CACHE_HEADER_SIZE + entry_count * _LD_SO_CACHE_ENTRY_SIZE
    strings_end = entries_end + strings_size
    if entries_end > len(data) or strings_end > len(data):
        raise NativeExecutionClosureError("ld.so.cache troncata")

    def cache_string(offset: int) -> str:
        if offset < entries_end or offset >= strings_end:
            raise NativeExecutionClosureError("Offset stringa ld.so.cache fuori limite")
        end = data.find(b"\0", offset, strings_end)
        if end < 0:
            raise NativeExecutionClosureError("Stringa ld.so.cache non terminata")
        try:
            value = data[offset:end].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise NativeExecutionClosureError("Stringa ld.so.cache non UTF-8") from exc
        if not value or "\n" in value or "\r" in value:
            raise NativeExecutionClosureError("Stringa ld.so.cache non canonica")
        return value

    result: list[tuple[str, str, int]] = []
    for index in range(entry_count):
        flags, key, value, _os_version, hwcap = struct.unpack_from(
            "<iIIIQ", data, _LD_SO_CACHE_HEADER_SIZE + index * _LD_SO_CACHE_ENTRY_SIZE
        )
        if flags < 0:
            raise NativeExecutionClosureError("Flag ld.so.cache non canonico")
        result.append((cache_string(key), cache_string(value), hwcap))
    return tuple(result)


def _expanded_search_directories(lexical: str) -> tuple[Path, ...]:
    rpath, runpath = NATIVE_CODE_SEARCH_PATHS[lexical]
    configured = runpath if runpath is not None else rpath
    result: list[Path] = []
    for raw in configured.split(":") if configured else ():
        expanded = raw.replace("$ORIGIN", str(PurePosixPath(lexical).parent))
        if "$" in expanded or not expanded.startswith("/"):
            raise NativeExecutionClosureError(
                f"Token loader non modellato nella policy: {lexical} {raw!r}"
            )
        result.append(Path(expanded))
    result.extend(DEFAULT_LOADER_LOOKUP_DIRECTORIES)
    return tuple(dict.fromkeys(result))


def expected_absent_hwcaps_candidates() -> frozenset[Path]:
    """Return the CPU-portable v2/v3/v4 candidate set for every lookup."""

    candidates: set[Path] = set()
    for lexical, dependencies in NATIVE_CODE_DEPENDENCIES.items():
        directories = _expanded_search_directories(lexical)
        for soname, _resolved in dependencies:
            if "/" in soname:
                raise NativeExecutionClosureError(
                    f"DT_NEEDED con slash fuori lookup policy: {lexical} {soname}"
                )
            for directory in directories:
                for level in GLIBC_HWCAPS_LEVELS:
                    candidates.add(directory / "glibc-hwcaps" / level / soname)
    return frozenset(candidates)


def _attest_loader_lookup_policy(
    *,
    cache_bytes: bytes,
    frozen_tree_identities: Mapping[Path, ReviewedTreeIdentity] | None,
) -> None:
    if GLIBC_LEGACY_HWCAPS_APPLICABLE:
        raise NativeExecutionClosureError("Legacy hwcaps applicabile ma non modellata")
    inherited = sorted(
        name for name in os.environ
        if name.startswith("LD_") or name in _LOADER_ENVIRONMENT_NAMES
    )
    if inherited:
        raise NativeExecutionClosureError(
            "Environment loader non ammesso: " + ",".join(inherited)
        )
    if frozen_tree_identities is None:
        raise NativeExecutionClosureError("Lookup tree identities frozen assenti")
    for path, expected in REVIEWED_BOOTSTRAP_LOOKUP_TREES.items():
        actual = frozen_tree_identities.get(path)
        if actual != expected:
            raise NativeExecutionClosureError(
                f"Loader lookup tree divergente: {path} actual={actual!r} expected={expected!r}"
            )
    cache_entries = _parse_ld_so_cache(cache_bytes)
    if len(cache_entries) != LD_SO_CACHE_REVIEWED_ENTRY_COUNT:
        raise NativeExecutionClosureError("Numero entry ld.so.cache divergente")
    hwcap_entries = tuple(entry for entry in cache_entries if entry[2] != 0)
    if hwcap_entries != LD_SO_CACHE_REVIEWED_HWCAP_ENTRIES:
        raise NativeExecutionClosureError("Entry hwcaps ld.so.cache fuori policy")
    for candidate in expected_absent_hwcaps_candidates():
        try:
            candidate.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise NativeExecutionClosureError(
                f"Candidate hwcaps non verificabile: {candidate}"
            ) from exc
        raise NativeExecutionClosureError(
            f"Candidate hwcaps EXPECTED_ABSENT presente: {candidate}"
        )


def _attest_digest(path: Path, frozen_digests: Mapping[Path, str] | None = None) -> None:
    expected = NATIVE_CODE_REVIEWED_SHA256.get(path.as_posix())
    if expected is None:
        raise NativeExecutionClosureError(f"Native code identity non revisionata: {path}")
    actual = frozen_digests.get(path) if frozen_digests is not None else _digest(path)
    if actual is None:
        raise NativeExecutionClosureError(f"Native code assente dal manifest frozen: {path}")
    if actual != expected:
        raise NativeExecutionClosureError(
            f"Native code digest divergente: {path} actual={actual} expected={expected}"
        )


def attest_native_execution_closure(
    executables: Iterable[Path],
    *,
    frozen_digests: Mapping[Path, str] | None = None,
    frozen_tree_identities: Mapping[Path, ReviewedTreeIdentity] | None = None,
) -> frozenset[Path]:
    """Attest the closed loader graph without executing a new native process."""

    try:
        LD_SO_PRELOAD.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise NativeExecutionClosureError("Stato ld.so.preload non verificabile") from exc
    else:
        raise NativeExecutionClosureError("/etc/ld.so.preload deve essere assente")
    cache_bytes = _stable_bytes(LD_SO_CACHE)
    if hashlib.sha256(cache_bytes).hexdigest() != LD_SO_CACHE_REVIEWED_SHA256:
        raise NativeExecutionClosureError("ld.so.cache fuori baseline revisionata")
    _attest_loader_lookup_policy(
        cache_bytes=cache_bytes,
        frozen_tree_identities=frozen_tree_identities,
    )
    for lexical, expected in DYNAMIC_LOADER_CONFIG_REVIEWED_SHA256.items():
        if _digest(Path(lexical)) != expected:
            raise NativeExecutionClosureError(
                f"Configurazione loader/plugin fuori baseline: {lexical}"
            )

    pending = [Path(path) for path in executables]
    reviewed: set[Path] = set()
    while pending:
        path = pending.pop()
        lexical = path.as_posix()
        if path in reviewed:
            continue
        _attest_digest(path, frozen_digests)
        expected_interpreter = NATIVE_EXECUTABLE_INTERPRETERS.get(lexical)
        expected_dependencies = NATIVE_CODE_DEPENDENCIES.get(lexical)
        if expected_dependencies is None or lexical not in NATIVE_CODE_SEARCH_PATHS:
            raise NativeExecutionClosureError(f"ELF closure policy assente: {path}")
        if frozen_digests is None:
            identity = parse_elf(path)
            if identity.interpreter != expected_interpreter:
                raise NativeExecutionClosureError(
                    f"PT_INTERP divergente: {path} actual={identity.interpreter!r} "
                    f"expected={expected_interpreter!r}"
                )
            if tuple(name for name, _resolved in expected_dependencies) != identity.needed:
                raise NativeExecutionClosureError(f"DT_NEEDED divergente: {path}")
            if NATIVE_CODE_SEARCH_PATHS[lexical] != (identity.rpath, identity.runpath):
                raise NativeExecutionClosureError(f"RPATH/RUNPATH divergente: {path}")
        reviewed.add(path)
        if expected_interpreter is not None:
            interpreter_identity = PT_INTERP_REVIEWED_IDENTITIES.get(expected_interpreter)
            if interpreter_identity is None:
                raise NativeExecutionClosureError(
                    f"PT_INTERP senza identity revisionata: {expected_interpreter}"
                )
            pending.append(Path(interpreter_identity))
        for _name, resolved in expected_dependencies:
            dependency = Path(resolved)
            if dependency not in reviewed:
                pending.append(dependency)

    for lexical in NATIVE_CODE_PLUGIN_IDENTITIES:
        plugin = Path(lexical)
        _attest_digest(plugin, frozen_digests)
        expected_dependencies = NATIVE_CODE_DEPENDENCIES.get(lexical)
        if expected_dependencies is None or lexical not in NATIVE_CODE_SEARCH_PATHS:
            raise NativeExecutionClosureError(f"Plugin policy assente: {plugin}")
        if frozen_digests is None:
            identity = parse_elf(plugin)
            if tuple(name for name, _resolved in expected_dependencies) != identity.needed:
                raise NativeExecutionClosureError(f"Plugin DT_NEEDED divergente: {plugin}")
            if NATIVE_CODE_SEARCH_PATHS[lexical] != (identity.rpath, identity.runpath):
                raise NativeExecutionClosureError(f"Plugin RPATH/RUNPATH divergente: {plugin}")
        reviewed.add(plugin)
        pending.extend(Path(resolved) for _name, resolved in expected_dependencies)
    while pending:
        path = pending.pop()
        if path in reviewed:
            continue
        _attest_digest(path, frozen_digests)
        lexical = path.as_posix()
        expected_dependencies = NATIVE_CODE_DEPENDENCIES.get(lexical)
        if expected_dependencies is None or lexical not in NATIVE_CODE_SEARCH_PATHS:
            raise NativeExecutionClosureError(f"Plugin closure policy assente: {path}")
        if frozen_digests is None:
            identity = parse_elf(path)
            if tuple(name for name, _resolved in expected_dependencies) != identity.needed:
                raise NativeExecutionClosureError(f"Plugin closure divergente: {path}")
            if NATIVE_CODE_SEARCH_PATHS[lexical] != (identity.rpath, identity.runpath):
                raise NativeExecutionClosureError(
                    f"Plugin closure search path divergente: {path}"
                )
        reviewed.add(path)
        pending.extend(Path(resolved) for _name, resolved in expected_dependencies)
    return frozenset(reviewed)


def detailed_closure_counts() -> Mapping[str, int]:
    from scripts.pilot_ubuntu_reviewed_executables import (
        REVIEWED_PACKAGE_EXECUTABLE_IDENTITIES,
    )

    execution_classes = [
        execution_class
        for _digest_value, execution_class in REVIEWED_PACKAGE_EXECUTABLE_IDENTITIES.values()
    ]
    plugins = tuple(NATIVE_CODE_PLUGIN_IDENTITIES)
    return {
        "static_direct_executable_roots": execution_classes.count("NATIVE_PACKAGE_BINARY"),
        "interpreted_package_roots": execution_classes.count("INTERPRETED_SCRIPT"),
        "bootstrap_static_executable_identities": 1,
        "bootstrap_dynamic_child_roots": 1,
        "pt_interp_identities": len(set(PT_INTERP_REVIEWED_IDENTITIES)),
        "ordinary_shared_library_identities": closure_counts()["shared_library_identities"],
        "hwcaps_reviewed_present_candidates": 0,
        "hwcaps_expected_absent_candidates": len(expected_absent_hwcaps_candidates()),
        "nss_identities": sum("/libnss_" in path for path in plugins),
        "gconv_identities": sum("/gconv/" in path for path in plugins),
        "openssl_provider_engine_identities": sum(
            "/engines-3/" in path or "/ossl-modules/" in path for path in plugins
        ),
        "nginx_module_identities": sum("/nginx/modules/" in path for path in plugins),
        "other_plugin_identities": 0,
        "unpinned_execution_selectable_candidates": 0,
    }


def closure_counts() -> Mapping[str, int]:
    from scripts.pilot_ubuntu_reviewed_executables import (  # avoid policy import cycle
        REVIEWED_PACKAGE_EXECUTABLE_IDENTITIES,
    )

    roots = {
        path.as_posix()
        for path, (_digest_value, execution_class) in
        REVIEWED_PACKAGE_EXECUTABLE_IDENTITIES.items()
        if execution_class == "NATIVE_PACKAGE_BINARY"
    }
    interpreters = {value for value in NATIVE_EXECUTABLE_INTERPRETERS.values() if value}
    libraries = set(NATIVE_CODE_REVIEWED_SHA256) - roots
    return {
        "native_elf_executables": len(roots),
        "pt_interp_identities": len(interpreters),
        "shared_library_identities": len(libraries - set(NATIVE_CODE_PLUGIN_IDENTITIES)),
        "plugin_provider_identities": len(NATIVE_CODE_PLUGIN_IDENTITIES),
        "hwcaps_reviewed_present_candidates": 0,
        "hwcaps_expected_absent_candidates": len(expected_absent_hwcaps_candidates()),
        "unpinned_execution_selectable_candidates": 0,
    }
