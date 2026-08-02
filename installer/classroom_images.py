"""Installazione end-to-end delle box Packer pubblicate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from urllib.request import urlopen

from installer.artifacts import (
    ArtifactError,
    download_box,
    load_release,
    select_artifact,
)
from installer.model import Host, Provider, VM_PROVIDERS
from installer.platforms import detect_host
from installer.vagrant_box import (
    configure_project,
    import_box,
    parse_installed_boxes,
    subprocess_runner,
)


CLASSROOM_RELEASE_VERSION = "1.0.0"
CLASSROOM_IMAGES_STATE = (
    Path(__file__).resolve().parents[1] / "packer" / "classroom-images.state"
)
OFFICIAL_MANIFEST_DIGEST = (
    Path(__file__).resolve().parents[1] / "packer" / "release-manifest.sha256"
)
OFFICIAL_MANIFEST_URL = (
    "https://github.com/TheBitPoets/2cornot2c/releases/download/"
    f"classroom-v{CLASSROOM_RELEASE_VERSION}/release-manifest.json"
)
MAX_MANIFEST_BYTES = 256 * 1024
MANIFEST_CACHE_MAX_AGE_SECONDS = 60 * 60


class ClassroomImageError(RuntimeError):
    """Errore presentabile all'utente durante la preparazione della box."""


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _read_bounded(response, maximum: int) -> bytes:
    content_length = response.headers.get("Content-Length")
    if content_length and int(content_length) > maximum:
        raise ClassroomImageError("Risposta GitHub troppo grande.")
    result = bytearray()
    while chunk := response.read(64 * 1024):
        result.extend(chunk)
        if len(result) > maximum:
            raise ClassroomImageError("Risposta GitHub troppo grande.")
    return bytes(result)


def latest_manifest_url() -> str:
    """Return the repository-pinned classroom manifest without API discovery."""

    return OFFICIAL_MANIFEST_URL


def _manifest_override() -> str | None:
    override = os.environ.get("CLASSROOM_RELEASE_MANIFEST") or None
    if (
        override is not None
        and os.environ.get("CLASSROOM_ALLOW_UNTRUSTED_MANIFEST") != "1"
    ):
        raise ClassroomImageError(
            "Override manifest non autorizzato; per sviluppo isolato impostare "
            "anche CLASSROOM_ALLOW_UNTRUSTED_MANIFEST=1."
        )
    return override


def _manifest_source() -> str:
    override = _manifest_override()
    return override if override else latest_manifest_url()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _official_manifest_digest() -> str | None:
    try:
        active = CLASSROOM_IMAGES_STATE.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise ClassroomImageError("Stato immagini classroom non leggibile.") from error
    if active == "pending":
        raise ClassroomImageError(
            "Immagini Packer non ancora attive; usare il fallback Bento."
        )
    if active != "active":
        raise ClassroomImageError(
            f"Stato immagini classroom non valido: {active!r}."
        )
    try:
        digest = OFFICIAL_MANIFEST_DIGEST.read_text(encoding="ascii").strip()
    except OSError as error:
        raise ClassroomImageError("Digest manifest classroom non leggibile.") from error
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise ClassroomImageError("Digest manifest classroom non valido.")
    return digest


def _cached_manifest_is_valid(
    path: Path,
    *,
    expected_version: str | None = None,
    expected_digest: str | None = None,
) -> bool:
    try:
        release = load_release(path)
        digest_matches = (
            expected_digest is None or _file_sha256(path) == expected_digest
        )
    except (ArtifactError, OSError):
        return False
    return (
        (expected_version is None or release.version == expected_version)
        and digest_matches
    )


def _cached_manifest_is_fresh(path: Path) -> bool:
    try:
        age = max(0.0, time.time() - path.stat().st_mtime)
    except OSError:
        return False
    return age <= MANIFEST_CACHE_MAX_AGE_SECONDS


