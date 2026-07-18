#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Installa la configurazione globale Codex su Linux/macOS.

Uso:
  scripts/install_codex_system_config.sh [--codex-home PATH] [--template PATH] [--agents-template PATH] [--overwrite] [--dry-run]

Default:
  --codex-home        $HOME/.codex
  --template          config/codex/codex-system.config.toml
  --agents-template   config/codex/AGENTS.md

Opzioni:
  --overwrite         Sovrascrive completamente config.toml con il template minimo.
  --dry-run           Mostra cosa farebbe senza scrivere.
  -h, --help          Mostra questa guida.
EOF
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
codex_home="${HOME}/.codex"
template_path="$repo_root/config/codex/codex-system.config.toml"
agents_template_path="$repo_root/config/codex/AGENTS.md"
overwrite=false
dry_run=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --codex-home)
      codex_home="${2:?Manca il valore per --codex-home}"
      shift 2
      ;;
    --template)
      template_path="${2:?Manca il valore per --template}"
      shift 2
      ;;
    --agents-template)
      agents_template_path="${2:?Manca il valore per --agents-template}"
      shift 2
      ;;
    --overwrite)
      overwrite=true
      shift
      ;;
    --dry-run)
      dry_run=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Opzione non riconosciuta: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -f "$template_path" ]]; then
  echo "Template TOML non trovato: $template_path" >&2
  exit 1
fi
if [[ ! -f "$agents_template_path" ]]; then
  echo "Template AGENTS.md non trovato: $agents_template_path" >&2
  exit 1
fi

config_path="$codex_home/config.toml"
agents_path="$codex_home/AGENTS.md"

backup_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    return 0
  fi
  local backup="${path}.bak-$(date +%Y%m%d-%H%M%S)"
  cp "$path" "$backup"
  echo "$backup"
}

render_merged_config() {
  local current="$1"
  local template="$2"
  python - "$current" "$template" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

current_path = Path(sys.argv[1])
template_path = Path(sys.argv[2])
current = current_path.read_text(encoding="utf-8") if current_path.exists() else ""
template = template_path.read_text(encoding="utf-8")


def top_level_value(text: str, key: str) -> str | None:
    match = re.search(rf'^{re.escape(key)}\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    return match.group(1) if match else None


def set_or_add_top_level(text: str, key: str, value: str) -> str:
    line = f'{key} = "{value}"'
    pattern = rf'^{re.escape(key)}\s*=\s*"[^"]*"'
    if re.search(pattern, text, flags=re.MULTILINE):
        return re.sub(pattern, line, text, flags=re.MULTILINE)
    return line + "\n" + text


def section(text: str, name: str) -> str | None:
    match = re.search(rf'^\[{re.escape(name)}\]\s*.*?(?=^\[[^\]]+\]\s*|\Z)', text, flags=re.MULTILINE | re.DOTALL)
    return match.group(0).strip() if match else None


result = current
for key in ("model", "model_reasoning_effort", "service_tier"):
    value = top_level_value(template, key)
    if value is not None:
        result = set_or_add_top_level(result, key, value)

agents = section(template, "agents")
if agents:
    result = re.sub(r'^\[agents\]\s*.*?(?=^\[[^\]]+\]\s*|\Z)', "", result, flags=re.MULTILINE | re.DOTALL).rstrip()
    result = result + "\n\n" + agents + "\n"

sys.stdout.write(result)
PY
}

echo "Codex home: $codex_home"
echo "Template TOML: $template_path"
echo "Template AGENTS.md: $agents_template_path"

if [[ "$dry_run" == true ]]; then
  echo "Dry run: nessun file verra scritto."
  if [[ -f "$config_path" && "$overwrite" != true ]]; then
    echo "Merge previsto su: $config_path"
  else
    echo "Scrittura prevista: $config_path"
  fi
  echo "Scrittura prevista: $agents_path"
  exit 0
fi

mkdir -p "$codex_home"

config_backup="$(backup_file "$config_path" || true)"
if [[ "$overwrite" == true || ! -f "$config_path" ]]; then
  cp "$template_path" "$config_path"
else
  tmp_config="$(mktemp)"
  render_merged_config "$config_path" "$template_path" > "$tmp_config"
  mv "$tmp_config" "$config_path"
fi

agents_backup="$(backup_file "$agents_path" || true)"
cp "$agents_template_path" "$agents_path"

echo "Configurazione Codex installata in: $codex_home"
if [[ -n "$config_backup" ]]; then
  echo "Backup config.toml: $config_backup"
fi
if [[ -n "$agents_backup" ]]; then
  echo "Backup AGENTS.md: $agents_backup"
fi
echo "Riavvia VS Code, Codex CLI o ChatGPT desktop per caricare le nuove impostazioni."
