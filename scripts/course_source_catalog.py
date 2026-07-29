from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from typing import Any, Iterable


MAX_SOURCES = 64
MAX_FILES_PER_SOURCE = 64
MAX_TEXT = 512
MAX_LOCAL_MARKDOWN_BYTES = 8 * 1024 * 1024
MAX_INDEXED_LOCAL_FILES = 256
MAX_TOTAL_LOCAL_MARKDOWN_BYTES = 64 * 1024 * 1024
SOURCE_ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,63})$")
GITHUB_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
GITLAB_REPOSITORY_RE = re.compile(
    r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+$"
)
GIT_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/@-]{0,127}$")
ALLOWED_PROVIDERS = frozenset({"local", "github", "gitlab"})
ALLOWED_TYPES = frozenset({"markdown"})
ALLOWED_INDEXING_STATUSES = frozenset({"ready", "pending", "error", "disabled"})


class CourseSourceCatalogError(ValueError):
    """Raised when a course-source catalog is malformed or ambiguous."""


@dataclass(frozen=True)
class CourseSource:
    """Provider-independent descriptor for one didactic content source."""

    source_id: str
    label: str
    source_type: str
    provider: str
    path: str
    repository: str | None
    ref: str | None
    files: tuple[str, ...]
    updated_at: str | None
    indexing_status: str
    legacy: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.source_id,
            "label": self.label,
            "type": self.source_type,
            "provider": self.provider,
            "path": self.path,
            "repository": self.repository,
            "ref": self.ref,
            "files": list(self.files),
            "updated_at": self.updated_at,
            "indexing_status": self.indexing_status,
            "legacy": self.legacy,
        }


@dataclass(frozen=True)
class LocalCourseSourceFile:
    """One repository-confined local Markdown file selected for indexing."""

    source: CourseSource
    relative_path: str
    resolved_path: Path
    expected_size: int | None
    expected_identity: tuple[int, int] | None
    expected_mtime_ns: int | None
    expected_ctime_ns: int | None


def normalize_course_sources(
    design: dict[str, Any],
    *,
    default_files: Iterable[str] = (),
) -> tuple[CourseSource, ...]:
    """Return explicit sources or a read-only legacy `source_files` projection."""

    if not isinstance(design, dict):
        raise CourseSourceCatalogError("Il progetto didattico deve essere un oggetto JSON.")
    if "sources" not in design:
        legacy_files = design.get("source_files") or list(default_files)
        return _legacy_sources(legacy_files)

    raw_sources = design["sources"]
    if not isinstance(raw_sources, list):
        raise CourseSourceCatalogError("sources deve essere un array.")
    if len(raw_sources) > MAX_SOURCES:
        raise CourseSourceCatalogError("Troppe fonti didattiche.")

    sources: list[CourseSource] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(raw_sources):
        source = _normalize_source(raw, index)
        if source.source_id in seen_ids:
            raise CourseSourceCatalogError(
                f"ID fonte duplicato: {source.source_id}."
            )
        seen_ids.add(source.source_id)
        sources.append(source)
    return tuple(sources)