def acquire_manifest(cache_dir: Path) -> Path:
    """Acquisisce il manifest da file locale o HTTPS con limite dimensionale."""

    override = _manifest_override()
    official_destination = cache_dir / "release-manifest.json"
    destination = (
        cache_dir / "override-release-manifest.json"
        if override is not None
        else official_destination
    )
    expected_official_digest = (
        None if override is not None else _official_manifest_digest()
    )
    cached_valid = _cached_manifest_is_valid(
        official_destination,
        expected_version=CLASSROOM_RELEASE_VERSION,
        expected_digest=expected_official_digest,
    )
    if override is None and cached_valid and _cached_manifest_is_fresh(destination):
        return destination

    try:
        source = _manifest_source()
    except ClassroomImageError:
        if override is None and cached_valid:
            return official_destination
        raise
    local = Path(source).expanduser()
    if "://" not in source:
        if not local.is_file():
            raise ClassroomImageError(f"Manifest box non trovato: {local}")
        return local

    if not source.startswith("https://"):
        raise ClassroomImageError("Il manifest remoto deve usare HTTPS.")
    cache_dir.mkdir(parents=True, exist_ok=True)
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            "wb",
            prefix=".release-manifest.",
            suffix=".part",
            dir=cache_dir,
            delete=False,
        ) as output:
            temporary_name = output.name
            with urlopen(source, timeout=30) as response:
                final_url = response.geturl()
                if not final_url.startswith("https://"):
                    raise ClassroomImageError(
                        "Il manifest è stato reindirizzato fuori da HTTPS."
                    )
                output.write(_read_bounded(response, MAX_MANIFEST_BYTES))
            output.flush()
            os.fsync(output.fileno())
        temporary = Path(temporary_name)
        downloaded_release = load_release(temporary)
        if override is None:
            if downloaded_release.version != CLASSROOM_RELEASE_VERSION:
                raise ArtifactError(
                    "Versione manifest ufficiale diversa dalla release fissata."
                )
            if (
                expected_official_digest is not None
                and _file_sha256(temporary) != expected_official_digest
            ):
                raise ArtifactError(
                    "Digest manifest ufficiale diverso dal lock revisionato."
                )
        temporary.replace(destination)
        return destination
    except (ArtifactError, ClassroomImageError, OSError, ValueError) as error:
        if override is None and cached_valid:
            return official_destination
        if isinstance(error, ClassroomImageError):
            raise
        if isinstance(error, ArtifactError):
            raise ClassroomImageError(str(error)) from error
        raise ClassroomImageError(
            f"Manifest delle box non disponibile: {error}"
        ) from error
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)


def _configured_identity(project: Path) -> tuple[str, str] | None:
    box = project / ".classroom-box"
    provider = project / ".classroom-provider"
    box_present = box.exists() or box.is_symlink()
    provider_present = provider.exists() or provider.is_symlink()
    if not box_present and not provider_present:
        return None
    if (box_present and not box.is_file()) or (
        provider_present and not provider.is_file()
    ):
        raise ClassroomImageError("Marker box Packer non valido.")
    return (
        box.read_text(encoding="utf-8").strip() if box_present else "",
        provider.read_text(encoding="utf-8").strip() if provider_present else "",
    )


def _installed_boxes() -> set[tuple[str, str]]:
    returncode, output = subprocess_runner(
        ("vagrant", "box", "list", "--machine-readable")
    )
    if returncode != 0:
        raise ClassroomImageError(output or "Impossibile interrogare Vagrant.")
    return parse_installed_boxes(output)


def _legacy_vm_exists(project: Path, provider: Provider) -> bool:
    state_dir = (
        project / ".vagrant-vmware"
        if provider is Provider.VMWARE
        else project / ".vagrant"
    )
    machines = state_dir / "machines"
    return machines.is_dir() and any(
        path.name == "id" and path.read_text(encoding="utf-8").strip()
        for path in machines.rglob("id")
    )


