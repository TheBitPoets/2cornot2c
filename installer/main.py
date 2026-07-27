"""Entry point iniziale dell'installer; uTUI verrà collegata sopra questo core."""

from __future__ import annotations

import argparse
from pathlib import Path

from installer.diagnostics import diagnose
from installer.executor import execute_plan
from installer.model import Provider
from installer.platforms import detect_host
from installer.plans import install_plan, supported_providers


def parser() -> argparse.ArgumentParser:
    """Crea il parser CLI usato anche dal futuro bootstrap."""

    result = argparse.ArgumentParser(description="Prepara l'ambiente 2cornot2c")
    result.add_argument(
        "--provider",
        choices=[provider.value for provider in Provider],
        help="provider desiderato; se omesso usa quello raccomandato",
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
    return result


def main(argv: list[str] | None = None) -> int:
    """Mostra una diagnosi sicura e il piano ancora da applicare."""

    args = parser().parse_args(argv)
    if args.yes and not args.apply:
        parser().error("--yes richiede --apply")
    host = detect_host()
    providers = supported_providers(host)
    provider = Provider(args.provider) if args.provider else providers[0]
    plan = install_plan(host, provider)

    print(f"Host: {host.value}")
    print(f"Provider: {provider.value}")
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
    if any(result.status in {"failed", "blocked"} for result in applied):
        print(f"\nInstallazione incompleta. Log: {args.log}")
        return 1
    print(f"\nInstallazione completata. Log: {args.log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