def local_markdown_source_files(
    design: dict[str, Any],
    root: Path,
    *,
    default_files: Iterable[str] = (),
    existing_only: bool = True,
) -> tuple[LocalCourseSourceFile, ...]:
    """Resolve ready local Markdown sources without allowing repository escape."""

    repository_root = root.resolve()
    files: list[LocalCourseSourceFile] = []
    seen_paths: set[str] = set()
    seen_resolved_paths: set[str] = set()
    seen_file_identities: set[tuple[int, int]] = set()
    indexed_file_count = 0
    total_existing_bytes = 0
    for source in normalize_course_sources(design, default_files=default_files):
        if source.provider != "local" or source.indexing_status != "ready":
            continue
        for declared_file in source.files:
            indexed_file_count += 1
            if indexed_file_count > MAX_INDEXED_LOCAL_FILES:
                raise CourseSourceCatalogError(
                    "Troppi file Markdown locali pronti per l'indicizzazione."
                )
            relative_path = _join_source_path(source.path, declared_file)
            if relative_path in seen_paths:
                raise CourseSourceCatalogError(
                    f"File fonte locale duplicato: {relative_path}."
                )
            seen_paths.add(relative_path)
            try:
                resolved = (repository_root / Path(relative_path)).resolve()
                metadata = resolved.stat() if resolved.exists() else None
            except OSError as exc:
                raise CourseSourceCatalogError(
                    f"File fonte locale non verificabile: {relative_path}."
                ) from exc
            try:
                resolved.relative_to(repository_root)
            except ValueError as exc:
                raise CourseSourceCatalogError(
                    f"File fonte fuori dal repository: {relative_path}."
                ) from exc
            if metadata is not None and not stat.S_ISREG(metadata.st_mode):
                raise CourseSourceCatalogError(
                    f"La fonte locale non è un file regolare: {relative_path}."
                )
            if metadata is not None:
                if metadata.st_size > MAX_LOCAL_MARKDOWN_BYTES:
                    raise CourseSourceCatalogError(
                        f"File fonte locale troppo grande: {relative_path}."
                    )
                total_existing_bytes += metadata.st_size
                if total_existing_bytes > MAX_TOTAL_LOCAL_MARKDOWN_BYTES:
                    raise CourseSourceCatalogError(
                        "Le fonti Markdown locali superano il limite complessivo."
                    )
            if existing_only and metadata is None:
                continue
            resolved_key = os.path.normcase(str(resolved))
            if resolved_key in seen_resolved_paths:
                raise CourseSourceCatalogError(
                    f"File fonte locale duplicato dopo la risoluzione: {relative_path}."
                )
            seen_resolved_paths.add(resolved_key)
            if metadata is not None:
                identity = (metadata.st_dev, metadata.st_ino)
                if metadata.st_ino and identity in seen_file_identities:
                    raise CourseSourceCatalogError(
                        f"File fonte locale duplicato dopo la risoluzione: {relative_path}."
                    )
                if metadata.st_ino:
                    seen_file_identities.add(identity)
            files.append(
                LocalCourseSourceFile(
                    source=source,
                    relative_path=relative_path,
                    resolved_path=resolved,
                    expected_size=None if metadata is None else metadata.st_size,
                    expected_identity=(
                        None
                        if metadata is None
                        else (metadata.st_dev, metadata.st_ino)
                    ),
                    expected_mtime_ns=(
                        None if metadata is None else metadata.st_mtime_ns
                    ),
                    expected_ctime_ns=(
                        None if metadata is None else metadata.st_ctime_ns
                    ),
                )
            )
    return tuple(files)


def read_local_markdown_text(item: LocalCourseSourceFile, root: Path) -> str:
    """Read one source through an opened handle verified against the repository."""

    repository_root = root.resolve()
    try:
        with item.resolved_path.open("rb") as stream:
            opened_path = _opened_file_path(stream.fileno()).resolve()
            try:
                opened_path.relative_to(repository_root)
            except ValueError as exc:
                raise CourseSourceCatalogError(
                    f"File fonte fuori dal repository: {item.relative_path}."
                ) from exc
            expected_key = os.path.normcase(str(item.resolved_path))
            opened_key = os.path.normcase(str(opened_path))
            if opened_key != expected_key:
                raise CourseSourceCatalogError(
                    f"File fonte locale cambiato durante la lettura: {item.relative_path}."
                )
            metadata = os.fstat(stream.fileno())
            opened_identity = (metadata.st_dev, metadata.st_ino)
            if (
                item.expected_size is None
                or item.expected_identity is None
                or item.expected_mtime_ns is None
                or item.expected_ctime_ns is None
                or metadata.st_size != item.expected_size
                or opened_identity != item.expected_identity
                or metadata.st_mtime_ns != item.expected_mtime_ns
                or metadata.st_ctime_ns != item.expected_ctime_ns
            ):
                raise CourseSourceCatalogError(
                    f"File fonte locale cambiato durante la lettura: {item.relative_path}."
                )
            if not stat.S_ISREG(metadata.st_mode):
                raise CourseSourceCatalogError(
                    f"La fonte locale non è un file regolare: {item.relative_path}."
                )
            if metadata.st_size > MAX_LOCAL_MARKDOWN_BYTES:
                raise CourseSourceCatalogError(
                    f"File fonte locale troppo grande: {item.relative_path}."
                )
            payload = stream.read(MAX_LOCAL_MARKDOWN_BYTES + 1)
            stream.seek(0)
            confirmation = stream.read(MAX_LOCAL_MARKDOWN_BYTES + 1)
            final_metadata = os.fstat(stream.fileno())
            if (
                payload != confirmation
                or final_metadata.st_size != metadata.st_size
                or final_metadata.st_mtime_ns != metadata.st_mtime_ns
                or final_metadata.st_ctime_ns != metadata.st_ctime_ns
                or (final_metadata.st_dev, final_metadata.st_ino) != opened_identity
            ):
                raise CourseSourceCatalogError(
                    f"File fonte locale cambiato durante la lettura: {item.relative_path}."
                )
    except OSError as exc:
        raise CourseSourceCatalogError(
            f"File fonte locale non leggibile: {item.relative_path}."
        ) from exc
    if len(payload) > MAX_LOCAL_MARKDOWN_BYTES:
        raise CourseSourceCatalogError(
            f"File fonte locale troppo grande: {item.relative_path}."
        )
    return payload.decode("utf-8", errors="replace")


