from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

try:
    from scripts.build_assignment_runner import (
        DIGEST_RE,
        IMAGE_REPOSITORY,
        SCHEMA_VERSION,
        SHA_RE,
        VERSION_RE,
    )
except ModuleNotFoundError:
    from build_assignment_runner import (
        DIGEST_RE,
        IMAGE_REPOSITORY,
        SCHEMA_VERSION,
        SHA_RE,
        VERSION_RE,
    )


MISSING_MANIFEST_MARKERS = (
    "manifest unknown",
    "no such manifest",
    "not found",
)


class ToolchainPublishError(RuntimeError):
    """Raised when an immutable toolchain release cannot be published safely."""


def load_build_metadata(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ToolchainPublishError(f"Metadata build non leggibili: {path}.") from error
    if not isinstance(payload, dict):
        raise ToolchainPublishError("Metadata build non valide.")
    checks = (
        payload.get("schema_version") == SCHEMA_VERSION,
        payload.get("image_repository") == IMAGE_REPOSITORY,
        isinstance(payload.get("version"), str)
        and VERSION_RE.fullmatch(payload["version"]) is not None,
        isinstance(payload.get("source_revision"), str)
        and SHA_RE.fullmatch(payload["source_revision"]) is not None,
        isinstance(payload.get("local_image_id"), str)
        and DIGEST_RE.fullmatch(payload["local_image_id"]) is not None,
        isinstance(payload.get("local_tag"), str)
        and bool(payload["local_tag"].strip()),
    )
    if not all(checks):
        raise ToolchainPublishError("Metadata build incomplete o non autorizzate.")
    return payload


def _run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if check and result.returncode != 0:
        sys.stderr.write(
            f"Comando non riuscito ({result.returncode}): {' '.join(command)}\n"
        )
        if result.stdout.strip():
            sys.stderr.write(f"stdout: {result.stdout.strip()}\n")
        if result.stderr.strip():
            sys.stderr.write(f"stderr: {result.stderr.strip()}\n")
        raise subprocess.CalledProcessError(
            result.returncode,
            command,
            output=result.stdout,
            stderr=result.stderr,
        )
    return result


def manifest_exists(reference: str) -> bool:
    result = _run(["docker", "manifest", "inspect", reference], check=False)
    if result.returncode == 0:
        return True
    details = f"{result.stdout}\n{result.stderr}".lower()
    if any(marker in details for marker in MISSING_MANIFEST_MARKERS):
        return False
    raise ToolchainPublishError(
        f"Impossibile verificare il tag remoto {reference}: "
        f"{result.stderr.strip() or result.stdout.strip()}."
    )


def remote_image_id(reference: str) -> str:
    _run(["docker", "pull", reference])
    inspected = _run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", reference]
    ).stdout.strip()
    if not DIGEST_RE.fullmatch(inspected):
        raise ToolchainPublishError(f"Image ID remoto non valido per {reference}.")
    return inspected


def remote_manifest_digest(reference: str) -> str:
    result = _run(["docker", "manifest", "inspect", "--verbose", reference])
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ToolchainPublishError(
            f"Manifest remoto non valido per {reference}."
        ) from error
    descriptor = payload.get("Descriptor") if isinstance(payload, dict) else None
    digest = descriptor.get("digest") if isinstance(descriptor, dict) else None
    if not isinstance(digest, str) or not DIGEST_RE.fullmatch(digest):
        raise ToolchainPublishError(f"Digest remoto non valido per {reference}.")
    return digest


def ensure_reference(
    *,
    reference: str,
    local_tag: str,
    local_image_id: str,
) -> str:
    if manifest_exists(reference):
        if remote_image_id(reference) != local_image_id:
            raise ToolchainPublishError(
                f"Il tag immutabile {reference} esiste con contenuto diverso."
            )
    else:
        _run(["docker", "tag", local_tag, reference])
        _run(["docker", "push", reference])
        if remote_image_id(reference) != local_image_id:
            raise ToolchainPublishError(
                f"Il tag appena pubblicato {reference} non corrisponde alla build locale."
            )
    return remote_manifest_digest(reference)


def publish(
    *,
    metadata_path: Path,
    release_path: Path,
    github_output_path: Path | None,
) -> dict[str, Any]:
    metadata = load_build_metadata(metadata_path)
    repository = metadata["image_repository"]
    version_reference = f"{repository}:{metadata['version']}"
    commit_reference = f"{repository}:sha-{metadata['source_revision']}"

    commit_digest = ensure_reference(
        reference=commit_reference,
        local_tag=metadata["local_tag"],
        local_image_id=metadata["local_image_id"],
    )
    version_digest = ensure_reference(
        reference=version_reference,
        local_tag=metadata["local_tag"],
        local_image_id=metadata["local_image_id"],
    )
    if version_digest != commit_digest:
        raise ToolchainPublishError(
            "I tag versione e commit non indicano lo stesso manifest immutabile."
        )

    release = dict(metadata)
    release.update(
        {
            "published_image": repository,
            "published_digest": version_digest,
            "immutable_reference": f"{repository}@{version_digest}",
            "version_reference": version_reference,
            "commit_reference": commit_reference,
        }
    )
    release_path.parent.mkdir(parents=True, exist_ok=True)
    release_path.write_text(
        json.dumps(release, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if github_output_path is not None:
        with github_output_path.open("a", encoding="utf-8", newline="\n") as output:
            output.write(f"version={metadata['version']}\n")
            output.write(f"image={repository}\n")
            output.write(f"digest={version_digest}\n")
    return release


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pubblica senza sovrascritture una toolchain grading validata."
    )
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        release = publish(
            metadata_path=args.metadata,
            release_path=args.release,
            github_output_path=args.github_output,
        )
    except (OSError, subprocess.CalledProcessError, ToolchainPublishError) as error:
        print(f"Pubblicazione runner non riuscita: {error}")
        return 1
    print(f"Runner pubblicato come {release['immutable_reference']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
