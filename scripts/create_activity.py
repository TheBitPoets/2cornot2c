from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Callable

from scripts import validate_activity


DEFAULT_OUTPUT_DIR = Path("activities/drafts")

DEFAULT_CORRECTION = {
    "compila": True,
    "test": True,
    "sandbox": True,
    "ai_feedback": True,
}

DEFAULT_METRICS = {
    "tempo_stimato_minuti": 30,
    "traccia_tempo_dichiarato": True,
    "traccia_sessioni_thebitlab": True,
    "traccia_eventi_didattici": True,
    "traccia_errori_compilazione": True,
}


def slugify(value: str) -> str:
    """Convert an activity id or title into a stable filesystem-friendly slug."""
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "attivita"


def split_csv(value: str) -> list[str]:
    """Split a comma-separated input into a clean list of non-empty values."""
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_topics(value: str) -> list[str]:
    """Parse topics and fail early when no valid topic is provided."""
    topics = split_csv(value)
    if not topics:
        raise ValueError("Inserisci almeno un argomento valido.")
    return topics


def build_activity(
    *,
    activity_id: str,
    title: str,
    activity_type: str,
    difficulty: str,
    topics: list[str],
    prompt: str,
    estimated_minutes: int,
    context: dict[str, str] | None = None,
) -> dict:
    """Build a minimal activity dictionary compatible with validate_activity."""
    activity = {
        "schema_version": validate_activity.SUPPORTED_SCHEMA_VERSION,
        "id": activity_id,
        "titolo": title,
        "tipo": activity_type,
        "difficolta": difficulty,
        "argomenti": topics,
        "consegna": prompt,
        "correzione": dict(DEFAULT_CORRECTION),
        "metriche": {
            **DEFAULT_METRICS,
            "tempo_stimato_minuti": estimated_minutes,
        },
    }

    clean_context = {key: value for key, value in (context or {}).items() if value}
    if clean_context:
        activity["contesto"] = clean_context

    return activity


def output_path_for(activity: dict, output_dir: Path) -> Path:
    """Return the default output path for a generated activity."""
    return output_dir / f"{slugify(activity['id'])}.json"