def course_source_catalog_payload(
    design: dict[str, Any],
    root: Path,
    *,
    default_files: Iterable[str] = (),
) -> dict[str, Any]:
    """Build the bounded public payload consumed by the Course Board."""

    sources = normalize_course_sources(design, default_files=default_files)
    indexed_by_id: dict[str, list[str]] = {source.source_id: [] for source in sources}
    for item in local_markdown_source_files(
        design,
        root,
        default_files=default_files,
    ):
        indexed_by_id[item.source.source_id].append(item.relative_path)
    return {
        "sources": [
            {
                **source.as_dict(),
                "indexed_files": indexed_by_id[source.source_id],
            }
            for source in sources
        ]
    }


def _legacy_sources(raw_files: Any) -> tuple[CourseSource, ...]:
    if not isinstance(raw_files, (list, tuple)):
        raise CourseSourceCatalogError("source_files deve essere un array.")
    if len(raw_files) > MAX_SOURCES:
        raise CourseSourceCatalogError("Troppi file sorgente legacy.")
    sources: list[CourseSource] = []
    seen_files: set[str] = set()
    for index, raw_file in enumerate(raw_files):
        relative = _relative_markdown_path(raw_file, f"source_files[{index}]")
        if relative in seen_files:
            raise CourseSourceCatalogError(f"File fonte locale duplicato: {relative}.")
        seen_files.add(relative)
        digest = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:16]
        sources.append(
            CourseSource(
                source_id=f"legacy-{digest}",
                label=relative,
                source_type="markdown",
                provider="local",
                path="",
                repository=None,
                ref=None,
                files=(relative,),
                updated_at=None,
                indexing_status="ready",
                legacy=True,
            )
        )
    return tuple(sources)


def _normalize_source(raw: Any, index: int) -> CourseSource:
    field = f"sources[{index}]"
    if not isinstance(raw, dict):
        raise CourseSourceCatalogError(f"{field} deve essere un oggetto.")
    allowed = {
        "id",
        "label",
        "type",
        "provider",
        "path",
        "repository",
        "ref",
        "files",
        "updated_at",
        "indexing_status",
    }
    unexpected = set(raw) - allowed
    if unexpected:
        raise CourseSourceCatalogError(
            f"Campi fonte non supportati in {field}: {', '.join(sorted(unexpected))}."
        )

    source_id = _text(raw.get("id"), f"{field}.id", required=True)
    if SOURCE_ID_RE.fullmatch(source_id) is None:
        raise CourseSourceCatalogError(f"{field}.id non valido.")
    label = _text(raw.get("label") or source_id, f"{field}.label", required=True)
    source_type = _text(raw.get("type"), f"{field}.type", required=True)
    if source_type not in ALLOWED_TYPES:
        raise CourseSourceCatalogError(f"{field}.type non supportato.")
    provider = _text(raw.get("provider"), f"{field}.provider", required=True)
    if provider not in ALLOWED_PROVIDERS:
        raise CourseSourceCatalogError(f"{field}.provider non supportato.")
    status = _text(
        raw.get("indexing_status"),
        f"{field}.indexing_status",
        required=True,
    )
    if status not in ALLOWED_INDEXING_STATUSES:
        raise CourseSourceCatalogError(f"{field}.indexing_status non valido.")

    files = _source_files(raw.get("files"), field)
    path = _optional_text(raw.get("path"), f"{field}.path") or ""
    repository = _optional_text(raw.get("repository"), f"{field}.repository")
    ref = _optional_text(raw.get("ref"), f"{field}.ref")
    updated_at = _optional_text(raw.get("updated_at"), f"{field}.updated_at")
    if updated_at is not None:
        _validate_utc_timestamp(updated_at, f"{field}.updated_at")

    if provider == "local":
        if repository is not None or ref is not None:
            raise CourseSourceCatalogError(
                f"{field}: una fonte locale non accetta repository o ref."
            )
        path = _relative_directory(path, f"{field}.path") if path else ""
    else:
        if path:
            raise CourseSourceCatalogError(
                f"{field}: una fonte remota non accetta path locale."
            )
        if repository is None or ref is None:
            raise CourseSourceCatalogError(
                f"{field}: repository e ref sono obbligatori per fonti remote."
            )
        repository_re = (
            GITHUB_REPOSITORY_RE if provider == "github" else GITLAB_REPOSITORY_RE
        )
        repository_parts = repository.split("/")
        if (
            repository_re.fullmatch(repository) is None
            or any(part in {".", ".."} for part in repository_parts)
        ):
            raise CourseSourceCatalogError(f"{field}.repository non valido.")
        ref_parts = ref.split("/")
        if (
            GIT_REF_RE.fullmatch(ref) is None
            or ref == "@"
            or ".." in ref
            or "//" in ref
            or "@{" in ref
            or ref.endswith(("/", ".", ".lock"))
            or any(
                not part
                or part.startswith(".")
                or part.endswith((".", ".lock"))
                for part in ref_parts
            )
        ):
            raise CourseSourceCatalogError(f"{field}.ref non valido.")
        if status == "ready":
            raise CourseSourceCatalogError(
                f"{field}: una fonte remota non può essere ready senza adapter di indicizzazione."
            )

    return CourseSource(
        source_id=source_id,
        label=label,
        source_type=source_type,
        provider=provider,
        path=path,
        repository=repository,
        ref=ref,
        files=files,
        updated_at=updated_at,
        indexing_status=status,
    )