def _legacy_vm_providers(project: Path) -> tuple[Provider, ...]:
    """Find every legacy VM state before selecting a replacement provider."""

    return tuple(
        provider
        for provider in (Provider.VIRTUALBOX, Provider.VMWARE)
        if _legacy_vm_exists(project, provider)
    )


def resolve_artifact(host: Host, provider: Provider, cache_dir: Path):
    if provider not in VM_PROVIDERS:
        raise ClassroomImageError(f"Provider non VM: {provider.value}")
    manifest = acquire_manifest(cache_dir)
    try:
        return select_artifact(load_release(manifest), host, provider)
    except ArtifactError as error:
        raise ClassroomImageError(str(error)) from error


def check_ready(project: Path, host: Host, provider: Provider) -> str:
    cache = Path.home() / ".2cornot2c" / "images"
    artifact = resolve_artifact(host, provider, cache)
    expected = (artifact.box_name, artifact.provider.value)
    configured = _configured_identity(project)
    if configured != expected:
        raise ClassroomImageError(
            "Box Packer non configurata; esegui Installa, completa o ripara."
        )
    if expected not in _installed_boxes():
        raise ClassroomImageError("Box Packer configurata ma non presente in Vagrant.")
    return f"box Packer {artifact.box_name} pronta"


def install_image(project: Path, host: Host, provider: Provider) -> str:
    cache = Path.home() / ".2cornot2c" / "images"
    artifact = resolve_artifact(host, provider, cache)
    expected = (artifact.box_name, artifact.provider.value)
    configured = _configured_identity(project)
    if configured is not None:
        configured_box, configured_provider = configured
        if (
            configured_box not in {"", expected[0]}
            or configured_provider not in {"", expected[1]}
        ):
            raise ClassroomImageError(
                "Il progetto usa un'altra box. Avvia la migrazione esplicita "
                "prima di cambiare immagine."
            )
        if not configured_box and _legacy_vm_exists(project, provider):
            raise ClassroomImageError(
                "Stato VM ambiguo: esiste soltanto il marker provider insieme "
                "a una VM. Ripristina il marker box da una fonte verificata o "
                "richiedi assistenza; nessuna migrazione viene avviata."
            )
        # The immutable box marker identifies an interrupted Packer setup. A
        # provider-only marker is recoverable only when no VM exists yet.
        configured = expected
    legacy_providers = _legacy_vm_providers(project)
    blocking_legacy = (
        legacy_providers
        if configured is None
        else tuple(
            legacy
            for legacy in legacy_providers
            if legacy is not provider
        )
    )
    if blocking_legacy:
        commands = ", ".join(
            "`python -m installer.migration --provider "
            f"{legacy.value}`"
            for legacy in blocking_legacy
        )
        raise ClassroomImageError(
            "È presente una VM Bento legacy incompatibile. Esegui prima la "
            f"migrazione esplicita per ogni stato rilevato: {commands}; la "
            "VM non verrà sostituita automaticamente."
        )

    cache_name = f"{artifact.box_name.replace('/', '--')}.box"
    box_path = cache / cache_name
    try:
        download_box(
            artifact,
            box_path,
            opener=lambda url: urlopen(url, timeout=60),
        )
        result = import_box(artifact, box_path)
    except ArtifactError as error:
        raise ClassroomImageError(str(error)) from error
    if result.status == "failed":
        raise ClassroomImageError(result.detail)
    configure_project(project, artifact)
    return f"{artifact.box_name}: {result.detail}"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Gestisce le box Packer 2cornot2c")
    action = result.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--install", action="store_true")
    result.add_argument("--host", choices=[item.value for item in Host])
    result.add_argument(
        "--provider",
        required=True,
        choices=[item.value for item in VM_PROVIDERS],
    )
    result.add_argument("--project", type=Path, default=project_root())
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        host = Host(args.host) if args.host else detect_host()
        provider = Provider(args.provider)
        project = args.project.resolve(strict=True)
        detail = (
            check_ready(project, host, provider)
            if args.check
            else install_image(project, host, provider)
        )
    except (ClassroomImageError, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(detail)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