def write_activity(activity: dict, output_dir: Path, *, overwrite: bool = False) -> Path:
    """Validate and write an activity JSON file."""
    errors = validate_activity.validate_activity(activity, activity["id"])
    if errors:
        raise ValueError("\n".join(errors))

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_path_for(activity, output_dir)
    if output_path.exists() and not overwrite:
        raise ValueError(f"File gia esistente: {output_path}. Usa --force per sovrascriverlo.")
    output_path.write_text(
        json.dumps(activity, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return output_path


def ask(prompt: str, *, default: str | None = None, input_fn: Callable[[str], str] = input) -> str:
    """Ask for a value, optionally showing and returning a default."""
    suffix = f" [{default}]" if default is not None else ""
    value = input_fn(f"{prompt}{suffix}: ").strip()
    if not value and default is not None:
        return default
    return value


def ask_required(prompt: str, *, input_fn: Callable[[str], str] = input) -> str:
    """Ask until a non-empty value is provided."""
    while True:
        value = ask(prompt, input_fn=input_fn)
        if value:
            return value
        print("Valore obbligatorio.")


def ask_choice(
    prompt: str,
    allowed: set[str],
    *,
    default: str,
    input_fn: Callable[[str], str] = input,
) -> str:
    """Ask until the value belongs to the allowed set."""
    while True:
        value = ask(prompt, default=default, input_fn=input_fn)
        if value in allowed:
            return value
        print(f"Valore non ammesso. Valori validi: {', '.join(sorted(allowed))}")


def ask_int(prompt: str, *, default: int, input_fn: Callable[[str], str] = input) -> int:
    """Ask until a non-negative integer is provided."""
    while True:
        value = ask(prompt, default=str(default), input_fn=input_fn)
        try:
            number = int(value)
        except ValueError:
            print("Inserisci un numero intero.")
            continue
        if number >= 0:
            return number
        print("Inserisci un numero non negativo.")


def create_interactive(input_fn: Callable[[str], str] = input) -> dict:
    """Collect fields interactively and return an activity dictionary."""
    title = ask_required("Titolo", input_fn=input_fn)
    suggested_id = slugify(title)
    activity_id = ask("ID attivita", default=suggested_id, input_fn=input_fn)
    activity_type = ask_choice(
        "Tipo attivita",
        validate_activity.ALLOWED_TYPES,
        default="compito-casa",
        input_fn=input_fn,
    )
    difficulty = ask_choice(
        "Difficolta",
        validate_activity.ALLOWED_DIFFICULTIES,
        default="B",
        input_fn=input_fn,
    )
    topics = split_csv(ask_required("Argomenti separati da virgola", input_fn=input_fn))
    prompt = ask_required("Consegna", input_fn=input_fn)
    estimated_minutes = ask_int("Tempo stimato minuti", default=30, input_fn=input_fn)

    context = {
        "classe": ask("Classe", input_fn=input_fn),
        "team_github": ask("Team GitHub", input_fn=input_fn),
        "percorso": ask("Percorso", input_fn=input_fn),
        "uda": ask("UDA", input_fn=input_fn),
    }

    return build_activity(
        activity_id=activity_id,
        title=title,
        activity_type=activity_type,
        difficulty=difficulty,
        topics=topics,
        prompt=prompt,
        estimated_minutes=estimated_minutes,
        context=context,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crea una scheda attivita TheBitLab.")
    parser.add_argument("--id", dest="activity_id", help="Identificativo stabile dell'attivita.")
    parser.add_argument("--titolo", help="Titolo leggibile dell'attivita.")
    parser.add_argument("--tipo", choices=sorted(validate_activity.ALLOWED_TYPES), help="Tipo attivita.")
    parser.add_argument("--difficolta", choices=sorted(validate_activity.ALLOWED_DIFFICULTIES), help="Difficolta A-F.")
    parser.add_argument("--argomenti", help="Argomenti separati da virgola.")
    parser.add_argument("--consegna", help="Testo della consegna.")
    parser.add_argument("--tempo-stimato", type=int, default=30, help="Tempo stimato in minuti.")
    parser.add_argument("--classe", default="", help="Classe collegata all'attivita.")
    parser.add_argument("--team-github", default="", help="Team GitHub collegato all'attivita.")
    parser.add_argument("--percorso", default="", help="Percorso didattico collegato.")
    parser.add_argument("--uda", default="", help="UDA collegata.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Cartella di output.")
    parser.add_argument("--interactive", action="store_true", help="Avvia la modalita guidata.")
    parser.add_argument("--force", action="store_true", help="Sovrascrive un file attivita gia esistente.")
    return parser.parse_args()


def activity_from_args(args: argparse.Namespace) -> dict:
    """Build an activity from CLI arguments."""
    required = {
        "--titolo": args.titolo,
        "--tipo": args.tipo,
        "--difficolta": args.difficolta,
        "--argomenti": args.argomenti,
        "--consegna": args.consegna,
    }
    missing = [flag for flag, value in required.items() if not value]
    if missing:
        raise ValueError(f"Argomenti mancanti: {', '.join(missing)}. Usa --interactive per la modalita guidata.")

    title = args.titolo
    activity_id = args.activity_id or slugify(title)

    return build_activity(
        activity_id=activity_id,
        title=title,
        activity_type=args.tipo,
        difficulty=args.difficolta,
        topics=parse_topics(args.argomenti),
        prompt=args.consegna,
        estimated_minutes=args.tempo_stimato,
        context={
            "classe": args.classe,
            "team_github": args.team_github,
            "percorso": args.percorso,
            "uda": args.uda,
        },
    )


def main() -> int:
    args = parse_args()

    try:
        activity = create_interactive() if args.interactive else activity_from_args(args)
        output_path = write_activity(activity, args.output_dir, overwrite=args.force)
    except ValueError as error:
        print(f"Creazione attivita non riuscita:\n{error}")
        return 1

    print(f"Attivita creata: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