def _source_files(raw: Any, field: str) -> tuple[str, ...]:
    if not isinstance(raw, list) or not raw:
        raise CourseSourceCatalogError(f"{field}.files deve essere un array non vuoto.")
    if len(raw) > MAX_FILES_PER_SOURCE:
        raise CourseSourceCatalogError(f"Troppi file in {field}.files.")
    files: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(raw):
        relative = _relative_markdown_path(value, f"{field}.files[{index}]")
        if relative in seen:
            raise CourseSourceCatalogError(f"File duplicato in {field}.files: {relative}.")
        seen.add(relative)
        files.append(relative)
    return tuple(files)


def _relative_markdown_path(value: Any, field: str) -> str:
    relative = _relative_path(value, field, allow_dot=False)
    if PurePosixPath(relative).suffix.lower() not in {".md", ".markdown"}:
        raise CourseSourceCatalogError(f"{field} deve indicare un file Markdown.")
    return relative


def _relative_directory(value: Any, field: str) -> str:
    return _relative_path(value, field, allow_dot=True)


def _relative_path(value: Any, field: str, *, allow_dot: bool) -> str:
    text = _text(value, field, required=not allow_dot)
    if text == "" and allow_dot:
        return ""
    if "\\" in text:
        raise CourseSourceCatalogError(f"{field} deve usare separatori '/'.")
    path = PurePosixPath(text)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CourseSourceCatalogError(f"{field} deve essere un path relativo canonico.")
    canonical = path.as_posix()
    if canonical != text:
        raise CourseSourceCatalogError(f"{field} deve essere un path relativo canonico.")
    return canonical


def _join_source_path(directory: str, filename: str) -> str:
    return f"{directory}/{filename}" if directory else filename


def _text(value: Any, field: str, *, required: bool) -> str:
    if not isinstance(value, str):
        raise CourseSourceCatalogError(f"{field} deve essere una stringa.")
    if value != value.strip() or len(value) > MAX_TEXT or any(ord(char) < 32 for char in value):
        raise CourseSourceCatalogError(f"{field} non valido.")
    if required and not value:
        raise CourseSourceCatalogError(f"{field} obbligatorio.")
    return value


def _optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _text(value, field, required=True)


def _opened_file_path(file_descriptor: int) -> Path:
    if os.name == "nt":
        import ctypes
        import msvcrt

        handle = msvcrt.get_osfhandle(file_descriptor)
        buffer = ctypes.create_unicode_buffer(32768)
        get_final_path = ctypes.windll.kernel32.GetFinalPathNameByHandleW
        get_final_path.argtypes = [
            ctypes.c_void_p,
            ctypes.c_wchar_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
        ]
        get_final_path.restype = ctypes.c_uint32
        length = get_final_path(
            ctypes.c_void_p(handle),
            buffer,
            len(buffer),
            0,
        )
        if length == 0 or length >= len(buffer):
            raise OSError("Impossibile risolvere il file aperto.")
        value = buffer.value
        if value.startswith("\\\\?\\UNC\\"):
            value = "\\\\" + value[8:]
        elif value.startswith("\\\\?\\"):
            value = value[4:]
        return Path(value)
    if sys.platform.startswith("linux"):
        return Path(os.readlink(f"/proc/self/fd/{file_descriptor}"))
    if sys.platform == "darwin":
        import fcntl

        try:
            value = fcntl.fcntl(file_descriptor, 50, b"\0" * 1024)
        except ValueError as exc:
            raise OSError("Impossibile risolvere il file aperto.") from exc
        return Path(value.split(b"\0", 1)[0].decode("utf-8"))
    raise OSError("Piattaforma non supportata per la verifica del file aperto.")


def _validate_utc_timestamp(value: str, field: str) -> None:
    if not value.endswith("Z"):
        raise CourseSourceCatalogError(f"{field} deve essere UTC con suffisso Z.")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise CourseSourceCatalogError(f"{field} non valido.") from exc
    if parsed.isoformat(timespec="seconds").replace("+00:00", "Z") != value:
        raise CourseSourceCatalogError(f"{field} deve essere UTC canonico ai secondi.")
