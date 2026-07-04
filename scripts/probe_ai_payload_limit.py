#!/usr/bin/env python3
"""Probe practical AI payload limits for OpenAI-compatible providers.

The Course Design Board sends didactic-frame requests to providers such as
Groq and OpenRouter. Some free or low-cost models reject large requests because
of context limits, token-per-minute limits, or provider-specific quotas.

This script sends small JSON-only chat-completion requests with an increasingly
large `target_topic.text` field and reports a safe value for:

- GROQ_COMPACT_TEXT_CHARS
- OPENROUTER_COMPACT_TEXT_CHARS

The result is empirical: provider limits can change by model, account, time,
and requests already sent in the current minute.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECRET_PATH = ROOT / ".secrets" / "ai.secret"

PROVIDERS = {
    "gemini": {
        "label": "Gemini",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        "secret_key": "GEMINI_API_KEY",
        "model_key": "GEMINI_MODEL",
        "default_model": "gemini-3-flash-preview",
    },
    "groq": {
        "label": "Groq",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "secret_key": "GROQ_API_KEY",
        "model_key": "GROQ_MODEL",
        "default_model": "llama-3.3-70b-versatile",
    },
    "openrouter": {
        "label": "OpenRouter",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "secret_key": "OPENROUTER_API_KEY",
        "model_key": "OPENROUTER_MODEL",
        "default_model": "openrouter/free",
    },
}


def read_secret_env() -> dict[str, str]:
    """Read local key-value pairs from .secrets/ai.secret."""

    values: dict[str, str] = {}
    if not SECRET_PATH.is_file():
        return values
    for line in SECRET_PATH.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def secret_value(key: str) -> str:
    """Return a value from the environment first, then .secrets/ai.secret."""

    return os.environ.get(key, "") or read_secret_env().get(key, "")


def build_payload(text_chars: int) -> dict:
    """Build a didactic-frame-like payload with controlled text size."""

    repeated_text = (
        "Questo e un testo didattico sintetico usato solo per misurare il limite "
        "pratico del payload. "
    )
    target_text = (repeated_text * ((text_chars // len(repeated_text)) + 1))[:text_chars]
    return {
        "course": {
            "years": [
                {
                    "title": "Terzo anno TPSI",
                    "description": "C base e intermedio",
                    "udas": [
                        {
                            "title": "UDA di prova",
                            "path": "Base",
                            "weeks": "1-3",
                        }
                    ],
                }
            ]
        },
        "target": {
            "year": {"title": "Terzo anno TPSI"},
            "uda": {"title": "UDA di prova", "path": "Base", "weeks": "1-3"},
            "position": {"index": 1, "total": 3},
            "previous_topics": [
                {"title": "Variabili", "source": "README.md", "level": 2},
                {"title": "Operatori", "source": "README.md", "level": 2},
            ],
            "target_topic": {
                "title": "Puntatori",
                "source": "README.md",
                "level": 2,
                "href": "README.md#puntatori",
                "text": target_text,
                "children": [
                    {"title": "Indirizzi", "source": "README.md", "level": 3},
                    {"title": "Dereferenziazione", "source": "README.md", "level": 3},
                ],
            },
            "next_topics": [
                {"title": "Array", "source": "README.md", "level": 2},
                {"title": "Stringhe", "source": "README.md", "level": 2},
            ],
        },
        "context_mode": "probe",
    }


def parse_json_object(text: str) -> dict:
    """Parse JSON even when the provider wraps it in markdown fences."""

    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end + 1]
    return json.loads(text)


def call_provider(provider_id: str, model: str, api_key: str, text_chars: int, timeout: int) -> tuple[bool, str, int]:
    """Send one probe request and return success, detail, and request bytes."""

    if provider_id == "gemini":
        return call_gemini_provider(model, api_key, text_chars, timeout)
    return call_chat_completions_provider(provider_id, model, api_key, text_chars, timeout)


def call_chat_completions_provider(provider_id: str, model: str, api_key: str, text_chars: int, timeout: int) -> tuple[bool, str, int]:
    """Send one probe request to an OpenAI-compatible provider."""

    provider = PROVIDERS[provider_id]
    payload = build_payload(text_chars)
    system_prompt = (
        "Rispondi solo con JSON valido. Compila in italiano questi campi: "
        "context, prerequisites, objectives, recall, preview, next_step, references."
    )
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 700,
    }
    encoded = json.dumps(body).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "2cornot2c-course-board/1.0",
        "Connection": "close",
    }
    if provider_id == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/TheBitPoets/2cornot2c"
        headers["X-Title"] = "2cornot2c Course Design Board"
    request = urllib.request.Request(provider["url"], data=encoded, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        parse_json_object(data["choices"][0]["message"]["content"])
        return True, "ok", len(encoded)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        return False, f"HTTP {error.code}: {detail}", len(encoded)
    except Exception as error:  # noqa: BLE001 - this is a diagnostic CLI.
        return False, f"{type(error).__name__}: {error}", len(encoded)


def call_gemini_provider(model: str, api_key: str, text_chars: int, timeout: int) -> tuple[bool, str, int]:
    """Send one probe request to Gemini."""

    payload = build_payload(text_chars)
    body = {
        "systemInstruction": {
            "parts": [
                {
                    "text": (
                        "Rispondi solo con JSON valido. Compila in italiano questi campi: "
                        "context, prerequisites, objectives, recall, preview, next_step, references."
                    )
                }
            ],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": json.dumps(payload, ensure_ascii=False, indent=2)}],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens": 900,
        },
    }
    encoded = json.dumps(body).encode("utf-8")
    url = PROVIDERS["gemini"]["url"].format(model=model, api_key=api_key)
    request = urllib.request.Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        parse_json_object(data["candidates"][0]["content"]["parts"][0]["text"])
        return True, "ok", len(encoded)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        return False, f"HTTP {error.code}: {detail}", len(encoded)
    except Exception as error:  # noqa: BLE001 - this is a diagnostic CLI.
        return False, f"{type(error).__name__}: {error}", len(encoded)


def main() -> int:
    """Run a bounded binary search for the practical provider payload limit."""

    parser = argparse.ArgumentParser(description="Probe AI payload limits for Course Design Board providers.")
    parser.add_argument("--provider", choices=sorted(PROVIDERS), required=True)
    parser.add_argument("--model", default="", help="Model id. Defaults to provider env/config default.")
    parser.add_argument("--min-chars", type=int, default=500)
    parser.add_argument("--max-chars", type=int, default=8000)
    parser.add_argument("--safety", type=float, default=0.8, help="Safety factor for the recommended value.")
    parser.add_argument("--sleep", type=float, default=2.0, help="Seconds between requests to reduce rate-limit noise.")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    provider = PROVIDERS[args.provider]
    api_key = secret_value(provider["secret_key"])
    if not api_key:
        print(f"Errore: manca {provider['secret_key']} in ambiente o in .secrets/ai.secret.", file=sys.stderr)
        return 2

    model = args.model or secret_value(provider["model_key"]) or provider["default_model"]
    low = max(0, args.min_chars)
    high = max(low, args.max_chars)
    best = 0
    best_bytes = 0
    last_error = ""

    print(f"Provider: {provider['label']}")
    print(f"Modello: {model}")
    print(f"Ricerca: {low}..{high} caratteri di testo target")
    print("Nota: se il provider ha un limite TPM, attendi 60 secondi prima di ripetere il probe.\n")

    while low <= high:
        mid = (low + high) // 2
        ok, detail, request_bytes = call_provider(args.provider, model, api_key, mid, args.timeout)
        status = "OK" if ok else "FAIL"
        print(f"{status} text_chars={mid} request_bytes={request_bytes}")
        if ok:
            best = mid
            best_bytes = request_bytes
            low = mid + 1
        else:
            last_error = detail
            high = mid - 1
            print(f"  dettaglio: {detail[:500]}")
        if low <= high and args.sleep > 0:
            time.sleep(args.sleep)

    recommended = int(best * args.safety)
    env_name = f"{args.provider.upper()}_COMPACT_TEXT_CHARS"
    print("\nRisultato")
    print(f"- massimo riuscito: {best} caratteri target ({best_bytes} byte circa di richiesta)")
    print(f"- valore consigliato con safety {args.safety:.2f}: {recommended}")
    print(f"- variabile da impostare: {env_name}={recommended}")
    if last_error:
        print(f"- ultimo errore osservato: {last_error[:500]}")
    return 0 if best else 1


if __name__ == "__main__":
    raise SystemExit(main())
