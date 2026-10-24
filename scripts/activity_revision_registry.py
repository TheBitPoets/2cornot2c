"""Authoritative active revisions; historical paths never move or disappear.

See doc/architecture/adr-imported-activity-updates.md for the disk contract.
Callers serialize mutations with course_storage_lock. Readers take one snapshot.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from scripts import create_submission_scaffold as scaffold

REGISTRY = "activities/imported/registry.txt"
REVISIONS = "activities/imported/revisions"
FORMAT = "thebitlab-activity-revisions/1"


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(hashes):
    return digest(encoded(hashes))


def read_json(path):
    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Provenienza/registro ambiguo: chiave duplicata.")
            result[key] = value
        return result
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise ValueError("Provenienza/registro non valido.")
    return value


def safe_file(root, relative):
    relative = scaffold.validate_relative_path(relative, "Percorso revisione")
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink() or (hasattr(cursor, "is_junction") and cursor.is_junction()):
            raise ValueError("Percorso revisione non sicuro.")
    if not cursor.resolve().is_relative_to(root.resolve()):
        raise ValueError("Percorso revisione fuori dalla root.")
    return cursor


def entry(package, origin, item):
    if (not isinstance(item, dict) or not isinstance(origin.get("sha256"), dict)
            or not isinstance(origin.get("repository"), str)
            or not isinstance(item.get("source_path"), str)):
        raise ValueError("Provenienza import incompleta.")
    identifier = scaffold.activity_id(item)
    names = {name: value for name, value in origin["sha256"].items()
             if name == f"{identifier}.json" or name.startswith(f"assets/{identifier}/")}
    if f"{identifier}.json" not in names:
        raise ValueError("Provenienza incompleta: descriptor senza digest.")
    return {"id": identifier, "path": f"{package}/{identifier}.json",
            "repository": origin["repository"].casefold(), "commit": origin.get("commit"),
            "ref": origin.get("ref"), "source_path": item["source_path"],
            "sha256": names, "fingerprint": fingerprint(names)}


def _validate(root, value):
    if (not isinstance(value, dict) or value.get("format") != FORMAT
            or not all(isinstance(value.get(key), dict) for key in ("active", "history", "operations"))):
        raise ValueError("Registro revisioni non valido; ripristinare dal backup.")
    for path, item in value["history"].items():
        if (not isinstance(item, dict) or item.get("path") != path
                or not path.startswith("activities/imported/")
                or Path(path).name != f"{item.get('id')}.json"
                or not isinstance(item.get("sha256"), dict)
                or not isinstance(item.get("repository"), str)
                or not isinstance(item.get("commit"), str)
                or not re.fullmatch(r"[0-9a-f]{40}", item.get("commit", ""))):
            raise ValueError("Revisione non valida nel registro.")
        safe_file(root, path)
        for name, sha in item["sha256"].items():
            safe_file(root, (Path(path).parent / name).as_posix())
            if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha):
                raise ValueError("Digest revisione non valido.")
        if (f"{item['id']}.json" not in item["sha256"]
                or item.get("fingerprint") != fingerprint(item["sha256"])):
            raise ValueError("Digest registro incoerente.")
    for identifier, path in value["active"].items():
        if not isinstance(path, str) or path not in value["history"] or value["history"][path]["id"] != identifier:
            raise ValueError("Revisione attiva non valida.")
    return value


def read(root: Path):
    path = safe_file(root, REGISTRY)
    if path.exists():
        return _validate(root, read_json(path))
    value = {"format": FORMAT, "active": {}, "history": {}, "operations": {}}
    # Read-only v1 migration. Never discover staged v2 packages as legacy data.
    parent = safe_file(root, "activities/imported")
    if parent.exists():
        for origin_path in sorted(parent.glob("*/origin.txt")):
            if origin_path.parent.name == "revisions":
                continue
            safe_file(root, origin_path.relative_to(root).as_posix())
            origin = read_json(origin_path)
            if (origin.get("format") != "thebitlab-activity-import/1"
                    or not isinstance(origin.get("activities"), list) or not origin["activities"]):
                raise ValueError("Provenienza import non riconosciuta.")
            for item in origin["activities"]:
                revision = entry(origin_path.parent.relative_to(root).as_posix(), origin, item)
                if revision["id"] in value["active"]:
                    raise ValueError("Provenienza ambigua: ID importato piu volte.")
                value["history"][revision["path"]] = revision
                value["active"][revision["id"]] = revision["path"]
    return _validate(root, value)


def verify(root, revision):
    parent = Path(revision["path"]).parent
    for name, sha in revision["sha256"].items():
        path = safe_file(root, (parent / name).as_posix())
        if not path.is_file() or digest(path.read_bytes()) != sha:
            raise ValueError(f"Conflitto: file locale modificato o mancante: {name}")
    descriptor = json.loads(safe_file(root, revision["path"]).read_text(encoding="utf-8-sig"))
    if scaffold.activity_id(descriptor) != revision["id"]:
        raise ValueError("Conflitto: identita locale incoerente.")
    for asset in descriptor.get("assets", []):
        if asset["path"] not in revision["sha256"]:
            raise ValueError("Conflitto: asset senza digest nella provenienza.")
    return descriptor


def write(root, value):
    from scripts import thebitlab_storage as storage
    _validate(root, value)
    target = safe_file(root, REGISTRY)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=target.parent, prefix=".registry-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, target)  # The sole commit point for a whole selection.
        storage.sync_directory(target.parent)
    finally:
        Path(name).unlink(missing_ok=True)


def catalog_visible(root, path, snapshot):
    relative = path.relative_to(root).as_posix()
    if relative in snapshot["history"]:
        item = snapshot["history"][relative]
        return snapshot["active"].get(item["id"]) == relative
    return not relative.startswith(REVISIONS + "/")


def require_active(root, path):
    """New assignments may only use the concrete active revision they previewed."""
    path = path.resolve()
    # External imports belong to their own registry, not the caller's catalog.
    root = imported_root(path) or root.resolve()
    if not path.is_relative_to(root):
        return  # Ordinary external local activities have no revision registry.
    relative = path.relative_to(root).as_posix()
    snapshot = read(root)
    revision = snapshot["history"].get(relative)
    if revision:
        if snapshot["active"].get(revision["id"]) != relative:
            raise ValueError("Revisione superata: seleziona la revisione attiva e ripeti l'anteprima.")
        verify(root, revision)
    elif relative.startswith(REVISIONS + "/"):
        raise ValueError("Revisione non attivata nel catalogo.")


def imported_root(path):
    """Find the owning root after resolving filesystem aliases and Windows case."""
    for parent in path.resolve().parents:
        if parent.name == "imported" and parent.parent.name == "activities":
            return parent.parent.parent
    return None
