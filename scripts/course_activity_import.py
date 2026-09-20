"""Preview and atomically import selected activities from public GitHub courses.

This is an activity importer, not a course-bundle loader. Remote code is never
executed. Only declared assets are acquired; source references stay metadata.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import tempfile
import threading
import time
from urllib.parse import quote, urlsplit

from scripts import course_github_markdown as github
from scripts import create_submission_scaffold as scaffold
from scripts import thebitlab_storage as storage

MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_BATCH_BYTES = 32 * 1024 * 1024
MAX_FILES = 256
MAX_SELECTION = 10
MAX_CANDIDATES = 500
MAX_TREE_ENTRIES = 20000
PREVIEW_TTL = 600
MAX_PREVIEWS = 4
MAX_PREVIEW_BYTES = 64 * 1024 * 1024
NETWORK_TIMEOUT = 90
SHA = re.compile(r"^[0-9a-f]{40}$")
_BLOBS = github.InMemoryGitHubBlobCache()
_PREVIEWS: dict[str, dict] = {}
_LOCK = threading.Lock()
_SLOTS = threading.BoundedSemaphore(2)


class ImportConflict(ValueError):
    """The preview expired or an activity already exists."""


def repository_name(value: str) -> str:
    if not isinstance(value, str) or len(value) > 250:
        raise ValueError("Indica un repository GitHub pubblico.")
    value = value.strip()
    if value.startswith("https://"):
        url = urlsplit(value)
        if url.netloc != "github.com" or url.query or url.fragment:
            raise ValueError("Usa un URL https://github.com/organizzazione/repository.")
        value = url.path.removeprefix("/").removesuffix("/")
    value = value.removesuffix(".git")
    parts = value.split("/")
    if len(parts) != 2 or any(
        not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", part)
        or part.endswith(".") for part in parts
    ):
        raise ValueError("Repository GitHub non valido.")
    return value


def safe_path(value: str) -> str:
    if not isinstance(value, str) or len(value) > 500:
        raise ValueError("Percorso del corso non valido.")
    result = scaffold.validate_relative_path(value, "Percorso del corso").as_posix()
    if any(part.casefold() == ".git" for part in PurePosixPath(result).parts):
        raise ValueError("Metadati Git non importabili.")
    return result


def _json(content: bytes) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Chiavi JSON duplicate nell'activity.")
            result[key] = value
        return result
    try:
        result = json.loads(content.decode("utf-8-sig"), object_pairs_hook=pairs,
                            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("JSON non finito.")))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("JSON activity non valido.") from error
    if not isinstance(result, dict):
        raise ValueError("L'activity deve essere un oggetto JSON.")
    return result


def _bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


class CourseSource:
    def __init__(self, repository, ref, transport=None):
        self.repository = repository_name(repository)
        if not isinstance(ref, str) or not re.fullmatch(r"[A-Za-z0-9_./-]{1,160}", ref):
            raise ValueError("Indica un branch, tag o commit GitHub valido.")
        self.transport = transport or github.GitHubApiTransport(None)
        self.deadline = time.monotonic() + NETWORK_TIMEOUT
        self.prefix = f"/repos/{self.repository}"
        commit = self.get(f"/commits/{quote(ref, safe='')}")
        self.commit = commit.get("sha") if isinstance(commit, dict) else None
        if not isinstance(self.commit, str) or not SHA.fullmatch(self.commit):
            raise ValueError("Revisione del corso non valida.")
        if SHA.fullmatch(ref) and self.commit != ref:
            raise ValueError("La revisione GitHub non corrisponde all'anteprima.")
        tree = self.get(f"/git/trees/{self.commit}?recursive=1")
        if (not isinstance(tree, dict) or tree.get("truncated") is not False
                or not isinstance(tree.get("tree"), list)
                or len(tree["tree"]) > MAX_TREE_ENTRIES):
            raise ValueError("Catalogo GitHub troppo grande o incompleto.")
        self.entries = {}
        for entry in tree["tree"]:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                raise ValueError("Catalogo GitHub non valido.")
            if entry["path"] in self.entries:
                raise ValueError("Percorso duplicato nel catalogo GitHub.")
            self.entries[entry["path"]] = entry
        self.used_bytes = 0
        self.used_files = set()

    def get(self, suffix):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("Tempo di importazione esaurito; seleziona meno activity.")
        return self.transport.get_json(self.prefix + suffix, timeout_seconds=remaining)

    def file(self, path):
        path = safe_path(path)
        for parent in PurePosixPath(path).parents:
            ancestor = self.entries.get(str(parent))
            if ancestor and (ancestor.get("type"), ancestor.get("mode")) != ("tree", "040000"):
                raise ValueError("Link o sottorepository non importabili.")
        entry = self.entries.get(path, {})
        oid = entry.get("sha", "")
        size = entry.get("size")
        if (entry.get("type") != "blob" or entry.get("mode") not in {"100644", "100755"}
                or not isinstance(oid, str) or not SHA.fullmatch(oid)
                or type(size) is not int or not 0 <= size <= MAX_FILE_BYTES):
            raise ValueError(f"File mancante, troppo grande o non regolare: {path}")
        if path not in self.used_files:
            self.used_files.add(path)
            self.used_bytes += size
        if len(self.used_files) > MAX_FILES or self.used_bytes > MAX_BATCH_BYTES:
            raise ValueError("Troppi file o dati: seleziona meno activity.")
        content = _BLOBS.get(oid)
        if content is None:
            content = github._decode_blob(self.get(f"/git/blobs/{oid}"), oid, path)
            _BLOBS.put(oid, content)
        if len(content) != size:
            raise ValueError("Dimensione file GitHub incoerente.")
        return content

    def candidates(self):
        result = sorted(path for path, entry in self.entries.items()
                        if path.startswith("activities/") and path.endswith(".json")
                        and "assets" not in PurePosixPath(path).parts
                        and (path.endswith("/activity.json") or len(PurePosixPath(path).parts) <= 3)
                        and entry.get("type") == "blob" and entry.get("mode") in {"100644", "100755"})
        if len(result) > MAX_CANDIDATES:
            raise ValueError("Il corso contiene troppi candidati activity.")
        return [safe_path(path) for path in result]


def catalog(repository, ref="main", *, transport=None):
    source = CourseSource(repository, ref, transport)
    return {"repository": source.repository, "commit": source.commit,
            "activities": source.candidates(), "max_selection": MAX_SELECTION}


def _activity(source, path):
    activity = _json(source.file(path))
    declarations = activity.get("assets", [])
    if not isinstance(declarations, list) or len(declarations) > MAX_FILES:
        raise ValueError("Troppi asset dichiarati nell'activity.")
    identifier = scaffold.activity_id(activity)
    if len(identifier) > 100:
        raise ValueError("ID activity troppo lungo per l'importazione.")
    normalized = scaffold.validate_activity_contract_or_raise(activity, identifier)
    language = scaffold.language_for(normalized)
    source_name = scaffold.validate_source_name(
        normalized.get("source_name") or scaffold.default_source_name_for(language))
    parent = PurePosixPath(path).parent
    adapted = copy.deepcopy(activity)
    files = {}
    assets = []
    warnings = []
    visibility = {}
    portable_sources = {}
    student_declarations = scaffold.student_assets(activity)
    for asset in declarations:
        relative = safe_path(asset["path"])
        upstream = (parent / relative).as_posix()
        entry = source.entries.get(upstream, {})
        directory = entry.get("type") == "tree" and entry.get("mode") == "040000"
        members = sorted(name for name in source.entries if name.startswith(upstream + "/")
                         and source.entries[name].get("type") != "tree") if directory else [upstream]
        if not members:
            raise ValueError(f"Directory asset vuota: {relative}")
        student = asset in student_declarations
        raw_target = asset.get("target_path", relative)
        if raw_target == "." and directory:
            target_base = PurePosixPath()
        else:
            target_base = PurePosixPath(safe_path(raw_target))
        for member in members:
            suffix = PurePosixPath(member).relative_to(upstream) if directory else None
            target = (target_base / suffix).as_posix() if suffix else str(target_base)
            if student and target == "README.md":
                target = "GUIDA.md"
                warnings.append("Guida studente rinominata README.md → GUIDA.md.")
            relative_member = PurePosixPath(member).relative_to(parent).as_posix()
            if student and any(part.casefold() in {"teacher", "solution", "solutions", "grading", "hidden_tests"}
                               for part in PurePosixPath(relative_member).parts):
                raise ValueError("Un asset studente punta a materiale docente/soluzione.")
            if member in visibility and visibility[member] != student:
                raise ValueError("Lo stesso file e dichiarato sia studente sia riservato.")
            visibility[member] = student
            local = safe_path(f"assets/{identifier}/{relative_member}")
            key = scaffold.portable_path_key(Path(local))
            for previous, previous_path in portable_sources.items():
                if (key[:len(previous)] == previous or previous[:len(key)] == key) and previous_path != local:
                    raise ValueError("Collisione portabile fra file degli asset.")
            portable_sources[key] = local
            files[local] = source.file(member)
            assets.append({**asset, "path": local, "target_path": safe_path(target)})
    adapted["assets"] = assets
    scaffold.validate_activity_contract_or_raise(adapted, identifier)
    # The real scaffold boundary checks duplicate/reserved targets and sources.
    with tempfile.TemporaryDirectory(prefix="thebitlab-import-check-") as temp:
        root = Path(temp)
        _write_files(root, files)
        asset_plan = scaffold.student_asset_copy_plan(root / f"{identifier}.json", adapted)
        scaffold.validate_student_asset_targets(asset_plan, source_name)
    files[f"{identifier}.json"] = _bytes(adapted)
    if activity.get("source_refs") or activity.get("materiali"):
        warnings.append("Riferimenti alle lezioni conservati; materiali esterni non importati.")
    correction = activity.get("correzione", {})
    if not correction.get("test"):
        warnings.append("Questa activity non prevede test automatici.")
    summary = {"id": identifier, "title": activity.get("titolo", activity.get("title", identifier)),
               "source_path": path, "language": language, "source_name": source_name,
               "student_assets": sum(asset in scaffold.student_assets(adapted) for asset in assets),
               "reserved_assets": sum(asset not in scaffold.student_assets(adapted) for asset in assets),
               "warnings": sorted(set(warnings))}
    return files, summary


def _write_files(root, files):
    for name, content in files.items():
        path = root / safe_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())


def _check_ids(root, summaries):
    catalog_storage = storage.JsonAssignmentStorage(
        root, root / "teacher-reports", [root / "activities", root / "examples" / "assignment_tracking"])
    existing = {item["id"] for item in catalog_storage.list_activities()}
    seen = set()
    for item in summaries:
        if item["id"] in existing or item["id"] in seen:
            raise ImportConflict(f"Activity gia presente o duplicata: {item['id']}. Nessun file sovrascritto.")
        seen.add(item["id"])


def _prune():
    for token in list(_PREVIEWS):
        if _PREVIEWS[token]["expires"] <= time.monotonic():
            del _PREVIEWS[token]


def preview(root: Path, repository, commit, paths, *, transport=None):
    if not isinstance(commit, str) or not SHA.fullmatch(commit):
        raise ValueError("Ricarica il catalogo per fissare la revisione del corso.")
    if (not isinstance(paths, list) or not 1 <= len(paths) <= MAX_SELECTION
            or any(not isinstance(path, str) for path in paths) or len(set(paths)) != len(paths)):
        raise ValueError(f"Seleziona da 1 a {MAX_SELECTION} activity diverse.")
    source = CourseSource(repository, commit, transport)
    candidates = set(source.candidates())
    files, summaries = {}, []
    for path in sorted(paths):
        if path not in candidates:
            raise ValueError("Activity assente dal catalogo della revisione scelta.")
        added, summary = _activity(source, path)
        summaries.append(summary)
        _check_ids(root, summaries)
        files.update(added)
    total = sum(map(len, files.values()))
    if total > MAX_BATCH_BYTES:
        raise ValueError("Import troppo grande.")
    token = secrets.token_urlsafe(32)
    with _LOCK:
        _prune()
        if len(_PREVIEWS) >= MAX_PREVIEWS or sum(p["bytes"] for p in _PREVIEWS.values()) + total > MAX_PREVIEW_BYTES:
            raise ValueError("Troppe anteprime aperte. Importa o attendi 10 minuti.")
        _PREVIEWS[token] = {"root": root.resolve(), "repository": source.repository,
                            "commit": source.commit, "files": files, "activities": summaries,
                            "bytes": total, "expires": time.monotonic() + PREVIEW_TTL}
    return {"preview_token": token, "repository": source.repository, "commit": source.commit,
            "activities": summaries, "bytes": total, "expires_in": PREVIEW_TTL}


def _safe_directory(root: Path, relative: str) -> Path:
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise ValueError("Directory import non sicura.")
        current.mkdir(exist_ok=True)
        if not current.is_dir() or not current.resolve().is_relative_to(root.resolve()):
            raise ValueError("Directory import non sicura.")
    return current


def publish(root: Path, token: str):
    if not isinstance(token, str):
        raise ImportConflict("Anteprima non valida.")
    with _LOCK:
        _prune()
        batch = _PREVIEWS.get(token)
        if batch is None or batch["root"] != root.resolve():
            raise ImportConflict("Anteprima scaduta o gia usata. Ripeti l'anteprima.")
        del _PREVIEWS[token]
    with storage.course_storage_lock(root):
        _check_ids(root, batch["activities"])
        destination_parent = _safe_directory(root, "activities/imported")
        staging_parent = _safe_directory(root, ".activity-import-staging")
        batch_id = secrets.token_hex(16)
        destination = destination_parent / batch_id
        with tempfile.TemporaryDirectory(dir=staging_parent, prefix="batch-") as temp:
            staging = Path(temp) / "content"
            staging.mkdir()
            _write_files(staging, batch["files"])
            origin = {"format": "thebitlab-activity-import/1", "repository": batch["repository"],
                      "commit": batch["commit"], "activities": batch["activities"],
                      "sha256": {name: hashlib.sha256(data).hexdigest() for name, data in batch["files"].items()}}
            _write_files(staging, {"origin.txt": _bytes(origin)})
            for folder, _, _ in os.walk(staging, topdown=False):
                storage.sync_directory(Path(folder))
            # Destination is a fresh random name; the root process lock excludes other writers.
            if destination.exists() or destination.is_symlink():
                raise ImportConflict("Destinazione import gia presente.")
            os.rename(staging, destination)
            storage.sync_directory(destination_parent)
    return {"imported": [{**item, "path": f"activities/imported/{batch_id}/{item['id']}.json"}
                         for item in batch["activities"]], "commit": batch["commit"]}


def handle(root: Path, action: str, payload: dict):
    """Bound concurrent imports independently from the HTTP worker pool."""
    fields = {"catalog": {"repository", "ref"}, "preview": {"repository", "commit", "paths"},
              "publish": {"preview_token"}, "discard": {"preview_token"}}
    if action not in fields or not isinstance(payload, dict) or set(payload) - fields[action]:
        raise ValueError("Richiesta import non valida.")
    if action == "discard":
        token = payload.get("preview_token")
        with _LOCK:
            if isinstance(token, str) and token in _PREVIEWS and _PREVIEWS[token]["root"] == root.resolve():
                del _PREVIEWS[token]
        return {"discarded": True}
    if not _SLOTS.acquire(blocking=False):
        raise ValueError("Importazione occupata. Riprova tra poco.")
    try:
        if action == "catalog":
            return catalog(payload.get("repository"), payload.get("ref", "main"))
        if action == "preview":
            return preview(root, payload.get("repository"), payload.get("commit"), payload.get("paths"))
        if action == "publish":
            return publish(root, payload.get("preview_token"))
        raise ValueError("Operazione import non valida.")
    finally:
        _SLOTS.release()
