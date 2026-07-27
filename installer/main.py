"""Entry point iniziale dell'installer; uTUI verrà collegata sopra questo core."""

from __future__ import annotations

import argparse

from installer.diagnostics import diagnose
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
    return result


def main(argv: list[str] | None = None) -> int:
    """Mostra una diagnosi sicura e il piano ancora da applicare."""

    args = parser().parse_args(argv)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
