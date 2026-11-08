"""Entry point iniziale dell'installer; uTUI verrà collegata sopra questo core."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from installer.diagnostics import diagnose
from installer.executor import execute_plan
from installer.model import Provider
from installer.platforms import detect_host
from installer.plans import install_plan, supported_providers
from installer.resources import order_by_recommendation, total_memory_bytes
from scripts import course_environment_contract, course_environment_report


def provider_profile(provider: Provider) -> str:
    """Map one concrete installer provider to the portable course profile contract."""

    return "docker-light" if provider is Provider.DOCKER else "vm-gui"


def load_course_manifest(path: Path, *, profile: str) -> dict:
    """Load and fail closed on an invalid/incompatible course environment manifest."""

    manifest = course_environment_contract.load_manifest(path)
    errors = course_environment_contract.validate_course_environment_manifest(manifest)
    if errors:
        raise ValueError("manifest corso non valido: " + "; ".join(errors))
    supported = manifest.get("supported_profiles")
    if not isinstance(supported, list) or profile not in supported:
        raise ValueError(f"il corso non dichiara il profilo classroom {profile}")
    return manifest


def write_environment_report(
    manifest: dict,
    *,
    profile: str,
    platform_root: Path,
    course_root: Path,
    output: Path | None,
) -> dict:
    """Observe current state and optionally persist one sanitized read-only report."""

    snapshot = course_environment_report.observe_machine(
        root=platform_root,
        course_root=course_root,
    )
    report = course_environment_report.resolve_environment(
        manifest,
        profile=profile,
        snapshot=snapshot,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print("\nCourse Environment:")
    print(rendered, end="")
    return report


def parser() -> argparse.ArgumentParser:
    """Crea il parser CLI usato anche dal futuro bootstrap."""

    result = argparse.ArgumentParser(description="Prepara l'ambiente 2cornot2c")
    result.add_argument(
        "--provider",
        choices=[provider.value for provider in Provider],
        help="ambiente desiderato; se omesso usa quello raccomandato",
    )
    result.add_argument(
        "--apply",
        action="store_true",
        help="applica i passi mancanti dopo una conferma esplicita",
    )
    result.add_argument(
        "--yes",
        action="store_true",
        help="conferma non interattiva; valido soltanto insieme a --apply",
    )
    result.add_argument(
        "--log",
        type=Path,
        default=Path.home() / ".2cornot2c" / "installer.jsonl",
        help="registro append-only usato per diagnosi e supporto",
    )
    result.add_argument(
        "--course-manifest",
        type=Path,
        help=(
            "manifest thebitlab.course-environment.v1 da validare contro il provider scelto; "
            "la sola lettura non installa capability"
        ),
    )
    result.add_argument(
        "--course-root",
        type=Path,
        help="workspace reale del corso usato solo per la verifica read-only",
    )
    result.add_argument(
        "--environment-report",
        type=Path,
        help="scrive il report sanitizzato thebitlab.environment-report.v1",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    """Mostra una diagnosi sicura e il piano ancora da applicare."""

    args = parser().parse_args(argv)
    if args.yes and not args.apply:
        parser().error("--yes richiede --apply")
    if args.environment_report is not None and args.course_manifest is None:
        parser().error("--environment-report richiede --course-manifest")
    if args.course_root is not None and args.course_manifest is None:
        parser().error("--course-root richiede --course-manifest")

    host = detect_host()
    memory_bytes = total_memory_bytes(host)
    providers = order_by_recommendation(supported_providers(host), memory_bytes)
    provider = Provider(args.provider) if args.provider else providers[0]
    profile = provider_profile(provider)
    platform_root = Path(__file__).resolve().parents[1]

    manifest = None
    course_root = None
    if args.course_manifest is not None:
        try:
            manifest_path = args.course_manifest.expanduser().resolve(strict=True)
            manifest = load_course_manifest(manifest_path, profile=profile)
            course_root = (
                args.course_root.expanduser().resolve(strict=True)
                if args.course_root is not None
                else manifest_path.parent
            )
        except (OSError, ValueError) as error:
            print(f"Manifest corso non utilizzabile: {error}")
            return 2

    plan = install_plan(host, provider)

    print(f"Host: {host.value}")
    if memory_bytes is not None:
        print(f"RAM: {memory_bytes / 1024**3:.1f} GiB")
    print(f"Ambiente: {provider.value}")
    if manifest is not None:
        print(f"Profilo corso: {profile}")
        print(f"Corso: {manifest['course_id']}")
    print("\nDiagnosi:")
    results = diagnose(plan)
    for result in results:
        marker = "OK" if result.ok else "MANCA"
        print(f"[{marker:5}] {result.check.label}: {result.detail}")

    missing = {result.check.key for result in results if not result.ok}
    print("\nPiano:")
    for step in plan.steps:
        marker = "da eseguire" if step.key in missing else "già presente"
        print(f"- {step.label}: {marker}")
        if step.manual and step.key in missing and step.detail:
            print(f"  {step.detail}")

    if manifest is not None and course_root is not None:
        write_environment_report(
            manifest,
            profile=profile,
            platform_root=platform_root,
            course_root=course_root,
            output=args.environment_report,
        )

    if not args.apply:
        return 0

    if not args.yes:
        confirmation = input("\nDigita INSTALLA per applicare il piano: ")
        if confirmation != "INSTALLA":
            print("Installazione annullata senza modifiche.")
            return 2

    print("\nEsecuzione:")
    applied = execute_plan(plan, results, log_path=args.log)
    for result in applied:
        print(f"[{result.status.upper():9}] {result.label}: {result.detail}")
    if any(result.status == "restart_required" for result in applied):
        print("\nRiavvia Windows per continuare. L'installer riprenderà automaticamente.")
        return 3
    if any(result.status in {"failed", "blocked"} for result in applied):
        print(f"\nInstallazione incompleta. Log: {args.log}")
        return 1

    if manifest is not None and course_root is not None:
        write_environment_report(
            manifest,
            profile=profile,
            platform_root=platform_root,
            course_root=course_root,
            output=args.environment_report,
        )
    print(f"\nInstallazione completata. Log: {args.log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
